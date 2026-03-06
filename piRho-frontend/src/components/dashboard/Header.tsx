"use client";

import { useSession } from "next-auth/react";
import { useDashboard } from "./DashboardContext";
import { Bell, User, Menu, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

interface HeaderProps {
  title: string;
}

export function Header({ title }: HeaderProps) {
  const { data: session } = useSession();
  const { toggleSidebar, isMobile } = useDashboard();

  return (
    <header className="sticky top-0 z-30 border-b border-neon-500/10 bg-surface-950/80 backdrop-blur-xl">
      {/* Bottom accent line */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-neon-500/30 via-transparent to-magenta-500/20" />
      
      <div className="flex items-center justify-between px-4 lg:px-6 py-4">
        <div className="flex items-center gap-3">
          {/* Mobile menu button */}
          {isMobile && (
            <button
              onClick={toggleSidebar}
              className={cn(
                "p-2 -ml-2 rounded-lg",
                "hover:bg-neon-500/10 transition-colors",
                "lg:hidden border border-transparent hover:border-neon-500/30"
              )}
              aria-label="Toggle menu"
            >
              <Menu className="h-5 w-5 text-surface-400 hover:text-neon-400" />
            </button>
          )}
          
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-neon-500 hidden sm:block" />
            <h1 className="text-lg lg:text-xl font-display font-bold truncate text-white">
              {title}
            </h1>
          </div>
        </div>
        
        <div className="flex items-center gap-2 lg:gap-4">
          {/* Live status indicator */}
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-900/50 border border-neon-500/20">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-neon-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-neon-500"></span>
            </span>
            <span className="text-xs font-mono text-neon-400 uppercase tracking-wider">Live</span>
          </div>

          {/* Notifications */}
          <button 
            className={cn(
              "p-2 rounded-lg transition-all duration-200",
              "hover:bg-neon-500/10 border border-transparent hover:border-neon-500/30",
              "relative group"
            )}
            aria-label="Notifications"
          >
            <Bell className="h-5 w-5 text-surface-400 group-hover:text-neon-400 transition-colors" />
            {/* Notification dot */}
            <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-neon-500 ring-2 ring-surface-950">
              <span className="absolute inset-0 rounded-full bg-neon-500 animate-ping opacity-75" />
            </span>
          </button>
          
          {/* User profile */}
          <div className="flex items-center gap-2 lg:gap-3">
            <div className={cn(
              "h-9 w-9 rounded-lg flex items-center justify-center relative overflow-hidden",
              "bg-surface-900 border border-neon-500/30"
            )}>
              {/* Gradient background */}
              <div className="absolute inset-0 bg-gradient-to-br from-neon-500/20 to-magenta-500/20" />
              {session?.user?.name ? (
                <span className="text-sm font-bold text-neon-400 relative z-10 font-mono">
                  {session.user.name.charAt(0).toUpperCase()}
                </span>
              ) : (
                <User className="h-4 w-4 text-neon-400 relative z-10" />
              )}
            </div>
            <div className="hidden sm:block">
              <span className="text-sm font-medium text-white block leading-none">
                {session?.user?.name || session?.user?.email?.split("@")[0] || "User"}
              </span>
              <span className="text-xs text-surface-500 font-mono">Trader</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
