"use client";

import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { Header } from "@/components/dashboard/Header";
import { api, ExchangeCredential, AddCredentialsData } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { PageTransition, SlideIn, ScaleIn } from "@/components/ui/PageTransition";
import { SkeletonList } from "@/components/ui/Skeleton";
import { Button, IconButton } from "@/components/ui/Button";
import {
  Key,
  Plus,
  Trash2,
  Shield,
  Eye,
  EyeOff,
  X,
} from "lucide-react";

export default function SettingsPage() {
  const { data: session } = useSession();
  const [credentials, setCredentials] = useState<ExchangeCredential[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      if (!session?.accessToken) return;
      
      try {
        const creds = await api.getCredentials(session.accessToken);
        setCredentials(creds);
      } catch (error) {
        console.error("Failed to fetch credentials:", error);
      } finally {
        setLoading(false);
      }
    }
    
    fetchData();
  }, [session]);

  const handleDelete = async (credId: string) => {
    if (!session?.accessToken) return;
    if (!confirm("Are you sure? This will disconnect your exchange.")) return;
    
    setDeleting(credId);
    try {
      await api.deleteCredentials(session.accessToken, credId);
      setCredentials((prev) => prev.filter((c) => c.id !== credId));
    } catch (error) {
      console.error("Failed to delete:", error);
    }
    setDeleting(null);
  };

  const handleAdd = async (data: AddCredentialsData) => {
    if (!session?.accessToken) return;
    
    const newCred = await api.addCredentials(session.accessToken, data);
    setCredentials((prev) => [...prev, newCred]);
    setShowModal(false);
  };

  if (loading) {
    return (
      <>
        <Header title="Settings" />
        <div className="p-4 lg:p-6 space-y-8">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="skeleton h-6 w-40 rounded" />
              <div className="skeleton h-10 w-32 rounded-lg" />
            </div>
            <SkeletonList items={2} />
          </div>
        </div>
      </>
    );
  }

  return (
    <PageTransition>
      <Header title="Settings" />
      <div className="p-4 lg:p-6 space-y-8">
        {/* Exchange Credentials */}
        <section>
          <SlideIn>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
              <div>
                <h2 className="text-lg font-semibold">Exchange API Keys</h2>
                <p className="text-sm text-surface-400">
                  Connect your exchange to enable live trading
                </p>
              </div>
              <Button
                onClick={() => setShowModal(true)}
                leftIcon={<Plus className="h-4 w-4" />}
              >
                Add API Key
              </Button>
            </div>
          </SlideIn>

          {credentials.length === 0 ? (
            <SlideIn delay={50}>
              <div className="card text-center py-10">
                <div className="h-14 w-14 rounded-2xl bg-surface-800 flex items-center justify-center mx-auto mb-4">
                  <Key className="h-7 w-7 text-surface-500" />
                </div>
                <p className="text-surface-400 mb-4">No API keys connected</p>
                <Button
                  variant="secondary"
                  onClick={() => setShowModal(true)}
                >
                  Connect Exchange
                </Button>
              </div>
            </SlideIn>
          ) : (
            <div className="space-y-3">
              {credentials.map((cred, index) => (
                <SlideIn key={cred.id} delay={index * 50}>
                  <div className="card-hover flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                      <div className="h-12 w-12 rounded-xl bg-brand-500/10 flex items-center justify-center flex-shrink-0">
                        <Shield className="h-6 w-6 text-brand-500" />
                      </div>
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-medium capitalize">{cred.exchange}</span>
                          <span
                            className={`badge ${
                              cred.is_testnet ? "badge-warning" : "badge-success"
                            }`}
                          >
                            {cred.is_testnet ? "Testnet" : "Mainnet"}
                          </span>
                        </div>
                        <p className="text-sm text-surface-400 font-mono mt-1">
                          {cred.api_key_masked}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-sm text-surface-400">
                        Added {formatDate(cred.created_at)}
                      </span>
                      <IconButton
                        variant="ghost"
                        onClick={() => handleDelete(cred.id)}
                        loading={deleting === cred.id}
                        label="Delete credential"
                        className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                      >
                        <Trash2 className="h-4 w-4" />
                      </IconButton>
                    </div>
                  </div>
                </SlideIn>
              ))}
            </div>
          )}
        </section>

        {/* Security Note */}
        <SlideIn delay={100}>
          <section className="card bg-brand-500/5 border-brand-500/20">
            <div className="flex gap-4">
              <div className="h-10 w-10 rounded-lg bg-brand-500/10 flex items-center justify-center flex-shrink-0">
                <Shield className="h-5 w-5 text-brand-400" />
              </div>
              <div>
                <h3 className="font-medium mb-1">Your keys are encrypted</h3>
                <p className="text-sm text-surface-400">
                  API keys are encrypted with AES-256 before storage. We recommend
                  using API keys with trading permissions only (no withdrawal).
                </p>
              </div>
            </div>
          </section>
        </SlideIn>

        {/* Add Credentials Modal */}
        {showModal && (
          <AddCredentialsModal
            onClose={() => setShowModal(false)}
            onAdd={handleAdd}
          />
        )}
      </div>
    </PageTransition>
  );
}

function AddCredentialsModal({
  onClose,
  onAdd,
}: {
  onClose: () => void;
  onAdd: (data: AddCredentialsData) => Promise<void>;
}) {
  const [apiKey, setApiKey] = useState("");
  const [apiSecret, setApiSecret] = useState("");
  const [isTestnet, setIsTestnet] = useState(true);
  const [showSecret, setShowSecret] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await onAdd({
        exchange: "bybit",
        api_key: apiKey,
        api_secret: apiSecret,
        is_testnet: isTestnet,
      });
    } catch (err: any) {
      setError(err.message || "Failed to add credentials");
    }
    setLoading(false);
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <ScaleIn>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold">Add Exchange API Key</h2>
            <IconButton variant="ghost" size="sm" onClick={onClose} label="Close">
              <X className="h-5 w-5" />
            </IconButton>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="alert-error text-sm">
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium mb-2">Exchange</label>
              <select className="input" disabled>
                <option value="bybit">Bybit</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">API Key</label>
              <input
                type="text"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="input font-mono text-sm"
                placeholder="Enter your API key"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">API Secret</label>
              <div className="relative">
                <input
                  type={showSecret ? "text" : "password"}
                  value={apiSecret}
                  onChange={(e) => setApiSecret(e.target.value)}
                  className="input font-mono text-sm pr-10"
                  placeholder="Enter your API secret"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowSecret(!showSecret)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-400 hover:text-white transition-colors"
                >
                  {showSecret ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <div className="flex items-center gap-3 p-3 rounded-lg bg-surface-800/50">
              <input
                type="checkbox"
                id="testnet"
                checked={isTestnet}
                onChange={(e) => setIsTestnet(e.target.checked)}
              />
              <label htmlFor="testnet" className="text-sm cursor-pointer">
                <span className="font-medium">Testnet</span>
                <span className="text-surface-400 ml-1">(paper trading)</span>
              </label>
            </div>

            <div className="flex gap-3 pt-4">
              <Button
                type="button"
                variant="secondary"
                onClick={onClose}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                loading={loading}
                className="flex-1"
              >
                Save API Key
              </Button>
            </div>
          </form>
        </div>
      </ScaleIn>
    </div>
  );
}
