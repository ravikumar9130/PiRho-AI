"use client";

import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { Header } from "@/components/dashboard/Header";
import { api, Trade, PerformanceStats } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import { cn } from "@/lib/utils";
import { PageTransition, SlideIn } from "@/components/ui/PageTransition";
import { SkeletonStatCard, SkeletonTable } from "@/components/ui/Skeleton";
import { History, TrendingUp, TrendingDown } from "lucide-react";

export default function HistoryPage() {
  const { data: session } = useSession();
  const [trades, setTrades] = useState<Trade[]>([]);
  const [stats, setStats] = useState<PerformanceStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      if (!session?.accessToken) return;
      
      try {
        const [tradesData, statsData] = await Promise.all([
          api.getTrades(session.accessToken, 50),
          api.getPerformance(session.accessToken, 30),
        ]);
        // Filter for closed trades
        setTrades(tradesData.filter((t) => t.closed_at));
        setStats(statsData);
      } catch (error) {
        console.error("Failed to fetch history:", error);
      } finally {
        setLoading(false);
      }
    }
    
    fetchData();
  }, [session]);

  if (loading) {
    return (
      <>
        <Header title="Trade History" />
        <div className="p-4 lg:p-6 space-y-6">
          <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <SkeletonStatCard key={i} />
            ))}
          </div>
          <SkeletonTable rows={5} columns={6} />
        </div>
      </>
    );
  }

  return (
    <PageTransition>
      <Header title="Trade History" />
      <div className="p-4 lg:p-6 space-y-6">
        {/* Stats */}
        {stats && stats.total_trades > 0 && (
          <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
            <SlideIn delay={0}>
              <div className="stat-card">
                <span className="stat-label">Total Trades</span>
                <span className="stat-value">{stats.total_trades}</span>
              </div>
            </SlideIn>
            <SlideIn delay={50}>
              <div className="stat-card">
                <span className="stat-label">Win Rate</span>
                <span className="stat-value text-brand-400">{stats.win_rate.toFixed(1)}%</span>
              </div>
            </SlideIn>
            <SlideIn delay={100}>
              <div className="stat-card">
                <span className="stat-label">Total P&L</span>
                <span
                  className={cn(
                    "stat-value",
                    stats.total_profit_loss >= 0 ? "text-emerald-500" : "text-red-500"
                  )}
                >
                  {formatCurrency(stats.total_profit_loss)}
                </span>
              </div>
            </SlideIn>
            <SlideIn delay={150}>
              <div className="stat-card">
                <span className="stat-label">Profit Factor</span>
                <span className="stat-value">{stats.profit_factor.toFixed(2)}</span>
              </div>
            </SlideIn>
          </div>
        )}

        {/* Trades Table */}
        {trades.length === 0 ? (
          <SlideIn>
            <div className="card text-center py-12">
              <div className="h-16 w-16 rounded-2xl bg-surface-800 flex items-center justify-center mx-auto mb-4">
                <History className="h-8 w-8 text-surface-500" />
              </div>
              <h3 className="text-lg font-medium mb-2">No trade history</h3>
              <p className="text-surface-400">
                Your completed trades will appear here
              </p>
            </div>
          </SlideIn>
        ) : (
          <SlideIn delay={200}>
            <div className="card overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full min-w-[700px]">
                  <thead>
                    <tr className="border-b border-surface-800 bg-surface-850">
                      <th className="text-left py-3 px-4 text-sm font-medium text-surface-400">
                        Symbol
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-surface-400">
                        Side
                      </th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-surface-400">
                        Entry
                      </th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-surface-400">
                        Exit
                      </th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-surface-400">
                        P&L
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-surface-400">
                        Strategy
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-surface-400">
                        Closed
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {trades.map((trade, index) => (
                      <tr
                        key={trade.id}
                        className={cn(
                          "border-b border-surface-800/50 last:border-0",
                          "hover:bg-surface-800/30 transition-colors"
                        )}
                        style={{ animationDelay: `${index * 30}ms` }}
                      >
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{trade.symbol}</span>
                            {trade.is_paper && (
                              <span className="badge badge-warning text-xs">Paper</span>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={cn(
                              "badge",
                              trade.side === "BUY" ? "badge-success" : "badge-danger"
                            )}
                          >
                            {trade.side}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-sm">
                          {formatCurrency(trade.entry_price)}
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-sm">
                          {trade.exit_price ? formatCurrency(trade.exit_price) : "-"}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            {(trade.profit_loss || 0) >= 0 ? (
                              <TrendingUp className="h-4 w-4 text-emerald-500" />
                            ) : (
                              <TrendingDown className="h-4 w-4 text-red-500" />
                            )}
                            <span
                              className={cn(
                                "font-medium font-mono text-sm",
                                (trade.profit_loss || 0) >= 0
                                  ? "text-emerald-500"
                                  : "text-red-500"
                              )}
                            >
                              {formatCurrency(trade.profit_loss || 0)}
                            </span>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-sm text-surface-400">
                          {trade.strategy || "-"}
                        </td>
                        <td className="py-3 px-4 text-sm text-surface-400">
                          {trade.closed_at ? formatDate(trade.closed_at) : "-"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </SlideIn>
        )}
      </div>
    </PageTransition>
  );
}
