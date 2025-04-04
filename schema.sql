DROP TABLE IF EXISTS verification_tokens;
DROP TABLE IF EXISTS captcha_data;
DROP TABLE IF EXISTS vote_records;
DROP TABLE IF EXISTS options;
DROP TABLE IF EXISTS polls;
DROP TABLE IF EXISTS sqlite_sequence;

PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

CREATE TABLE polls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id INTEGER NOT NULL,
    option_text TEXT NOT NULL,
    votes INTEGER DEFAULT 0,
    FOREIGN KEY (poll_id) REFERENCES polls (id)
);

CREATE TABLE vote_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id INTEGER NOT NULL,
    option_id INTEGER NOT NULL,
    ip_address TEXT NOT NULL,
    browser_fingerprint TEXT NOT NULL,
    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (poll_id) REFERENCES polls (id),
    FOREIGN KEY (option_id) REFERENCES options (id)
);

DROP TABLE IF EXISTS captcha_data;
DROP TABLE IF EXISTS verification_tokens;
DROP TABLE IF EXISTS vote_records;
DROP TABLE IF EXISTS options;
DROP TABLE IF EXISTS polls;

CREATE TABLE polls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id INTEGER NOT NULL,
    option_text TEXT NOT NULL,
    votes INTEGER DEFAULT 0,
    FOREIGN KEY (poll_id) REFERENCES polls (id)
);

CREATE TABLE vote_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id INTEGER NOT NULL,
    option_id INTEGER NOT NULL,
    ip_address TEXT NOT NULL,
    browser_fingerprint TEXT NOT NULL,
    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (poll_id) REFERENCES polls (id),
    FOREIGN KEY (option_id) REFERENCES options (id)
);

CREATE TABLE captcha_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    verification_token TEXT UNIQUE NOT NULL,
    target_position INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE verification_tokens (
    verification_token TEXT PRIMARY KEY,
    expires REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMIT;
PRAGMA foreign_keys = ON;
CREATE TABLE verification_tokens (
    verification_token TEXT PRIMARY KEY,
    expires REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);