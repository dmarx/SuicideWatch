CREATE TABLE IF NOT EXISTS submissions
    (id          TEXT PRIMARY KEY,
     author      TEXT,
     created_utc INTEGER,
     updated     INTEGER,
     is_self     INTEGER,
     title       TEXT,
     selftext    TEXT,
     subreddit   TEXT,
     sentparsed  INTEGER
     );

CREATE TABLE IF NOT EXISTS comments
    (id          TEXT PRIMARY KEY,
     link_id     TEXT,
     author      TEXT,
     created_utc INTEGER,
     updated     INTEGER,
     subreddit   TEXT,
     body        TEXT,
     sentparsed  INTEGER
     );

CREATE TABLE IF NOT EXISTS sentences
    (sentence_id    INTEGER PRIMARY KEY AUTOINCREMENT,
     src_id         TEXT,
     src_is_subm    INTEGER,
     text           TEXT
     );

CREATE TABLE IF NOT EXISTS metrics
    (id                INTEGER PRIMARY KEY AUTOINCREMENT,
     name              TEXT,
     value             TEXT,
     last_updated_date INTEGER,
     last_recalculated_date INTEGER
    );

CREATE TABLE IF NOT EXISTS submissions_stg AS
  SELECT * FROM submissions LIMIT 1;

DELETE FROM submissions_stg;

CREATE TABLE IF NOT EXISTS comments_stg AS
  SELECT * FROM comments LIMIT 1;

DELETE FROM comments_stg;

CREATE INDEX IF NOT EXISTS ix_comm_auth ON comments (author);
CREATE INDEX IF NOT EXISTS ix_subm_auth ON submissions (author);
CREATE INDEX IF NOT EXISTS ix_comm_subr ON comments (subreddit);
CREATE INDEX IF NOT EXISTS ix_subm_is_self ON submissions (is_self);

CREATE INDEX IF NOT EXISTS ix_comm_auth_stg ON comments_stg (author);
CREATE INDEX IF NOT EXISTS ix_subm_auth_stg ON submissions_stg (author);
CREATE INDEX IF NOT EXISTS ix_comm_subr_stg ON comments_stg (subreddit);
CREATE INDEX IF NOT EXISTS ix_subm_is_self_stg ON submissions_stg (is_self);

CREATE INDEX IF NOT EXISTS ix_sent_src_id ON sentences (src_id);
CREATE INDEX IF NOT EXISTS ix_sent_src_is_subm ON sentences (src_is_subm);
