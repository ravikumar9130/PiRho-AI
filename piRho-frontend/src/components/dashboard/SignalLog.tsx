"use client";

import { useState } from "react";
import { SignalLog } from "@/lib/api";
import { cn } from "@/lib/utils";
import { ChevronDown, ChevronUp, TrendingUp, TrendingDown, Clock } from "lucide-react";

interface SignalLogItemProps {
  log: SignalLog;
}

export function SignalLogItem({ log }: SignalLogItemProps) {
  const [expanded, setExpanded] = useState(false);

  const isBuy = log.signal === "BUY";
  const signalColor = isBuy ? "neon" : "hotpink";
  
  // Format timestamp
  const timestamp = new Date(log.created_at);
  const timeAgo = getTimeAgo(timestamp);

  return (
    <div className="border border-surface-800/50 rounded-xl bg-surface-900/30 hover:bg-surface-900/50 transition-all overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full p-4 flex items-center justify-between text-left hover:bg-surface-900/30 transition-colors"
      >
        <div className="flex items-center gap-4 flex-1 min-w-0">
          {/* Signal Badge */}
          <div
            className={cn(
              "flex items-center justify-center w-12 h-12 rounded-xl flex-shrink-0 border-2",
              isBuy
                ? "bg-neon-500/10 border-neon-500/30 text-neon-400"
                : "bg-hotpink-500/10 border-hotpink-500/30 text-hotpink-400"
            )}
          >
            {isBuy ? (
              <TrendingUp className="h-6 w-6" />
            ) : (
              <TrendingDown className="h-6 w-6" />
            )}
          </div>

          {/* Main Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-1">
              <span
                className={cn(
                  "text-sm font-display font-semibold uppercase tracking-wider",
                  isBuy ? "text-neon-400" : "text-hotpink-400"
                )}
              >
                {log.signal}
              </span>
              <span className="text-xs text-surface-400 font-mono">
                {log.symbol}
              </span>
              <span className="text-xs text-surface-500 font-mono">
                {log.strategy}
              </span>
            </div>
            <p className="text-sm text-surface-300 line-clamp-1">
              {log.signal_reason || "Signal triggered"}
            </p>
          </div>

          {/* Time */}
          <div className="flex items-center gap-2 text-xs text-surface-500 font-mono flex-shrink-0">
            <Clock className="h-3 w-3" />
            <span>{timeAgo}</span>
          </div>
        </div>

        {/* Expand Button */}
        <div className="ml-4 flex-shrink-0">
          {expanded ? (
            <ChevronUp className="h-5 w-5 text-surface-500" />
          ) : (
            <ChevronDown className="h-5 w-5 text-surface-500" />
          )}
        </div>
      </button>

      {/* Expanded Details */}
      {expanded && (
        <div className="px-4 pb-4 pt-0 border-t border-surface-800/50">
          <div className="mt-4 space-y-3">
            {/* Technical Indicators */}
            <div>
              <h4 className="text-xs text-surface-400 uppercase tracking-wider font-mono mb-2">
                Technical Context
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {log.market_data.price != null && (
                  <div className="bg-surface-900/50 rounded-lg p-2 border border-surface-800/50">
                    <div className="text-xs text-surface-500 font-mono mb-1">Price</div>
                    <div className="text-sm font-mono text-white">
                      ${Number(log.market_data.price).toFixed(2)}
                    </div>
                  </div>
                )}
                {log.market_data.rsi != null && (
                  <div className="bg-surface-900/50 rounded-lg p-2 border border-surface-800/50">
                    <div className="text-xs text-surface-500 font-mono mb-1">RSI</div>
                    <div className="text-sm font-mono text-white">
                      {Number(log.market_data.rsi).toFixed(1)}
                    </div>
                  </div>
                )}
                {log.market_data.ema_9 != null && (
                  <div className="bg-surface-900/50 rounded-lg p-2 border border-surface-800/50">
                    <div className="text-xs text-surface-500 font-mono mb-1">EMA 9</div>
                    <div className="text-sm font-mono text-white">
                      ${Number(log.market_data.ema_9).toFixed(2)}
                    </div>
                  </div>
                )}
                {log.market_data.ema_21 != null && (
                  <div className="bg-surface-900/50 rounded-lg p-2 border border-surface-800/50">
                    <div className="text-xs text-surface-500 font-mono mb-1">EMA 21</div>
                    <div className="text-sm font-mono text-white">
                      ${Number(log.market_data.ema_21).toFixed(2)}
                    </div>
                  </div>
                )}
                {log.market_data.direction_probability != null && (
                  <div className="bg-surface-900/50 rounded-lg p-2 border border-surface-800/50">
                    <div className="text-xs text-surface-500 font-mono mb-1">Direction Prob</div>
                    <div className="text-sm font-mono text-white">
                      {(Number(log.market_data.direction_probability) * 100).toFixed(1)}%
                    </div>
                  </div>
                )}
                {log.market_data.magnitude != null && (
                  <div className="bg-surface-900/50 rounded-lg p-2 border border-surface-800/50">
                    <div className="text-xs text-surface-500 font-mono mb-1">Magnitude</div>
                    <div className="text-sm font-mono text-white">
                      {Number(log.market_data.magnitude).toFixed(2)}%
                    </div>
                  </div>
                )}
                {log.funding_rate != null && (
                  <div className="bg-surface-900/50 rounded-lg p-2 border border-surface-800/50">
                    <div className="text-xs text-surface-500 font-mono mb-1">Funding Rate</div>
                    <div className="text-sm font-mono text-white">
                      {(Number(log.funding_rate) * 100).toFixed(4)}%
                    </div>
                  </div>
                )}
                {log.sentiment && (
                  <div className="bg-surface-900/50 rounded-lg p-2 border border-surface-800/50">
                    <div className="text-xs text-surface-500 font-mono mb-1">Sentiment</div>
                    <div className="text-sm font-mono text-white">{log.sentiment}</div>
                  </div>
                )}
              </div>
            </div>

            {/* Additional Context */}
            {Object.keys(log.market_data).length > 0 && (
              <div>
                <h4 className="text-xs text-surface-400 uppercase tracking-wider font-mono mb-2">
                  Additional Data
                </h4>
                <div className="bg-surface-900/50 rounded-lg p-3 border border-surface-800/50">
                  <pre className="text-xs font-mono text-surface-400 overflow-x-auto">
                    {JSON.stringify(log.market_data, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {/* Timestamp */}
            <div className="text-xs text-surface-500 font-mono pt-2 border-t border-surface-800/50">
              {timestamp.toLocaleString()}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function getTimeAgo(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

interface SignalLogListProps {
  logs: SignalLog[];
  loading?: boolean;
}

export function SignalLogList({ logs, loading }: SignalLogListProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(3)].map((_, i) => (
          <div
            key={i}
            className="border border-surface-800/50 rounded-xl bg-surface-900/30 h-20 animate-pulse"
          />
        ))}
      </div>
    );
  }

  if (logs.length === 0) {
    return (
      <div className="text-center py-8 text-surface-500">
        <TrendingUp className="h-12 w-12 mx-auto mb-3 text-surface-600" />
        <p className="font-mono text-sm">No signal logs yet</p>
        <p className="text-xs text-surface-600 mt-1">
          Signal logs will appear here when trades are triggered
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {logs.map((log) => (
        <SignalLogItem key={log.id} log={log} />
      ))}
    </div>
  );
}

