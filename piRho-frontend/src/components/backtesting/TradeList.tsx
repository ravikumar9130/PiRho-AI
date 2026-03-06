"use client";

import { useState, useMemo } from "react";
import { cn } from "@/lib/utils";
import { BacktestTradeDetail } from "@/lib/api";
import {
  ArrowUpCircle,
  ArrowDownCircle,
  ChevronUp,
  ChevronDown,
  Clock,
  Search,
  Download,
} from "lucide-react";

interface TradeListProps {
  trades: BacktestTradeDetail[];
}

type SortField = "trade_id" | "entry_time" | "pnl" | "pnl_percent" | "duration_minutes";
type SortDirection = "asc" | "desc";

export function TradeList({ trades }: TradeListProps) {
  const [sortField, setSortField] = useState<SortField>("trade_id");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
  const [filter, setFilter] = useState<"all" | "wins" | "losses">("all");
  const [searchTerm, setSearchTerm] = useState("");

  const filteredAndSortedTrades = useMemo(() => {
    let result = [...trades];

    // Filter
    if (filter === "wins") {
      result = result.filter((t) => t.pnl > 0);
    } else if (filter === "losses") {
      result = result.filter((t) => t.pnl < 0);
    }

    // Search
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter(
        (t) =>
          t.exit_reason.toLowerCase().includes(term) ||
          (t.signal_reason && t.signal_reason.toLowerCase().includes(term))
      );
    }

    // Sort
    result.sort((a, b) => {
      let comparison = 0;
      switch (sortField) {
        case "trade_id":
          comparison = a.trade_id - b.trade_id;
          break;
        case "entry_time":
          comparison = new Date(a.entry_time).getTime() - new Date(b.entry_time).getTime();
          break;
        case "pnl":
          comparison = a.pnl - b.pnl;
          break;
        case "pnl_percent":
          comparison = a.pnl_percent - b.pnl_percent;
          break;
        case "duration_minutes":
          comparison = a.duration_minutes - b.duration_minutes;
          break;
      }
      return sortDirection === "asc" ? comparison : -comparison;
    });

    return result;
  }, [trades, sortField, sortDirection, filter, searchTerm]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  const formatCurrency = (value: number) => {
    const sign = value >= 0 ? "+" : "";
    return `${sign}$${Math.abs(value).toFixed(2)}`;
  };

  const formatPercent = (value: number) => {
    const sign = value >= 0 ? "+" : "";
    return `${sign}${value.toFixed(2)}%`;
  };

  const formatDuration = (minutes: number) => {
    if (minutes < 60) return `${minutes}m`;
    if (minutes < 1440) return `${Math.floor(minutes / 60)}h ${minutes % 60}m`;
    return `${Math.floor(minutes / 1440)}d ${Math.floor((minutes % 1440) / 60)}h`;
  };

  const exportCSV = () => {
    const headers = [
      "Trade ID",
      "Entry Time",
      "Exit Time",
      "Side",
      "Entry Price",
      "Exit Price",
      "Quantity",
      "Leverage",
      "P&L",
      "P&L %",
      "Fees",
      "Exit Reason",
      "Duration (min)",
    ];

    const rows = trades.map((t) => [
      t.trade_id,
      t.entry_time,
      t.exit_time,
      t.side,
      t.entry_price,
      t.exit_price,
      t.quantity,
      t.leverage,
      t.pnl,
      t.pnl_percent,
      t.fees,
      t.exit_reason,
      t.duration_minutes,
    ]);

    const csv = [headers, ...rows].map((row) => row.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "backtest_trades.csv";
    a.click();
  };

  const SortButton = ({ field, label }: { field: SortField; label: string }) => (
    <button
      onClick={() => handleSort(field)}
      className="flex items-center gap-1 text-xs font-mono uppercase tracking-wider text-surface-400 hover:text-white transition-colors"
    >
      {label}
      {sortField === field && (
        sortDirection === "asc" ? (
          <ChevronUp className="h-3 w-3" />
        ) : (
          <ChevronDown className="h-3 w-3" />
        )
      )}
    </button>
  );

  return (
    <div className="card-cyber p-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h3 className="text-lg font-display font-semibold text-white">
            Trade History
          </h3>
          <p className="text-xs text-surface-400 font-mono mt-1">
            {filteredAndSortedTrades.length} of {trades.length} trades
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-surface-500" />
            <input
              type="text"
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-cyber pl-10 py-1.5 text-sm w-48"
            />
          </div>

          {/* Filter */}
          <div className="flex items-center gap-1 p-1 bg-surface-900 rounded-lg">
            {["all", "wins", "losses"].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f as typeof filter)}
                className={cn(
                  "px-3 py-1 text-xs font-mono uppercase tracking-wider rounded-md transition-colors",
                  filter === f
                    ? "bg-neon-500/20 text-neon-400"
                    : "text-surface-400 hover:text-white"
                )}
              >
                {f}
              </button>
            ))}
          </div>

          {/* Export */}
          <button
            onClick={exportCSV}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-mono uppercase tracking-wider text-surface-400 hover:text-neon-400 bg-surface-900 rounded-lg transition-colors"
          >
            <Download className="h-4 w-4" />
            CSV
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-surface-800">
              <th className="text-left py-3 px-2">
                <SortButton field="trade_id" label="#" />
              </th>
              <th className="text-left py-3 px-2">
                <SortButton field="entry_time" label="Time" />
              </th>
              <th className="text-left py-3 px-2">
                <span className="text-xs font-mono uppercase tracking-wider text-surface-400">
                  Side
                </span>
              </th>
              <th className="text-right py-3 px-2">
                <span className="text-xs font-mono uppercase tracking-wider text-surface-400">
                  Entry
                </span>
              </th>
              <th className="text-right py-3 px-2">
                <span className="text-xs font-mono uppercase tracking-wider text-surface-400">
                  Exit
                </span>
              </th>
              <th className="text-right py-3 px-2">
                <SortButton field="pnl" label="P&L" />
              </th>
              <th className="text-right py-3 px-2">
                <SortButton field="pnl_percent" label="%" />
              </th>
              <th className="text-right py-3 px-2">
                <SortButton field="duration_minutes" label="Duration" />
              </th>
              <th className="text-left py-3 px-2">
                <span className="text-xs font-mono uppercase tracking-wider text-surface-400">
                  Exit Reason
                </span>
              </th>
            </tr>
          </thead>
          <tbody>
            {filteredAndSortedTrades.slice(0, 100).map((trade) => (
              <tr
                key={trade.trade_id}
                className="border-b border-surface-800/50 hover:bg-surface-900/50 transition-colors"
              >
                <td className="py-3 px-2">
                  <span className="text-sm font-mono text-surface-400">
                    {trade.trade_id}
                  </span>
                </td>
                <td className="py-3 px-2">
                  <div className="text-sm">
                    <p className="text-white font-mono">
                      {new Date(trade.entry_time).toLocaleDateString()}
                    </p>
                    <p className="text-xs text-surface-500 font-mono">
                      {new Date(trade.entry_time).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </p>
                  </div>
                </td>
                <td className="py-3 px-2">
                  <div className="flex items-center gap-1.5">
                    {trade.side === "BUY" ? (
                      <ArrowUpCircle className="h-4 w-4 text-neon-400" />
                    ) : (
                      <ArrowDownCircle className="h-4 w-4 text-hotpink-400" />
                    )}
                    <span
                      className={cn(
                        "text-sm font-mono",
                        trade.side === "BUY" ? "text-neon-400" : "text-hotpink-400"
                      )}
                    >
                      {trade.side}
                    </span>
                  </div>
                </td>
                <td className="py-3 px-2 text-right">
                  <span className="text-sm font-mono text-white">
                    ${trade.entry_price.toFixed(2)}
                  </span>
                </td>
                <td className="py-3 px-2 text-right">
                  <span className="text-sm font-mono text-white">
                    ${trade.exit_price.toFixed(2)}
                  </span>
                </td>
                <td className="py-3 px-2 text-right">
                  <span
                    className={cn(
                      "text-sm font-mono font-medium",
                      trade.pnl >= 0 ? "text-neon-400" : "text-hotpink-400"
                    )}
                  >
                    {formatCurrency(trade.pnl)}
                  </span>
                </td>
                <td className="py-3 px-2 text-right">
                  <span
                    className={cn(
                      "text-sm font-mono",
                      trade.pnl_percent >= 0 ? "text-neon-400" : "text-hotpink-400"
                    )}
                  >
                    {formatPercent(trade.pnl_percent)}
                  </span>
                </td>
                <td className="py-3 px-2 text-right">
                  <div className="flex items-center justify-end gap-1 text-surface-400">
                    <Clock className="h-3 w-3" />
                    <span className="text-sm font-mono">
                      {formatDuration(trade.duration_minutes)}
                    </span>
                  </div>
                </td>
                <td className="py-3 px-2">
                  <span
                    className={cn(
                      "text-xs font-mono px-2 py-1 rounded",
                      trade.exit_reason === "Take Profit" &&
                        "bg-neon-500/10 text-neon-400",
                      trade.exit_reason === "Stop Loss" &&
                        "bg-hotpink-500/10 text-hotpink-400",
                      trade.exit_reason === "Signal Reversal" &&
                        "bg-purple-500/10 text-purple-400",
                      !["Take Profit", "Stop Loss", "Signal Reversal"].includes(
                        trade.exit_reason
                      ) && "bg-surface-800 text-surface-300"
                    )}
                  >
                    {trade.exit_reason}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredAndSortedTrades.length > 100 && (
          <p className="text-center text-sm text-surface-500 py-4 font-mono">
            Showing first 100 of {filteredAndSortedTrades.length} trades
          </p>
        )}

        {filteredAndSortedTrades.length === 0 && (
          <p className="text-center text-sm text-surface-500 py-8 font-mono">
            No trades match your criteria
          </p>
        )}
      </div>
    </div>
  );
}

