"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  ShieldCheck,
  Zap,
  BarChart3,
  LogOut,
  Menu,
  X,
  CreditCard,
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);

  const menuItems = [
    {
      name: "Dashboard",
      icon: LayoutDashboard,
      path: "/dashboard",
    },
    {
      name: "Simulator",
      icon: Zap,
      path: "/analyze",
    },
    {
      name: "Transactions",
      icon: CreditCard,
      path: "/transactions",
    },
    {
      name: "Analytics",
      icon: BarChart3,
      path: "/analytics",
    },
  ];

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  const toggleMobileSidebar = () => setIsOpen(!isOpen);

  return (
    <>
      {/* Mobile Toggle Button */}
      <button
        onClick={toggleMobileSidebar}
        className="fixed top-4 left-4 z-50 rounded-lg bg-slate-900 p-2 text-slate-100 border border-slate-800 shadow-md md:hidden hover:bg-slate-800 transition-colors"
      >
        {isOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* Backdrop overlay for mobile */}
      {isOpen && (
        <div
          onClick={toggleMobileSidebar}
          className="fixed inset-0 z-40 bg-slate-950/60 backdrop-blur-sm md:hidden"
        />
      )}

      {/* Sidebar container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-40 flex w-64 flex-col border-r border-slate-900 bg-slate-950 px-4 py-6 text-slate-100 transition-transform duration-300 ease-in-out md:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Header Branding */}
        <div className="flex items-center gap-3 px-2 mb-8">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 shadow-lg shadow-indigo-600/30">
            <ShieldCheck className="h-5 w-5 text-indigo-50" />
          </div>
          <div>
            <h1 className="font-heading font-bold text-lg leading-tight tracking-tight">Vigil</h1>
            <span className="font-heading text-[10px] text-slate-400 font-semibold tracking-wider uppercase">
              Fraud Shield
            </span>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 space-y-1.5">
          {menuItems.map((item) => {
            const isActive = pathname === item.path;
            return (
              <Link
                key={item.name}
                href={item.path}
                onClick={() => setIsOpen(false)}
                className={`flex items-center gap-3.5 rounded-lg px-3.5 py-2.5 text-sm font-medium transition-all ${
                  isActive
                    ? "bg-indigo-600/10 text-indigo-400 border-l-2 border-indigo-500"
                    : "text-slate-400 hover:bg-slate-900/60 hover:text-slate-100"
                }`}
              >
                <item.icon size={18} className={isActive ? "text-indigo-400" : "text-slate-400"} />
                {item.name}
              </Link>
            );
          })}
        </nav>

        {/* Footer Area with user profile and Logout */}
        <div className="border-t border-slate-900 pt-5 mt-auto space-y-4">
          {user && (
            <div className="flex items-center gap-3 px-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-800 text-xs font-bold uppercase text-slate-300">
                {user.username.substring(0, 2)}
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-semibold text-slate-200">
                  {user.username}
                </p>
                <p className="truncate text-[10px] text-slate-500 uppercase tracking-wider font-medium">
                  {user.username === "demo" ? "Demo Account" : "Analyst"}
                </p>
              </div>
            </div>
          )}

          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3.5 rounded-lg px-3.5 py-2.5 text-sm font-medium text-slate-400 hover:bg-red-500/10 hover:text-red-400 transition-colors"
          >
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </aside>
    </>
  );
}
