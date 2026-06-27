"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  ShieldCheck,
  Zap,
  Activity,
  Layers,
  ArrowRight,
  GitBranch,
  ExternalLink,
  Terminal,
} from "lucide-react";
import { useAuth } from "@/hooks/use-auth";

export default function LandingPage() {
  const router = useRouter();
  const { loginAsDemo, token, isAuthenticated } = useAuth();
  const [isDemoLoading, setIsDemoLoading] = useState(false);

  useEffect(() => {
    // If already logged in, show dashboard directly
    if (token && isAuthenticated) {
      router.push("/dashboard");
    }
  }, [token, isAuthenticated, router]);

  const handleDemoClick = async () => {
    setIsDemoLoading(true);
    const success = await loginAsDemo();
    setIsDemoLoading(false);
    if (success) {
      router.push("/dashboard");
    }
  };


  const flowSteps = [
    { label: "Incoming Transaction", desc: "Amount, Country, Merchant, Device", color: "border-slate-800 text-slate-400" },
    { label: "Static Rules", desc: "+30 amount, +25 country, +20 device", color: "border-emerald-950 text-emerald-400 bg-emerald-950/10" },
    { label: "Behavioral Engine", desc: "Velocity burst, new device, spending check", color: "border-amber-950 text-amber-400 bg-amber-950/10" },
    { label: "Machine Learning Model", desc: "Random Forest scoring (0 - 20 points)", color: "border-indigo-950 text-indigo-400 bg-indigo-950/10" },
    { label: "Capped Risk Score", desc: "Blended final score (capped at 100)", color: "border-red-950 text-red-400 bg-red-950/10" },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 overflow-x-hidden font-sans relative">
      {/* Background Gradients */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[500px] bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-500/10 via-transparent to-transparent pointer-events-none -z-10" />
      <div className="absolute top-[20%] left-[10%] w-[300px] h-[300px] bg-indigo-500/5 blur-[120px] rounded-full pointer-events-none -z-10" />
      <div className="absolute top-[60%] right-[10%] w-[350px] h-[350px] bg-emerald-500/5 blur-[120px] rounded-full pointer-events-none -z-10" />

      {/* Grid Pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#0f172a_1px,transparent_1px),linear-gradient(to_bottom,#0f172a_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] opacity-35 pointer-events-none -z-10" />

      {/* Navigation Header */}
      <header className="mx-auto max-w-7xl px-6 h-20 flex items-center justify-between border-b border-slate-900/80">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 shadow-md shadow-indigo-600/30">
            <ShieldCheck className="h-5 w-5 text-indigo-50" />
          </div>
          <span className="font-heading font-bold text-lg tracking-tight bg-gradient-to-r from-slate-50 to-slate-300 bg-clip-text text-transparent">
            Vigil Transaction Risk Platform
          </span>
        </div>
        <div className="flex items-center gap-4">
          <Link
            href="/login"
            className="text-sm font-semibold text-slate-300 hover:text-slate-100 transition-colors px-4 py-2"
          >
            Sign In
          </Link>
          <Link
            href="/register"
            className="hidden sm:inline-flex items-center justify-center rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-slate-200 border border-slate-800 hover:bg-slate-850 hover:text-slate-100 transition-all"
          >
            Register
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <section className="mx-auto max-w-5xl px-6 pt-20 pb-16 text-center">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-xs font-semibold text-indigo-400 mb-8"
        >
          <Terminal size={12} />
          Phase 3 ML Integration Live
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1 }}
          className="text-4xl sm:text-6xl font-extrabold tracking-tight bg-gradient-to-b from-slate-50 via-slate-100 to-slate-400 bg-clip-text text-transparent leading-[1.1] mb-6 font-heading"
        >
          AI-Powered Real-Time <br className="hidden sm:inline" />
          Transaction Risk Analysis
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="max-w-2xl mx-auto text-base sm:text-lg text-slate-400 leading-relaxed mb-10"
        >
          A premium full-stack fraud detection platform. Protect your ecosystem with a hybrid scoring engine blending rule hierarchies, behavioral velocity checks, and a Random Forest ML model.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <button
            onClick={handleDemoClick}
            disabled={isDemoLoading}
            className="w-full sm:w-auto inline-flex items-center justify-center rounded-lg bg-indigo-600 px-6 py-3.5 text-sm font-semibold text-slate-50 shadow-md shadow-indigo-600/20 hover:bg-indigo-500 active:scale-[0.98] transition-all disabled:opacity-50"
          >
            {isDemoLoading ? (
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-50 border-t-transparent mr-2" />
            ) : (
              <Activity className="mr-2" size={16} />
            )}
            Try Demo (Auto Login)
          </button>
          <Link
            href="/login"
            className="w-full sm:w-auto inline-flex items-center justify-center rounded-lg bg-slate-900 px-6 py-3.5 text-sm font-semibold text-slate-200 border border-slate-800 hover:bg-slate-800 hover:text-slate-100 transition-colors"
          >
            Launch Dashboard
            <ArrowRight className="ml-2" size={16} />
          </Link>
        </motion.div>
      </section>

      {/* Pipeline Visual Flow Section */}
      <section className="mx-auto max-w-6xl px-6 py-16">
        <div className="text-center mb-12">
          <h2 className="font-heading text-2xl font-bold tracking-tight text-slate-100">Hybrid Scoring Architecture</h2>
          <p className="text-sm text-slate-400 mt-2">How transactions are scored sequentially by the platform</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 relative">
          {flowSteps.map((step, idx) => (
            <div
              key={idx}
              className={`flex flex-col p-5 rounded-xl border bg-slate-900/30 backdrop-blur-sm relative ${step.color}`}
            >
              <div className="absolute top-4 right-4 text-xs font-bold text-slate-600">0{idx + 1}</div>
              <h3 className="font-bold text-sm text-slate-200 mb-2">{step.label}</h3>
              <p className="text-xs text-slate-400 leading-relaxed">{step.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features Grid */}
      <section className="mx-auto max-w-6xl px-6 py-16 border-t border-slate-900">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 rounded-xl border border-slate-900 bg-slate-950/50">
            <div className="h-10 w-10 flex items-center justify-center rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 mb-5">
              <ShieldCheck size={20} />
            </div>
            <h3 className="font-heading text-lg font-bold text-slate-200 mb-2">Rule Engine</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Verify amounts, device identifiers, and geographic indicators in real-time. Instantly flag high-dollar or unrecognized origin patterns.
            </p>
          </div>

          <div className="p-6 rounded-xl border border-slate-900 bg-slate-950/50">
            <div className="h-10 w-10 flex items-center justify-center rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 mb-5">
              <Zap size={20} />
            </div>
            <h3 className="font-heading text-lg font-bold text-slate-200 mb-2">Behavioral Analytics</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Analyze recent transaction frequencies (velocity bursts), device changes, and spending deviations comparing current volumes with historical averages.
            </p>
          </div>

          <div className="p-6 rounded-xl border border-slate-900 bg-slate-950/50">
            <div className="h-10 w-10 flex items-center justify-center rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 mb-5">
              <Layers size={20} />
            </div>
            <h3 className="font-heading text-lg font-bold text-slate-200 mb-2">Machine Learning</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              A trained Random Forest model predicts fraud probabilities. The score blends seamlessly as a weight component capping risk scores at 100.
            </p>
          </div>
        </div>
      </section>

      {/* Live Metrics Showcase */}
      <section className="mx-auto max-w-5xl px-6 py-16 border-t border-slate-900 text-center">
        <h2 className="font-heading text-2xl font-bold tracking-tight mb-12">Platform Health & Specifications</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="p-5 rounded-lg bg-slate-900/40 border border-slate-900">
            <div className="text-2xl sm:text-3xl font-extrabold text-indigo-400">65 / 65</div>
            <p className="text-xs text-slate-400 font-semibold uppercase mt-2 tracking-wider">Pytest Suites</p>
          </div>
          <div className="p-5 rounded-lg bg-slate-900/40 border border-slate-900">
            <div className="text-2xl sm:text-3xl font-extrabold text-emerald-400">FastAPI</div>
            <p className="text-xs text-slate-400 font-semibold uppercase mt-2 tracking-wider">Backend Core</p>
          </div>
          <div className="p-5 rounded-lg bg-slate-900/40 border border-slate-900">
            <div className="text-2xl sm:text-3xl font-extrabold text-amber-400">PostgreSQL</div>
            <p className="text-xs text-slate-400 font-semibold uppercase mt-2 tracking-wider">Database</p>
          </div>
          <div className="p-5 rounded-lg bg-slate-900/40 border border-slate-900">
            <div className="text-2xl sm:text-3xl font-extrabold text-indigo-400">Random Forest</div>
            <p className="text-xs text-slate-400 font-semibold uppercase mt-2 tracking-wider">Primary Classifier</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mx-auto max-w-7xl px-6 py-12 border-t border-slate-900 flex flex-col sm:flex-row items-center justify-between gap-6 text-sm text-slate-500">
        <div>&copy; 2026 Vigil Transaction Risk Platform. Open Source Portfolio Project.</div>
        <div className="flex gap-4">
          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            className="hover:text-slate-300 transition-colors inline-flex items-center gap-1.5"
          >
            <GitBranch size={16} /> GitHub
          </a>
          <a
            href="https://linkedin.com"
            target="_blank"
            rel="noreferrer"
            className="hover:text-slate-300 transition-colors inline-flex items-center gap-1.5"
          >
            <ExternalLink size={16} /> LinkedIn
          </a>
        </div>
      </footer>
    </div>
  );
}
