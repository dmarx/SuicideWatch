from nltk.tokenize import sent_tokenize
from contextlib import closing
import sys, os
import time

#db = DbApi()

def initialize_table(db):

    try:
        db.conn.execute("select 1 from sentences")
    except:
        print("creating table 'sentences'...")
        db.conn.execute("""
            CREATE TABLE sentences (
                sentence_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id   TEXT,
                text            TEXT);""")

def atleast_k_spaces(s,k=2):
    i=0
    for c in s:
        if c == ' ':
            i+=1
            if i>=k:
                return True
    return False

def parse_sentences(db):
    initialize_table(db)

    # 1. Get posts that haven't been processed
    qry = """
        SELECT a.id, a.title, a.selftext
        FROM submissions    a
        LEFT JOIN sentences b
          on a.id = b.submission_id
        WHERE b.submission_id IS NULL
    """

    insert_sql = "INSERT INTO sentences (submission_id, text) VALUES (?,?)"
    n_subm = n_sent = 0
    start = 0

    for subm_id, title, selftext in db.conn.execute(qry):
        sents = []
        sents.extend(sent_tokenize(title))
        if selftext:
            sents.extend(sent_tokenize(selftext))

        recs = [(subm_id, s) for s in sents if atleast_k_spaces(s,2) ]
        with closing(db.conn.cursor()) as c:
            c.executemany(insert_sql, recs)
            db.conn.commit()

        n_subm +=1
        n_sent +=len(recs)
        if time.time() - start > 30:
            print(n_subm, n_sent)
            start = time.time()

    print(n_subm, n_sent)
