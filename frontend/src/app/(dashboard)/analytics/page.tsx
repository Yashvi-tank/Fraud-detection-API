"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  BarChart3,
  RefreshCw,
  TrendingUp,
  Globe,
  Cpu,
  Activity,
} from "lucide-react";
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
  PieChart,
  Pie,
  LineChart,
  Line,
  Legend,
} from "recharts";
import { apiClient } from "@/lib/api-client";

interface Summary {
  total_count: number;
  safe_count: number;
  suspicious_count: number;
  average_risk_score: number;
}

interface ChartsData {
  risk_distribution: { status: string; value: number }[];
  timeline: { date: string; total: number; safe: number; suspicious: number }[];
  probability_distribution: { bin: string; count: number }[];
  top_countries: { country: string; suspicious_count: number; total_count: number }[];
}

const STATUS_COLORS: Record<string, string> = {
  Safe: "#10b981",
  Review: "#f59e0b",
  Suspicious: "#ef4444",
};

interface TooltipEntry {
  name: string;
  value: number | string;
  color?: string;
  fill?: string;
}

const CustomTooltip = ({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: TooltipEntry[];
  label?: string;
}) => {
  if (active && payload && payload.length) {
    return (
      <div className="rounded-lg border border-slate-700 bg-slate-900 p-3 text-xs shadow-xl">
        <p className="font-semibold text-slate-300 mb-2">{label}</p>
        {payload.map((entry, i) => (
          <p key={i} style={{ color: entry.color || entry.fill }} className="font-medium">
            {entry.name}: {entry.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color,
  index,
}: {
  title: string;
  value: string | number;
  subtitle: string;
  icon: React.ElementType;
  color: string;
  index: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.07, duration: 0.5 }}
      className="relative overflow-hidden rounded-xl border border-slate-800 bg-slate-900/60 p-5"
    >
      <div className={`absolute -top-6 -right-6 h-24 w-24 rounded-full blur-2xl opacity-15 ${color}`} />
      <div className="flex items-center gap-3 mb-3">
        <div className={`h-9 w-9 rounded-lg flex items-center justify-center ${color} bg-current/10`}>
          <Icon size={16} className="opacity-80" />
        </div>
        <p className="text-xs font-semibold uppercase tracking-widest text-slate-500">{title}</p>
      </div>
      <p className="text-3xl font-extrabold text-slate-50 tracking-tight">{value}</p>
      <p className="text-xs text-slate-500 mt-1.5">{subtitle}</p>
    </motion.div>
  );
}

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [charts, setCharts] = useState<ChartsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [s, c] = await Promise.all([
        apiClient.get("/analytics/summary"),
        apiClient.get("/analytics/charts"),
      ]);
      setSummary(s.data);
      setCharts(c.data);
    } catch (err) {
      console.error("Analytics fetch error", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void fetchData();
  }, []);

  const fraudRate = summary
    ? ((summary.suspicious_count / Math.max(summary.total_count, 1)) * 100).toFixed(1)
    : "0.0";

  const safeRate = summary
    ? ((summary.safe_count / Math.max(summary.total_count, 1)) * 100).toFixed(1)
    : "0.0";

  // Compute rolling 7-day average from timeline for trend line
  const timelineWithRolling = (charts?.timeline ?? []).map((d, i, arr) => {
    const window = arr.slice(Math.max(0, i - 6), i + 1);
    const avgSusp = window.reduce((sum, x) => sum + x.suspicious, 0) / window.length;
    return { ...d, date: d.date.slice(5), rolling_suspicious: parseFloat(avgSusp.toFixed(1)) };
  });

  // Country risk rates
  const countryRates = (charts?.top_countries ?? []).map((c) => ({
    ...c,
    risk_rate: c.total_count > 0 ? parseFloat(((c.suspicious_count / c.total_count) * 100).toFixed(1)) : 0,
  }));


  return (
    <div className="space-y-8">
      {/* Page Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col sm:flex-row sm:items-center justify-between gap-4"
      >
        <div>
          <h1 className="font-heading text-2xl font-extrabold tracking-tight text-slate-50">Analytics</h1>
          <p className="text-sm text-slate-400 mt-1">Deep-dive into transaction patterns and ML model performance</p>
        </div>
        <button
          onClick={fetchData}
          disabled={isLoading}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900 px-4 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-800 hover:text-slate-100 transition-all disabled:opacity-50"
        >
          <RefreshCw size={13} className={isLoading ? "animate-spin" : ""} />
          Refresh
        </button>
      </motion.div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard
          index={0}
          title="Total Analyzed"
          value={isLoading ? "—" : (summary?.total_count ?? 0).toLocaleString()}
          subtitle="Lifetime transactions"
          icon={Activity}
          color="text-indigo-400 bg-indigo-500"
        />
        <StatCard
          index={1}
          title="Fraud Rate"
          value={isLoading ? "—" : `${fraudRate}%`}
          subtitle={`${summary?.suspicious_count ?? 0} flagged suspicious`}
          icon={TrendingUp}
          color="text-red-400 bg-red-500"
        />
        <StatCard
          index={2}
          title="Safe Rate"
          value={isLoading ? "—" : `${safeRate}%`}
          subtitle={`${summary?.safe_count ?? 0} cleared transactions`}
          icon={BarChart3}
          color="text-emerald-400 bg-emerald-500"
        />
        <StatCard
          index={3}
          title="Avg. Risk Score"
          value={isLoading ? "—" : `${summary?.average_risk_score ?? 0}`}
          subtitle="Platform-wide average"
          icon={Cpu}
          color="text-amber-400 bg-amber-500"
        />
      </div>

      {/* Section: Volume Analysis */}
      <div>
        <motion.h2
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-4 flex items-center gap-2"
        >
          <Activity size={12} className="text-indigo-400" />
          Volume & Trend Analysis
        </motion.h2>
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Timeline + Rolling Avg */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.33 }}
            className="xl:col-span-2 rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm p-6"
          >
            <div className="mb-5">
              <h3 className="font-heading text-sm font-bold text-slate-200">Daily Transaction Volume</h3>
              <p className="text-xs text-slate-500 mt-0.5">30-day history with 7-day rolling suspicious average</p>
            </div>
            {isLoading ? (
              <div className="h-56 flex items-center justify-center">
                <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={230}>
                <LineChart data={timelineWithRolling} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 9 }} tickLine={false} axisLine={false} interval={4} />
                  <YAxis tick={{ fill: "#64748b", fontSize: 10 }} tickLine={false} axisLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: "11px", paddingTop: "10px" }} />
                  <Line type="monotone" dataKey="total" name="Total" stroke="#6366f1" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="safe" name="Safe" stroke="#10b981" strokeWidth={1.5} dot={false} strokeDasharray="4 2" />
                  <Line type="monotone" dataKey="suspicious" name="Suspicious" stroke="#ef4444" strokeWidth={1.5} dot={false} />
                  <Line type="monotone" dataKey="rolling_suspicious" name="7d Avg (Susp)" stroke="#f59e0b" strokeWidth={2} dot={false} strokeDasharray="6 3" />
                </LineChart>
              </ResponsiveContainer>
            )}
          </motion.div>

          {/* Donut + Legend */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm p-6"
          >
            <div className="mb-5">
              <h3 className="font-heading text-sm font-bold text-slate-200">Status Breakdown</h3>
              <p className="text-xs text-slate-500 mt-0.5">Outcome distribution across all transactions</p>
            </div>
            {isLoading ? (
              <div className="h-52 flex items-center justify-center">
                <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
              </div>
            ) : (
              <>
                <ResponsiveContainer width="100%" height={160}>
                  <PieChart>
                    <Pie
                      data={charts?.risk_distribution ?? []}
                      cx="50%"
                      cy="50%"
                      innerRadius={45}
                      outerRadius={68}
                      paddingAngle={3}
                      dataKey="value"
                    >
                      {(charts?.risk_distribution ?? []).map((e) => (
                        <Cell key={e.status} fill={STATUS_COLORS[e.status] ?? "#64748b"} />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="mt-2 space-y-2.5">
                  {(charts?.risk_distribution ?? []).map((d) => {
                    const pct = summary ? ((d.value / Math.max(summary.total_count, 1)) * 100).toFixed(1) : "0";
                    return (
                      <div key={d.status} className="flex items-center justify-between text-xs">
                        <span className="flex items-center gap-2 text-slate-400">
                          <span className="h-2.5 w-2.5 rounded-full shrink-0" style={{ background: STATUS_COLORS[d.status] }} />
                          {d.status}
                        </span>
                        <div className="flex items-center gap-3">
                          <div className="w-20 h-1.5 rounded-full bg-slate-800">
                            <div className="h-full rounded-full" style={{ width: `${pct}%`, background: STATUS_COLORS[d.status] }} />
                          </div>
                          <span className="font-bold text-slate-300 tabular-nums w-8 text-right">{d.value}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            )}
          </motion.div>
        </div>
      </div>

      {/* Section: Geographic Analysis */}
      <div>
        <motion.h2
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.45 }}
          className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-4 flex items-center gap-2"
        >
          <Globe size={12} className="text-indigo-400" />
          Geographic Risk Analysis
        </motion.h2>
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {/* Country Volume Grouped Bar */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.48 }}
            className="rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm p-6"
          >
            <div className="mb-5">
              <h3 className="font-heading text-sm font-bold text-slate-200">Top Countries — Volume vs Fraud</h3>
              <p className="text-xs text-slate-500 mt-0.5">Total transactions and suspicious flags per country</p>
            </div>
            {isLoading ? (
              <div className="h-48 flex items-center justify-center">
                <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={charts?.top_countries ?? []} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="country" tick={{ fill: "#64748b", fontSize: 10 }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fill: "#64748b", fontSize: 10 }} tickLine={false} axisLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend iconType="square" iconSize={8} wrapperStyle={{ fontSize: "11px", paddingTop: "10px" }} />
                  <Bar dataKey="total_count" name="Total" fill="#6366f1" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="suspicious_count" name="Suspicious" fill="#ef4444" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </motion.div>

          {/* Country Fraud Rate */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.54 }}
            className="rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm p-6"
          >
            <div className="mb-5">
              <h3 className="font-heading text-sm font-bold text-slate-200">Country Fraud Rate (%)</h3>
              <p className="text-xs text-slate-500 mt-0.5">Percentage of suspicious transactions by origin</p>
            </div>
            {isLoading ? (
              <div className="h-48 flex items-center justify-center">
                <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
              </div>
            ) : (
              <div className="space-y-3 pt-1">
                {countryRates.map((c, i) => (
                  <div key={c.country} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-slate-300">{c.country}</span>
                      <span className={`font-bold tabular-nums ${c.risk_rate >= 50 ? "text-red-400" : c.risk_rate >= 25 ? "text-amber-400" : "text-emerald-400"}`}>
                        {c.risk_rate}%
                      </span>
                    </div>
                    <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${c.risk_rate}%` }}
                        transition={{ delay: 0.6 + i * 0.08, duration: 0.6, ease: "easeOut" }}
                        className="h-full rounded-full"
                        style={{
                          background: c.risk_rate >= 50 ? "#ef4444" : c.risk_rate >= 25 ? "#f59e0b" : "#10b981",
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        </div>
      </div>

      {/* Section: ML Model Analysis */}
      <div>
        <motion.h2
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-4 flex items-center gap-2"
        >
          <Cpu size={12} className="text-indigo-400" />
          ML Model Performance
        </motion.h2>
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Probability Histogram */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.63 }}
            className="xl:col-span-2 rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm p-6"
          >
            <div className="mb-5">
              <h3 className="font-heading text-sm font-bold text-slate-200">Fraud Probability Distribution</h3>
              <p className="text-xs text-slate-500 mt-0.5">Random Forest output bins (0%–100%). Green = safe, amber = review, red = fraud</p>
            </div>
            {isLoading ? (
              <div className="h-52 flex items-center justify-center">
                <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={charts?.probability_distribution ?? []} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="bin" tick={{ fill: "#64748b", fontSize: 9 }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fill: "#64748b", fontSize: 10 }} tickLine={false} axisLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="count" name="Transactions" radius={[4, 4, 0, 0]}>
                    {(charts?.probability_distribution ?? []).map((_, i) => {
                      const binStart = i * 10;
                      const color = binStart < 40 ? "#10b981" : binStart < 70 ? "#f59e0b" : "#ef4444";
                      return <Cell key={i} fill={color} />;
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </motion.div>

          {/* ML Insight Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.68 }}
            className="rounded-xl border border-indigo-900/50 bg-indigo-950/20 backdrop-blur-sm p-6 space-y-5"
          >
            <div>
              <h3 className="font-heading text-sm font-bold text-slate-200">Model Details</h3>
              <p className="text-xs text-slate-500 mt-0.5">Random Forest classifier details</p>
            </div>

            <div className="space-y-3">
              {[
                { label: "Algorithm", value: "Random Forest" },
                { label: "Training Samples", value: "5,500" },
                { label: "Score Contribution", value: "Up to +20 pts" },
                { label: "Score Formula", value: "min(100, rules + round(p × 20))" },
                { label: "Features", value: "8 engineered features" },
              ].map(({ label, value }) => (
                <div key={label} className="flex flex-col gap-0.5">
                  <span className="text-xs text-slate-500 uppercase tracking-wider">{label}</span>
                  <span className="text-sm font-semibold text-slate-200 font-mono">{value}</span>
                </div>
              ))}
            </div>

            <div className="rounded-lg bg-indigo-950/40 border border-indigo-900/50 p-3 mt-2">
              <p className="text-xs text-indigo-300 leading-relaxed">
                The ML model score is blended additively with rule-engine and behavioral scores. High probability scores
                from the classifier contribute up to +20 points, capped at 100 final.
              </p>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
