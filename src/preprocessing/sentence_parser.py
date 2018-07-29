from nltk.tokenize import sent_tokenize
from contextlib import closing
import sys, os
import time
from collections import defaultdict

def atleast_k_spaces(s,k=2):
    i=0
    for c in s:
        if c == ' ':
            i+=1
            if i>=k:
                return True
    return False

def persist_sentences(db, batch):
    insert_sql = "INSERT INTO sentences (src_id, src_is_subm, text) VALUES (?,?,?)"
    migrate_sql = "INSERT INTO {kind} SELECT * FROM {kind}_stg"
    truncate_sql = "DELETE FROM {kind}_stg"
    with closing(db.conn.cursor()) as c:
        if batch:
            c.executemany(insert_sql, batch)
        for kind in ('comments','submissions'):
            c.execute(migrate_sql.format(kind=kind))
            c.execute(truncate_sql.format(kind=kind))
        db.conn.commit()

def parse_sentences(db, insert_every=5000):

    # 1. Get posts that haven't been processed

    qry = """
        SELECT a.id, 1 as is_subm, a.title as text
        FROM submissions_stg a
        UNION
        ------
        SELECT a.id, 1 as is_subm, a.selftext as text
        FROM submissions_stg a
        WHERE is_self = 1
        UNION
        -----
        SELECT a.id, 0 as is_subm, a.body as text
        FROM comments_stg a
    """

    n_subm = n_sent = 0
    start = 0

    batch = []
    n_i = 0
    for src_id, src_is_subm, text in db.conn.execute(qry):
        sents = []
        sents.extend(sent_tokenize(text))

        recs = [(src_id, src_is_subm, s) for s in sents if atleast_k_spaces(s,2) ]
        batch.extend(recs)

        n_i += 1
        if n_i > insert_every:
             persist_sentences(db, batch)
             batch = []
             n_i =0

        n_subm +=1
        n_sent +=len(recs)
        if time.time() - start > 30:
            print(n_subm, n_sent)
            start = time.time()
    if n_subm:
        persist_sentences(db, batch)
    print(n_subm, n_sent)
