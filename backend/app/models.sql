-- Focus Areas table for user geographic preferences
CREATE TABLE IF NOT EXISTS focus_areas (
    account_id TEXT PRIMARY KEY,
    mode TEXT NOT NULL,           -- 'zip' | 'council' | 'neighborhood' | 'radius'
    codes TEXT,                   -- JSON array of zip/district/neighborhood codes (nullable for radius)
    center_lat REAL,              -- for radius mode
    center_lon REAL,              -- for radius mode
    radius_miles REAL,            -- radius in miles (nullable for non-radius modes)
    created_at TEXT NOT NULL,     -- ISO timestamp
    updated_at TEXT NOT NULL      -- ISO timestamp
);

-- Index for fast lookups by account
CREATE INDEX IF NOT EXISTS idx_focus_areas_account ON focus_areas(account_id);