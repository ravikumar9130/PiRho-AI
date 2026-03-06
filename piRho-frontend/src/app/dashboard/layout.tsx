import { redirect } from "next/navigation";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { Sidebar } from "@/components/dashboard/Sidebar";
import { DashboardProvider } from "@/components/dashboard/DashboardContext";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await getServerSession(authOptions);

  if (!session) {
    redirect("/login");
  }

  return (
    <DashboardProvider>
      <div className="min-h-screen bg-surface-950 relative">
        {/* Dashboard Background */}
        <div className="fixed inset-0 pointer-events-none -z-10">
          {/* Base gradient */}
          <div className="absolute inset-0 bg-gradient-to-b from-surface-950 via-surface-900 to-surface-950" />
          
          {/* Subtle grid */}
          <div 
            className="absolute inset-0 opacity-20"
            style={{
              backgroundImage: `
                linear-gradient(rgba(0, 255, 255, 0.015) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 255, 255, 0.015) 1px, transparent 1px)
              `,
              backgroundSize: "40px 40px",
            }}
          />
          
          {/* Corner glows */}
          <div 
            className="absolute -top-1/4 -right-1/4 w-1/2 h-1/2 rounded-full blur-3xl"
            style={{
              background: "radial-gradient(circle, rgba(0, 255, 255, 0.03) 0%, transparent 70%)",
            }}
          />
          <div 
            className="absolute -bottom-1/4 -left-1/4 w-1/2 h-1/2 rounded-full blur-3xl"
            style={{
              background: "radial-gradient(circle, rgba(255, 0, 255, 0.02) 0%, transparent 70%)",
            }}
          />
        </div>

        <Sidebar />
        {/* Main content - responsive padding */}
        <main className="lg:pl-64 min-h-screen transition-all duration-300 relative">
          {children}
        </main>
      </div>
    </DashboardProvider>
  );
}
