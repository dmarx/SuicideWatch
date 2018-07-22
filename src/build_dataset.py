"""
Entry point for running data processing scripts.
"""
import argparse
from preprocessing.sentence_parser import parse_sentences
from scraper.get_submissions import Scraper
from scraper.datamodel import DbApi

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Dispatcher for data-building processes.')
    parser.add_argument('--backfill-submissions', action='store_true',
                        help='Scrape historical <subreddit> submissions from Pushshift. Gets submission id, author, title, selftext, and created_utc. Does not download comments.')
    parser.add_argument('--get-new-submissions', action='store_true',
                        help='Scrape new <subreddit> submissions from Pushshift. Gets submission id, author, title, selftext, and created_utc. Does not download comments.')
    parser.add_argument('--parse-sentences', action='store_true',
                    help='Extracts sentences from submissions.')
    parser.add_argument('--subreddit', default='SuicideWatch',
                    help='Target subreddit for scraping. Default is /r/SuicideWatch.')
    parser.add_argument('--n', default=None, type=int,
                    help='Target subreddit for scraping. Default is /r/SuicideWatch.')

    args = parser.parse_args()
    par={'subreddit':args.subreddit}
    if args.n is not None:
        par['limit'] = args.n
    scraper = Scraper(**par)
    if args.backfill_submissions:
        scraper.backfill_submissions()
    if args.get_new_submissions:
        scraper.get_new_submissions()
    if args.parse_sentences:
        db = DbApi()
        parse_sentences(db)
