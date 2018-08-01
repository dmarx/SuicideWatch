"""
Entry point for running data processing scripts.
"""
import argparse
from preprocessing.sentence_parser import parse_sentences
from scraper.get_submissions import Scraper
#Scraper = lambda **x: x
from scraper.datamodel import DbApi
import time
import sys

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Dispatcher for data-building processes.')

    parser.add_argument('--backfill', action='store_true',
                        help='Scrape historical content from Pushshift without regard to anything that has already been downloaded.')

    parser.add_argument('--get-new-submissions', action='store_true',
                        help='Scrape new <subreddit> submissions from Pushshift. Gets submission id, author, title, selftext, and created_utc. Does not download comments.')

    parser.add_argument('--parse-sentences', action='store_true',
                    help='Extracts sentences from submissions.')

    parser.add_argument('--subreddit', default='SuicideWatch',
                    help='Target subreddit for scraping. Default is /r/SuicideWatch.')

    parser.add_argument('--n', default=None, type=int,
                    help='Target subreddit for scraping. Default is /r/SuicideWatch.')

    parser.add_argument('--comments', action='store_const',
                        const='comments', default='submissions', dest='kind',
                    help="Get comments. If not provided, submissions downloaded instead.")

    parser.add_argument('--submissions', action='store_const',
                        dest='kind', const='submissions', default='submissions',
                    help="Get submissions (default).")

    parser.add_argument('--update-neg', action='store_true',
                    help='Update negative class content.')

    parser.add_argument('--batch-size', action='store_const', type=int, default=500*100
                    help='Approximate backfill batch size prior to parsing sentences.')

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

    db = DbApi()
    args = parser.parse_args()
    #if args.subreddit=='all':
    #    del args.subreddit

    if args.update_neg:
        args.backfill = True
        args.kind = 'comments'
        args.n = None
        args.subreddit = 'all'

    par={'subreddit':args.subreddit,
         'kind':args.kind,
         'db':db}
    if args.n is not None:
        par['n'] = args.n
    scraper = Scraper(**par)
    print(args)
    print(par)
    sys.stdout.flush()

    # This really belongs somewhere else...
    if args.update_neg or (
       (args.backfill and
       (args.kind == 'comments') and
       (args.n is None)
       and (args.subreddit == 'all')
       )):
        while True:
            start = time.time()
            response = db.conn.execute(qry).fetchall()
            elaps = time.time() - start
            print("base query time:", elaps); sys.stdout.flush()
            if not response:
                raise Exception("Must prepopulate positive class before parity-downloading negative class")
            d = {}
            for rec in response:
                d[rec[0]] = rec[1]
            delta = d['pos']- d.get('neg',0)
            print(delta, d); sys.stdout.flush()
            if delta <= 0:
                print("Parity achieved"); sys.stdout.flush()
                #break
                exit()

            scraper = Scraper(**par)
            scraper.n = args.batch_size
            scraper.backfill()
            print('parsing sentences'); sys.stdout.flush()
            parse_sentences(db)

    if args.backfill:
        scraper.backfill()
    if args.get_new_submissions:
        scraper.get_new_submissions()
    if args.parse_sentences:
        parse_sentences(db)
