CREATE TABLE IF NOT EXISTS tokens (
  address TEXT PRIMARY KEY,
  symbol TEXT,
  decimals INT
);

CREATE TABLE IF NOT EXISTS wallets (
  address TEXT PRIMARY KEY,
  trade_count INT DEFAULT 0,
  pnl_usd NUMERIC DEFAULT 0,
  is_smart BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS swaps (
  tx_hash TEXT,
  block_time TIMESTAMP,
  wallet TEXT,
  token TEXT,
  side TEXT,
  amount NUMERIC,
  usd_value NUMERIC
);

CREATE TABLE IF NOT EXISTS blocks (
  block_number BIGINT PRIMARY KEY,
  timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS uniswap_swaps (
  tx_hash TEXT,
  block_number BIGINT,
  pool TEXT,
  sender TEXT,
  recipient TEXT,
  amount0 NUMERIC,
  amount1 NUMERIC,
  timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_uni_swaps_block ON uniswap_swaps(block_number);
CREATE INDEX idx_uni_swaps_pool ON uniswap_swaps(pool);

CREATE INDEX idx_swaps_time ON swaps(block_time);
CREATE INDEX idx_swaps_token ON swaps(token);
CREATE INDEX idx_swaps_wallet ON swaps(wallet);
