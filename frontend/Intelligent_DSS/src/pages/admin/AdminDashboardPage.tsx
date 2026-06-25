import { useQuery } from "@tanstack/react-query";
import { format, parseISO } from "date-fns";
import { Link } from "react-router-dom";
import {
  Users, ClipboardList, Brain, FileText, RefreshCw,
  Building2, ScrollText, ShieldCheck, Settings,
  ChevronRight, Activity, TrendingUp, UserCheck, Clock, Wifi,
  LogIn, LogOut, UserPlus, Key, AlertCircle, Info,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboardStats, useRiskDistribution } from "@/hooks/useAnalytics";
import { analyticsService } from "@/services/analytics.service";

const EVENT_ICONS: Record<string, typeof Activity> = {
  login: LogIn as any,
  logout: LogOut as any,
  register: UserPlus as any,
  prediction: Brain as any,
  report: FileText as any,
  password_change: Key as any,
  failed_login: AlertCircle as any,
};

const EVENT_COLORS: Record<string, string> = {
  login:           "text-emerald-600 bg-emerald-50 border-emerald-200",
  logout:          "text-slate-500 bg-slate-50 border-slate-200",
  register:        "text-sky-600 bg-sky-50 border-sky-200",
  prediction:      "text-purple-600 bg-purple-50 border-purple-200",
  report:          "text-indigo-600 bg-indigo-50 border-indigo-200",
  password_change: "text-amber-600 bg-amber-50 border-amber-200",
  failed_login:    "text-red-600 bg-red-50 border-red-200",
};

function inferEventType(event: any): string {
  const raw = (event.event_type ?? event.action ?? "").toLowerCase();
  if (raw.includes("login") && (raw.includes("fail") || raw.includes("denied"))) return "failed_login";
  if (raw.includes("login")) return "login";
  if (raw.includes("logout")) return "logout";
  if (raw.includes("register")) return "register";
  if (raw.includes("predict")) return "prediction";
  if (raw.includes("report")) return "report";
  if (raw.includes("password")) return "password_change";
  return "info";
}

const ADMIN_LINKS = [
  { label: "User Management",     to: "/admin/users",      icon: Users,          desc: "Manage clinician accounts and permissions",  color: "bg-sky-50 text-sky-600 border-sky-200" },
  { label: "Facility Management", to: "/admin/facilities", icon: Building2,       desc: "Monitor clinic nodes and departments",        color: "bg-emerald-50 text-emerald-600 border-emerald-200" },
  { label: "System Logs",         to: "/admin/logs",       icon: ScrollText,      desc: "Inspect live audit and system events",        color: "bg-amber-50 text-amber-600 border-amber-200" },
  { label: "Audit Trail",         to: "/admin/audit",      icon: ShieldCheck,     desc: "Compliance tracking and reporting",           color: "bg-purple-50 text-purple-600 border-purple-200" },
  { label: "AI Report",           to: "/admin/ai-report",  icon: Brain,           desc: "Model performance and risk analytics",        color: "bg-rose-50 text-rose-600 border-rose-200" },
  { label: "System Config",       to: "/admin/config",     icon: Settings,        desc: "Configure platform settings",                 color: "bg-slate-50 text-slate-600 border-slate-200" },
];

export default function AdminDashboardPage() {
  const { data: stats, isLoading: statsLoading, refetch, isFetching } = useDashboardStats();
  const { data: riskData } = useRiskDistribution();

  const { data: activities = [], isLoading: activitiesLoading } = useQuery<any[]>({
    queryKey: ["audit", "activities", 10],
    queryFn: () => analyticsService.recentActivities(10),
    staleTime: 1000 * 60 * 2,
    retry: false,
  });

  const riskDist = (riskData as any)?.distribution?.diabetes ?? {};
  const highRisk   = riskDist.High     ?? stats?.high_risk_count     ?? 0;
  const modRisk    = riskDist.Moderate ?? stats?.moderate_risk_count  ?? 0;
  const lowRisk    = riskDist.Low      ?? stats?.low_risk_count       ?? 0;

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Administrator Overview</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Platform health, activity, and system status at a glance.
          </p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border text-sm text-muted-foreground hover:bg-muted transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* System Status Banner */}
      <div className="rounded-xl border border-emerald-200 bg-emerald-50/60 px-5 py-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-emerald-100 border border-emerald-200">
            <Wifi className="h-5 w-5 text-emerald-600" />
          </div>
          <div>
            <p className="text-sm font-semibold text-emerald-800">All Systems Operational</p>
            <p className="text-xs text-emerald-600">Backend API · Database · ML Engine · Reporting Service</p>
          </div>
        </div>
        <div className="flex items-center gap-4 text-xs text-emerald-700">
          <span className="flex items-center gap-1">
            <TrendingUp className="h-3.5 w-3.5" /> 99.9% Uptime
          </span>
          <span className="flex items-center gap-1">
            <Clock className="h-3.5 w-3.5" /> Last 30 days
          </span>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border bg-emerald-100 text-emerald-700 border-emerald-300">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            Operational
          </span>
        </div>
      </div>

      {/* Stat Tiles */}
      {statsLoading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-28 rounded-xl" />)}
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="rounded-xl border border-border bg-card p-5">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm text-muted-foreground">Patients Registered</p>
              <div className="p-2 rounded-lg bg-sky-50"><Users className="h-4 w-4 text-sky-600" /></div>
            </div>
            <p className="text-3xl font-bold text-foreground">{(stats?.total_patients ?? 0).toLocaleString()}</p>
            <p className="text-xs text-muted-foreground mt-1">{(stats?.active_patients ?? 0)} active</p>
          </div>
          <div className="rounded-xl border border-border bg-card p-5">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm text-muted-foreground">Total Screenings</p>
              <div className="p-2 rounded-lg bg-purple-50"><ClipboardList className="h-4 w-4 text-purple-600" /></div>
            </div>
            <p className="text-3xl font-bold text-foreground">{(stats?.total_screenings ?? 0).toLocaleString()}</p>
            <p className="text-xs text-muted-foreground mt-1">{(stats?.recent_activities ?? 0)} in last 24h</p>
          </div>
          <div className="rounded-xl border border-border bg-card p-5">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm text-muted-foreground">Predictions Run</p>
              <div className="p-2 rounded-lg bg-rose-50"><Brain className="h-4 w-4 text-rose-600" /></div>
            </div>
            <p className="text-3xl font-bold text-foreground">{(stats?.total_predictions ?? 0).toLocaleString()}</p>
            <p className="text-xs text-muted-foreground mt-1">{highRisk} high-risk cases</p>
          </div>
          <div className="rounded-xl border border-border bg-card p-5">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm text-muted-foreground">Reports Generated</p>
              <div className="p-2 rounded-lg bg-indigo-50"><FileText className="h-4 w-4 text-indigo-600" /></div>
            </div>
            <p className="text-3xl font-bold text-foreground">{(stats?.total_reports ?? 0).toLocaleString()}</p>
            <p className="text-xs text-muted-foreground mt-1">Clinical PDFs</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Recent Activity Feed */}
        <div className="lg:col-span-2 rounded-xl border border-border bg-card overflow-hidden">
          <div className="px-5 py-4 border-b border-border/50 bg-muted/20 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Activity className="h-4 w-4 text-primary" /> Recent Activity
            </h2>
            <Link to="/admin/audit" className="text-xs text-primary hover:underline flex items-center gap-1">
              View all <ChevronRight className="h-3 w-3" />
            </Link>
          </div>
          <div className="px-5 divide-y divide-border/30">
            {activitiesLoading ? (
              Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full my-2 rounded-lg" />
              ))
            ) : activities.length === 0 ? (
              <div className="py-10 text-center">
                <p className="text-sm text-muted-foreground">No recent activity recorded.</p>
              </div>
            ) : (
              activities.slice(0, 8).map((event: any, i: number) => {
                const type = inferEventType(event);
                const Icon = EVENT_ICONS[type] ?? (Info as any);
                const color = EVENT_COLORS[type] ?? "text-muted-foreground bg-muted/30 border-border";
                const ts = event.created_at ?? event.timestamp;
                let timeStr = "";
                try { if (ts) timeStr = format(parseISO(ts), "HH:mm · MMM d"); } catch {}
                return (
                  <div key={event.audit_id ?? i} className="flex items-start gap-3 py-3">
                    <span className={`inline-flex items-center justify-center w-7 h-7 rounded-lg border shrink-0 mt-0.5 ${color}`}>
                      <Icon className="h-3.5 w-3.5" />
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-medium text-foreground capitalize">
                          {(event.event_type ?? event.action ?? "System event").replace(/_/g, " ")}
                        </p>
                        {timeStr && (
                          <time className="text-xs text-muted-foreground shrink-0">{timeStr}</time>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground truncate">
                        {event.worker_email ?? event.user_email ?? "System"}
                        {event.ip_address ? ` · ${event.ip_address}` : ""}
                      </p>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Risk Summary */}
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          <div className="px-5 py-4 border-b border-border/50 bg-muted/20 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <UserCheck className="h-4 w-4 text-primary" /> Risk Summary
            </h2>
            <Link to="/analytics" className="text-xs text-primary hover:underline flex items-center gap-1">
              Analytics <ChevronRight className="h-3 w-3" />
            </Link>
          </div>
          <div className="px-5 py-4 space-y-3">
            {statsLoading ? (
              Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-12 w-full rounded-lg" />)
            ) : (
              [
                { label: "High Risk", val: highRisk, color: "bg-red-50 border-red-200 text-red-700" },
                { label: "Moderate Risk", val: modRisk, color: "bg-amber-50 border-amber-200 text-amber-700" },
                { label: "Low Risk", val: lowRisk, color: "bg-emerald-50 border-emerald-200 text-emerald-700" },
              ].map(({ label, val, color }) => (
                <div key={label} className={`flex items-center justify-between px-4 py-3 rounded-lg border ${color}`}>
                  <span className="text-sm font-medium">{label}</span>
                  <span className="text-lg font-bold">{val.toLocaleString()}</span>
                </div>
              ))
            )}
          </div>
          <div className="px-5 pb-4 pt-1">
            <div className="rounded-lg bg-muted/30 border border-border/50 px-4 py-3 text-center">
              <p className="text-2xl font-bold text-foreground">
                {((highRisk + modRisk + lowRisk) || 0).toLocaleString()}
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">Total Predictions</p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Nav */}
      <div>
        <h2 className="text-sm font-semibold text-foreground mb-3">Administration</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {ADMIN_LINKS.map(({ label, to, icon: Icon, desc, color }) => (
            <Link
              key={to}
              to={to}
              className="rounded-xl border border-border bg-card p-4 hover:border-primary/40 hover:shadow-sm transition-all group"
            >
              <div className={`inline-flex p-2 rounded-lg border mb-3 ${color}`}>
                <Icon className="h-4 w-4" />
              </div>
              <p className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">{label}</p>
              <p className="text-xs text-muted-foreground mt-0.5">{desc}</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
