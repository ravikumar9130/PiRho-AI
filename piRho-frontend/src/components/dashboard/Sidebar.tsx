"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { signOut } from "next-auth/react";
import { cn } from "@/lib/utils";
import { useDashboard } from "./DashboardContext";
import { Logo } from "@/components/ui/Logo";
import {
  Bot,
  LayoutDashboard,
  LineChart,
  History,
  Settings,
  LogOut,
  CreditCard,
  X,
  Zap,
  Activity,
  FlaskConical,
} from "lucide-react";

const navItems = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/bots", label: "Trading Bots", icon: Bot },
  { href: "/dashboard/backtesting", label: "Backtesting", icon: FlaskConical },
  { href: "/dashboard/positions", label: "Positions", icon: LineChart },
  { href: "/dashboard/signals", label: "Signal Log", icon: Activity },
  { href: "/dashboard/history", label: "Trade History", icon: History },
  { href: "/dashboard/billing", label: "Billing", icon: CreditCard },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarOpen, setSidebarOpen, isMobile } = useDashboard();

  const handleNavClick = () => {
    if (isMobile) {
      setSidebarOpen(false);
    }
  };

  const handleSignOut = () => {
    signOut({ callbackUrl: "/" });
  };

  return (
    <>
      {/* Mobile Overlay */}
      {isMobile && sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/80 backdrop-blur-md lg:hidden animate-fade-in"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 border-r border-neon-500/10",
          "bg-surface-950/95 backdrop-blur-xl flex flex-col",
          "transition-transform duration-300 ease-out",
          // Mobile: slide in/out
          isMobile && !sidebarOpen && "-translate-x-full",
          isMobile && sidebarOpen && "translate-x-0",
          // Desktop: always visible
          !isMobile && "translate-x-0"
        )}
      >
        {/* Accent line on right edge */}
        <div className="absolute top-0 right-0 bottom-0 w-px bg-gradient-to-b from-neon-500/50 via-magenta-500/20 to-transparent" />

        {/* Logo Header */}
        <div className="flex items-center justify-between px-4 py-4 border-b border-neon-500/10 relative">
          <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-neon-500/50 via-transparent to-transparent" />
          <Link href="/dashboard" onClick={handleNavClick}>
            <Logo size="md" animated />
          </Link>
          
          {/* Close button on mobile */}
          {isMobile && (
            <button
              onClick={() => setSidebarOpen(false)}
              className="p-2 rounded-lg hover:bg-surface-800 transition-colors lg:hidden"
              aria-label="Close sidebar"
            >
              <X className="h-5 w-5 text-surface-400" />
            </button>
          )}
        </div>

        {/* Status indicator */}
        <div className="px-4 py-3 border-b border-surface-800/50">
          <div className="flex items-center gap-2 text-xs font-mono text-surface-400">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-neon-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-neon-500"></span>
            </span>
            <span className="uppercase tracking-wider">System Online</span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto scrollbar-thin">
          {navItems.map((item, index) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={handleNavClick}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium",
                  "transition-all duration-200 relative overflow-hidden",
                  "font-mono uppercase tracking-wider text-xs",
                  isActive
                    ? "bg-neon-500/10 text-neon-400"
                    : "text-surface-400 hover:text-white hover:bg-surface-800/50",
                  // Stagger animation on mount
                  "animate-fade-up opacity-0",
                )}
                style={{ 
                  animationDelay: `${index * 50}ms`, 
                  animationFillMode: "forwards" 
                }}
              >
                {/* Active indicator glow */}
                {isActive && (
                  <>
                    <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-neon-500" 
                      style={{ boxShadow: "0 0 10px rgba(0, 255, 255, 0.5)" }} 
                    />
                    <div className="absolute inset-0 bg-gradient-to-r from-neon-500/10 to-transparent" />
                  </>
                )}
                
                <item.icon className={cn(
                  "h-4 w-4 transition-colors relative z-10",
                  isActive && "text-neon-400"
                )} />
                <span className="relative z-10">{item.label}</span>
                
                {isActive && (
                  <Zap className="ml-auto h-3 w-3 text-neon-400 animate-pulse" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* User Section & Logout */}
        <div className="p-4 border-t border-neon-500/10 space-y-2">
          <div className="absolute top-0 left-4 right-4 h-px bg-gradient-to-r from-transparent via-neon-500/30 to-transparent" />
          <button
            onClick={handleSignOut}
            className={cn(
              "flex items-center gap-3 w-full px-3 py-2.5 rounded-lg",
              "text-xs font-mono uppercase tracking-wider text-surface-400",
              "hover:text-hotpink-400 hover:bg-hotpink-500/10",
              "transition-all duration-200"
            )}
          >
            <LogOut className="h-4 w-4" />
            Sign Out
          </button>
        </div>
      </aside>
    </>
  );
}
