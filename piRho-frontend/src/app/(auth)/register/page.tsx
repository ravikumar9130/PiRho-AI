"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Logo } from "@/components/ui/Logo";
import { Button } from "@/components/ui/Button";
import { PageTransition, SlideIn, FadeIn } from "@/components/ui/PageTransition";
import { CyberpunkBackground } from "@/components/ui/CyberpunkBackground";
import { Mail, Lock, User, Key, ArrowRight, Sparkles, Zap } from "lucide-react";

export default function RegisterPage() {
  const router = useRouter();
  
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [promoCode, setPromoCode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    const result = await signIn("credentials", {
      email,
      password,
      name,
      promoCode: promoCode.trim(),
      isRegister: "true",
      redirect: false,
    });

    setLoading(false);

    if (result?.error) {
      setError("Registration failed. Email may already be in use.");
    } else {
      router.push("/dashboard");
    }
  };

  return (
    <PageTransition>
      <div className="min-h-screen flex items-center justify-center px-4 py-12 relative overflow-hidden">
        {/* Cyberpunk Background */}
        <CyberpunkBackground variant="minimal" showParticles={false} />

        <div className="w-full max-w-md relative z-10">
          <SlideIn>
            <div className="text-center mb-8">
              <Link href="/" className="inline-block">
                <Logo size="lg" animated />
              </Link>
              <h1 className="mt-8 text-2xl sm:text-3xl font-display font-bold text-white">
                Create your account
              </h1>
              <p className="mt-2 text-surface-400 font-mono text-sm">
                Start trading with AI-powered strategies
              </p>
            </div>
          </SlideIn>

          <SlideIn delay={100}>
            <div className="card-cyber relative overflow-hidden">
              {/* Top accent line */}
              <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neon-500/50 to-transparent" />
              
              <form onSubmit={handleSubmit} className="space-y-5">
                {error && (
                  <FadeIn>
                    <div className="alert-error text-sm font-mono">
                      <svg className="h-5 w-5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                      <span>{error}</span>
                    </div>
                  </FadeIn>
                )}

                <div>
                  <label htmlFor="name" className="block text-xs font-mono uppercase tracking-wider text-surface-400 mb-2">
                    Name
                  </label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-surface-500" />
                    <input
                      id="name"
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="input pl-10 font-mono"
                      placeholder="Your name"
                      autoComplete="name"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="email" className="block text-xs font-mono uppercase tracking-wider text-surface-400 mb-2">
                    Email
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-surface-500" />
                    <input
                      id="email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="input pl-10 font-mono"
                      placeholder="you@example.com"
                      required
                      autoComplete="email"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="password" className="block text-xs font-mono uppercase tracking-wider text-surface-400 mb-2">
                    Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-surface-500" />
                    <input
                      id="password"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="input pl-10 font-mono"
                      placeholder="Min. 8 characters"
                      required
                      minLength={8}
                      autoComplete="new-password"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="promoCode" className="block text-xs font-mono uppercase tracking-wider text-surface-400 mb-2">
                    <span className="flex items-center gap-2">
                      Promo Code
                      <span className="badge bg-gradient-to-r from-neon-500/20 to-magenta-500/20 text-neon-400 border border-neon-500/30 text-[10px]">
                        <Sparkles className="h-2.5 w-2.5 mr-1" />
                        Optional
                      </span>
                    </span>
                  </label>
                  <div className="relative">
                    <Key className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-surface-500" />
                    <input
                      id="promoCode"
                      type="text"
                      value={promoCode}
                      onChange={(e) => setPromoCode(e.target.value)}
                      className="input pl-10 font-mono"
                      placeholder="Enter promo code for Pro access"
                      autoComplete="off"
                    />
                  </div>
                </div>

                <Button
                  type="submit"
                  loading={loading}
                  fullWidth
                  size="lg"
                  rightIcon={<ArrowRight className="h-4 w-4" />}
                  className="font-mono uppercase tracking-wider"
                >
                  Create Account
                </Button>

                <p className="text-xs text-surface-500 text-center pt-2 font-mono">
                  By signing up, you agree to our Terms of Service and Privacy Policy.
                </p>
              </form>
            </div>
          </SlideIn>

          <SlideIn delay={200}>
            <p className="mt-8 text-center text-sm text-surface-400 font-mono">
              Already have an account?{" "}
              <Link href="/login" className="text-neon-400 hover:text-neon-300 font-medium transition-colors">
                Sign in
              </Link>
            </p>
          </SlideIn>
        </div>
      </div>
    </PageTransition>
  );
}
