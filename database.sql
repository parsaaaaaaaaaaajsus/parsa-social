-- =========================================
-- USERS
-- =========================================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    user_name VARCHAR(50) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);


-- =========================================
-- SESSIONS
-- =========================================

CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL
        REFERENCES users(id) ON DELETE CASCADE,

    token_hash VARCHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL
);


-- =========================================
-- POSTS
-- =========================================

CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,

    user_id INTEGER NOT NULL
        REFERENCES users(id) ON DELETE CASCADE,

    name TEXT NOT NULL,
    user_name VARCHAR(50) NOT NULL,

    title TEXT NOT NULL,
    text TEXT NOT NULL,

    likes INTEGER[] NOT NULL DEFAULT '{}',
    reactions JSONB NOT NULL DEFAULT '{}'::jsonb
);


-- =========================================
-- COMMENTS
-- =========================================

CREATE TABLE IF NOT EXISTS comments (
    id SERIAL PRIMARY KEY,

    user_id INTEGER NOT NULL
        REFERENCES users(id) ON DELETE CASCADE,

    post_id INTEGER NOT NULL
        REFERENCES posts(id) ON DELETE CASCADE,

    name TEXT NOT NULL,
    user_name VARCHAR(50) NOT NULL,

    text TEXT NOT NULL,

    likes INTEGER[] NOT NULL DEFAULT '{}',
    reactions JSONB NOT NULL DEFAULT '{}'::jsonb
);


-- =========================================
-- REPLYS
-- =========================================

CREATE TABLE IF NOT EXISTS replys (
    id SERIAL PRIMARY KEY,

    user_id INTEGER NOT NULL
        REFERENCES users(id) ON DELETE CASCADE,

    name TEXT NOT NULL,
    user_name VARCHAR(50) NOT NULL,

    -- ریپلای مستقیم به کامنت
    comment_or_reply_id INTEGER
        REFERENCES comments(id) ON DELETE CASCADE,

    -- اطلاعات ریپلای به یک ریپلای دیگر
    comment_id INTEGER
        REFERENCES comments(id) ON DELETE CASCADE,

    reply_id INTEGER
        REFERENCES replys(id) ON DELETE CASCADE,

    text TEXT NOT NULL,

    likes INTEGER[] NOT NULL DEFAULT '{}',

    reply_to_user_name VARCHAR(50) NOT NULL,

    -- هر ریپلای باید دقیقاً یکی از دو ساختار معتبر را داشته باشد
    CONSTRAINT valid_reply_structure CHECK (
        (
            comment_or_reply_id IS NOT NULL
            AND comment_id IS NULL
            AND reply_id IS NULL
        )
        OR
        (
            comment_or_reply_id IS NULL
            AND comment_id IS NOT NULL
            AND reply_id IS NOT NULL
        )
    )
);


-- =========================================
-- INDEXES
-- =========================================

CREATE INDEX IF NOT EXISTS idx_sessions_user_id
ON sessions(user_id);

CREATE INDEX IF NOT EXISTS idx_sessions_expires_at
ON sessions(expires_at);

CREATE INDEX IF NOT EXISTS idx_posts_user_id
ON posts(user_id);

CREATE INDEX IF NOT EXISTS idx_comments_post_id
ON comments(post_id);

CREATE INDEX IF NOT EXISTS idx_comments_user_id
ON comments(user_id);

CREATE INDEX IF NOT EXISTS idx_replys_user_id
ON replys(user_id);

CREATE INDEX IF NOT EXISTS idx_replys_comment_or_reply_id
ON replys(comment_or_reply_id);

CREATE INDEX IF NOT EXISTS idx_replys_comment_id
ON replys(comment_id);

CREATE INDEX IF NOT EXISTS idx_replys_reply_id
ON replys(reply_id);
