"use client";

import { cn } from "@/lib/utils";
import { BacktestMetrics } from "@/lib/api";
import {
  TrendingUp,
  TrendingDown,
  Target,
  Percent,
  Activity,
  Trophy,
  AlertTriangle,
  Clock,
  DollarSign,
  BarChart2,
  Zap,
} from "lucide-react";

interface MetricsGridProps {
  metrics: BacktestMetrics;
  initialCapital: number;
  finalCapital: number;
}

export function MetricsGrid({ metrics, initialCapital, finalCapital }: MetricsGridProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    const sign = value >= 0 ? "+" : "";
    return `${sign}${value.toFixed(2)}%`;
  };

  const metricsCards = [
    {
      label: "Total P&L",
      value: formatCurrency(metrics.total_pnl),
      subValue: formatPercent(metrics.total_return),
      icon: metrics.total_pnl >= 0 ? TrendingUp : TrendingDown,
      color: metrics.total_pnl >= 0 ? "neon" : "hotpink",
      highlight: true,
    },
    {
      label: "Simple APY",
      value: formatPercent(metrics.simple_apy),
      subValue: "Annualized",
      icon: BarChart2,
      color: metrics.simple_apy >= 0 ? "neon" : "hotpink",
      highlight: true,
    },
    {
      label: "Compound APY",
      value: formatPercent(metrics.compound_apy),
      subValue: "With reinvestment",
      icon: Zap,
      color: metrics.compound_apy >= 0 ? "neon" : "hotpink",
      highlight: true,
    },
    {
      label: "Win Rate",
      value: `${metrics.win_rate.toFixed(1)}%`,
      subValue: `${metrics.winning_trades}W / ${metrics.losing_trades}L`,
      icon: Target,
      color: metrics.win_rate >= 50 ? "neon" : "yellow",
    },
    {
      label: "Sharpe Ratio",
      value: metrics.sharpe_ratio.toFixed(2),
      subValue: metrics.sharpe_ratio >= 1 ? "Good" : metrics.sharpe_ratio >= 0.5 ? "Moderate" : "Low",
      icon: Activity,
      color: metrics.sharpe_ratio >= 1 ? "neon" : metrics.sharpe_ratio >= 0.5 ? "yellow" : "hotpink",
    },
    {
      label: "Max Drawdown",
      value: formatPercent(-metrics.max_drawdown_percent),
      subValue: formatCurrency(metrics.max_drawdown),
      icon: AlertTriangle,
      color: metrics.max_drawdown_percent <= 10 ? "neon" : metrics.max_drawdown_percent <= 20 ? "yellow" : "hotpink",
    },
    {
      label: "Profit Factor",
      value: metrics.profit_factor.toFixed(2),
      subValue: metrics.profit_factor >= 1.5 ? "Strong" : metrics.profit_factor >= 1 ? "Profitable" : "Losing",
      icon: Trophy,
      color: metrics.profit_factor >= 1.5 ? "neon" : metrics.profit_factor >= 1 ? "yellow" : "hotpink",
    },
    {
      label: "Total Trades",
      value: metrics.total_trades.toString(),
      subValue: `Avg duration: ${Math.round(metrics.average_trade_duration_minutes)}m`,
      icon: Activity,
      color: "surface",
    },
    {
      label: "Avg Win",
      value: formatCurrency(metrics.average_win),
      subValue: `Best: ${formatCurrency(metrics.largest_win)}`,
      icon: TrendingUp,
      color: "neon",
    },
    {
      label: "Avg Loss",
      value: formatCurrency(metrics.average_loss),
      subValue: `Worst: ${formatCurrency(metrics.largest_loss)}`,
      icon: TrendingDown,
      color: "hotpink",
    },
    {
      label: "Expectancy",
      value: formatCurrency(metrics.expectancy),
      subValue: "Per trade avg",
      icon: DollarSign,
      color: metrics.expectancy >= 0 ? "neon" : "hotpink",
    },
    {
      label: "Total Fees",
      value: formatCurrency(metrics.total_fees),
      subValue: `Slippage: ${formatCurrency(metrics.total_slippage)}`,
      icon: Clock,
      color: "surface",
    },
  ];

  const colorClasses = {
    neon: {
      bg: "bg-neon-500/10 border-neon-500/30",
      text: "text-neon-400",
      icon: "text-neon-400",
    },
    hotpink: {
      bg: "bg-hotpink-500/10 border-hotpink-500/30",
      text: "text-hotpink-400",
      icon: "text-hotpink-400",
    },
    yellow: {
      bg: "bg-yellow-500/10 border-yellow-500/30",
      text: "text-yellow-400",
      icon: "text-yellow-400",
    },
    purple: {
      bg: "bg-purple-500/10 border-purple-500/30",
      text: "text-purple-400",
      icon: "text-purple-400",
    },
    surface: {
      bg: "bg-surface-800/50 border-surface-700/30",
      text: "text-surface-300",
      icon: "text-surface-400",
    },
  };

  return (
    <div className="space-y-6">
      {/* Capital Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card-cyber p-6 text-center">
          <p className="text-xs font-mono text-surface-400 uppercase tracking-wider mb-2">
            Initial Capital
          </p>
          <p className="text-2xl font-display font-bold text-white">
            {formatCurrency(initialCapital)}
          </p>
        </div>
        <div className="card-cyber p-6 text-center relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-neon-500/5 to-magenta-500/5" />
          <p className="text-xs font-mono text-surface-400 uppercase tracking-wider mb-2 relative z-10">
            Final Capital
          </p>
          <p className={cn(
            "text-2xl font-display font-bold relative z-10",
            finalCapital >= initialCapital ? "text-neon-400" : "text-hotpink-400"
          )}>
            {formatCurrency(finalCapital)}
          </p>
        </div>
        <div className="card-cyber p-6 text-center">
          <p className="text-xs font-mono text-surface-400 uppercase tracking-wider mb-2">
            Streak
          </p>
          <p className="text-lg font-display">
            <span className="text-neon-400">{metrics.max_consecutive_wins} wins</span>
            <span className="text-surface-500 mx-2">/</span>
            <span className="text-hotpink-400">{metrics.max_consecutive_losses} losses</span>
          </p>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {metricsCards.map((card, index) => {
          const colors = colorClasses[card.color as keyof typeof colorClasses];
          return (
            <div
              key={card.label}
              className={cn(
                "rounded-xl border p-4 transition-all duration-200",
                colors.bg,
                card.highlight && "ring-1 ring-neon-500/20"
              )}
            >
              <div className="flex items-start justify-between mb-2">
                <span className="text-xs font-mono text-surface-400 uppercase tracking-wider">
                  {card.label}
                </span>
                <card.icon className={cn("h-4 w-4", colors.icon)} />
              </div>
              <p className={cn("text-xl font-display font-bold", colors.text)}>
                {card.value}
              </p>
              {card.subValue && (
                <p className="text-xs text-surface-500 mt-1 font-mono">
                  {card.subValue}
                </p>
              )}
            </div>
          );
        })}
      </div>

      {/* Best/Worst Days */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card-cyber p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="h-4 w-4 text-neon-400" />
            <span className="text-xs font-mono text-surface-400 uppercase tracking-wider">
              Best Day
            </span>
          </div>
          <p className="text-xl font-display font-bold text-neon-400">
            {formatCurrency(metrics.best_day)}
          </p>
        </div>
        <div className="card-cyber p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingDown className="h-4 w-4 text-hotpink-400" />
            <span className="text-xs font-mono text-surface-400 uppercase tracking-wider">
              Worst Day
            </span>
          </div>
          <p className="text-xl font-display font-bold text-hotpink-400">
            {formatCurrency(metrics.worst_day)}
          </p>
        </div>
      </div>
    </div>
  );
}

