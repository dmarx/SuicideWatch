from scraper.datamodel import DbApi
import time
import sys
from contextlib import closing

class MetricCalculator(object):
    def __init__(self,
                 db=None,
                 refresh_time={'sent_in_class_pos':60*60*24}):
        if not db:
            db = DbApi()
        self.db = db
        self.refresh_time = refresh_time
        self.metric_map = {'sent_in_class_pos':'count_sentences_by_class'}

    def update(self, name, value):
        

    def recalculate(self, metrics=None):
        if not metrics:
            metrics = self.refresh_time.keys()
        for metric in self.needs_updating:
            if metric not in metrics:
                continue
            f = getattr(self, self.metric_map.get(metric, metric))
            f()

    def needs_updating(self):
        qry = "SELECT name, last_recalculated_date FROM metrics WHERE name = ?;"
        now = time.time()
        with closing(self.db.conn.cursor()) as c:
            for k, v in self.refresh_time.items():
                last_recalculated = c.execute(qry, [k]).fetchone()
                if now - last_recalculated > v:
                    yield k

    def count_sentences_by_class(self):
        qry = """
            SELECT class, sum(n_sent)
            FROM (
                SELECT
                    CASE
                        WHEN subm.subreddit = 'SuicideWatch' THEN 'pos'
                        ELSE 'neg'
                    END class,
                    count(distinct sentence_id) n_sent
                FROM submissions subm
                JOIN sentences sent
                  on subm.id = sent.src_id
                  and sent.src_is_subm = 1
                GROUP BY 1
                UNION ALL
                SELECT
                    'neg' as class,
                    count(distinct sentence_id) n_sent
                FROM comments comm
                JOIN sentences sent
                  on comm.id = sent.src_id
                  and sent.src_is_subm = 0
                GROUP BY 1
                )
            group by 1
            ;
            """
        response = self.db.conn.execute(qry).fetchall()
        d = {'pos':0, 'neg':0}
        for rec in response:
            d[rec[0]].update(rec[1])
        now = time.time()
        recs = [('sent_in_class_{}'.format(k), v, now, now) for k,v in d.items()]
        update_sql = "UPDATE TABLE metrics (name, value, last_updated_date, last_recalculated_date) VALUES (?,?,?,?)"
        with closing(self.db.conn.cursor()) as c:
            c.executemany(update_sql, recs)
            self.db.conn.commit()
