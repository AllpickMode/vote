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
    votes INTEGER DEFAULT 0,
    FOREIGN KEY (poll_id) REFERENCES polls (id)
);
