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

def persist_sentences(db, batch, ids):
    insert_sql = "INSERT INTO sentences (src_id, src_is_subm, text) VALUES (?,?,?)"
    update_sql = "UPDATE {tbl} SET sentparsed = 1 WHERE id = ?"
    k_trans = {0:'comments', 1:'submissions'}
    with closing(db.conn.cursor()) as c:
        if batch:
            c.executemany(insert_sql, batch)
        for k,v in ids.items():
            print("yo", k, len(v))
            print(update_sql.format(tbl=k_trans[k]))
            print(v)
            c.executemany(update_sql.format(tbl=k_trans[k]), v)
        db.conn.commit()

def parse_sentences(db, insert_every=500):

    # 1. Get posts that haven't been processed
    qry = """
        SELECT a.id, 1 as is_subm, a.title as text
        FROM submissions a
        LEFT JOIN sentences b
          on a.id = b.src_id
          and b.src_is_subm = 1
        WHERE b.src_id IS NULL
        AND COALESCE(a.sentparsed,0) <> 1
        UNION
        ------
        SELECT a.id, 1 as is_subm, a.selftext as text
        FROM submissions a
        LEFT JOIN sentences b
          on a.id = b.src_id
          and b.src_is_subm = 1
        WHERE b.src_id IS NULL
        AND a.is_self = 1
        AND COALESCE(a.sentparsed,0) <> 1
        UNION
        -----
        SELECT a.id, 0 as is_subm, a.body as text
        FROM comments a
        LEFT JOIN sentences b
          on a.id = b.src_id
          and b.src_is_subm = 0
        WHERE b.src_id IS NULL
        AND COALESCE(a.sentparsed,0) <> 1
    """

    insert_sql = "INSERT INTO sentences (src_id, src_is_subm, text) VALUES (?,?,?)"
    n_subm = n_sent = 0
    start = 0

    batch = []
    ids = defaultdict(list)
    for src_id, src_is_subm, text in db.conn.execute(qry):
        sents = []
        sents.extend(sent_tokenize(text))

        recs = [(src_id, src_is_subm, s) for s in sents if atleast_k_spaces(s,2) ]
        batch.extend(recs)
        ids[src_is_subm].append([src_id])

        if len(ids) > insert_every:
             persist_sentences(db, batch, ids)
             batch = []
             ids = defaultdict(list)

        n_subm +=1
        n_sent +=len(recs)
        if time.time() - start > 30:
            print(n_subm, n_sent)
            start = time.time()
    if ids:
        print("persisting {},{} ids".format(len(ids.get(0,[])), len(ids.get(1,[]) )))
        persist_sentences(db, batch, ids)
    print(n_subm, n_sent)
