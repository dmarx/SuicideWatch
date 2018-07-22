from psaw import PushshiftAPI
from scraper.datamodel import DbApi
import time
import numpy as np
import datetime as dt

db = DbApi()
api = PushshiftAPI()

class Scraper(object):
    def __init__(self,
                 db=db,
                 api=api,
                 report_every = 30,
                 subreddit='SuicideWatch',
                 n=None
                 ):
        self.db = db
        self.api = api
        self.report_every = report_every
        self.last_report = 0
        self.subreddit = subreddit
        self.n=n

    def emit_report(self, last_rec):
        now = time.time()
        if (now - self.last_report) > self.report_every:
            self.last_report = now
            report = '[{now}] {n} {at} - {title}'.format(
                now = str(dt.datetime.now()),
                #n =  len(self.db.loaded_ids),
                n=self.db.conn.execute('select count(*) from submissions').fetchone(),
                at = np.datetime64(last_rec.created_utc, 's').astype(str),
                title = last_rec.title
            )
            print(report)

    def _get_submissions(self, gen):
        batch=None
        for batch in gen:
            self.db.persist_submissions(batch)
            self.emit_report(last_rec=batch[-1])
        print("Process complete.")
        if batch:
            self.last_report = 0
            self.emit_report(last_rec=batch[-1])

    def backfill_submissions(self):
        gen = self.api.search_submissions(subreddit=self.subreddit, limit=self.n, return_batch=True)
        self._get_submissions(gen)

    def get_new_submissions(self):
        gen = self.api.search_submissions(subreddit=self.subreddit, limit=self.n, return_batch=True)
        for batch in gen:
            recs = []
            for item in batch:
                test = item.id in self.db.loaded_ids
                if test:
                    break
                recs.append(item)
            if recs:
                self.db.persist_submissions(recs)
                self.emit_report(last_rec=recs[-1])
            if test:
                break
        print("Process complete.")
        if recs:
            self.last_report = 0
            self.emit_report(last_rec=recs[-1])
