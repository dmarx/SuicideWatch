from nltk.tokenize import sent_tokenize
from contextlib import closing
import sys, os
import time

def atleast_k_spaces(s,k=2):
    i=0
    for c in s:
        if c == ' ':
            i+=1
            if i>=k:
                return True
    return False

def parse_sentences(db):

    # 1. Get posts that haven't been processed
    qry = """
        SELECT a.id, 1 as is_subm, a.title as text
        FROM submissions a
        LEFT JOIN sentences b
          on a.id = b.src_id
          and b.src_is_subm = 1
        WHERE b.src_id IS NULL
        UNION
        ------
        SELECT a.id, 1 as is_subm, a.selftext as text
        FROM submissions a
        LEFT JOIN sentences b
          on a.id = b.src_id
          and b.src_is_subm = 1
        WHERE b.src_id IS NULL
        AND a.is_self = 1
        UNION
        -----
        SELECT a.id, 0 as is_subm, a.body as text
        FROM comments a
        LEFT JOIN sentences b
          on a.id = b.src_id
          and b.src_is_subm = 0
        WHERE b.src_id IS NULL
    """

    insert_sql = "INSERT INTO sentences (src_id, src_is_subm, text) VALUES (?,?,?)"
    n_subm = n_sent = 0
    start = 0

    for src_id, src_is_subm, text in db.conn.execute(qry):
        sents = []
        sents.extend(sent_tokenize(text))

        recs = [(src_id, src_is_subm, s) for s in sents if atleast_k_spaces(s,2) ]
        with closing(db.conn.cursor()) as c:
            c.executemany(insert_sql, recs)
            db.conn.commit()

        n_subm +=1
        n_sent +=len(recs)
        if time.time() - start > 30:
            print(n_subm, n_sent)
            start = time.time()

    print(n_subm, n_sent)
