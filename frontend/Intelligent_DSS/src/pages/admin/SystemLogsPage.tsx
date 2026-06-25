import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { format, parseISO } from "date-fns";
import {
  Terminal, RefreshCw, AlertCircle, Info, CheckCircle2, AlertTriangle,
  Download, Search, Filter,
} from "lucide-react";
import { analyticsService } from "@/services/analytics.service";
import { Skeleton } from "@/components/ui/skeleton";

type LogLevel = "info" | "warning" | "error" | "success";

function inferLevel(event: any): LogLevel {
  const type = (event.event_type ?? event.action ?? "").toLowerCase();
  if (type.includes("fail") || type.includes("error") || type.includes("denied")) return "error";
  if (type.includes("warn") || type.includes("attempt")) return "warning";
  if (type.includes("login") || type.includes("register") || type.includes("predict") || type.includes("report")) return "success";
  return "info";
}

const LEVEL_CONFIG: Record<LogLevel, { icon: typeof Info; badgeClass: string; rowClass: string; label: string }> = {
  info:    { icon: Info,         badgeClass: "text-sky-400 bg-sky-900/40 border-sky-700",     rowClass: "",                    label: "INFO"    },
  success: { icon: CheckCircle2, badgeClass: "text-emerald-400 bg-emerald-900/40 border-emerald-700", rowClass: "",            label: "OK"      },
  warning: { icon: AlertTriangle,badgeClass: "text-amber-400 bg-amber-900/40 border-amber-700",  rowClass: "bg-amber-950/10", label: "WARN"    },
  error:   { icon: AlertCircle,  badgeClass: "text-red-400 bg-red-900/40 border-red-700",     rowClass: "bg-red-950/20",       label: "ERROR"   },
};

function LogRow({ event }: { event: any }) {
  const level = inferLevel(event);
  const { icon: Icon, badgeClass, rowClass, label } = LEVEL_CONFIG[level];
  const ts = event.created_at ?? event.timestamp ?? event.occurred_at;

  return (
    <div className={`flex items-start gap-3 py-2 px-4 border-b border-zinc-800/60 last:border-0 font-mono text-xs ${rowClass}`}>
      <time className="text-zinc-500 shrink-0 tabular-nums w-28 pt-0.5">
        {ts ? (() => { try { return format(parseISO(ts), "HH:mm:ss.SSS"); } catch { return "—:—:—.———"; } })() : "—:—:—.———"}
      </time>
      <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded border text-[10px] font-bold shrink-0 ${badgeClass}`}>
        <Icon className="h-2.5 w-2.5" />{label}
      </span>
      <span className="text-zinc-300 break-all">
        <span className="text-zinc-500">[</span>
        <span className="text-amber-300">{(event.event_type ?? event.action ?? "SYSTEM").toUpperCase().replace(/ /g, "_")}</span>
        <span className="text-zinc-500">]</span>
        {event.worker_email ? <span className="text-sky-400"> {event.worker_email}</span> : ""}
        {event.description ? <span className="text-zinc-400"> — {event.description}</span> : ""}
        {event.ip_address ? <span className="text-zinc-600"> ({event.ip_address})</span> : ""}
      </span>
    </div>
  );
}

const LIMIT_OPTIONS = [50, 100, 200];

export default function SystemLogsPage() {
  const [limit, setLimit] = useState(50);
  const [levelFilter, setLevelFilter] = useState<LogLevel | "all">("all");
  const [search, setSearch] = useState("");

  const { data: activities = [], isLoading, refetch, isFetching, dataUpdatedAt } = useQuery<any[]>({
    queryKey: ["system-logs", limit],
    queryFn: () => analyticsService.recentActivities(limit),
    staleTime: 1000 * 60 * 2,
    retry: false,
  });

  const filtered = activities.filter((e) => {
    if (levelFilter !== "all" && inferLevel(e) !== levelFilter) return false;
    if (search) {
      const q = search.toLowerCase();
      const text = `${e.event_type ?? ""} ${e.action ?? ""} ${e.worker_email ?? ""} ${e.description ?? ""} ${e.ip_address ?? ""}`.toLowerCase();
      if (!text.includes(q)) return false;
    }
    return true;
  });

  const counts = {
    info:    activities.filter((e) => inferLevel(e) === "info").length,
    success: activities.filter((e) => inferLevel(e) === "success").length,
    warning: activities.filter((e) => inferLevel(e) === "warning").length,
    error:   activities.filter((e) => inferLevel(e) === "error").length,
  };

  const handleExport = () => {
    const lines = filtered.map((e) => {
      const ts = e.created_at ?? e.timestamp ?? "";
      return `${ts}\t${(e.event_type ?? "").toUpperCase()}\t${e.worker_email ?? ""}\t${e.description ?? ""}`;
    });
    const blob = new Blob(["Timestamp\tEvent\tUser\tDescription\n" + lines.join("\n")], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `system-logs-${format(new Date(), "yyyy-MM-dd")}.tsv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-5 pb-8">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">System Logs</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Live audit trail from the system event service.
            {dataUpdatedAt > 0 && (
              <span className="ml-2 text-xs text-muted-foreground/60">
                Updated {format(new Date(dataUpdatedAt), "HH:mm:ss")}
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border text-sm text-muted-foreground hover:bg-muted transition-colors"
          >
            <Download className="h-3.5 w-3.5" /> Export
          </button>
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border text-sm text-muted-foreground hover:bg-muted transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Summary chips */}
      {!isLoading && (
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Filter className="h-3.5 w-3.5" /> Filter:
          </div>
          {(["all", "success", "info", "warning", "error"] as const).map((lvl) => {
            const count = lvl === "all" ? activities.length : counts[lvl as LogLevel];
            const active = levelFilter === lvl;
            const cfg = lvl !== "all" ? LEVEL_CONFIG[lvl as LogLevel] : null;
            return (
              <button
                key={lvl}
                onClick={() => setLevelFilter(lvl)}
                className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                  active
                    ? "bg-foreground text-background border-foreground"
                    : "border-border text-muted-foreground hover:bg-muted"
                }`}
              >
                {lvl === "all" ? "All" : cfg?.label} ({count})
              </button>
            );
          })}

          {/* Show limit controls */}
          <div className="ml-auto flex items-center gap-1.5">
            <span className="text-xs text-muted-foreground">Show</span>
            {LIMIT_OPTIONS.map((l) => (
              <button
                key={l}
                onClick={() => setLimit(l)}
                className={`px-2 py-1 rounded text-xs font-medium border transition-colors ${
                  limit === l
                    ? "bg-primary text-primary-foreground border-primary"
                    : "border-border text-foreground hover:bg-muted"
                }`}
              >
                {l}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search logs…"
          className="w-full pl-9 pr-3 py-2 bg-card border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
        />
      </div>

      {/* Log terminal */}
      <div className="rounded-xl border border-zinc-700 bg-zinc-950 overflow-hidden shadow-lg">
        {/* Terminal bar */}
        <div className="flex items-center gap-2 px-4 py-2.5 border-b border-zinc-800 bg-zinc-900">
          <div className="flex gap-1.5">
            <span className="w-3 h-3 rounded-full bg-red-500/80" />
            <span className="w-3 h-3 rounded-full bg-amber-500/80" />
            <span className="w-3 h-3 rounded-full bg-emerald-500/80" />
          </div>
          <div className="flex items-center gap-2 ml-2">
            <Terminal className="h-3.5 w-3.5 text-emerald-400" />
            <span className="text-xs font-mono text-emerald-400">cdss://system.audit.log</span>
          </div>
          <div className="ml-auto flex items-center gap-3 text-xs font-mono">
            <span className="text-zinc-500">{filtered.length} entries</span>
            {isFetching && <span className="text-emerald-400 animate-pulse">● live</span>}
          </div>
        </div>

        {/* Log entries */}
        <div className="min-h-[320px] max-h-[580px] overflow-y-auto py-1">
          {isLoading ? (
            <div className="px-4 py-4 space-y-1.5">
              {Array.from({ length: 12 }).map((_, i) => (
                <Skeleton key={i} className="h-5 bg-zinc-800 rounded" />
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <Terminal className="h-8 w-8 text-zinc-700 mb-3" />
              <p className="text-xs font-mono text-zinc-500">No log entries match the current filter.</p>
            </div>
          ) : (
            filtered.map((a: any, i: number) => (
              <LogRow key={a.audit_id ?? a.id ?? i} event={a} />
            ))
          )}
        </div>
      </div>
    </div>
  );
}
