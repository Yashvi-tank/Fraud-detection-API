"use client";

import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  Filter,
  X,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  ArrowUpDown,
  SlidersHorizontal,
  ShieldCheck,
  AlertTriangle,
  CreditCard,
  Cpu,
  Globe,
  DollarSign,
  Calendar,
  Hash,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";

interface Transaction {
  id: string;
  amount: number;
  merchant: string;
  country: string;
  device_id: string;
  status: string;
  risk_score: number;
  reasons: string[];
  fraud_probability: number | null;
  model_version: string | null;
  created_at: string;
}

interface PaginatedResponse {
  items: Transaction[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

type SortField = "created_at" | "amount" | "risk_score";
type SortOrder = "asc" | "desc";

function SortIcon({
  field,
  sortBy,
  sortOrder,
}: {
  field: SortField;
  sortBy: SortField;
  sortOrder: SortOrder;
}) {
  if (sortBy !== field) return <ArrowUpDown size={12} className="text-slate-600" />;
  return sortOrder === "asc" ? (
    <ChevronUp size={12} className="text-indigo-400" />
  ) : (
    <ChevronDown size={12} className="text-indigo-400" />
  );
}

const STATUS_OPTIONS = ["", "SAFE", "REVIEW", "SUSPICIOUS"];

function StatusBadge({ status }: { status: string }) {
  const cfg: Record<string, string> = {
    SAFE: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    REVIEW: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    SUSPICIOUS: "bg-red-500/10 text-red-400 border-red-500/20",
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${cfg[status] ?? "bg-slate-800 text-slate-400 border-slate-700"}`}>
      {status}
    </span>
  );
}

function RiskBar({ score }: { score: number }) {
  const color = score >= 70 ? "bg-red-500" : score >= 40 ? "bg-amber-500" : "bg-emerald-500";
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-1.5 rounded-full bg-slate-800">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${score}%` }} />
      </div>
      <span className={`text-xs font-bold tabular-nums ${score >= 70 ? "text-red-400" : score >= 40 ? "text-amber-400" : "text-emerald-400"}`}>
        {score}
      </span>
    </div>
  );
}

function DetailDrawer({ tx, onClose }: { tx: Transaction; onClose: () => void }) {
  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 z-40 bg-slate-950/70 backdrop-blur-sm"
      />
      <motion.aside
        initial={{ x: "100%" }}
        animate={{ x: 0 }}
        exit={{ x: "100%" }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="fixed top-0 right-0 bottom-0 z-50 w-full max-w-md border-l border-slate-800 bg-slate-900 overflow-y-auto shadow-2xl"
      >
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-800 bg-slate-900/95 backdrop-blur-sm px-6 py-4">
          <div>
            <h2 className="font-heading font-bold text-slate-100">Transaction Detail</h2>
            <p className="text-xs text-slate-500 font-mono mt-0.5 truncate max-w-[220px]">{tx.id}</p>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Status & Score */}
          <div className="flex items-center justify-between">
            <StatusBadge status={tx.status} />
            <div className="text-right">
              <p className="text-xs text-slate-500 uppercase tracking-wider">Risk Score</p>
              <p className={`text-3xl font-extrabold tabular-nums ${tx.risk_score >= 70 ? "text-red-400" : tx.risk_score >= 40 ? "text-amber-400" : "text-emerald-400"}`}>
                {tx.risk_score}
              </p>
            </div>
          </div>

          {/* Core Fields */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/40 divide-y divide-slate-800">
            {[
              { icon: DollarSign, label: "Amount", value: `$${tx.amount.toLocaleString("en-US", { minimumFractionDigits: 2 })}`, mono: true },
              { icon: CreditCard, label: "Merchant", value: tx.merchant, mono: false },
              { icon: Globe, label: "Country", value: tx.country, mono: true },
              { icon: Hash, label: "Device ID", value: tx.device_id, mono: true },
              { icon: Calendar, label: "Timestamp", value: new Date(tx.created_at).toLocaleString(), mono: false },
            ].map(({ icon: Icon, label, value, mono }) => (
              <div key={label} className="flex items-center gap-3 px-4 py-3.5">
                <div className="h-8 w-8 rounded-lg bg-slate-800/80 flex items-center justify-center">
                  <Icon size={14} className="text-slate-400" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-xs text-slate-500 uppercase tracking-wider">{label}</p>
                  <p className={`text-sm font-semibold text-slate-200 truncate mt-0.5 ${mono ? "font-mono" : ""}`}>{value}</p>
                </div>
              </div>
            ))}
          </div>

          {/* ML Analysis */}
          {tx.fraud_probability !== null && (
            <div className="rounded-xl border border-indigo-900/50 bg-indigo-950/20 p-4 space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-indigo-400">
                <Cpu size={12} />
                ML Model Analysis
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-400">Fraud Probability</span>
                <span className="font-bold text-slate-200">{((tx.fraud_probability ?? 0) * 100).toFixed(1)}%</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2">
                <div
                  className="h-2 rounded-full"
                  style={{
                    width: `${(tx.fraud_probability ?? 0) * 100}%`,
                    background: `linear-gradient(to right, #6366f1, ${(tx.fraud_probability ?? 0) > 0.7 ? "#ef4444" : (tx.fraud_probability ?? 0) > 0.4 ? "#f59e0b" : "#10b981"})`,
                  }}
                />
              </div>
              {tx.model_version && (
                <p className="text-xs text-slate-500 font-mono">{tx.model_version}</p>
              )}
            </div>
          )}

          {/* Reasons / Evidence */}
          {tx.reasons && tx.reasons.length > 0 && (
            <div>
              <p className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-3 flex items-center gap-1.5">
                <ShieldCheck size={12} className="text-emerald-400" />
                Risk Triggers
              </p>
              <ul className="space-y-2">
                {tx.reasons.map((r, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-sm rounded-lg bg-slate-950/50 border border-slate-800 px-3 py-2.5">
                    <AlertTriangle size={13} className="text-amber-400 mt-0.5 shrink-0" />
                    <span className="text-slate-300">{r}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </motion.aside>
    </AnimatePresence>
  );
}

export default function TransactionsPage() {
  const [data, setData] = useState<PaginatedResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(12);
  const [sortBy, setSortBy] = useState<SortField>("created_at");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [selectedTx, setSelectedTx] = useState<Transaction | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 350);
    return () => clearTimeout(timer);
  }, [search]);

  const fetchTransactions = useCallback(async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      if (statusFilter) params.append("status", statusFilter);
      if (debouncedSearch) params.append("merchant", debouncedSearch);

      const res = await apiClient.get(`/transactions/?${params.toString()}`);
      setData(res.data);
    } catch (err) {
      console.error("Transactions fetch error", err);
    } finally {
      setIsLoading(false);
    }
  }, [page, pageSize, sortBy, sortOrder, statusFilter, debouncedSearch]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void fetchTransactions();
  }, [fetchTransactions]);

  // Reset to page 1 on filter/sort change
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void Promise.resolve(setPage(1));
  }, [sortBy, sortOrder, statusFilter, debouncedSearch]);

  const toggleSort = (field: SortField) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(field);
      setSortOrder("desc");
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="font-heading text-2xl font-extrabold tracking-tight text-slate-50">Transactions</h1>
        <p className="text-sm text-slate-400 mt-1">
          {data ? `${data.total.toLocaleString()} total records` : "Loading…"} · Click any row for details
        </p>
      </motion.div>

      {/* Toolbar */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="flex flex-col sm:flex-row gap-3"
      >
        {/* Search */}
        <div className="relative flex-1">
          <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search by merchant…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-900 pl-9 pr-4 py-2.5 text-sm text-slate-200 placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition"
          />
          {search && (
            <button onClick={() => setSearch("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300">
              <X size={14} />
            </button>
          )}
        </div>

        {/* Filter Toggle */}
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`inline-flex items-center gap-2 rounded-lg border px-4 py-2.5 text-sm font-semibold transition-all ${
            statusFilter
              ? "border-indigo-500/50 bg-indigo-600/10 text-indigo-400"
              : "border-slate-700 bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
          }`}
        >
          <SlidersHorizontal size={14} />
          Filters {statusFilter && `(${statusFilter})`}
        </button>
      </motion.div>

      {/* Filter Panel */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
                  <Filter size={11} />
                  Status:
                </span>
                {STATUS_OPTIONS.map((s) => (
                  <button
                    key={s || "all"}
                    onClick={() => setStatusFilter(s)}
                    className={`rounded-full px-3.5 py-1.5 text-xs font-semibold border transition-all ${
                      statusFilter === s
                        ? s === ""
                          ? "border-indigo-500/50 bg-indigo-600/20 text-indigo-300"
                          : s === "SAFE"
                          ? "border-emerald-500/50 bg-emerald-500/20 text-emerald-300"
                          : s === "SUSPICIOUS"
                          ? "border-red-500/50 bg-red-500/20 text-red-300"
                          : "border-amber-500/50 bg-amber-500/20 text-amber-300"
                        : "border-slate-700 text-slate-400 hover:border-slate-600 hover:text-slate-300"
                    }`}
                  >
                    {s || "All"}
                  </button>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Table */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm overflow-hidden"
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/50">
                <th className="px-5 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                  <button onClick={() => toggleSort("created_at")} className="inline-flex items-center gap-1.5 hover:text-slate-300 transition-colors">
                    Time <SortIcon field="created_at" sortBy={sortBy} sortOrder={sortOrder} />
                  </button>
                </th>
                <th className="px-5 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">Merchant</th>
                <th className="px-5 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">Country</th>
                <th className="px-5 py-3.5 text-right text-xs font-semibold uppercase tracking-wider text-slate-500">
                  <button onClick={() => toggleSort("amount")} className="inline-flex items-center gap-1.5 hover:text-slate-300 transition-colors">
                    Amount <SortIcon field="amount" sortBy={sortBy} sortOrder={sortOrder} />
                  </button>
                </th>
                <th className="px-5 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                  <button onClick={() => toggleSort("risk_score")} className="inline-flex items-center gap-1.5 hover:text-slate-300 transition-colors">
                    Risk <SortIcon field="risk_score" sortBy={sortBy} sortOrder={sortOrder} />
                  </button>
                </th>
                <th className="px-5 py-3.5 text-center text-xs font-semibold uppercase tracking-wider text-slate-500">Status</th>
                <th className="px-5 py-3.5 text-right text-xs font-semibold uppercase tracking-wider text-slate-500">ML Prob</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40">
              {isLoading
                ? Array.from({ length: 8 }).map((_, i) => (
                    <tr key={i}>
                      {Array.from({ length: 7 }).map((_, j) => (
                        <td key={j} className="px-5 py-4">
                          <div className="h-3.5 w-full rounded-md bg-slate-800 animate-pulse" style={{ width: `${60 + Math.random() * 40}%` }} />
                        </td>
                      ))}
                    </tr>
                  ))
                : (data?.items ?? []).map((tx) => (
                    <tr
                      key={tx.id}
                      onClick={() => setSelectedTx(tx)}
                      className="hover:bg-slate-800/40 cursor-pointer transition-colors"
                    >
                      <td className="px-5 py-3.5 text-xs text-slate-400 whitespace-nowrap">
                        {new Date(tx.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}{" "}
                        <span className="text-slate-600">{new Date(tx.created_at).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })}</span>
                      </td>
                      <td className="px-5 py-3.5 font-medium text-slate-200 whitespace-nowrap">{tx.merchant}</td>
                      <td className="px-5 py-3.5 text-slate-400">{tx.country}</td>
                      <td className="px-5 py-3.5 text-right font-bold text-slate-200 tabular-nums whitespace-nowrap">
                        ${tx.amount.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      <td className="px-5 py-3.5">
                        <RiskBar score={tx.risk_score} />
                      </td>
                      <td className="px-5 py-3.5 text-center">
                        <StatusBadge status={tx.status} />
                      </td>
                      <td className="px-5 py-3.5 text-right text-xs tabular-nums text-slate-400 font-mono">
                        {tx.fraud_probability !== null ? `${((tx.fraud_probability ?? 0) * 100).toFixed(1)}%` : "—"}
                      </td>
                    </tr>
                  ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && data.total_pages > 1 && (
          <div className="flex items-center justify-between border-t border-slate-800 px-5 py-3.5">
            <p className="text-xs text-slate-500">
              Page {data.page} of {data.total_pages} · {data.total} results
            </p>
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="rounded-lg border border-slate-700 bg-slate-900 p-2 text-slate-400 hover:bg-slate-800 hover:text-slate-200 disabled:opacity-40 transition-all"
              >
                <ChevronLeft size={14} />
              </button>
              {Array.from({ length: Math.min(5, data.total_pages) }, (_, i) => {
                const pageNum = Math.max(1, Math.min(data.total_pages - 4, page - 2)) + i;
                return (
                  <button
                    key={pageNum}
                    onClick={() => setPage(pageNum)}
                    className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                      pageNum === page
                        ? "bg-indigo-600 text-white border border-indigo-500"
                        : "border border-slate-700 bg-slate-900 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}
              <button
                onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                disabled={page === data.total_pages}
                className="rounded-lg border border-slate-700 bg-slate-900 p-2 text-slate-400 hover:bg-slate-800 hover:text-slate-200 disabled:opacity-40 transition-all"
              >
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}

        {/* Empty state */}
        {!isLoading && data?.items.length === 0 && (
          <div className="py-20 text-center">
            <div className="h-14 w-14 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-4">
              <CreditCard size={24} className="text-slate-600" />
            </div>
            <p className="text-slate-400 font-semibold">No transactions found</p>
            <p className="text-xs text-slate-600 mt-1">Try adjusting your filters</p>
          </div>
        )}
      </motion.div>

      {/* Detail Drawer */}
      <AnimatePresence>
        {selectedTx && (
          <DetailDrawer tx={selectedTx} onClose={() => setSelectedTx(null)} />
        )}
      </AnimatePresence>
    </div>
  );
}
