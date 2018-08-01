from psaw import PushshiftAPI
from scraper.datamodel import DbApi
import time
import numpy as np
import datetime as dt
import sys

db = DbApi()
api = PushshiftAPI()

class Scraper(object):
    def __init__(self,
                 db=db,
                 api=api,
                 report_every = 30,
                 subreddit=None,
                 n=None,
                 kind='submissions',
                 verbose=True,
                 skip_garbage=True
                 ):
        self.db = db
        self.api = api
        self.report_every = report_every
        self.last_report = 0
        self.subreddit = subreddit
        self.n=n
        self.kind=kind
        self.verbose=verbose
        self.skip_garbage = skip_garbage

        if self.subreddit == 'all':
            self.subreddit = None

    def emit_report(self, last_rec):
        if not self.verbose:
            return
        now = time.time()
        if (now - self.last_report) > self.report_every:
            self.last_report = now

            if self.kind == 'submissions':
                text = last_rec.title
            else:
                text = last_rec.body[:120]
                if len(last_rec.body) > 120:
                    text += '...'
            report = '[{now}] {n} {at} - {subr} - {text}'.format(
                now = str(dt.datetime.now()),
                #n =  len(self.db.loaded_ids),
                n=self.db.conn.execute('select count(*) from {}'.format(self.kind)).fetchone(),
                at = np.datetime64(last_rec.created_utc, 's').astype(str),
                text = text,
                subr = last_rec.subreddit
            )
            print(report)
            sys.stdout.flush()

    def _clean_batch(self, batch):
        recs = []
        for b in batch:
            if b.author == 'AutoModerator':
                continue
            if b.author == '[deleted]':
                continue
            if 'bot' in b.author.lower():
                continue
            recs.append(b)
        return recs
    def _get_content(self, gen):
        batch=None
        for batch in gen:
            if self.skip_garbage:
                batch = self._clean_batch(batch)
            print("_get_content", len(batch))
            self.db.persist_content(batch, kind=self.kind)
            self.emit_report(last_rec=batch[-1])
        print("Process complete.")
        if batch:
            self.last_report = 0
            self.emit_report(last_rec=batch[-1])

    def backfill(self):
        print("BACKFILL")
        print(self.kind)
        if self.kind == 'submissions':
            f = self.api.search_submissions
        else:
            f = self.api.search_comments
        par = {'return_batch':True}
        if self.subreddit:
            par['subreddit'] = self.subreddit
        if self.n:
            par['limit']=self.n
        print(par)
        print(f)
        gen = f(**par)
        self._get_content(gen)

    def get_new_submissions(self):
        if not self.kind == 'submissions':
            raise Exception("Only supported for submissions.")
        gen = self.api.search_submissions(subreddit=self.subreddit, limit=self.n, return_batch=True)
        for batch in gen:
            recs = []
            for item in batch:
                test = item.id in self.db.loaded_ids
                if test:
                    break
                recs.append(item)
            if self.skip_garbage:
                recs = self._clean_batch(recs)
            if recs:
                self.db.persist_content(recs, kind=self.kind)
                self.emit_report(last_rec=recs[-1])
            if test:
                break
        print("Process complete.")
        if recs:
            self.last_report = 0
            self.emit_report(last_rec=recs[-1])
