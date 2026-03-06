"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, Plan } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Logo } from "@/components/ui/Logo";
import { PageTransition, SlideIn, FadeIn } from "@/components/ui/PageTransition";
import { CyberpunkBackground } from "@/components/ui/CyberpunkBackground";
import { Skeleton } from "@/components/ui/Skeleton";
import { TiltCard, NeonCard } from "@/components/ui/TiltCard";
import { Check, Sparkles, ArrowLeft, Key, ChevronDown, ChevronUp, Zap } from "lucide-react";

export default function PricingPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  useEffect(() => {
    api.getPlans().then((res) => {
      setPlans(res.plans);
      setLoading(false);
    });
  }, []);

  return (
    <PageTransition>
      <div className="min-h-screen bg-surface-950 overflow-hidden relative">
        {/* Cyberpunk Background */}
        <CyberpunkBackground variant="minimal" />

        {/* Header */}
        <header className="relative border-b border-neon-500/10 backdrop-blur-xl bg-surface-950/60 sticky top-0 z-50">
          <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neon-500/50 to-transparent" />
          <div className="mx-auto max-w-7xl px-4 sm:px-6 py-4 flex items-center justify-between">
            <Link href="/">
              <Logo size="md" animated />
            </Link>
            <div className="flex items-center gap-2 sm:gap-4">
              <Link href="/login" className="btn-ghost text-sm font-mono uppercase tracking-wider">
                Sign In
              </Link>
              <Link href="/register" className="btn-primary text-sm font-mono uppercase tracking-wider">
                Get Started
              </Link>
            </div>
          </div>
        </header>

        {/* Pricing Section */}
        <section className="relative py-16 sm:py-20">
          <div className="mx-auto max-w-7xl px-4 sm:px-6">
            <SlideIn>
              <div className="text-center mb-16">
                <h1 className="text-3xl sm:text-4xl lg:text-5xl font-display font-bold">
                  Simple, <span className="text-gradient-cyber">transparent</span> pricing
                </h1>
                <p className="mt-4 text-lg text-surface-400 font-mono">
                  Start free, upgrade with a promo code
                </p>
              </div>
            </SlideIn>

            {loading ? (
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4 max-w-6xl mx-auto">
                {[...Array(4)].map((_, i) => (
                  <Skeleton key={i} className="h-96 rounded-xl" />
                ))}
              </div>
            ) : (
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4 max-w-6xl mx-auto items-stretch">
                {plans.map((plan, index) => (
                  <SlideIn key={plan.id} delay={100 + index * 50}>
                    <TiltCard 
                      glowColor={plan.id === "pro" ? "rgba(0, 255, 255, 0.3)" : "rgba(255, 255, 255, 0.1)"}
                      tiltAmount={8}
                      className="h-full"
                    >
                      <div
                        className={cn(
                          "card-cyber relative h-full flex flex-col",
                          plan.id === "pro" && "ring-1 ring-neon-500/50"
                        )}
                      >
                        {plan.id === "pro" && (
                          <div className="absolute top-[42px] left-[75px] z-10">
                            <span className="badge bg-gradient-to-r from-neon-500 to-magenta-500 text-black font-bold  px-3 py-1 text-[11px] whitespace-nowrap">
                              <Sparkles className="h-4 w-3 mr-1 inline" />
                              Promo Available
                            </span>
                          </div>
                        )}

                        <div className={cn(
                          "mb-6 flex-shrink-0",
                          plan.id === "pro" && "pt-4"
                        )}>
                          <h3 className="text-xl font-display font-semibold text-white">{plan.name}</h3>
                          <div className="mt-4">
                            <span className="text-4xl font-display font-bold text-gradient-cyber">${plan.price}</span>
                            {plan.price > 0 && (
                              <span className="text-surface-400 font-mono text-sm">/month</span>
                            )}
                          </div>
                        </div>

                        <ul className="space-y-3 mb-8 flex-1 min-h-0">
                          {plan.features.map((feature, i) => (
                            <li key={i} className="flex items-start gap-2">
                              <Check className="h-5 w-5 text-neon-400 flex-shrink-0 mt-0.5" />
                              <span className="text-surface-300 text-sm leading-relaxed">{feature}</span>
                            </li>
                          ))}
                        </ul>

                        <Link
                          href="/register"
                          className={cn(
                            "w-full block text-center font-mono uppercase tracking-wider text-sm flex-shrink-0",
                            plan.id === "pro" ? "btn-primary" : "btn-secondary"
                          )}
                        >
                          {plan.price === 0 ? "Start Free" : plan.promo_available ? "Use Promo Code" : "Contact Us"}
                        </Link>
                      </div>
                    </TiltCard>
                  </SlideIn>
                ))}
              </div>
            )}

            {/* Promo Code Info */}
            <SlideIn delay={300}>
              <div className="mt-16 max-w-xl mx-auto">
                <NeonCard color="dual" className="p-6">
                  <div className="flex items-center gap-4">
                    <div className="h-14 w-14 rounded-xl bg-gradient-to-br from-neon-500/20 to-magenta-500/20 flex items-center justify-center flex-shrink-0 border border-neon-500/30">
                      <Key className="h-7 w-7 text-neon-400" />
                    </div>
                    <div>
                      <h3 className="font-display font-semibold text-lg text-white">Have a Promo Code?</h3>
                      <p className="text-sm text-surface-400 mt-1">
                        Enter it during registration or in the billing section to unlock Pro features
                      </p>
                    </div>
                  </div>
                </NeonCard>
              </div>
            </SlideIn>

            <FadeIn delay={400}>
              <div className="mt-10 text-center">
                <Link href="/" className="text-surface-400 hover:text-neon-400 inline-flex items-center gap-2 transition-colors font-mono text-sm uppercase tracking-wider">
                  <ArrowLeft className="h-4 w-4" />
                  Back to home
                </Link>
              </div>
            </FadeIn>
          </div>
        </section>

        {/* FAQ */}
        <section className="relative py-16 sm:py-20 border-t border-neon-500/10">
          <div className="mx-auto max-w-3xl px-4 sm:px-6">
            <SlideIn>
              <h2 className="text-2xl sm:text-3xl font-display font-bold text-center mb-12">
                Frequently Asked <span className="text-neon-400">Questions</span>
              </h2>
            </SlideIn>
            <div className="space-y-4">
              {faqs.map((faq, index) => (
                <SlideIn key={index} delay={index * 50}>
                  <FaqItem
                    question={faq.question}
                    answer={faq.answer}
                    isOpen={openFaq === index}
                    onToggle={() => setOpenFaq(openFaq === index ? null : index)}
                  />
                </SlideIn>
              ))}
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="relative border-t border-neon-500/10 py-8 bg-surface-950/80 backdrop-blur-xl">
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neon-500/30 to-transparent" />
          <div className="mx-auto max-w-7xl px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
            <Logo size="sm" />
            <p className="text-xs sm:text-sm text-surface-500 text-center sm:text-right font-mono">
              © 2025 piRho. Trading involves risk. Past performance is not indicative of future results.
            </p>
          </div>
        </footer>
      </div>
    </PageTransition>
  );
}

const faqs = [
  {
    question: "How do I get a promo code?",
    answer: "Promo codes are shared through our Telegram community and social media channels. Sign up and use your code during registration or in the billing section.",
  },
  {
    question: "What does the promo code unlock?",
    answer: "Valid promo codes unlock the Pro plan with access to all 11 strategies, LSTM models, 5 bots, and priority support.",
  },
  {
    question: "Is my data secure?",
    answer: "Yes. API keys are encrypted with AES-256 at rest. We never have access to your exchange withdrawal permissions.",
  },
  {
    question: "What exchanges are supported?",
    answer: "Currently we support Bybit perpetual futures. Binance support is coming soon.",
  },
  {
    question: "Can I upgrade later?",
    answer: "Yes! You can apply a promo code anytime from the billing section in your dashboard.",
  },
];

function FaqItem({ 
  question, 
  answer, 
  isOpen, 
  onToggle 
}: { 
  question: string; 
  answer: string;
  isOpen: boolean;
  onToggle: () => void;
}) {
  return (
    <div className={cn(
      "card-cyber transition-all duration-300",
      isOpen && "ring-1 ring-neon-500/30"
    )}>
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between text-left p-1"
      >
        <h3 className="font-display font-semibold pr-4 text-white">{question}</h3>
        <div className={cn(
          "p-1.5 rounded-lg transition-colors",
          isOpen ? "bg-neon-500/20 text-neon-400" : "bg-surface-800 text-surface-400"
        )}>
          {isOpen ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </div>
      </button>
      <div
        className={cn(
          "overflow-hidden transition-all duration-300",
          isOpen ? "max-h-40 mt-4 opacity-100" : "max-h-0 opacity-0"
        )}
      >
        <p className="text-surface-400 text-sm leading-relaxed">{answer}</p>
      </div>
    </div>
  );
}
