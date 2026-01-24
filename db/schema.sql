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

CREATE TABLE IF NOT EXISTS trades (
  token TEXT,
  tx_hash TEXT,
  block_number BIGINT,
  trader TEXT,
  side TEXT,              -- buy / sell
  eth_amount NUMERIC,
  usdc_amount NUMERIC,
  usd_value NUMERIC,
  timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS token_flow (
  token TEXT,
  period TEXT,             -- '5m', '1h', '24h'
  inflow NUMERIC,
  outflow NUMERIC,
  net_flow NUMERIC,
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS wallet_stats (
  wallet TEXT PRIMARY KEY,
  trade_count INT,
  buy_volume NUMERIC,
  sell_volume NUMERIC,
  net_flow NUMERIC,
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS smart_wallets (
  wallet TEXT PRIMARY KEY,
  trades INT,
  volume NUMERIC,
  rank INT,
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS token_profiles (
  token TEXT PRIMARY KEY,
  avg_raw_1h NUMERIC,
  avg_smart_1h NUMERIC,
  avg_volume_24h NUMERIC,
  updated_at TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_smart_wallets_rank ON smart_wallets(rank);


CREATE INDEX idx_wallet_stats_flow ON wallet_stats(net_flow);


CREATE INDEX idx_flow_period ON token_flow(period);


CREATE INDEX idx_trades_block ON trades(block_number);
CREATE INDEX idx_trades_trader ON trades(trader);
CREATE INDEX idx_trades_side ON trades(side);

CREATE INDEX idx_uni_swaps_block ON uniswap_swaps(block_number);
CREATE INDEX idx_uni_swaps_pool ON uniswap_swaps(pool);

CREATE INDEX idx_swaps_time ON swaps(block_time);
CREATE INDEX idx_swaps_token ON swaps(token);
CREATE INDEX idx_swaps_wallet ON swaps(wallet);
