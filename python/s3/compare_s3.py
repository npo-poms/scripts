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
import datetime
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from npoapi.media_s3 import MediaS3

log = logging.getLogger(__name__)




def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv", default="mids.txt", help="Path to the CSV file exported from the database")
    parser.add_argument("-e", "--env", choices=["prod", "acc", "test"], default="prod",
                        help="Environment (default: prod)")
    parser.add_argument("--workers", type=int, default=16,
                        help="Number of parallel S3 fetch workers (default: 16)")
    parser.add_argument("--partial", action="store_true",
                        help="Use the CSV as leading: only check MIDs listed there (no EXTRA/MISSING reporting)")
    parser.add_argument("--output", "-o", help="Write report to this file instead of stdout")
    parser.add_argument("--since", metavar="DATE",
                        help="Only consider S3 objects (and CSV rows) modified after this date (YYYY-MM-DD or ISO-8601)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    csv_modified_ms = os.stat(args.csv).st_mtime_ns // 1_000_000
    log.info("CSV export was last modified at %s",
             datetime.datetime.fromtimestamp(
                 csv_modified_ms / 1000, tz=datetime.timezone.utc
             ).isoformat())

    since: datetime.datetime | None = None
    since_ms = 0
    if args.since:
        since = datetime.datetime.fromisoformat(args.since)
        if since.tzinfo is None:
            since = since.replace(tzinfo=datetime.timezone.utc)
        log.info("Filtering to objects modified after %s", since.isoformat())
        since_ms = int(since.timestamp() * 1000)

    client = MediaS3(env=args.env, max_pool_connections=args.workers * 2).configured_login()
    out = open(args.output, "w", buffering=1) if args.output else sys.stdout

    print(f"#\tMID\tDB_MODIFIED\t\tS3_MODIFIED\tDB_PUBLISHED\t\tS3_PUBLISHED", file=out, flush=True)

    # Read CSV; db_rows is also used to track what hasn't been seen in S3 yet
    db_rows: dict[str, dict] = {}
    db_count = 0
    with open(args.csv, newline="") as f:
        for row in csv.DictReader(f, fieldnames=["mid", "lastmodified", "lastpublished"], dialect="excel-tab"):
            row = {k.lower(): v for k, v in row.items()}
            mid = row.get("mid", "").strip()
            if not mid:
                continue
            db_rows[mid] = row
            db_lastmodified = int(row.get("lastmodified", 0))
            db_lastpublished = 0
            if row.get("lastpublished") != "\\N":
                db_lastpublished = int(row.get("lastpublished", 0))

            if (db_lastmodified > since_ms or db_lastpublished > since_ms):
                db_count += 1

            if len(db_rows) % 100_000 == 0:
                log.info("Read %s rows from CSV", f"{len(db_rows):,}")


    log.info("Read %s rows from CSV, estimated relevant %s", f"{len(db_rows):,}", f"{db_count:,}")

    n_extra = 0
    n_diff = [0]
    done = [0]
    skip = [0]
    checked = [0]
    total = db_count
    start = time.monotonic()

    def check(mid: str, db: dict) -> None:
        content = client.get(mid, fmt="json")
        checked[0] += 1
        if checked[0] % 500 == 0:
            elapsed = time.monotonic() - start
            rate = checked[0] / elapsed if elapsed > 0 else 0
            eta = (total - checked[0]) / rate if rate > 0 else float("inf")
            eta_clock = time.strftime("%H:%M:%S", time.localtime(time.time() + eta))
            log.info("S3 listed %s, checked %s/%s, differences %s, ETA %s",
                     f"{done[0]:,}", f"{checked[0]:,}", f"{total:,}", f"{n_diff[0]:,}",
                     eta_clock)
        data = json.loads(content) if content else None
        if data is None:
            print(f"FETCH_FAILED\t{mid}", file=out, flush=True)
            n_diff[0] += 1
            return
        db_modified  = int(db.get("lastmodified"))
        db_published = int(db.get("lastpublished"))
        s3_modified  = data.get("lastModified")
        s3_published = data.get("publishDate")
        # allow a 1 ms rounding error
        if abs(db_modified - s3_modified) > 1 or abs(db_published - s3_published) > 1:
            if s3_modified > csv_modified_ms or s3_published > csv_modified_ms:
                log.debug("Ignoring %s: S3 document changed after the CSV export", mid)
                return
            modified_op = ">" if  db_modified > s3_modified else "<" if db_modified < s3_published else "="
            lastpublished_op = ">" if  db_published > s3_published else  "<" if db_published > s3_published  else "="
            print(f"DIFF\t{mid}\t{str(db_modified)}\t{modified_op}\t{str(s3_modified)}\t{str(db_published)}\t{lastpublished_op}\t{str(s3_published)}", file=out, flush=True)
            n_diff[0] += 1

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        if args.partial:
            log.info("Partial just comparing %s mids from csv", db_count)
            for mid, db in db_rows.items():
                done[0] += 1
                pool.submit(check, mid, db)
        else:
            def on_hit(mid, obj, yielded):
                done[0] += 1
                if not yielded:
                    skip[0] += 1
                if done[0] % 1000 == 0:
                    log.info("Iterating s3://%s/media/json/ done %s, skipped %s", client.bucket, done[0], skip[0])


            log.info("Iterating s3://%s/media/json/", client.bucket)
            for mid in client.list_mids(modified_since=since, on_hit=on_hit):
                if mid not in db_rows:
                    print(f"EXTRA\t{mid}", file=out, flush=True)
                    n_extra += 1
                    continue
                pool.submit(check, mid, db_rows.pop(mid))

    if not args.partial:
        for mid in db_rows:
            print(f"MISSING\t{mid}", file=out)

    log.info("Done. %d issue(s) found (%d extra in S3).", n_diff[0] + db_count, n_extra)

    if args.output:
        out.close()


if __name__ == "__main__":
    main()
