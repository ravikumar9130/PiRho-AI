"use client";

import { Suspense, useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Logo } from "@/components/ui/Logo";
import { Button } from "@/components/ui/Button";
import { PageTransition, SlideIn, FadeIn } from "@/components/ui/PageTransition";
import { BrandedSpinner } from "@/components/ui/Spinner";
import { CyberpunkBackground } from "@/components/ui/CyberpunkBackground";
import { Mail, Lock, ArrowRight, Zap } from "lucide-react";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("callbackUrl") || "/dashboard";
  
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    const result = await signIn("credentials", {
      email,
      password,
      redirect: false,
    });

    setLoading(false);

    if (result?.error) {
      setError("Invalid email or password");
    } else {
      router.push(callbackUrl);
    }
  };

  return (
    <PageTransition>
      <div className="w-full max-w-md relative z-10">
        <SlideIn>
          <div className="text-center mb-8">
            <Link href="/" className="inline-block">
              <Logo size="lg" animated />
            </Link>
            <h1 className="mt-8 text-2xl sm:text-3xl font-display font-bold text-white">
              Welcome back
            </h1>
            <p className="mt-2 text-surface-400 font-mono text-sm">
              Sign in to your account
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
                    placeholder="••••••••"
                    required
                    minLength={8}
                    autoComplete="current-password"
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
                Sign In
              </Button>
            </form>
          </div>
        </SlideIn>

        <SlideIn delay={200}>
          <p className="mt-8 text-center text-sm text-surface-400 font-mono">
            Don&apos;t have an account?{" "}
            <Link href="/register" className="text-neon-400 hover:text-neon-300 font-medium transition-colors">
              Sign up
            </Link>
          </p>
        </SlideIn>
      </div>
    </PageTransition>
  );
}

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12 relative overflow-hidden">
      {/* Cyberpunk Background */}
      <CyberpunkBackground variant="minimal" showParticles={false} />

      <Suspense fallback={
        <div className="flex items-center justify-center">
          <BrandedSpinner />
        </div>
      }>
        <LoginForm />
      </Suspense>
    </div>
  );
}
