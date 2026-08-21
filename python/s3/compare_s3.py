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
    python compare_s3.py --workers 32 /tmp/mids.csv
"""

import argparse
import csv
import json
import logging
import sys
from concurrent.futures import as_completed
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime, timezone

from npoapi.media_s3 import MediaS3

log = logging.getLogger(__name__)


def fetch_fields(client: MediaS3, mid: str) -> dict | None:
    raw = client.get(mid, fmt="json")
    return json.loads(raw) if raw is not None else None


def normalise_ts(value: str | int | None, millis: bool = False) -> str | None:
    if not value:
        return None
    if millis:
        return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    return datetime.fromisoformat(str(value).strip()).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv", default="mids.txt", help="Path to the CSV file exported from the database")
    parser.add_argument("-e", "--env", choices=["prod", "acc"], default="prod",
                        help="Environment (default: prod)")
    parser.add_argument("--workers", type=int, default=8,
                        help="Number of parallel S3 fetch workers (default: 8)")
    parser.add_argument("--no-extra", action="store_true",
                        help="Do not report MIDs present in S3 but absent from the CSV")
    parser.add_argument("--output", "-o", help="Write report to this file instead of stdout")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    client = MediaS3(env=args.env)
    out = open(args.output, "w") if args.output else sys.stdout

    # Read CSV; db_rows is also used to track what hasn't been seen in S3 yet
    db_rows: dict[str, dict] = {}
    with open(args.csv, newline="") as f:
        fieldnames = ["mid", "lastmodified", "lastpublished"]
        for row in csv.DictReader(f, fieldnames=fieldnames, dialect="excel-tab"):
            row = {k.lower(): v for k, v in row.items()}
            mid = row.get("mid", "").strip()
            if mid:
                db_rows[mid] = row
            if len(db_rows) % 100_000 == 0:
                log.info("Read %s rows from CSV", f"{len(db_rows):,}")


    log.info("Read %s rows from CSV", f"{len(db_rows):,}")
    log.info("Iterating s3://%s/media/json/ …", client.bucket)

    differences = []
    n_extra = 0
    done = 0

    def check(mid: str):
        db = db_rows[mid]
        data = fetch_fields(client, mid)
        if data is None:
            return mid, "FETCH_FAILED", None, None, None, None
        db_modified  = normalise_ts(db.get("lastmodified"))
        db_published = normalise_ts(db.get("lastpublished"))
        s3_modified  = normalise_ts(data.get("lastModified"), millis=True)
        s3_published = normalise_ts(data.get("publishDate"), millis=True)
        if db_modified != s3_modified or db_published != s3_published:
            return mid, "DIFF", db_modified, s3_modified, db_published, s3_published
        return None

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {}
        for mid in client.list_mids(fmt="json"):
            done += 1
            if done % 1000 == 0:
                log.info("… listed %s", f"{done:,}")

            if mid in db_rows:
                futures[pool.submit(check, mid)] = mid
                del db_rows[mid]
            elif not args.no_extra:
                print(f"  EXTRA    {mid}", file=out)
                n_extra += 1

        for future in as_completed(futures):
            result = future.result()
            if result:
                differences.append(result)

    # Whatever remains in db_rows was never seen in S3
    missing_in_s3 = sorted(db_rows)
    if missing_in_s3:
        print(f"\n=== MISSING IN S3 ({len(missing_in_s3)}) ===", file=out)
        for mid in missing_in_s3:
            print(f"  MISSING  {mid}", file=out)

    if differences:
        differences.sort()
        print(f"\n=== TIMESTAMP DIFFERENCES ({len(differences)}) ===", file=out)
        print(f"{'mid':<30}  {'db_lastModified':<20}  {'s3_lastModified':<20}  {'db_lastPublished':<20}  {'s3_lastPublished'}", file=out)
        for mid, reason, db_mod, s3_mod, db_pub, s3_pub in differences:
            print(f"{mid:<30}  {str(db_mod):<20}  {str(s3_mod):<20}  {str(db_pub):<20}  {str(s3_pub)}", file=out)

    log.info("Done. %d issue(s) found (%d extra in S3).", len(missing_in_s3) + len(differences), n_extra)

    if args.output:
        out.close()


if __name__ == "__main__":
    main()
