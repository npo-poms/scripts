#!/usr/bin/env python3
"""Script to find gaps in the schedule"""
from typing import Any

import psycopg2
from config import db_config


def check_duplicates_schedules():

    duplicate_scheduleevents = """
        select maintitle(id), start, max(mid), min(mid), count(*) as duplicates
        from mediaobject  m join scheduleevent e on m.id = e.mediaobject_id
        where mediatype(id) = 'BROADCAST'
        and createdby_principalid = 'prepr-service'
        group by maintitle(id), start having count(*) > 1 order by start desc
        """
    count_duplicate_schedulesevents = "select count(*) from (" + duplicate_scheduleevents + ") as t"

    nr_of_duplicates = execute(count_duplicate_schedulesevents)

    if nr_of_duplicates > 0:
        return AssertionError("We found " + str(nr_of_duplicates)
                              + "   duplicates. Execute the following query for extra details: ["
                              + duplicate_scheduleevents + "  ]")


def check_gaps_in_crids():
    find_crids_gaps = """
    select * from (
        select mediaobject_id as id, max(list_index) as maxIndex, (count(*) -1) as count
    from mediaobject_crids group by mediaobject_id having count(*) > 1
    ) as t
    where t.maxIndex <> count
    """
    count_gaps = "select count(*) from (" + find_crids_gaps + "  ) as t"

    nr_of_gaps = execute(count_gaps)

    if nr_of_gaps > 0:
        return AssertionError("We found " + nr_of_gaps +
                              "   gaps. Execute the following query for extra details: [" + find_crids_gaps + " ]")


def execute(sql):
    results = Any
    conn = None
    params = db_config()

    try:
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
        cur = conn.cursor()

        cur.execute(sql)

        results = cur.fetchone()[0]

        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')
    return results

def logErrors(errs):
    for error in errs:
        print(error)


if __name__ == "__main__":
    results = list()
    results.append(check_duplicates_schedules())
    results.append(check_gaps_in_crids())
    errors = list(filter(None, results))
    print(errors)
    logErrors(errors)
    if errors:
        raise errors[0]



