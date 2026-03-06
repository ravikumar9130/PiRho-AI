"use client";

import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { Header } from "@/components/dashboard/Header";
import { api, Bot, CreateBotData } from "@/lib/api";
import { cn } from "@/lib/utils";
import { PageTransition, SlideIn, ScaleIn } from "@/components/ui/PageTransition";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { Button, IconButton } from "@/components/ui/Button";
import { TiltCard, NeonCard } from "@/components/ui/TiltCard";
import {
  Bot as BotIcon,
  Plus,
  Play,
  Square,
  Trash2,
  X,
  Zap,
  Settings,
} from "lucide-react";

export default function BotsPage() {
  const { data: session } = useSession();
  const [bots, setBots] = useState<Bot[]>([]);
  const [strategies, setStrategies] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      if (!session?.accessToken) return;
      
      try {
        const [botsData, strategiesData] = await Promise.all([
          api.getBots(session.accessToken),
          api.getStrategies(session.accessToken),
        ]);
        setBots(botsData);
        setStrategies(strategiesData.strategies);
      } catch (error) {
        console.error("Failed to fetch bots:", error);
      } finally {
        setLoading(false);
      }
    }
    
    fetchData();
  }, [session]);

  const handleStart = async (botId: string) => {
    if (!session?.accessToken) return;
    setActionLoading(botId);
    try {
      const updated = await api.startBot(session.accessToken, botId);
      setBots((prev) => prev.map((b) => (b.id === botId ? updated : b)));
    } catch (error) {
      console.error("Failed to start bot:", error);
    }
    setActionLoading(null);
  };

  const handleStop = async (botId: string) => {
    if (!session?.accessToken) return;
    setActionLoading(botId);
    try {
      const updated = await api.stopBot(session.accessToken, botId);
      setBots((prev) => prev.map((b) => (b.id === botId ? updated : b)));
    } catch (error) {
      console.error("Failed to stop bot:", error);
    }
    setActionLoading(null);
  };

  const handleDelete = async (botId: string) => {
    if (!session?.accessToken) return;
    if (!confirm("Are you sure you want to delete this bot?")) return;
    
    setActionLoading(botId);
    try {
      await api.deleteBot(session.accessToken, botId);
      setBots((prev) => prev.filter((b) => b.id !== botId));
    } catch (error) {
      console.error("Failed to delete bot:", error);
    }
    setActionLoading(null);
  };

  const handleCreate = async (data: CreateBotData) => {
    if (!session?.accessToken) return;
    
    try {
      const newBot = await api.createBot(session.accessToken, data);
      setBots((prev) => [newBot, ...prev]);
      setShowModal(false);
    } catch (error) {
      console.error("Failed to create bot:", error);
      throw error;
    }
  };

  if (loading) {
    return (
      <>
        <Header title="Trading Bots" />
        <div className="p-4 lg:p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="skeleton h-5 w-32 rounded" />
            <div className="skeleton h-10 w-28 rounded-lg" />
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(3)].map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        </div>
      </>
    );
  }

  return (
    <PageTransition>
      <Header title="Trading Bots" />
      <div className="p-4 lg:p-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-2">
            <BotIcon className="h-5 w-5 text-neon-400" />
            <p className="text-surface-400 font-mono text-sm">
              <span className="text-neon-400 font-bold">{bots.length}</span> bot{bots.length !== 1 ? "s" : ""} configured
            </p>
          </div>
          <Button 
            onClick={() => setShowModal(true)} 
            leftIcon={<Plus className="h-4 w-4" />}
            className="font-mono uppercase tracking-wider text-xs"
          >
            New Bot
          </Button>
        </div>

        {/* Bots Grid */}
        {bots.length === 0 ? (
          <SlideIn>
            <NeonCard color="dual" className="text-center py-12">
              <div className="h-20 w-20 rounded-2xl bg-surface-800/50 border border-neon-500/20 flex items-center justify-center mx-auto mb-4">
                <BotIcon className="h-10 w-10 text-neon-500/50" />
              </div>
              <h3 className="text-xl font-display font-semibold mb-2 text-white">No bots yet</h3>
              <p className="text-surface-400 mb-6 font-mono text-sm">
                Create your first trading bot to get started
              </p>
              <Button 
                onClick={() => setShowModal(true)} 
                leftIcon={<Plus className="h-4 w-4" />}
                className="font-mono uppercase tracking-wider text-xs"
              >
                Create Bot
              </Button>
            </NeonCard>
          </SlideIn>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {bots.map((bot, index) => (
              <SlideIn key={bot.id} delay={index * 50}>
                <TiltCard glowColor={bot.status === "running" ? "rgba(0, 255, 255, 0.2)" : "rgba(255, 255, 255, 0.05)"} tiltAmount={5}>
                  <div className={cn(
                    "card-cyber group h-full",
                    bot.status === "running" && "ring-1 ring-neon-500/30"
                  )}>
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className={cn(
                          "h-10 w-10 rounded-xl flex items-center justify-center border",
                          bot.status === "running" 
                            ? "bg-neon-500/10 border-neon-500/30" 
                            : "bg-surface-800/50 border-surface-700"
                        )}>
                          <BotIcon className={cn(
                            "h-5 w-5",
                            bot.status === "running" ? "text-neon-400" : "text-surface-400"
                          )} />
                        </div>
                        <div>
                          <h3 className="font-display font-semibold text-white">{bot.name}</h3>
                          <p className="text-xs text-surface-400 font-mono">{bot.symbol}</p>
                        </div>
                      </div>
                      <span
                        className={cn(
                          "badge font-mono",
                          bot.status === "running"
                            ? "badge-success"
                            : bot.status === "error"
                            ? "badge-danger"
                            : "badge-info"
                        )}
                      >
                        {bot.status === "running" && <Zap className="h-3 w-3 mr-1" />}
                        {bot.status}
                      </span>
                    </div>

                    <div className="space-y-2 text-sm mb-4">
                      <div className="flex justify-between py-1.5 border-b border-surface-800/50">
                        <span className="text-surface-400 font-mono text-xs uppercase tracking-wider">Strategy</span>
                        <span className="font-mono text-neon-400 text-xs">{bot.strategy}</span>
                      </div>
                      <div className="flex justify-between py-1.5 border-b border-surface-800/50">
                        <span className="text-surface-400 font-mono text-xs uppercase tracking-wider">Leverage</span>
                        <span className="font-mono text-white text-xs">{(bot.config as any)?.leverage || 5}x</span>
                      </div>
                      <div className="flex justify-between py-1.5">
                        <span className="text-surface-400 font-mono text-xs uppercase tracking-wider">Mode</span>
                        <span className={cn(
                          "font-mono text-xs",
                          (bot.config as any)?.paper_trading ? "text-amber-400" : "text-neon-400"
                        )}>
                          {(bot.config as any)?.paper_trading ? "Paper" : "Live"}
                        </span>
                      </div>
                    </div>

                    <div className="flex gap-2 pt-4 border-t border-neon-500/10">
                      {bot.status === "running" ? (
                        <Button
                          variant="secondary"
                          onClick={() => handleStop(bot.id)}
                          loading={actionLoading === bot.id}
                          leftIcon={<Square className="h-4 w-4" />}
                          className="flex-1 font-mono uppercase tracking-wider text-xs"
                        >
                          Stop
                        </Button>
                      ) : (
                        <Button
                          onClick={() => handleStart(bot.id)}
                          loading={actionLoading === bot.id}
                          leftIcon={<Play className="h-4 w-4" />}
                          className="flex-1 font-mono uppercase tracking-wider text-xs"
                        >
                          Start
                        </Button>
                      )}
                      <IconButton
                        variant="ghost"
                        onClick={() => handleDelete(bot.id)}
                        disabled={actionLoading === bot.id || bot.status === "running"}
                        label="Delete bot"
                        className="text-hotpink-400 hover:text-hotpink-300 hover:bg-hotpink-500/10 border border-transparent hover:border-hotpink-500/30"
                      >
                        <Trash2 className="h-4 w-4" />
                      </IconButton>
                    </div>
                  </div>
                </TiltCard>
              </SlideIn>
            ))}
          </div>
        )}

        {/* Create Bot Modal */}
        {showModal && (
          <CreateBotModal
            strategies={strategies}
            onClose={() => setShowModal(false)}
            onCreate={handleCreate}
          />
        )}
      </div>
    </PageTransition>
  );
}

function CreateBotModal({
  strategies,
  onClose,
  onCreate,
}: {
  strategies: string[];
  onClose: () => void;
  onCreate: (data: CreateBotData) => Promise<void>;
}) {
  const [name, setName] = useState("");
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [strategy, setStrategy] = useState(strategies[0] || "");
  const [leverage, setLeverage] = useState(5);
  const [paperTrading, setPaperTrading] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await onCreate({
        name,
        symbol,
        strategy,
        config: {
          leverage,
          paper_trading: paperTrading,
        },
      });
    } catch (err: any) {
      setError(err.message || "Failed to create bot");
    }
    setLoading(false);
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <ScaleIn>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          {/* Header accent line */}
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neon-500/50 to-transparent" />
          
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-neon-500/10 border border-neon-500/30 flex items-center justify-center">
                <BotIcon className="h-5 w-5 text-neon-400" />
              </div>
              <h2 className="text-lg font-display font-semibold text-white">Create Trading Bot</h2>
            </div>
            <IconButton variant="ghost" size="sm" onClick={onClose} label="Close">
              <X className="h-5 w-5" />
            </IconButton>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="alert-error text-sm font-mono">
                {error}
              </div>
            )}

            <div>
              <label className="block text-xs font-mono uppercase tracking-wider text-surface-400 mb-2">Bot Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="input font-mono"
                placeholder="My BTC Bot"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-mono uppercase tracking-wider text-surface-400 mb-2">Symbol</label>
              <select
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="input font-mono"
              >
                <option value="BTCUSDT">BTCUSDT</option>
                <option value="ETHUSDT">ETHUSDT</option>
                <option value="SOLUSDT">SOLUSDT</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-mono uppercase tracking-wider text-surface-400 mb-2">Strategy</label>
              <select
                value={strategy}
                onChange={(e) => setStrategy(e.target.value)}
                className="input font-mono text-sm"
              >
                {strategies.map((s) => (
                  <option key={s} value={s}>
                    {s.replace(/_/g, " ")}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-mono uppercase tracking-wider text-surface-400 mb-2">
                Leverage: <span className="text-neon-400">{leverage}x</span>
              </label>
              <input
                type="range"
                min="1"
                max="20"
                value={leverage}
                onChange={(e) => setLeverage(Number(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-surface-500 mt-1 font-mono">
                <span>1x</span>
                <span>20x</span>
              </div>
            </div>

            <div className="flex items-center gap-3 p-4 rounded-xl bg-surface-900/50 border border-surface-800/50">
              <input
                type="checkbox"
                id="paperTrading"
                checked={paperTrading}
                onChange={(e) => setPaperTrading(e.target.checked)}
              />
              <label htmlFor="paperTrading" className="text-sm cursor-pointer">
                <span className="font-medium text-white">Paper Trading</span>
                <span className="text-surface-400 ml-1 font-mono text-xs">(simulated, no real funds)</span>
              </label>
            </div>

            <div className="flex gap-3 pt-4">
              <Button 
                type="button" 
                variant="secondary" 
                onClick={onClose} 
                className="flex-1 font-mono uppercase tracking-wider text-xs"
              >
                Cancel
              </Button>
              <Button 
                type="submit" 
                loading={loading} 
                className="flex-1 font-mono uppercase tracking-wider text-xs"
              >
                Create Bot
              </Button>
            </div>
          </form>
        </div>
      </ScaleIn>
    </div>
  );
}
