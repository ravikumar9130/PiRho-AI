"use client";

import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { Header } from "@/components/dashboard/Header";
import { api, Trade } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import { cn } from "@/lib/utils";
import { PageTransition, SlideIn } from "@/components/ui/PageTransition";
import { SkeletonList } from "@/components/ui/Skeleton";
import { Activity, TrendingUp, TrendingDown } from "lucide-react";

export default function PositionsPage() {
  const { data: session } = useSession();
  const [positions, setPositions] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      if (!session?.accessToken) return;
      
      try {
        const trades = await api.getTrades(session.accessToken, 50);
        // Filter for open positions (no closed_at)
        const openPositions = trades.filter((t) => !t.closed_at);
        setPositions(openPositions);
      } catch (error) {
        console.error("Failed to fetch positions:", error);
      } finally {
        setLoading(false);
      }
    }
    
    fetchData();
  }, [session]);

  if (loading) {
    return (
      <>
        <Header title="Positions" />
        <div className="p-4 lg:p-6">
          <SkeletonList items={3} />
        </div>
      </>
    );
  }

  return (
    <PageTransition>
      <Header title="Positions" />
      <div className="p-4 lg:p-6">
        {positions.length === 0 ? (
          <SlideIn>
            <div className="card text-center py-12">
              <div className="h-16 w-16 rounded-2xl bg-surface-800 flex items-center justify-center mx-auto mb-4">
                <Activity className="h-8 w-8 text-surface-500" />
              </div>
              <h3 className="text-lg font-medium mb-2">No open positions</h3>
              <p className="text-surface-400">
                Your active trades will appear here
              </p>
            </div>
          </SlideIn>
        ) : (
          <div className="space-y-4">
            {positions.map((position, index) => (
              <SlideIn key={position.id} delay={index * 50}>
                <div className="card-hover">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                      <div
                        className={cn(
                          "h-12 w-12 rounded-xl flex items-center justify-center flex-shrink-0",
                          position.side === "BUY"
                            ? "bg-emerald-500/10"
                            : "bg-red-500/10"
                        )}
                      >
                        {position.side === "BUY" ? (
                          <TrendingUp className="h-6 w-6 text-emerald-500" />
                        ) : (
                          <TrendingDown className="h-6 w-6 text-red-500" />
                        )}
                      </div>
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-semibold text-lg">{position.symbol}</span>
                          <span
                            className={cn(
                              "badge",
                              position.side === "BUY" ? "badge-success" : "badge-danger"
                            )}
                          >
                            {position.side}
                          </span>
                          {position.is_paper && (
                            <span className="badge badge-warning">Paper</span>
                          )}
                        </div>
                        <p className="text-sm text-surface-400 mt-1">
                          {position.strategy || "Manual"} • {position.leverage}x leverage
                        </p>
                      </div>
                    </div>

                    <div className="text-left sm:text-right">
                      <p className="font-semibold text-lg font-mono">
                        {formatCurrency(position.entry_price)}
                      </p>
                      <p className="text-sm text-surface-400">
                        Entry • {position.quantity} contracts
                      </p>
                    </div>
                  </div>

                  <div className="mt-4 pt-4 border-t border-surface-800 flex flex-wrap items-center justify-between gap-2 text-sm">
                    <span className="text-surface-400">
                      Opened {formatDate(position.opened_at)}
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="text-surface-500">Position ID:</span>
                      <code className="text-xs bg-surface-800 px-2 py-1 rounded font-mono">
                        {position.id.slice(0, 8)}...
                      </code>
                    </div>
                  </div>
                </div>
              </SlideIn>
            ))}
          </div>
        )}
      </div>
    </PageTransition>
  );
}
