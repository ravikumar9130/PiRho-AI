"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { Header } from "@/components/dashboard/Header";
import { BacktestConfigForm, BacktestResults } from "@/components/backtesting";
import { api, BacktestRequest, BacktestResult, BacktestResultSummary } from "@/lib/api";
import { PageTransition, SlideIn } from "@/components/ui/PageTransition";
import { cn } from "@/lib/utils";
import {
  FlaskConical,
  History,
  Trash2,
  Eye,
  Calendar,
  TrendingUp,
  TrendingDown,
  Clock,
  AlertCircle,
} from "lucide-react";

export default function BacktestingPage() {
  const { data: session } = useSession();
  const [strategies, setStrategies] = useState<string[]>([]);
  const [symbols, setSymbols] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [history, setHistory] = useState<BacktestResultSummary[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Fetch available strategies and symbols
  useEffect(() => {
    async function fetchOptions() {
      try {
        const [strategiesRes, symbolsRes] = await Promise.all([
          session?.accessToken
            ? api.getBacktestStrategies(session.accessToken)
            : Promise.resolve({ strategies: [], all_strategies: [] }),
          api.getBacktestSymbols(),
        ]);

        setStrategies(
          strategiesRes.all_strategies?.length > 0
            ? strategiesRes.all_strategies
            : [
                "MA_Crossover",
                "RSI_Divergence",
                "Supertrend_MACD",
                "BB_Squeeze_Breakout",
                "Momentum_VWAP_RSI",
                "EMA_Cross_RSI",
                "Volume_Spread_Analysis",
                "Volatility_Cluster_Reversal",
                "Reversal_Detector",
              ]
        );
        setSymbols(
          symbolsRes.symbols?.length > 0
            ? symbolsRes.symbols
            : ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT"]
        );
      } catch (err) {
        console.error("Failed to fetch options:", err);
        // Use defaults
        setStrategies([
          "MA_Crossover",
          "RSI_Divergence",
          "Supertrend_MACD",
          "BB_Squeeze_Breakout",
        ]);
        setSymbols(["BTCUSDT", "ETHUSDT", "SOLUSDT"]);
      }
    }

    fetchOptions();
  }, [session?.accessToken]);

  // Fetch history
  const fetchHistory = async () => {
    if (!session?.accessToken) return;

    setLoadingHistory(true);
    try {
      const res = await api.getBacktestHistory(session.accessToken);
      setHistory(res.results);
    } catch (err) {
      console.error("Failed to fetch history:", err);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    if (showHistory) {
      fetchHistory();
    }
  }, [showHistory, session?.accessToken]);

  const handleRunBacktest = async (config: BacktestRequest) => {
    if (!session?.accessToken) {
      setError("Please log in to run backtests");
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await api.runBacktest(session.accessToken, config);
      setResult(res);

      // Refresh history if saving
      if (config.save_result) {
        fetchHistory();
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Backtest failed";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewResult = async (resultId: string) => {
    if (!session?.accessToken) return;

    setIsLoading(true);
    setError(null);

    try {
      const res = await api.getBacktestResult(session.accessToken, resultId);
      setResult(res);
      setShowHistory(false);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load result";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteResult = async (resultId: string) => {
    if (!session?.accessToken) return;

    try {
      await api.deleteBacktestResult(session.accessToken, resultId);
      setHistory((prev) => prev.filter((r) => r.result_id !== resultId));
    } catch (err) {
      console.error("Failed to delete result:", err);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  return (
    <PageTransition>
      <Header title="Backtesting" />

      <div className="p-4 lg:p-6 space-y-6">
        {/* Header Banner */}
        <SlideIn delay={0}>
          <div className="card-cyber p-6 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-neon-500/5 via-purple-500/5 to-magenta-500/5" />
            <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-xl bg-neon-500/10 border border-neon-500/20">
                  <FlaskConical className="h-6 w-6 text-neon-400" />
                </div>
                <div>
                  <h2 className="text-xl font-display font-bold text-white">
                    Strategy Backtesting
                  </h2>
                  <p className="text-sm text-surface-400 font-mono mt-1">
                    Test your trading strategies against historical market data
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={() => {
                    setShowHistory(!showHistory);
                    setResult(null);
                  }}
                  className={cn(
                    "flex items-center gap-2 px-4 py-2 rounded-lg font-mono text-xs uppercase tracking-wider transition-colors",
                    showHistory
                      ? "bg-neon-500/20 text-neon-400"
                      : "bg-surface-800 text-surface-300 hover:bg-surface-700"
                  )}
                >
                  <History className="h-4 w-4" />
                  History
                </button>
              </div>
            </div>
          </div>
        </SlideIn>

        {/* Error Display */}
        {error && (
          <SlideIn delay={50}>
            <div className="bg-hotpink-500/10 border border-hotpink-500/20 rounded-xl p-4 flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-hotpink-400 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-hotpink-400">
                  Backtest Error
                </p>
                <p className="text-sm text-surface-300 mt-1">{error}</p>
              </div>
            </div>
          </SlideIn>
        )}

        {/* Main Content */}
        {showHistory ? (
          <SlideIn delay={100}>
            <div className="card-cyber p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-display font-semibold text-white">
                  Saved Backtests
                </h3>
                <span className="text-xs font-mono text-surface-400">
                  {history.length} results
                </span>
              </div>

              {loadingHistory ? (
                <div className="flex items-center justify-center py-12">
                  <Clock className="h-6 w-6 text-neon-400 animate-spin" />
                </div>
              ) : history.length === 0 ? (
                <div className="text-center py-12">
                  <FlaskConical className="h-12 w-12 mx-auto text-surface-600 mb-3" />
                  <p className="text-surface-400 font-mono">
                    No saved backtests yet
                  </p>
                  <p className="text-sm text-surface-500 mt-1">
                    Run a backtest and enable &quot;Save result&quot; to see it here
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {history.map((item) => (
                    <div
                      key={item.result_id}
                      className="flex items-center justify-between p-4 rounded-xl bg-surface-900/50 border border-surface-800/50 hover:border-neon-500/20 transition-colors"
                    >
                      <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-bold text-neon-400">
                            {item.symbol}
                          </span>
                          <span className="text-xs font-mono text-surface-500 px-2 py-0.5 bg-surface-800 rounded">
                            {item.strategy.replace(/_/g, " ")}
                          </span>
                        </div>
                        <div className="flex items-center gap-1 text-xs text-surface-400 font-mono">
                          <Calendar className="h-3 w-3" />
                          {formatDate(item.start_date)} - {formatDate(item.end_date)}
                        </div>
                      </div>

                      <div className="flex items-center gap-6">
                        <div className="text-right">
                          <p className="text-xs text-surface-500 font-mono">
                            Win Rate
                          </p>
                          <p className="text-sm font-mono text-white">
                            {item.win_rate.toFixed(1)}%
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-surface-500 font-mono">
                            Return
                          </p>
                          <p
                            className={cn(
                              "text-sm font-mono font-medium flex items-center gap-1",
                              item.total_return >= 0
                                ? "text-neon-400"
                                : "text-hotpink-400"
                            )}
                          >
                            {item.total_return >= 0 ? (
                              <TrendingUp className="h-3 w-3" />
                            ) : (
                              <TrendingDown className="h-3 w-3" />
                            )}
                            {item.total_return >= 0 ? "+" : ""}
                            {item.total_return.toFixed(2)}%
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-surface-500 font-mono">
                            APY
                          </p>
                          <p
                            className={cn(
                              "text-sm font-mono font-medium",
                              item.compound_apy >= 0
                                ? "text-neon-400"
                                : "text-hotpink-400"
                            )}
                          >
                            {item.compound_apy >= 0 ? "+" : ""}
                            {item.compound_apy.toFixed(1)}%
                          </p>
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleViewResult(item.result_id)}
                            className="p-2 rounded-lg bg-surface-800 hover:bg-neon-500/20 text-surface-400 hover:text-neon-400 transition-colors"
                            title="View details"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteResult(item.result_id)}
                            className="p-2 rounded-lg bg-surface-800 hover:bg-hotpink-500/20 text-surface-400 hover:text-hotpink-400 transition-colors"
                            title="Delete"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </SlideIn>
        ) : result ? (
          <SlideIn delay={100}>
            <div className="space-y-6">
              <button
                onClick={() => setResult(null)}
                className="text-sm font-mono text-surface-400 hover:text-neon-400 transition-colors"
              >
                ← Back to configuration
              </button>
              <BacktestResults result={result} />
            </div>
          </SlideIn>
        ) : (
          <SlideIn delay={100}>
            <BacktestConfigForm
              strategies={strategies}
              symbols={symbols}
              onSubmit={handleRunBacktest}
              isLoading={isLoading}
            />
          </SlideIn>
        )}
      </div>
    </PageTransition>
  );
}

