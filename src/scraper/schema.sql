CREATE TABLE submissions
    (id          TEXT PRIMARY KEY,
     author      TEXT,
     created_utc INTEGER,
     updated     INTEGER,
     is_self     INTEGER,
     title       TEXT,
     selftext    TEXT
     );
