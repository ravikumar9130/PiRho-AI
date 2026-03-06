"use client";

import { BacktestResult, MonthlyReturn } from "@/lib/api";
import { MetricsGrid } from "./MetricsGrid";
import { EquityCurveChart, DrawdownChart } from "./EquityCurveChart";
import { TradeList } from "./TradeList";
import { cn } from "@/lib/utils";
import {
  Calendar,
  Clock,
  Database,
  TrendingUp,
  Activity,
} from "lucide-react";

interface BacktestResultsProps {
  result: BacktestResult;
}

export function BacktestResults({ result }: BacktestResultsProps) {
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card-cyber p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="text-xl font-display font-bold text-neon-400">
                {result.symbol}
              </span>
              <span className="px-3 py-1 text-xs font-mono uppercase tracking-wider bg-surface-800 text-surface-300 rounded">
                {result.strategy.replace(/_/g, " ")}
              </span>
              <span className="px-2 py-1 text-xs font-mono text-surface-400 bg-surface-900 rounded">
                {result.timeframe}m
              </span>
            </div>
            <div className="flex items-center gap-4 text-sm text-surface-400 font-mono">
              <div className="flex items-center gap-1.5">
                <Calendar className="h-4 w-4" />
                {formatDate(result.start_date)} - {formatDate(result.end_date)}
              </div>
              <div className="flex items-center gap-1.5">
                <Clock className="h-4 w-4" />
                {result.execution_time_seconds.toFixed(2)}s
              </div>
              <div className="flex items-center gap-1.5">
                <Database className="h-4 w-4" />
                {result.data_points_analyzed.toLocaleString()} candles
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-xs font-mono text-surface-400 uppercase tracking-wider">
                Total Return
              </p>
              <p
                className={cn(
                  "text-2xl font-display font-bold",
                  result.metrics.total_return >= 0 ? "text-neon-400" : "text-hotpink-400"
                )}
              >
                {result.metrics.total_return >= 0 ? "+" : ""}
                {result.metrics.total_return.toFixed(2)}%
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <MetricsGrid
        metrics={result.metrics}
        initialCapital={result.initial_capital}
        finalCapital={result.final_capital}
      />

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <EquityCurveChart
          data={result.equity_curve}
          initialCapital={result.initial_capital}
        />
        <DrawdownChart data={result.equity_curve} />
      </div>

      {/* Monthly Returns */}
      {result.monthly_returns.length > 0 && (
        <MonthlyReturnsChart returns={result.monthly_returns} />
      )}

      {/* Trade List */}
      <TradeList trades={result.trades} />
    </div>
  );
}

function MonthlyReturnsChart({ returns }: { returns: MonthlyReturn[] }) {
  const maxReturn = Math.max(...returns.map((r) => Math.abs(r.return_percent)));

  return (
    <div className="card-cyber p-6">
      <div className="flex items-center gap-2 mb-6">
        <Activity className="h-5 w-5 text-neon-400" />
        <h3 className="text-lg font-display font-semibold text-white">
          Monthly Returns
        </h3>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        {returns.map((month) => (
          <div
            key={month.month}
            className={cn(
              "p-3 rounded-lg text-center transition-colors",
              month.return_percent >= 0
                ? "bg-neon-500/10 hover:bg-neon-500/20"
                : "bg-hotpink-500/10 hover:bg-hotpink-500/20"
            )}
          >
            <p className="text-xs font-mono text-surface-400 mb-1">
              {month.month}
            </p>
            <p
              className={cn(
                "text-lg font-display font-bold",
                month.return_percent >= 0 ? "text-neon-400" : "text-hotpink-400"
              )}
            >
              {month.return_percent >= 0 ? "+" : ""}
              {month.return_percent.toFixed(1)}%
            </p>
            <p className="text-xs font-mono text-surface-500 mt-1">
              {month.trades} trades
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

