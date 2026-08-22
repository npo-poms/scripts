#!/usr/bin/env python3
"""
Compare media objects in S3 against a CSV exported from the database.

The input file is expected to have columns: mid, lastModified, lastPublished
It can be CSV (comma-separated, .csv) or tab-separated (.txt/.tsv).
Generate a tab-separated export with:
  \\copy (select mid, lastmodified, lastpublished from mediaobject) to '/tmp/mids.txt'
Or CSV:
  \\copy (select mid, lastmodified, lastpublished from mediaobject) to '/tmp/mids.csv' csv header

For each row in the CSV the corresponding S3 object is fetched and the two
timestamp fields are compared.  Objects missing from S3 are reported, as are
objects present in S3 but absent from the CSV (use --no-extra to suppress the
latter).

Usage:
    python compare_s3.py /tmp/mids.csv
    python compare_s3.py -e acc /tmp/mids.csv
"""

import argparse
import csv
import json
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from npoapi.media_s3 import MediaS3

log = logging.getLogger(__name__)




def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv", default="mids.txt", help="Path to the CSV file exported from the database")
    parser.add_argument("-e", "--env", choices=["prod", "acc"], default="prod",
                        help="Environment (default: prod)")
    parser.add_argument("--workers", type=int, default=16,
                        help="Number of parallel S3 fetch workers (default: 16)")
    parser.add_argument("--partial", action="store_true",
                        help="Use the CSV as leading: only check MIDs listed there (no EXTRA/MISSING reporting)")
    parser.add_argument("--output", "-o", help="Write report to this file instead of stdout")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    client = MediaS3(env=args.env, max_pool_connections=args.workers)
    out = open(args.output, "w", buffering=1) if args.output else sys.stdout

    # Read CSV; db_rows is also used to track what hasn't been seen in S3 yet
    db_rows: dict[str, dict] = {}
    with open(args.csv, newline="") as f:
        for row in csv.DictReader(f, fieldnames=["mid", "lastmodified", "lastpublished"], dialect="excel-tab"):
            row = {k.lower(): v for k, v in row.items()}
            mid = row.get("mid", "").strip()
            if mid:
                db_rows[mid] = row
            if len(db_rows) % 100_000 == 0:
                log.info("Read %s rows from CSV", f"{len(db_rows):,}")


    log.info("Read %s rows from CSV", f"{len(db_rows):,}")

    n_extra = 0
    n_diff = [0]
    done = 0
    checked = [0]
    total = len(db_rows)
    start = time.monotonic()

    def check(mid: str, db: dict) -> None:
        content = client.get(mid, fmt="json")
        checked[0] += 1
        if checked[0] % 1000 == 0:
            elapsed = time.monotonic() - start
            rate = checked[0] / elapsed if elapsed > 0 else 0
            eta = (total - checked[0]) / rate if rate > 0 else float("inf")
            eta_clock = time.strftime("%H:%M:%S", time.localtime(time.time() + eta))
            log.info("S3 listed %s, checked %s/%s, differences %s, ETA %s",
                     f"{done:,}", f"{checked[0]:,}", f"{total:,}", f"{n_diff[0]:,}",
                     eta_clock)
        data = json.loads(content) if content else None
        if data is None:
            print(f"FETCH_FAILED  {mid}", file=out, flush=True)
            n_diff[0] += 1
            return
        db_modified  = int(db.get("lastmodified"))
        db_published = int(db.get("lastpublished"))
        s3_modified  = data.get("lastModified")
        s3_published = data.get("publishDate")
        # allow a 1 ms rounding error
        if abs(db_modified - s3_modified) > 1 or abs(db_published - s3_published) > 1:
            print(f"DIFF  {mid:<30}  {str(db_modified):<20}  {str(s3_modified):<20}  {str(db_published):<20}  {str(s3_published)}", file=out, flush=True)
            n_diff[0] += 1

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        if args.partial:
            log.info("Partial just comparing %s mids from csv", len(db_rows))
            for mid, db in db_rows.items():
                done += 1
                pool.submit(check, mid, db)
        else:
            log.info("Iterating s3://%s/media/json/ …", client.bucket)
            for mid in client.list_mids():
                done += 1
                if mid not in db_rows:
                    print(f"EXTRA    {mid}", file=out, flush=True)
                    n_extra += 1
                    continue
                pool.submit(check, mid, db_rows.pop(mid))

    if not args.partial:
        for mid in db_rows:
            print(f"MISSING  {mid}", file=out)

    log.info("Done. %d issue(s) found (%d extra in S3).", n_diff[0] + len(db_rows), n_extra)

    if args.output:
        out.close()


if __name__ == "__main__":
    main()
