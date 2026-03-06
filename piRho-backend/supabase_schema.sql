-- piRho SaaS Database Schema for Supabase
-- Run this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);

-- Tenants table
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255),
    plan VARCHAR(50) DEFAULT 'free',
    promo_code_used VARCHAR(50),
    promo_applied_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    settings JSONB DEFAULT '{}'
);

CREATE INDEX idx_tenants_user ON tenants(user_id);
CREATE INDEX idx_tenants_plan ON tenants(plan);

-- Exchange credentials table (encrypted)
CREATE TABLE IF NOT EXISTS exchange_credentials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    exchange VARCHAR(50) NOT NULL,
    encrypted_api_key TEXT NOT NULL,
    encrypted_api_secret TEXT NOT NULL,
    is_testnet BOOLEAN DEFAULT TRUE,
    permissions JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_validated_at TIMESTAMPTZ
);

CREATE INDEX idx_credentials_tenant ON exchange_credentials(tenant_id);

-- Trading bots table
CREATE TABLE IF NOT EXISTS bots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    strategy VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'stopped',
    config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_active_at TIMESTAMPTZ
);

CREATE INDEX idx_bots_tenant ON bots(tenant_id);
CREATE INDEX idx_bots_status ON bots(status);

-- Trades table
CREATE TABLE IF NOT EXISTS trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    bot_id UUID REFERENCES bots(id) ON DELETE SET NULL,
    symbol VARCHAR(50) NOT NULL,
    side VARCHAR(10) NOT NULL,
    entry_price DECIMAL(20, 8),
    exit_price DECIMAL(20, 8),
    quantity DECIMAL(20, 8),
    leverage INTEGER DEFAULT 1,
    profit_loss DECIMAL(20, 8),
    profit_loss_percent DECIMAL(10, 4),
    strategy VARCHAR(100),
    exit_reason VARCHAR(100),
    opened_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    is_paper BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_trades_tenant ON trades(tenant_id);
CREATE INDEX idx_trades_bot ON trades(bot_id);
CREATE INDEX idx_trades_closed ON trades(closed_at);
CREATE INDEX idx_trades_symbol ON trades(symbol);

-- Signal logs table
CREATE TABLE IF NOT EXISTS signal_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    bot_id UUID REFERENCES bots(id) ON DELETE SET NULL,
    trade_id UUID REFERENCES trades(id) ON DELETE SET NULL,
    symbol VARCHAR(50) NOT NULL,
    signal VARCHAR(10) NOT NULL,
    strategy VARCHAR(100) NOT NULL,
    signal_reason TEXT,
    market_data JSONB DEFAULT '{}',
    sentiment VARCHAR(50),
    funding_rate DECIMAL(20, 8),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_signal_logs_tenant ON signal_logs(tenant_id);
CREATE INDEX idx_signal_logs_bot ON signal_logs(bot_id);
CREATE INDEX idx_signal_logs_trade ON signal_logs(trade_id);
CREATE INDEX idx_signal_logs_created ON signal_logs(created_at);

-- Audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID,
    user_id UUID,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_tenant ON audit_logs(tenant_id);
CREATE INDEX idx_audit_created ON audit_logs(created_at);

-- Row Level Security Policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE exchange_credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE bots ENABLE ROW LEVEL SECURITY;
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE signal_logs ENABLE ROW LEVEL SECURITY;

-- Allow service role full access (for backend)
CREATE POLICY "Service role has full access to users" ON users FOR ALL USING (true);
CREATE POLICY "Service role has full access to tenants" ON tenants FOR ALL USING (true);
CREATE POLICY "Service role has full access to credentials" ON exchange_credentials FOR ALL USING (true);
CREATE POLICY "Service role has full access to bots" ON bots FOR ALL USING (true);
CREATE POLICY "Service role has full access to trades" ON trades FOR ALL USING (true);
CREATE POLICY "Service role has full access to signal_logs" ON signal_logs FOR ALL USING (true);

-- =====================================================
-- Bot Orchestrator Schema Updates
-- Run these to add monitoring and heartbeat fields
-- =====================================================

-- Add heartbeat and monitoring fields to bots table
ALTER TABLE bots ADD COLUMN IF NOT EXISTS heartbeat_at TIMESTAMPTZ;
ALTER TABLE bots ADD COLUMN IF NOT EXISTS error_message TEXT;
ALTER TABLE bots ADD COLUMN IF NOT EXISTS trades_count INTEGER DEFAULT 0;
ALTER TABLE bots ADD COLUMN IF NOT EXISTS pnl_total DECIMAL(20, 8) DEFAULT 0;

-- Create index for heartbeat monitoring (find stale bots)
CREATE INDEX IF NOT EXISTS idx_bots_heartbeat ON bots(heartbeat_at);

-- Orchestrator locks table (for distributed deployments)
CREATE TABLE IF NOT EXISTS orchestrator_locks (
    id VARCHAR(50) PRIMARY KEY,
    instance_id VARCHAR(50) NOT NULL,
    acquired_at TIMESTAMPTZ DEFAULT NOW(),
    heartbeat_at TIMESTAMPTZ DEFAULT NOW()
);

-- Orchestrator status table (for monitoring)
CREATE TABLE IF NOT EXISTS orchestrator_status (
    id SERIAL PRIMARY KEY,
    instance_id VARCHAR(50) NOT NULL,
    active_bots_count INTEGER DEFAULT 0,
    total_trades_today INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'running',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    last_heartbeat TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_orchestrator_status_instance ON orchestrator_status(instance_id);

-- Function to check for stale bots (heartbeat older than 5 minutes)
CREATE OR REPLACE FUNCTION get_stale_bots(stale_minutes INTEGER DEFAULT 5)
RETURNS TABLE (
    bot_id UUID,
    tenant_id UUID,
    name VARCHAR,
    symbol VARCHAR,
    last_heartbeat TIMESTAMPTZ,
    minutes_since_heartbeat DOUBLE PRECISION
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        b.id as bot_id,
        b.tenant_id,
        b.name,
        b.symbol,
        b.heartbeat_at as last_heartbeat,
        EXTRACT(EPOCH FROM (NOW() - b.heartbeat_at)) / 60 as minutes_since_heartbeat
    FROM bots b
    WHERE b.status = 'running'
    AND (
        b.heartbeat_at IS NULL 
        OR b.heartbeat_at < NOW() - (stale_minutes || ' minutes')::INTERVAL
    );
END;
$$ LANGUAGE plpgsql;

-- Function to auto-stop stale bots
CREATE OR REPLACE FUNCTION auto_stop_stale_bots(stale_minutes INTEGER DEFAULT 10)
RETURNS INTEGER AS $$
DECLARE
    affected_count INTEGER;
BEGIN
    UPDATE bots
    SET 
        status = 'error',
        error_message = 'Automatically stopped: No heartbeat for ' || stale_minutes || ' minutes'
    WHERE status = 'running'
    AND (
        heartbeat_at IS NULL 
        OR heartbeat_at < NOW() - (stale_minutes || ' minutes')::INTERVAL
    );
    
    GET DIAGNOSTICS affected_count = ROW_COUNT;
    RETURN affected_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Backtesting Schema
-- Store backtest results for historical analysis
-- =====================================================

-- Backtest results table
CREATE TABLE IF NOT EXISTS backtest_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    symbol VARCHAR(50) NOT NULL,
    strategy VARCHAR(100) NOT NULL,
    timeframe VARCHAR(10) NOT NULL DEFAULT '15',
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    initial_capital DECIMAL(20, 8) NOT NULL DEFAULT 10000,
    final_capital DECIMAL(20, 8) NOT NULL,
    
    -- Core metrics (for quick filtering/sorting)
    total_trades INTEGER NOT NULL DEFAULT 0,
    winning_trades INTEGER NOT NULL DEFAULT 0,
    losing_trades INTEGER NOT NULL DEFAULT 0,
    win_rate DECIMAL(10, 4) NOT NULL DEFAULT 0,
    total_pnl DECIMAL(20, 8) NOT NULL DEFAULT 0,
    total_return DECIMAL(10, 4) NOT NULL DEFAULT 0,
    simple_apy DECIMAL(10, 4) NOT NULL DEFAULT 0,
    compound_apy DECIMAL(10, 4) NOT NULL DEFAULT 0,
    sharpe_ratio DECIMAL(10, 4) DEFAULT 0,
    max_drawdown DECIMAL(20, 8) DEFAULT 0,
    max_drawdown_percent DECIMAL(10, 4) DEFAULT 0,
    profit_factor DECIMAL(10, 4) DEFAULT 0,
    
    -- Full configuration and results as JSONB
    config JSONB NOT NULL DEFAULT '{}',
    indicators JSONB NOT NULL DEFAULT '{}',
    metrics JSONB NOT NULL DEFAULT '{}',
    equity_curve JSONB NOT NULL DEFAULT '[]',
    trades JSONB NOT NULL DEFAULT '[]',
    daily_returns JSONB NOT NULL DEFAULT '[]',
    monthly_returns JSONB NOT NULL DEFAULT '[]',
    
    -- Metadata
    execution_time_seconds DECIMAL(10, 4) DEFAULT 0,
    data_points_analyzed INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for backtest_results
CREATE INDEX IF NOT EXISTS idx_backtest_results_tenant ON backtest_results(tenant_id);
CREATE INDEX IF NOT EXISTS idx_backtest_results_symbol ON backtest_results(symbol);
CREATE INDEX IF NOT EXISTS idx_backtest_results_strategy ON backtest_results(strategy);
CREATE INDEX IF NOT EXISTS idx_backtest_results_created ON backtest_results(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_backtest_results_apy ON backtest_results(compound_apy DESC);
CREATE INDEX IF NOT EXISTS idx_backtest_results_win_rate ON backtest_results(win_rate DESC);

-- Enable RLS on backtest_results
ALTER TABLE backtest_results ENABLE ROW LEVEL SECURITY;

-- Policy for backtest_results
CREATE POLICY "Service role has full access to backtest_results" ON backtest_results FOR ALL USING (true);
