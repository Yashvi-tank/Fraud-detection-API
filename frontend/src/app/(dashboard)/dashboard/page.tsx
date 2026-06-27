"use client";

import { useEffect, useState } from "react";
import { motion, Variants } from "framer-motion";
import {
  ShieldCheck,
  AlertTriangle,
  Activity,
  TrendingUp,
  RefreshCw,
  ArrowUpRight,
  ArrowDownRight,
  Clock,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
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

interface Transaction {
  id: string;
  amount: number;
  merchant: string;
  country: string;
  status: string;
  risk_score: number;
  fraud_probability: number | null;
  created_at: string;
}

const STATUS_COLORS: Record<string, string> = {
  Safe: "#10b981",
  Review: "#f59e0b",
  Suspicious: "#ef4444",
};

const cardVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.5, ease: "easeOut" },
  }),
};

function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color,
  trend,
  index,
}: {
  title: string;
  value: string | number;
  subtitle: string;
  icon: React.ElementType;
  color: string;
  trend?: "up" | "down" | "neutral";
  index: number;
}) {
  return (
    <motion.div
      custom={index}
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      className="relative overflow-hidden rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm p-6"
    >
      <div className={`absolute top-0 right-0 w-32 h-32 rounded-full blur-3xl opacity-10 -translate-y-8 translate-x-8 ${color}`} />
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-2">{title}</p>
          <p className="text-3xl font-extrabold text-slate-50 tracking-tight">{value}</p>
          <p className="text-xs text-slate-400 mt-2">{subtitle}</p>
        </div>
        <div className={`flex h-11 w-11 items-center justify-center rounded-lg border ${color} bg-current/10`}>
          <Icon className="h-5 w-5" style={{ opacity: 0.85 }} />
        </div>
      </div>
      {trend && trend !== "neutral" && (
        <div className={`absolute bottom-4 right-4 flex items-center gap-1 text-xs font-semibold ${trend === "up" ? "text-emerald-400" : "text-red-400"}`}>
          {trend === "up" ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
          Live
        </div>
      )}
    </motion.div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const cfg: Record<string, string> = {
    SAFE: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    REVIEW: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    SUSPICIOUS: "bg-red-500/10 text-red-400 border-red-500/20",
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${cfg[status] || "bg-slate-800 text-slate-400"}`}>
      {status}
    </span>
  );
}

interface TooltipEntry {
  name: string;
  value: number | string;
  color: string;
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
          <p key={i} style={{ color: entry.color }} className="font-medium">
            {entry.name}: {entry.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function DashboardPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [charts, setCharts] = useState<ChartsData | null>(null);
  const [recentTx, setRecentTx] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState(new Date());

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [summaryRes, chartsRes, txRes] = await Promise.all([
        apiClient.get("/analytics/summary"),
        apiClient.get("/analytics/charts"),
        apiClient.get("/transactions/?page=1&page_size=8&sort_by=created_at&sort_order=desc"),
      ]);
      setSummary(summaryRes.data);
      setCharts(chartsRes.data);
      setRecentTx(txRes.data.items || []);
      setLastRefresh(new Date());
    } catch (err) {
      console.error("Dashboard fetch error", err);
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

  const slimTimeline = charts?.timeline
    .filter((_, i) => i % 2 === 0)
    .map((d) => ({ ...d, date: d.date.slice(5) })) ?? [];

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col sm:flex-row sm:items-center justify-between gap-4"
      >
        <div>
          <h1 className="font-heading text-2xl font-extrabold tracking-tight text-slate-50">Dashboard</h1>
          <p className="text-sm text-slate-400 mt-1 flex items-center gap-1.5">
            <Clock size={13} />
            Last refreshed: {lastRefresh.toLocaleTimeString()}
          </p>
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

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <MetricCard
          index={0}
          title="Total Transactions"
          value={isLoading ? "—" : (summary?.total_count ?? 0).toLocaleString()}
          subtitle="All-time in system"
          icon={Activity}
          color="border-indigo-500/30 text-indigo-400"
          trend="neutral"
        />
        <MetricCard
          index={1}
          title="Safe Transactions"
          value={isLoading ? "—" : (summary?.safe_count ?? 0).toLocaleString()}
          subtitle={`${summary ? (100 - parseFloat(fraudRate)).toFixed(1) : 0}% of total`}
          icon={ShieldCheck}
          color="border-emerald-500/30 text-emerald-400"
          trend="up"
        />
        <MetricCard
          index={2}
          title="Suspicious Flagged"
          value={isLoading ? "—" : (summary?.suspicious_count ?? 0).toLocaleString()}
          subtitle={`${fraudRate}% fraud rate`}
          icon={AlertTriangle}
          color="border-red-500/30 text-red-400"
          trend="down"
        />
        <MetricCard
          index={3}
          title="Avg. Risk Score"
          value={isLoading ? "—" : `${summary?.average_risk_score ?? 0}`}
          subtitle="Across all transactions"
          icon={TrendingUp}
          color="border-amber-500/30 text-amber-400"
          trend="neutral"
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Timeline Chart - 2/3 width */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35, duration: 0.5 }}
          className="xl:col-span-2 rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm p-6"
        >
          <div className="mb-5">
            <h2 className="font-heading text-sm font-bold text-slate-200 tracking-tight">Transaction Volume — Last 30 Days</h2>
            <p className="text-xs text-slate-500 mt-0.5">Daily activity breakdown (safe vs suspicious)</p>
          </div>
          {isLoading ? (
            <div className="h-52 flex items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={210}>
              <AreaChart data={slimTimeline} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="safeGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="suspGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 10 }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fill: "#64748b", fontSize: 10 }} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: "11px", paddingTop: "12px" }} />
                <Area type="monotone" dataKey="safe" name="Safe" stroke="#10b981" fill="url(#safeGrad)" strokeWidth={2} dot={false} />
                <Area type="monotone" dataKey="suspicious" name="Suspicious" stroke="#ef4444" fill="url(#suspGrad)" strokeWidth={2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </motion.div>

        {/* Pie Chart - 1/3 width */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.42, duration: 0.5 }}
          className="rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm p-6"
        >
          <div className="mb-5">
            <h2 className="font-heading text-sm font-bold text-slate-200 tracking-tight">Risk Distribution</h2>
            <p className="text-xs text-slate-500 mt-0.5">Status breakdown by count</p>
          </div>
          {isLoading ? (
            <div className="h-52 flex items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
            </div>
          ) : (
            <>
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie
                    data={charts?.risk_distribution ?? []}
                    cx="50%"
                    cy="50%"
                    innerRadius={52}
                    outerRadius={74}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {(charts?.risk_distribution ?? []).map((entry) => (
                      <Cell key={entry.status} fill={STATUS_COLORS[entry.status] ?? "#64748b"} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
              <div className="mt-3 space-y-2">
                {(charts?.risk_distribution ?? []).map((d) => (
                  <div key={d.status} className="flex items-center justify-between text-xs">
                    <span className="flex items-center gap-2 text-slate-400">
                      <span className="h-2 w-2 rounded-full" style={{ background: STATUS_COLORS[d.status] }} />
                      {d.status}
                    </span>
                    <span className="font-bold text-slate-300">{d.value}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </motion.div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Top Countries */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.5 }}
          className="rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm p-6"
        >
          <div className="mb-5">
            <h2 className="font-heading text-sm font-bold text-slate-200 tracking-tight">Top Risk Countries</h2>
            <p className="text-xs text-slate-500 mt-0.5">Countries with highest suspicious activity</p>
          </div>
          {isLoading ? (
            <div className="h-40 flex items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={charts?.top_countries ?? []} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="country" tick={{ fill: "#64748b", fontSize: 10 }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fill: "#64748b", fontSize: 10 }} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="total_count" name="Total" fill="#6366f1" radius={[4, 4, 0, 0]} />
                <Bar dataKey="suspicious_count" name="Suspicious" fill="#ef4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </motion.div>

        {/* ML Probability Distribution */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.57, duration: 0.5 }}
          className="rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm p-6"
        >
          <div className="mb-5">
            <h2 className="font-heading text-sm font-bold text-slate-200 tracking-tight">ML Fraud Probability Distribution</h2>
            <p className="text-xs text-slate-500 mt-0.5">Random Forest confidence bins</p>
          </div>
          {isLoading ? (
            <div className="h-40 flex items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={charts?.probability_distribution ?? []} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="bin" tick={{ fill: "#64748b", fontSize: 9 }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fill: "#64748b", fontSize: 10 }} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="count" name="Transactions" radius={[4, 4, 0, 0]}>
                  {(charts?.probability_distribution ?? []).map((entry, index) => {
                    const binStart = index * 10;
                    const color = binStart < 40 ? "#10b981" : binStart < 70 ? "#f59e0b" : "#ef4444";
                    return <Cell key={index} fill={color} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </motion.div>
      </div>

      {/* Recent Transactions Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.65, duration: 0.5 }}
        className="rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm overflow-hidden"
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
          <div>
            <h2 className="font-heading text-sm font-bold text-slate-200">Recent Transactions</h2>
            <p className="text-xs text-slate-500 mt-0.5">Latest 8 transactions processed</p>
          </div>
          <a
            href="/transactions"
            className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1"
          >
            View All <ArrowUpRight size={12} />
          </a>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800/60 bg-slate-950/30">
                <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">Time</th>
                <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">Merchant</th>
                <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">Country</th>
                <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-slate-500">Amount</th>
                <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-slate-500">Risk</th>
                <th className="px-6 py-3 text-center text-xs font-semibold uppercase tracking-wider text-slate-500">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40">
              {isLoading
                ? Array.from({ length: 5 }).map((_, i) => (
                    <tr key={i}>
                      {Array.from({ length: 6 }).map((_, j) => (
                        <td key={j} className="px-6 py-4">
                          <div className="h-4 w-full rounded-md bg-slate-800 animate-pulse" />
                        </td>
                      ))}
                    </tr>
                  ))
                : recentTx.map((tx) => (
                    <tr key={tx.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-6 py-3.5 text-xs text-slate-400 whitespace-nowrap">
                        {new Date(tx.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                      </td>
                      <td className="px-6 py-3.5 font-medium text-slate-200 whitespace-nowrap">{tx.merchant}</td>
                      <td className="px-6 py-3.5 text-slate-400">{tx.country}</td>
                      <td className="px-6 py-3.5 text-right font-bold text-slate-200 tabular-nums">
                        ${tx.amount.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      <td className="px-6 py-3.5 text-right">
                        <span
                          className={`text-xs font-bold tabular-nums ${
                            tx.risk_score >= 70
                              ? "text-red-400"
                              : tx.risk_score >= 40
                              ? "text-amber-400"
                              : "text-emerald-400"
                          }`}
                        >
                          {tx.risk_score}
                        </span>
                      </td>
                      <td className="px-6 py-3.5 text-center">
                        <StatusBadge status={tx.status} />
                      </td>
                    </tr>
                  ))}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  );
}
