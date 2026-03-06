const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface ApiError {
  detail: string;
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {},
  token?: string
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error: ApiError = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail);
  }

  return response.json();
}

export const api = {
  // Auth
  register: (data: { email: string; password: string; name?: string; promo_code?: string }) =>
    fetchApi<{ access_token: string; refresh_token: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  login: (data: { email: string; password: string }) =>
    fetchApi<{ access_token: string; refresh_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  refresh: (refreshToken: string) =>
    fetchApi<{ access_token: string; refresh_token: string }>("/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    }),

  // User
  getProfile: (token: string) =>
    fetchApi<{ id: string; email: string; name: string }>("/users/me", {}, token),

  getDashboard: (token: string) =>
    fetchApi<DashboardStats>("/users/dashboard", {}, token),

  // Bots
  getBots: (token: string) =>
    fetchApi<Bot[]>("/bots", {}, token),

  createBot: (token: string, data: CreateBotData) =>
    fetchApi<Bot>("/bots", { method: "POST", body: JSON.stringify(data) }, token),

  startBot: (token: string, botId: string) =>
    fetchApi<Bot>(`/bots/${botId}/start`, { method: "POST" }, token),

  stopBot: (token: string, botId: string) =>
    fetchApi<Bot>(`/bots/${botId}/stop`, { method: "POST" }, token),

  deleteBot: (token: string, botId: string) =>
    fetchApi<void>(`/bots/${botId}`, { method: "DELETE" }, token),

  getStrategies: (token: string) =>
    fetchApi<{ strategies: string[] }>("/bots/strategies/available", {}, token),

  // Trades
  getTrades: (token: string, limit: number = 50) =>
    fetchApi<Trade[]>(`/trades?limit=${limit}`, {}, token),

  getPerformance: (token: string, days: number = 30) =>
    fetchApi<PerformanceStats>(`/trades/performance?days=${days}`, {}, token),

  getDailySummary: (token: string, days: number = 7) =>
    fetchApi<{ summary: DailySummary[] }>(`/trades/daily-summary?days=${days}`, {}, token),

  getSignalLogs: (token: string, limit: number = 50, botId?: string) => {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (botId) params.append("bot_id", botId);
    return fetchApi<SignalLog[]>(`/trades/signals?${params.toString()}`, {}, token);
  },

  // Billing / Promo
  getPlans: () => fetchApi<{ plans: Plan[] }>("/billing/plans"),

  getCurrentPlan: (token: string) =>
    fetchApi<{ plan: string; promo_code_used?: string }>("/billing/current-plan", {}, token),

  applyPromoCode: (token: string, code: string) =>
    fetchApi<{ success: boolean; message: string; plan: string }>("/billing/apply-promo", {
      method: "POST",
      body: JSON.stringify({ code }),
    }, token),

  // Exchange Credentials
  addCredentials: (token: string, data: AddCredentialsData) =>
    fetchApi<ExchangeCredential>("/users/exchange-credentials", {
      method: "POST",
      body: JSON.stringify(data),
    }, token),

  getCredentials: (token: string) =>
    fetchApi<ExchangeCredential[]>("/users/exchange-credentials", {}, token),

  deleteCredentials: (token: string, credId: string) =>
    fetchApi<void>(`/users/exchange-credentials/${credId}`, { method: "DELETE" }, token),

  // Backtesting
  getBacktestStrategies: (token: string) =>
    fetchApi<{ strategies: string[]; all_strategies: string[] }>("/backtesting/strategies", {}, token),

  getBacktestSymbols: () =>
    fetchApi<{ symbols: string[] }>("/backtesting/symbols"),

  runBacktest: (token: string, config: BacktestRequest) =>
    fetchApi<BacktestResult>("/backtesting/run", {
      method: "POST",
      body: JSON.stringify(config),
    }, token),

  getBacktestHistory: (token: string, limit: number = 50) =>
    fetchApi<BacktestHistoryResponse>(`/backtesting/history?limit=${limit}`, {}, token),

  getBacktestResult: (token: string, resultId: string) =>
    fetchApi<BacktestResult>(`/backtesting/results/${resultId}`, {}, token),

  deleteBacktestResult: (token: string, resultId: string) =>
    fetchApi<void>(`/backtesting/results/${resultId}`, { method: "DELETE" }, token),
};

// Types
export interface DashboardStats {
  total_balance: number;
  unrealized_pnl: number;
  today_pnl: number;
  active_positions: number;
  running_bots: number;
  total_trades_today: number;
  win_rate_7d: number;
}

export interface Bot {
  id: string;
  tenant_id: string;
  name: string;
  symbol: string;
  strategy: string;
  status: "stopped" | "running" | "error" | "paused";
  config: Record<string, unknown>;
  created_at: string;
  last_active_at: string | null;
}

export interface CreateBotData {
  name: string;
  symbol: string;
  strategy: string;
  config?: {
    leverage?: number;
    risk_per_trade?: number;
    stop_loss_percent?: number;
    take_profit_percent?: number;
    paper_trading?: boolean;
  };
}

export interface Trade {
  id: string;
  symbol: string;
  side: "BUY" | "SELL";
  entry_price: number;
  exit_price: number | null;
  quantity: number;
  leverage: number;
  profit_loss: number | null;
  profit_loss_percent: number | null;
  strategy: string | null;
  exit_reason: string | null;
  opened_at: string;
  closed_at: string | null;
  is_paper: boolean;
}

export interface PerformanceStats {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_profit_loss: number;
  average_profit: number;
  average_loss: number;
  max_drawdown: number;
  profit_factor: number;
}

export interface DailySummary {
  date: string;
  pnl: number;
}

export interface Plan {
  id: string;
  name: string;
  price: number;
  features: string[];
  promo_available?: boolean;
}

export interface ExchangeCredential {
  id: string;
  exchange: string;
  is_testnet: boolean;
  api_key_masked: string;
  created_at: string;
}

export interface AddCredentialsData {
  exchange: "bybit";
  api_key: string;
  api_secret: string;
  is_testnet: boolean;
}

export interface SignalLog {
  id: string;
  tenant_id: string;
  bot_id: string | null;
  trade_id: string | null;
  symbol: string;
  signal: "BUY" | "SELL";
  strategy: string;
  signal_reason: string | null;
  market_data: Record<string, unknown>;
  sentiment: string | null;
  funding_rate: number | null;
  created_at: string;
}

// Backtesting Types
export interface IndicatorConfig {
  enabled?: boolean;
  rsi_period?: number;
  rsi_overbought?: number;
  rsi_oversold?: number;
  macd_fast?: number;
  macd_slow?: number;
  macd_signal?: number;
  ema_short?: number;
  ema_medium?: number;
  ema_long?: number;
  ema_trend?: number;
  bb_period?: number;
  bb_std_dev?: number;
  atr_period?: number;
  supertrend_period?: number;
  supertrend_multiplier?: number;
  vwap_enabled?: boolean;
}

export interface BacktestConfig {
  initial_capital?: number;
  leverage?: number;
  risk_per_trade?: number;
  stop_loss_percent?: number;
  take_profit_percent?: number;
  use_trailing_stop?: boolean;
  trailing_stop_percent?: number;
  slippage_percent?: number;
  commission_percent?: number;
  max_trades_per_day?: number;
}

export interface BacktestRequest {
  symbol: string;
  start_date: string;
  end_date: string;
  strategy: string;
  timeframe?: string;
  indicators?: IndicatorConfig;
  config?: BacktestConfig;
  save_result?: boolean;
}

export interface BacktestTradeDetail {
  trade_id: number;
  entry_time: string;
  exit_time: string;
  side: string;
  entry_price: number;
  exit_price: number;
  quantity: number;
  leverage: number;
  pnl: number;
  pnl_percent: number;
  fees: number;
  exit_reason: string;
  signal_reason: string | null;
  duration_minutes: number;
}

export interface EquityCurvePoint {
  timestamp: string;
  equity: number;
  drawdown: number;
  drawdown_percent: number;
}

export interface DailyReturn {
  date: string;
  pnl: number;
  return_percent: number;
  trades: number;
}

export interface MonthlyReturn {
  month: string;
  pnl: number;
  return_percent: number;
  trades: number;
}

export interface BacktestMetrics {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  total_return: number;
  simple_apy: number;
  compound_apy: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown: number;
  max_drawdown_percent: number;
  profit_factor: number;
  average_win: number;
  average_loss: number;
  largest_win: number;
  largest_loss: number;
  average_trade_duration_minutes: number;
  total_fees: number;
  total_slippage: number;
  best_day: number;
  worst_day: number;
  max_consecutive_wins: number;
  max_consecutive_losses: number;
  expectancy: number;
}

export interface BacktestResult {
  result_id: string | null;
  symbol: string;
  strategy: string;
  start_date: string;
  end_date: string;
  timeframe: string;
  initial_capital: number;
  final_capital: number;
  config: BacktestConfig;
  indicators: IndicatorConfig;
  metrics: BacktestMetrics;
  equity_curve: EquityCurvePoint[];
  trades: BacktestTradeDetail[];
  daily_returns: DailyReturn[];
  monthly_returns: MonthlyReturn[];
  execution_time_seconds: number;
  data_points_analyzed: number;
  created_at: string | null;
}

export interface BacktestResultSummary {
  result_id: string;
  symbol: string;
  strategy: string;
  start_date: string;
  end_date: string;
  total_trades: number;
  win_rate: number;
  total_return: number;
  simple_apy: number;
  compound_apy: number;
  sharpe_ratio: number;
  max_drawdown_percent: number;
  created_at: string;
}

export interface BacktestHistoryResponse {
  results: BacktestResultSummary[];
  total: number;
}
