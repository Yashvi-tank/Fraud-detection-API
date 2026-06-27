"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "@/hooks/use-auth";
import {
  Zap,
  ShieldCheck,
  AlertTriangle,
  HelpCircle,
  ChevronRight,
  Info,
  Cpu,
  Activity,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";

interface AnalysisResult {
  transaction_id: string;
  risk_score: number;
  status: string;
  reasons: string[];
  fraud_probability: number | null;
  model_version: string | null;
}

const MERCHANTS = [
  "Amazon",
  "eBay",
  "Walmart",
  "Apple Store",
  "Steam",
  "Airbnb",
  "Uber",
  "Netflix",
  "PayPal Transfer",
  "Western Union",
  "Coinbase",
  "Binance",
  "Unknown Merchant",
];

const COUNTRIES = [
  "US", "UK", "CA", "AU", "DE", "FR", "JP",
  "CN", "NG", "RU", "BR", "MX", "IN", "KR", "UA",
];

const DEFAULT_FORM = {
  amount: 250,
  merchant: "Amazon",
  country: "US",
  device_id: "device_abc_123",
};

function RiskGauge({ score }: { score: number }) {
  const capped = Math.min(100, Math.max(0, score));
  const angle = (capped / 100) * 180;
  const color = capped >= 70 ? "#ef4444" : capped >= 40 ? "#f59e0b" : "#10b981";
  const label = capped >= 70 ? "HIGH RISK" : capped >= 40 ? "REVIEW" : "SAFE";

  // SVG gauge arc helpers
  const r = 70;
  const cx = 100;
  const cy = 90;
  const startAngle = 180;
  const endAngle = startAngle + angle;
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const x1 = cx + r * Math.cos(toRad(startAngle));
  const y1 = cy + r * Math.sin(toRad(startAngle));
  const x2 = cx + r * Math.cos(toRad(endAngle));
  const y2 = cy + r * Math.sin(toRad(endAngle));
  const largeArc = angle > 180 ? 1 : 0;

  return (
    <div className="flex flex-col items-center">
      <svg width="200" height="110" viewBox="0 0 200 110">
        {/* Background track */}
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          stroke="#1e293b"
          strokeWidth="12"
          strokeLinecap="round"
        />
        {/* Score arc */}
        {capped > 0 && (
          <path
            d={`M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`}
            fill="none"
            stroke={color}
            strokeWidth="12"
            strokeLinecap="round"
            style={{ filter: `drop-shadow(0 0 8px ${color}80)` }}
          />
        )}
        {/* Score text */}
        <text x={cx} y={cy - 10} textAnchor="middle" fill="#f1f5f9" fontSize="28" fontWeight="800">
          {capped}
        </text>
        <text x={cx} y={cy + 12} textAnchor="middle" fill={color} fontSize="11" fontWeight="700" letterSpacing="2">
          {label}
        </text>
        {/* Tick labels */}
        <text x={cx - r - 6} y={cy + 4} textAnchor="middle" fill="#475569" fontSize="9">0</text>
        <text x={cx + r + 6} y={cy + 4} textAnchor="middle" fill="#475569" fontSize="9">100</text>
      </svg>
    </div>
  );
}

function ScoreBreakdown({ reasons, fraudProbability, modelVersion }: {
  reasons: string[];
  fraudProbability: number | null;
  modelVersion: string | null;
}) {
  const ruleReasons = reasons.filter(r => !r.toLowerCase().includes("ml") && !r.toLowerCase().includes("model"));
  const mlReason = reasons.find(r => r.toLowerCase().includes("ml") || r.toLowerCase().includes("model"));

  return (
    <div className="space-y-4">
      {/* Rule Engine Points */}
      <div>
        <p className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-2.5 flex items-center gap-1.5">
          <ShieldCheck size={12} className="text-emerald-400" />
          Rule Engine Triggers
        </p>
        {ruleReasons.length > 0 ? (
          <ul className="space-y-2">
            {ruleReasons.map((reason, i) => (
              <li key={i} className="flex items-start gap-2.5 text-sm">
                <ChevronRight size={14} className="text-red-400 mt-0.5 shrink-0" />
                <span className="text-slate-300">{reason}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-slate-500 italic">No rule triggers detected</p>
        )}
      </div>

      {/* ML Contribution */}
      <div className="rounded-lg bg-indigo-950/30 border border-indigo-900/50 p-4">
        <p className="text-xs font-bold uppercase tracking-widest text-indigo-400 mb-3 flex items-center gap-1.5">
          <Cpu size={12} />
          ML Model Contribution
        </p>
        {fraudProbability !== null ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">Fraud Probability</span>
              <span className="font-bold text-slate-200 tabular-nums">
                {(fraudProbability * 100).toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-2">
              <div
                className="h-2 rounded-full transition-all duration-700"
                style={{
                  width: `${fraudProbability * 100}%`,
                  background: `linear-gradient(to right, #6366f1, ${fraudProbability > 0.7 ? "#ef4444" : fraudProbability > 0.4 ? "#f59e0b" : "#10b981"})`,
                }}
              />
            </div>
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span>ML Score Boost: +{Math.round(fraudProbability * 20)} pts</span>
              {modelVersion && <span className="font-mono bg-slate-800 px-2 py-0.5 rounded">{modelVersion}</span>}
            </div>
            {mlReason && (
              <p className="text-xs text-indigo-300 flex items-start gap-1.5 pt-1 border-t border-indigo-900/40">
                <Info size={11} className="mt-0.5 shrink-0" />
                {mlReason}
              </p>
            )}
          </div>
        ) : (
          <p className="text-sm text-slate-500 italic">ML scoring not available</p>
        )}
      </div>

      {/* Score Formula */}
      <div className="rounded-lg bg-slate-950/50 border border-slate-800 p-3">
        <p className="text-xs font-mono text-slate-400">
          <span className="text-slate-500">{"// Final Score Formula"}</span>
          <br />
          <span className="text-emerald-400">rule_score</span>
          <span className="text-slate-400"> + </span>
          <span className="text-indigo-400">round(ml_prob × 20)</span>
          <span className="text-slate-400"> → capped at 100</span>
        </p>
      </div>
    </div>
  );
}

export default function AnalyzePage() {
  const { user } = useAuth();
  const [form, setForm] = useState(DEFAULT_FORM);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const payload = {
        user_id: user?.id ?? user?.username ?? "simulator",
        amount: parseFloat(form.amount as unknown as string),
        merchant: form.merchant,
        country: form.country,
        device_id: form.device_id,
      };
      const res = await apiClient.post("/transactions/check", payload);
      setResult(res.data);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(axiosErr.response?.data?.detail || "Analysis failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const statusCfg: Record<string, { bg: string; border: string; text: string; icon: React.ElementType }> = {
    SAFE: { bg: "bg-emerald-500/10", border: "border-emerald-500/30", text: "text-emerald-400", icon: ShieldCheck },
    REVIEW: { bg: "bg-amber-500/10", border: "border-amber-500/30", text: "text-amber-400", icon: AlertTriangle },
    SUSPICIOUS: { bg: "bg-red-500/10", border: "border-red-500/30", text: "text-red-400", icon: AlertTriangle },
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="font-heading text-2xl font-extrabold tracking-tight text-slate-50">Transaction Simulator</h1>
        <p className="text-sm text-slate-400 mt-1">
          Submit a mock transaction and see the full risk analysis with ML explainability.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Input Form */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm p-6"
        >
          <h2 className="font-heading text-sm font-bold text-slate-200 mb-5 flex items-center gap-2">
            <Zap size={16} className="text-indigo-400" />
            Transaction Parameters
          </h2>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Amount */}
            <div>
              <label htmlFor="amount" className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Amount (USD)
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 font-semibold">$</span>
                <input
                  id="amount"
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={form.amount}
                  onChange={(e) => setForm({ ...form, amount: parseFloat(e.target.value) })}
                  className="w-full rounded-lg border border-slate-700 bg-slate-800/50 pl-8 pr-4 py-2.5 text-sm text-slate-200 placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition"
                  required
                />
              </div>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {[100, 500, 1500, 5000, 15000].map((v) => (
                  <button
                    type="button"
                    key={v}
                    onClick={() => setForm({ ...form, amount: v })}
                    className="rounded-md bg-slate-800 px-2.5 py-1 text-xs text-slate-400 hover:bg-slate-700 hover:text-slate-200 transition"
                  >
                    ${v.toLocaleString()}
                  </button>
                ))}
              </div>
            </div>

            {/* Merchant */}
            <div>
              <label htmlFor="merchant" className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Merchant
              </label>
              <select
                id="merchant"
                value={form.merchant}
                onChange={(e) => setForm({ ...form, merchant: e.target.value })}
                className="w-full rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2.5 text-sm text-slate-200 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition"
              >
                {MERCHANTS.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>

            {/* Country */}
            <div>
              <label htmlFor="country" className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Origin Country
                <span className="ml-2 font-normal text-slate-500">(US / UK = low risk · CN / RU / NG = high risk)</span>
              </label>
              <select
                id="country"
                value={form.country}
                onChange={(e) => setForm({ ...form, country: e.target.value })}
                className="w-full rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2.5 text-sm text-slate-200 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition"
              >
                {COUNTRIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            {/* Device ID */}
            <div>
              <label htmlFor="device_id" className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Device ID
              </label>
              <input
                id="device_id"
                type="text"
                value={form.device_id}
                onChange={(e) => setForm({ ...form, device_id: e.target.value })}
                placeholder="e.g. device_abc_123"
                className="w-full rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2.5 text-sm text-slate-200 placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition font-mono"
              />
              <div className="mt-2 flex flex-wrap gap-1.5">
                {["device_abc_123", "new_device_xyz", "unknown_99z"].map((d) => (
                  <button
                    type="button"
                    key={d}
                    onClick={() => setForm({ ...form, device_id: d })}
                    className="rounded-md bg-slate-800 px-2.5 py-1 text-xs text-slate-400 font-mono hover:bg-slate-700 hover:text-slate-200 transition"
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>

            {error && (
              <div className="rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              id="analyze-btn"
              className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-indigo-600/20 hover:bg-indigo-500 active:scale-[0.98] transition-all disabled:opacity-60"
            >
              {isLoading ? (
                <>
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Activity size={16} />
                  Run Fraud Analysis
                </>
              )}
            </button>

            {/* Presets */}
            <div className="pt-2 border-t border-slate-800">
              <p className="text-xs text-slate-500 mb-2">Quick presets:</p>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => setForm({ amount: 50, merchant: "Amazon", country: "US", device_id: "device_abc_123" })}
                  className="rounded-md bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 text-xs font-semibold text-emerald-400 hover:bg-emerald-500/20 transition"
                >
                  ✅ Low Risk
                </button>
                <button
                  type="button"
                  onClick={() => setForm({ amount: 2500, merchant: "Unknown Merchant", country: "RU", device_id: "unknown_99z" })}
                  className="rounded-md bg-amber-500/10 border border-amber-500/20 px-3 py-1.5 text-xs font-semibold text-amber-400 hover:bg-amber-500/20 transition"
                >
                  ⚠️ Medium Risk
                </button>
                <button
                  type="button"
                  onClick={() => setForm({ amount: 12000, merchant: "Binance", country: "NG", device_id: "new_device_xyz" })}
                  className="rounded-md bg-red-500/10 border border-red-500/20 px-3 py-1.5 text-xs font-semibold text-red-400 hover:bg-red-500/20 transition"
                >
                  🚨 High Risk
                </button>
              </div>
            </div>
          </form>
        </motion.div>

        {/* Results Panel */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm p-6"
        >
          <h2 className="font-heading text-sm font-bold text-slate-200 mb-5 flex items-center gap-2">
            <HelpCircle size={16} className="text-indigo-400" />
            Analysis Result & Explainability
          </h2>

          <AnimatePresence mode="wait">
            {!result && !isLoading && (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col items-center justify-center py-20 text-center"
              >
                <div className="h-16 w-16 rounded-full bg-slate-800 flex items-center justify-center mb-4">
                  <Zap size={28} className="text-slate-600" />
                </div>
                <p className="text-slate-400 font-semibold">No analysis yet</p>
                <p className="text-xs text-slate-600 mt-1">Fill in the form and click &ldquo;Run Fraud Analysis&rdquo;</p>
              </motion.div>
            )}

            {isLoading && (
              <motion.div
                key="loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col items-center justify-center py-20"
              >
                <div className="h-14 w-14 rounded-full border-4 border-indigo-500/20 border-t-indigo-500 animate-spin mb-4" />
                <p className="text-slate-400 font-semibold animate-pulse">Running analysis pipeline…</p>
                <p className="text-xs text-slate-600 mt-1">Rules → Behavioral → ML Model</p>
              </motion.div>
            )}

            {result && !isLoading && (
              <motion.div
                key="result"
                initial={{ opacity: 0, scale: 0.97 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-6"
              >
                {/* Status Banner */}
                {(() => {
                  const cfg = statusCfg[result.status] ?? statusCfg.SAFE;
                  const Icon = cfg.icon;
                  return (
                    <div className={`rounded-lg border ${cfg.border} ${cfg.bg} px-4 py-3 flex items-center gap-3`}>
                      <Icon size={18} className={cfg.text} />
                      <div>
                        <p className={`text-sm font-bold ${cfg.text}`}>{result.status}</p>
                        <p className="text-xs text-slate-400 font-mono">ID: {result.transaction_id}</p>
                      </div>
                    </div>
                  );
                })()}

                {/* Risk Gauge */}
                <div className="flex justify-center">
                  <RiskGauge score={result.risk_score} />
                </div>

                {/* Explainability */}
                <ScoreBreakdown
                  reasons={result.reasons}
                  fraudProbability={result.fraud_probability}
                  modelVersion={result.model_version}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </div>
  );
}
