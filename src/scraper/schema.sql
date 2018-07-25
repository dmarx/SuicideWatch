CREATE TABLE IF NOT EXISTS submissions
    (id          TEXT PRIMARY KEY,
     author      TEXT,
     created_utc INTEGER,
     updated     INTEGER,
     is_self     INTEGER,
     title       TEXT,
     selftext    TEXT,
     subreddit   TEXT
     );

CREATE TABLE IF NOT EXISTS comments
    (id          TEXT PRIMARY KEY,
     link_id     TEXT,
     author      TEXT,
     created_utc INTEGER,
     updated     INTEGER,
     subreddit   TEXT,
     body        TEXT
     );

CREATE TABLE IF NOT EXISTS sentences
    (sentence_id    INTEGER PRIMARY KEY AUTOINCREMENT,
     src_id         TEXT,
     src_is_subm    INTEGER,
     text           TEXT
     );
