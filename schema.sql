DROP TABLE IF EXISTS polls;
DROP TABLE IF EXISTS options;

CREATE TABLE polls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 为现有数据添加created_at时间戳（假设投票按id顺序创建）
UPDATE polls SET created_at = DATETIME('now', '-' || id || ' minutes') 
WHERE created_at IS NULL;

CREATE TABLE options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id INTEGER NOT NULL,
    option_text TEXT NOT NULL,
    votes INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (poll_id) REFERENCES polls(id)
);

CREATE TABLE voter_ips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poll_id INTEGER NOT NULL,
    ip_address TEXT NOT NULL CHECK(LENGTH(ip_address) BETWEEN 7 AND 15),
    country_code CHAR(2) NOT NULL,
    user_agent TEXT NOT NULL,
    is_vpn BOOLEAN DEFAULT 0,
    voted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    request_count INTEGER DEFAULT 1 CHECK(request_count >= 1),
    block_until DATETIME,
    UNIQUE(poll_id, ip_address),
    FOREIGN KEY (poll_id) REFERENCES polls(id),
    CHECK (block_until IS NULL OR block_until > CURRENT_TIMESTAMP)
);

CREATE INDEX idx_voter_ips_block ON voter_ips (block_until);
CREATE INDEX idx_voter_ips_country ON voter_ips (country_code);
