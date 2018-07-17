from psaw import PushshiftAPI
from datamodel import DbApi
import time
import numpy as np
import datetime as dt

if __name__ == '__main__':
    db = DbApi()
    api = PushshiftAPI()

    report_every = 30
    last_report = 0
    gen = api.search_submissions(subreddit='SuicideWatch', return_batch=True)
    for batch in gen:
        db.persist_submissions(batch)

        now = time.time()
        if (now - last_report) > report_every:
            last_report = now
            report = '[{now}] {n} {at} - {title}'.format(
                now = str(dt.datetime.now()),
                n =  len(db.loaded_ids),
                at = np.datetime64(batch[-1].created_utc, 's').astype(str),
                title = batch[-1].title
            )
            print(report)

    #print(db.conn.execute('select * from submissions').fetchall())
    print(db.conn.execute('select count(*) from submissions').fetchall())
