"use client";

import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { Header } from "@/components/dashboard/Header";
import { api, Plan } from "@/lib/api";
import { cn } from "@/lib/utils";
import { PageTransition, SlideIn, FadeIn } from "@/components/ui/PageTransition";
import { SkeletonCard, Skeleton } from "@/components/ui/Skeleton";
import { Button } from "@/components/ui/Button";
import { Check, Sparkles, Key, CheckCircle, Crown } from "lucide-react";

export default function BillingPage() {
  const { data: session } = useSession();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [currentPlan, setCurrentPlan] = useState("free");
  const [loading, setLoading] = useState(true);
  const [promoCode, setPromoCode] = useState("");
  const [promoLoading, setPromoLoading] = useState(false);
  const [promoError, setPromoError] = useState("");
  const [promoSuccess, setPromoSuccess] = useState("");

  useEffect(() => {
    async function fetchData() {
      try {
        const [{ plans: planData }, planInfo] = await Promise.all([
          api.getPlans(),
          session?.accessToken ? api.getCurrentPlan(session.accessToken) : Promise.resolve({ plan: "free" }),
        ]);
        setPlans(planData);
        setCurrentPlan(planInfo.plan);
      } catch (error) {
        console.error("Failed to fetch data:", error);
      } finally {
        setLoading(false);
      }
    }
    
    fetchData();
  }, [session]);

  const handleApplyPromo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!session?.accessToken || !promoCode.trim()) return;
    
    setPromoError("");
    setPromoSuccess("");
    setPromoLoading(true);
    
    try {
      const result = await api.applyPromoCode(session.accessToken, promoCode.trim());
      setPromoSuccess(result.message);
      setCurrentPlan(result.plan);
      setPromoCode("");
    } catch (error: any) {
      setPromoError(error.message || "Invalid promo code");
    } finally {
      setPromoLoading(false);
    }
  };

  if (loading) {
    return (
      <>
        <Header title="Billing" />
        <div className="p-4 lg:p-6 space-y-6">
          <SkeletonCard />
          <SkeletonCard />
          <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-64 rounded-xl" />
            ))}
          </div>
        </div>
      </>
    );
  }

  return (
    <PageTransition>
      <Header title="Billing" />
      <div className="p-4 lg:p-6 space-y-6">
        {/* Current Plan */}
        <SlideIn>
          <div className="card bg-gradient-to-br from-surface-900 to-surface-950">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className={cn(
                  "h-14 w-14 rounded-xl flex items-center justify-center",
                  currentPlan === "free" ? "bg-surface-800" : "bg-brand-500/20"
                )}>
                  <Crown className={cn(
                    "h-7 w-7",
                    currentPlan === "free" ? "text-surface-400" : "text-brand-400"
                  )} />
                </div>
                <div>
                  <p className="text-sm text-surface-400">Current Plan</p>
                  <h2 className="text-2xl font-bold capitalize">{currentPlan}</h2>
                </div>
              </div>
              {currentPlan !== "free" && (
                <span className="badge-success text-sm px-3 py-1">
                  <CheckCircle className="h-4 w-4 mr-1.5" />
                  Active
                </span>
              )}
            </div>
          </div>
        </SlideIn>

        {/* Promo Code Section */}
        <SlideIn delay={50}>
          <div className="card">
            <div className="flex items-center gap-4 mb-5">
              <div className="h-12 w-12 rounded-xl bg-brand-500/10 flex items-center justify-center flex-shrink-0">
                <Key className="h-6 w-6 text-brand-500" />
              </div>
              <div>
                <h3 className="font-semibold text-lg">Have a Promo Code?</h3>
                <p className="text-sm text-surface-400">Enter your code to unlock premium features</p>
              </div>
            </div>
            
            <form onSubmit={handleApplyPromo} className="flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                value={promoCode}
                onChange={(e) => setPromoCode(e.target.value)}
                className="input flex-1 text-center sm:text-left font-mono uppercase tracking-wider"
                placeholder="Enter promo code"
              />
              <Button
                type="submit"
                loading={promoLoading}
                disabled={!promoCode.trim()}
                className="sm:w-32"
              >
                Apply
              </Button>
            </form>
            
            {promoError && (
              <FadeIn>
                <div className="mt-4 alert-error text-sm">
                  {promoError}
                </div>
              </FadeIn>
            )}
            {promoSuccess && (
              <FadeIn>
                <div className="mt-4 alert-success text-sm">
                  <CheckCircle className="h-4 w-4 flex-shrink-0" />
                  {promoSuccess}
                </div>
              </FadeIn>
            )}
          </div>
        </SlideIn>

        {/* Plans Grid */}
        <div>
          <SlideIn delay={100}>
            <h3 className="text-lg font-semibold mb-4">Available Plans</h3>
          </SlideIn>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {plans.map((plan, index) => (
              <SlideIn key={plan.id} delay={150 + index * 50}>
                <div
                  className={cn(
                    "card-hover relative h-full flex flex-col",
                    plan.id === "pro" && "ring-2 ring-brand-500 bg-brand-500/5",
                    plan.id === currentPlan && "border-brand-500/50"
                  )}
                >


                  <div className="mb-4">
                    <h4 className="text-lg font-semibold">{plan.name}</h4>
                    <div className="mt-2">
                      <span className="text-3xl font-bold">${plan.price}</span>
                      {plan.price > 0 && (
                        <span className="text-surface-400 text-sm">/month</span>
                      )}
                    </div>
                  </div>

                  <ul className="space-y-2.5 mb-6 flex-1">
                    {plan.features.map((feature, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <Check className="h-4 w-4 text-brand-500 flex-shrink-0 mt-0.5" />
                        <span className="text-surface-300">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  {plan.id === currentPlan ? (
                    <div className="btn-secondary w-full justify-center cursor-default pointer-events-none">
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Current Plan
                    </div>
                  ) : plan.promo_available ? (
                    <p className="text-center text-sm text-surface-400 py-2">
                      Use promo code above
                    </p>
                  ) : (
                    <p className="text-center text-sm text-surface-500 py-2">
                      {plan.price === 0 ? "Default" : "Contact us"}
                    </p>
                  )}
                </div>
              </SlideIn>
            ))}
          </div>
        </div>

        {/* Info */}
        <SlideIn delay={350}>
          <div className="card bg-surface-850">
            <h3 className="text-lg font-semibold mb-4">How it works</h3>
            <div className="grid gap-6 sm:grid-cols-2">
              <div>
                <h4 className="font-medium mb-2 flex items-center gap-2">
                  <div className="h-6 w-6 rounded-full bg-brand-500/10 flex items-center justify-center text-xs font-bold text-brand-400">1</div>
                  Promo Codes
                </h4>
                <p className="text-sm text-surface-400">
                  Enter a valid promo code to instantly unlock premium features. 
                  Your plan will be upgraded immediately.
                </p>
              </div>
              <div>
                <h4 className="font-medium mb-2 flex items-center gap-2">
                  <div className="h-6 w-6 rounded-full bg-brand-500/10 flex items-center justify-center text-xs font-bold text-brand-400">2</div>
                  Need a Code?
                </h4>
                <p className="text-sm text-surface-400">
                  Contact us on Telegram or follow our social channels for exclusive promo codes.
                </p>
              </div>
            </div>
          </div>
        </SlideIn>
      </div>
    </PageTransition>
  );
}
