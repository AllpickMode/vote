
DROP TABLE IF EXISTS polls;
DROP TABLE IF EXISTS options;
DROP TABLE IF EXISTS vote_records;

CREATE TABLE polls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
    voted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (poll_id) REFERENCES polls (id),
    FOREIGN KEY (option_id) REFERENCES options (id)
);

-- 创建索引以加快查询速度
CREATE INDEX idx_vote_records_poll_ip ON vote_records(poll_id, ip_address);
CREATE INDEX idx_vote_records_fingerprint ON vote_records(poll_id, browser_fingerprint);
CREATE INDEX idx_vote_records_time ON vote_records(voted_at);