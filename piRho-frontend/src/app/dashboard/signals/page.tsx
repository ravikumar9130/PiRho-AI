"use client";

import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { Header } from "@/components/dashboard/Header";
import { api, SignalLog, Bot } from "@/lib/api";
import { PageTransition, SlideIn } from "@/components/ui/PageTransition";
import { SignalLogList } from "@/components/dashboard/SignalLog";
import { SkeletonStatCard } from "@/components/ui/Skeleton";
import { TrendingUp, TrendingDown, Filter, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

export default function SignalsPage() {
  const { data: session } = useSession();
  const [signalLogs, setSignalLogs] = useState<SignalLog[]>([]);
  const [bots, setBots] = useState<Bot[]>([]);
  const [selectedBotId, setSelectedBotId] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    async function fetchData() {
      if (!session?.accessToken) return;
      
      try {
        const [logsData, botsData] = await Promise.all([
          api.getSignalLogs(session.accessToken, 100, selectedBotId),
          api.getBots(session.accessToken),
        ]);
        setSignalLogs(logsData);
        setBots(botsData);
      } catch (error) {
        console.error("Failed to fetch signal logs:", error);
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    }
    
    fetchData();
  }, [session, selectedBotId]);

  const handleRefresh = async () => {
    if (!session?.accessToken) return;
    setRefreshing(true);
    try {
      const logsData = await api.getSignalLogs(session.accessToken, 100, selectedBotId);
      setSignalLogs(logsData);
    } catch (error) {
      console.error("Failed to refresh signal logs:", error);
    } finally {
      setRefreshing(false);
    }
  };

  // Calculate stats
  const buySignals = signalLogs.filter((log) => log.signal === "BUY").length;
  const sellSignals = signalLogs.filter((log) => log.signal === "SELL").length;
  const uniqueStrategies = new Set(signalLogs.map((log) => log.strategy)).size;
  const uniqueSymbols = new Set(signalLogs.map((log) => log.symbol)).size;

  if (loading) {
    return (
      <>
        <Header title="Signal Log" />
        <div className="p-4 lg:p-6 space-y-6">
          <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <SkeletonStatCard key={i} />
            ))}
          </div>
          <div className="card-cyber">
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div
                  key={i}
                  className="border border-surface-800/50 rounded-xl bg-surface-900/30 h-20 animate-pulse"
                />
              ))}
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <PageTransition>
      <Header title="Signal Log" />
      <div className="p-4 lg:p-6 space-y-6">
        {/* Stats */}
        <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
          <SlideIn delay={0}>
            <div className="card-cyber p-5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-surface-400 uppercase tracking-wider font-mono">
                  Total Signals
                </span>
                <TrendingUp className="h-5 w-5 text-neon-400" />
              </div>
              <span className="text-2xl font-display font-bold text-white">
                {signalLogs.length}
              </span>
            </div>
          </SlideIn>
          <SlideIn delay={50}>
            <div className="card-cyber p-5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-surface-400 uppercase tracking-wider font-mono">
                  BUY Signals
                </span>
                <TrendingUp className="h-5 w-5 text-neon-400" />
              </div>
              <span className="text-2xl font-display font-bold text-neon-400">
                {buySignals}
              </span>
            </div>
          </SlideIn>
          <SlideIn delay={100}>
            <div className="card-cyber p-5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-surface-400 uppercase tracking-wider font-mono">
                  SELL Signals
                </span>
                <TrendingDown className="h-5 w-5 text-hotpink-400" />
              </div>
              <span className="text-2xl font-display font-bold text-hotpink-400">
                {sellSignals}
              </span>
            </div>
          </SlideIn>
          <SlideIn delay={150}>
            <div className="card-cyber p-5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-surface-400 uppercase tracking-wider font-mono">
                  Strategies
                </span>
                <Filter className="h-5 w-5 text-purple-400" />
              </div>
              <span className="text-2xl font-display font-bold text-white">
                {uniqueStrategies}
              </span>
            </div>
          </SlideIn>
        </div>

        {/* Filters and Actions */}
        <SlideIn delay={200}>
          <div className="card-cyber p-4">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="flex items-center gap-4 flex-1">
                <div className="flex items-center gap-2">
                  <Filter className="h-4 w-4 text-surface-400" />
                  <span className="text-xs text-surface-400 font-mono uppercase tracking-wider">
                    Filter by Bot:
                  </span>
                </div>
                <select
                  value={selectedBotId || ""}
                  onChange={(e) => setSelectedBotId(e.target.value || undefined)}
                  className={cn(
                    "px-3 py-2 rounded-lg bg-surface-900/50 border border-surface-800/50",
                    "text-sm font-mono text-white",
                    "hover:border-neon-500/30 focus:border-neon-500/50 focus:outline-none",
                    "transition-colors"
                  )}
                >
                  <option value="">All Bots</option>
                  {bots.map((bot) => (
                    <option key={bot.id} value={bot.id}>
                      {bot.name} ({bot.symbol})
                    </option>
                  ))}
                </select>
              </div>
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-lg",
                  "bg-neon-500/10 border border-neon-500/30 text-neon-400",
                  "hover:bg-neon-500/20 hover:border-neon-500/50",
                  "transition-all font-mono text-xs uppercase tracking-wider",
                  "disabled:opacity-50 disabled:cursor-not-allowed"
                )}
              >
                <RefreshCw className={cn("h-4 w-4", refreshing && "animate-spin")} />
                Refresh
              </button>
            </div>
          </div>
        </SlideIn>

        {/* Signal Logs */}
        <SlideIn delay={250}>
          <div className="card-cyber">
            <div className="flex items-center justify-between mb-6 p-4 border-b border-surface-800/50">
              <div>
                <h2 className="text-lg font-display font-semibold text-white">Signal Logs</h2>
                <p className="text-xs text-surface-400 font-mono mt-1">
                  Complete transparency on why trades were triggered
                  {selectedBotId && ` • Filtered by bot`}
                </p>
              </div>
              <div className="text-xs text-surface-500 font-mono">
                {signalLogs.length} {signalLogs.length === 1 ? "signal" : "signals"}
              </div>
            </div>
            <div className="p-4">
              <SignalLogList logs={signalLogs} loading={refreshing} />
            </div>
          </div>
        </SlideIn>
      </div>
    </PageTransition>
  );
}

