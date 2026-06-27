"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ShieldCheck, UserPlus, Lock, User } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";

export default function RegisterPage() {
  const router = useRouter();
  const { register, token, isAuthenticated, isLoading, error, clearError } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    clearError();
  }, [clearError]);

  useEffect(() => {
    if (token && isAuthenticated) {
      router.push("/dashboard");
    }
  }, [token, isAuthenticated, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) return;
    const ok = await register(username, password);
    if (ok) {
      setSuccess(true);
      setTimeout(() => {
        router.push("/login");
      }, 1500);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-6 py-12 relative font-sans">
      <div className="absolute top-[10%] left-[30%] w-[300px] h-[300px] bg-indigo-500/5 blur-[120px] rounded-full pointer-events-none -z-10" />

      <div className="w-full max-w-md space-y-6">
        {/* Branding header */}
        <div className="flex flex-col items-center text-center">
          <Link href="/" className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-600 shadow-md shadow-indigo-600/30 mb-4 hover:scale-[1.03] transition-all">
            <ShieldCheck className="h-6 w-6 text-indigo-50" />
          </Link>
          <h2 className="font-heading text-2xl font-bold tracking-tight text-slate-100">Create Account</h2>
          <p className="text-sm text-slate-400 mt-1">Get started with our transaction risk analysis tools</p>
        </div>

        {/* Card Panel */}
        <div className="rounded-xl border border-slate-900 bg-slate-950/60 backdrop-blur-md p-8 shadow-2xl">
          {success ? (
            <div className="flex flex-col items-center text-center py-6 space-y-3">
              <div className="h-10 w-10 flex items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400">
                <ShieldCheck size={24} />
              </div>
              <h3 className="font-heading font-bold text-slate-200">Registration Successful!</h3>
              <p className="text-xs text-slate-400">Redirecting you to the login screen...</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-xs text-red-400 font-medium leading-relaxed">
                  {error}
                </div>
              )}

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider" htmlFor="username">
                  Username
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
                    <User size={16} />
                  </span>
                  <input
                    id="username"
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full rounded-lg bg-slate-900 border border-slate-800 py-2.5 pl-10 pr-4 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
                    placeholder="choose username"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider" htmlFor="password">
                  Password
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
                    <Lock size={16} />
                  </span>
                  <input
                    id="password"
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full rounded-lg bg-slate-900 border border-slate-800 py-2.5 pl-10 pr-4 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
                    placeholder="minimum 6 characters"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex items-center justify-center gap-2 rounded-lg bg-indigo-600 py-3 text-sm font-semibold text-slate-50 shadow-md shadow-indigo-600/20 hover:bg-indigo-500 active:scale-[0.98] transition-all disabled:opacity-50 mt-2"
              >
                {isLoading ? (
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-50 border-t-transparent" />
                ) : (
                  <UserPlus size={16} />
                )}
                Register
              </button>
            </form>
          )}
        </div>

        {/* Navigation Link */}
        <p className="text-center text-xs text-slate-500">
          Already have an account?{" "}
          <Link href="/login" className="font-semibold text-indigo-400 hover:text-indigo-300 transition-colors">
            Log In here
          </Link>
        </p>
      </div>
    </div>
  );
}
