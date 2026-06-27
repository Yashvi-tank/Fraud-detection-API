"use client";

import Sidebar from "@/components/sidebar";
import AuthGuard from "@/components/auth-guard";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-slate-950 text-slate-100">
        <Sidebar />
        <div className="md:pl-64">
          <main className="mx-auto max-w-7xl p-4 md:p-8 pt-20 md:pt-8">
            {children}
          </main>
        </div>
      </div>
    </AuthGuard>
  );
}
