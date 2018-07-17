from contextlib import closing
import datetime as dt
import os
from pathlib import Path
import sqlite3
import numpy as np

here    = os.path.dirname(__file__)
datapath = Path('/'.join(Path(here).parts[:-2])) / Path('data')
DB_NAME = str(datapath / Path('scrape_results.db'))

def epoch_now(resolution='s'):
     return np.datetime64(dt.datetime.now(),resolution).astype(np.int64)

class DbApi(object):
    def __init__(self, db_name=DB_NAME, conn=None):
        if not conn:
            conn = sqlite3.Connection(db_name)
        self.conn = conn
        c = conn.cursor()
        try:
            c.execute('SELECT 1 FROM SUBMISSIONS')
        except:
            #with open(os.path.join(here,'schema.sql'), 'r') as f:
            with open(os.path.join(here,'schema.sql'), 'r') as f:
                c.executescript(f.read())

        ids_cursor = c.execute("select distinct id from submissions").fetchall()
        self.loaded_ids = set([r[0] for r in ids_cursor])

    def persist_submissions(self, subms):
        base_sql = "INSERT INTO SUBMISSIONS ({keys}) VALUES ({v});"
        keys = 'updated,id,author,created_utc,title,is_self,selftext'
        recs = []
        for subm in subms:
            if subm.id in self.loaded_ids:
                continue
            vals = [subm.d_.get(k,'') for k in keys.split(',')]
            vals[0] = epoch_now()
            recs.append(vals)
        if not recs:
            return

        ids = [r[1] for r in recs]
        insert_sql = base_sql.format(keys=keys, v=','.join(['?']*len(vals)) )
        with closing(self.conn.cursor()) as c:
            c.executemany(insert_sql, recs)
            self.loaded_ids.update(ids)
            #c.commit()
            self.conn.commit()
