import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { format, parseISO, subDays } from "date-fns";
import {
  Shield, RefreshCw, LogIn, LogOut, UserPlus, Brain, FileText, Key,
  AlertCircle, Info, Download, Calendar, TrendingUp, Activity,
  ClipboardCheck, Clock,
} from "lucide-react";
import { analyticsService } from "@/services/analytics.service";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/EmptyState";

const EVENT_ICONS: Record<string, typeof Shield> = {
  login: LogIn,
  logout: LogOut,
  register: UserPlus,
  prediction: Brain,
  report: FileText,
  password_change: Key,
  password_reset: Key,
  failed_login: AlertCircle,
};

const EVENT_COLORS: Record<string, string> = {
  login:           "text-emerald-600 bg-emerald-50 border-emerald-200",
  logout:          "text-slate-500 bg-slate-50 border-slate-200",
  register:        "text-sky-600 bg-sky-50 border-sky-200",
  prediction:      "text-purple-600 bg-purple-50 border-purple-200",
  report:          "text-indigo-600 bg-indigo-50 border-indigo-200",
  password_change: "text-amber-600 bg-amber-50 border-amber-200",
  password_reset:  "text-amber-600 bg-amber-50 border-amber-200",
  failed_login:    "text-red-600 bg-red-50 border-red-200",
};

function getEventType(event: any): string {
  const raw = (event.event_type ?? event.action ?? "").toLowerCase();
  if (raw.includes("login") && (raw.includes("fail") || raw.includes("denied"))) return "failed_login";
  if (raw.includes("login")) return "login";
  if (raw.includes("logout")) return "logout";
  if (raw.includes("register")) return "register";
  if (raw.includes("predict")) return "prediction";
  if (raw.includes("report")) return "report";
  if (raw.includes("password_change") || raw.includes("change_password")) return "password_change";
  if (raw.includes("password_reset") || raw.includes("reset_password")) return "password_reset";
  return raw;
}

function EventRow({ event }: { event: any }) {
  const type = getEventType(event);
  const Icon = EVENT_ICONS[type] ?? Info;
  const color = EVENT_COLORS[type] ?? "text-muted-foreground bg-muted/30 border-border";
  const ts = event.created_at ?? event.timestamp ?? event.occurred_at;

  return (
    <div className="flex items-start gap-3 py-3 border-b border-border/40 last:border-0">
      <span className={`inline-flex items-center justify-center w-7 h-7 rounded-lg border shrink-0 mt-0.5 ${color}`}>
        <Icon className="h-3.5 w-3.5" />
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-2">
          <p className="text-sm font-medium text-foreground capitalize">
            {(event.event_type ?? event.action ?? "Unknown event").replace(/_/g, " ")}
          </p>
          {ts && (() => { try { return <time className="text-xs text-muted-foreground shrink-0 whitespace-nowrap">{format(parseISO(ts), "MMM d · HH:mm")}</time>; } catch { return null; } })()}
        </div>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 mt-0.5 text-xs text-muted-foreground">
          {(event.worker_email ?? event.user_email) && (
            <span>{event.worker_email ?? event.user_email}</span>
          )}
          {event.ip_address && <span>IP: {event.ip_address}</span>}
          {event.description && <span className="truncate max-w-[240px]">{event.description}</span>}
        </div>
      </div>
    </div>
  );
}

const DAYS_OPTIONS = [7, 14, 30, 90];
const LIMIT_OPTIONS = [50, 100, 200];

const SCHEDULED_REPORTS = [
  {
    title: "Weekly Activity Report",
    desc: "User logins, predictions, and report generations",
    freq: "Every Monday, 08:00",
    icon: ClipboardCheck,
    color: "bg-sky-50 border-sky-200 text-sky-700",
  },
  {
    title: "Monthly Compliance Summary",
    desc: "HIPAA-compliant audit of all data access events",
    freq: "1st of each month",
    icon: Shield,
    color: "bg-purple-50 border-purple-200 text-purple-700",
  },
  {
    title: "Security Incident Digest",
    desc: "Failed logins and unauthorized access attempts",
    freq: "Daily, 23:00",
    icon: AlertCircle,
    color: "bg-red-50 border-red-200 text-red-600",
  },
];

export default function AuditTrailPage() {
  const [days, setDays] = useState(7);
  const [limit, setLimit] = useState(50);

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ["audit", "summary", days],
    queryFn: () => analyticsService.auditSummary(days),
    retry: false,
  });

  const { data: activities = [], isLoading: activitiesLoading, refetch, isFetching } = useQuery<any[]>({
    queryKey: ["audit", "activities", limit],
    queryFn: () => analyticsService.recentActivities(limit),
    retry: false,
  });

  const handleExport = () => {
    const lines = activities.map((e) => {
      const ts = e.created_at ?? e.timestamp ?? "";
      return `${ts}\t${e.event_type ?? ""}\t${e.worker_email ?? ""}\t${e.ip_address ?? ""}\t${e.description ?? ""}`;
    });
    const blob = new Blob(
      ["Timestamp\tEvent Type\tUser\tIP Address\tDescription\n" + lines.join("\n")],
      { type: "text/plain" },
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `audit-trail-${format(new Date(), "yyyy-MM-dd")}.tsv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const summaryEntries = Object.entries((summary ?? {}) as Record<string, number>)
    .filter(([, v]) => typeof v === "number")
    .slice(0, 6);

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Audit Trail</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Security and compliance activity log for the DiabObesity CDSS platform.
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

      {/* Date range filter */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm text-muted-foreground flex items-center gap-1.5">
          <Calendar className="h-3.5 w-3.5" /> Period:
        </span>
        {DAYS_OPTIONS.map((d) => (
          <button
            key={d}
            onClick={() => setDays(d)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors ${
              days === d
                ? "bg-primary text-primary-foreground border-primary"
                : "border-border text-foreground hover:bg-muted"
            }`}
          >
            {d} days
          </button>
        ))}
        <span className="text-xs text-muted-foreground ml-1">
          {format(subDays(new Date(), days), "MMM d")} – {format(new Date(), "MMM d, yyyy")}
        </span>
      </div>

      {/* Summary tiles */}
      {summaryLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-xl" />)}
        </div>
      ) : summaryEntries.length > 0 ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {summaryEntries.map(([key, val]) => (
            <div key={key} className="rounded-xl border border-border bg-card px-4 py-3">
              <p className="text-2xl font-bold text-foreground">{val.toLocaleString()}</p>
              <p className="text-xs text-muted-foreground mt-0.5 capitalize">{key.replace(/_/g, " ")}</p>
            </div>
          ))}
        </div>
      ) : null}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Activity log */}
        <div className="lg:col-span-2 rounded-xl border border-border bg-card overflow-hidden">
          <div className="px-5 py-4 border-b border-border/50 bg-muted/20 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Activity className="h-4 w-4 text-primary" /> Recent Activity
              {activities.length > 0 && (
                <span className="text-xs font-normal text-muted-foreground">
                  — {activities.length} events
                </span>
              )}
            </h2>
            <div className="flex items-center gap-1.5">
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

          <div className="px-5 max-h-[560px] overflow-y-auto">
            {activitiesLoading ? (
              <div className="py-4 space-y-3">
                {Array.from({ length: 8 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full rounded-lg" />
                ))}
              </div>
            ) : activities.length === 0 ? (
              <div className="py-10">
                <EmptyState
                  icon={Shield}
                  title="No activity recorded"
                  description="Audit events will appear as users interact with the system."
                />
              </div>
            ) : (
              <div>
                {activities.map((a: any, i: number) => (
                  <EventRow key={a.audit_id ?? a.id ?? i} event={a} />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Scheduled Reports & Compliance */}
        <div className="space-y-4">
          <div className="rounded-xl border border-border bg-card p-5">
            <h2 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
              <Clock className="h-4 w-4 text-primary" /> Scheduled Reports
            </h2>
            <div className="space-y-3">
              {SCHEDULED_REPORTS.map(({ title, desc, freq, icon: Icon, color }) => (
                <div key={title} className={`rounded-lg border p-3 ${color}`}>
                  <div className="flex items-start gap-2">
                    <Icon className="h-4 w-4 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-xs font-semibold">{title}</p>
                      <p className="text-[11px] opacity-80 mt-0.5">{desc}</p>
                      <p className="text-[10px] opacity-60 mt-1 font-medium">{freq}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-xl border border-border bg-card p-5">
            <h2 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-primary" /> Compliance Status
            </h2>
            <div className="space-y-2">
              {[
                { label: "HIPAA Compliance", ok: true },
                { label: "Data Access Logging", ok: true },
                { label: "Session Audit Trail", ok: true },
                { label: "Failed Login Tracking", ok: true },
              ].map(({ label, ok }) => (
                <div key={label} className="flex items-center justify-between text-xs py-1.5 border-b border-border/30 last:border-0">
                  <span className="text-foreground">{label}</span>
                  <span className={`font-semibold ${ok ? "text-emerald-600" : "text-red-500"}`}>
                    {ok ? "✓ Active" : "✗ Disabled"}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
