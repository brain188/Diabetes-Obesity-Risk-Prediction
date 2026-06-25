import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  BarChart, Bar,
} from "recharts";
import {
  Users, Brain, ClipboardList, AlertTriangle,
  TrendingUp, Activity, Database, CheckCircle2, RefreshCw,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useDashboardStats,
  useFeatureImportance,
  useMonthlyTrends,
} from "@/hooks/useAnalytics";
import { cn } from "@/lib/utils";

const RISK_COLORS = { Low: "#10b981", Moderate: "#f59e0b", High: "#ef4444" };

/* ── Stat card ── */
function StatCard({
  label, value, icon: Icon, color, sub,
}: {
  label: string; value: string | number; icon: typeof Users; color: string; sub?: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm text-muted-foreground">{label}</p>
        <div className={cn("p-2 rounded-lg", color)}>
          <Icon className="h-4 w-4" />
        </div>
      </div>
      <p className="text-3xl font-bold text-foreground">{typeof value === "number" ? value.toLocaleString() : value}</p>
      {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
    </div>
  );
}

/* ── Pie chart with clean percentage legend ── */
function RiskPie({ title, data }: { title: string; data: { name: string; value: number; color: string }[] }) {
  const total = data.reduce((s, d) => s + d.value, 0);
  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <h2 className="text-sm font-semibold text-foreground mb-1">{title}</h2>
      <p className="text-xs text-muted-foreground mb-3">
        {total.toLocaleString()} total predictions
      </p>
      {total === 0 ? (
        <p className="text-sm text-muted-foreground py-12 text-center">No data yet.</p>
      ) : (
        <div className="flex items-center gap-4">
          {/* Pie — no labels on slices, tooltip only */}
          <div className="shrink-0" style={{ width: 160, height: 160 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={42}
                  outerRadius={72}
                  paddingAngle={2}
                  label={false}
                >
                  {data.map((d, i) => <Cell key={i} fill={d.color} />)}
                </Pie>
                <Tooltip
                  formatter={(v: number) => [
                    `${v.toLocaleString()} (${total > 0 ? ((v / total) * 100).toFixed(1) : 0}%)`,
                    "Patients",
                  ]}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          {/* Custom legend showing pct + count */}
          <div className="flex-1 space-y-2.5 min-w-0">
            {data.map((d) => {
              const pct = total > 0 ? ((d.value / total) * 100) : 0;
              return (
                <div key={d.name} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="flex items-center gap-1.5 font-medium text-foreground">
                      <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: d.color }} />
                      {d.name}
                    </span>
                    <span className="font-semibold text-foreground">{pct.toFixed(1)}%</span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{ width: `${pct}%`, background: d.color }}
                    />
                  </div>
                  <p className="text-[10px] text-muted-foreground text-right">{d.value.toLocaleString()} patients</p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export default function AnalyticsDashboardPage() {
  const { data: stats, isLoading: statsLoading, refetch, isFetching } = useDashboardStats();
  const { data: fiData, isLoading: fiLoading } = useFeatureImportance();
  const { data: trends = [], isLoading: trendsLoading } = useMonthlyTrends(6);

  /* Build pie data from stats.risk_distribution */
  const riskDist = (stats as any)?.risk_distribution ?? {};
  const diabetesDist = riskDist.diabetes ?? {};
  const obesityDist = riskDist.obesity ?? {};

  const diabetesPie = [
    { name: "Low", value: diabetesDist.Low ?? 0, color: RISK_COLORS.Low },
    { name: "Moderate", value: diabetesDist.Moderate ?? 0, color: RISK_COLORS.Moderate },
    { name: "High", value: diabetesDist.High ?? 0, color: RISK_COLORS.High },
  ];
  const obesityPie = [
    { name: "Normal", value: obesityDist.Low ?? 0, color: RISK_COLORS.Low },
    { name: "Overweight", value: obesityDist.Moderate ?? 0, color: RISK_COLORS.Moderate },
    { name: "Obese", value: obesityDist.High ?? 0, color: RISK_COLORS.High },
  ];

  /* Feature importance bar data */
  const fiImportance: Record<string, number> = fiData?.feature_importance ?? {};
  const featureBarData = Object.entries(fiImportance)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([feature, importance]) => ({
      feature: feature.replace(/_/g, " "),
      importance: Math.round((importance as number) * 100),
    }));

  const totalPatients = (stats as any)?.total_patients ?? 0;
  const totalScreenings = (stats as any)?.total_screenings ?? 0;
  const highRisk = diabetesDist.High ?? 0;
  const sexDist = (stats as any)?.sex_distribution ?? {};

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Unit Analytics</h1>
          <p className="text-sm text-muted-foreground mt-1">Real-time clinical insights and predictive performance metrics.</p>
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

      {/* Stat cards */}
      {statsLoading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-28 rounded-xl" />)}
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label="Total Patients" value={totalPatients} icon={Users} color="bg-blue-50 text-blue-600" sub={`${sexDist.Male ?? 0}M · ${sexDist.Female ?? 0}F`} />
          <StatCard label="Total Screenings" value={totalScreenings} icon={ClipboardList} color="bg-purple-50 text-purple-600" />
          <StatCard label="High Risk Cases" value={highRisk} icon={AlertTriangle} color="bg-red-50 text-red-600" sub="Require follow-up" />
          <StatCard label="Recent Activity" value={(stats as any)?.recent_activities ?? 0} icon={Activity} color="bg-emerald-50 text-emerald-600" sub="Last 24 hours" />
        </div>
      )}

      {/* Pie charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {statsLoading ? (
          <>
            <Skeleton className="h-64 rounded-xl" />
            <Skeleton className="h-64 rounded-xl" />
          </>
        ) : (
          <>
            <RiskPie title="Diabetes Risk Distribution" data={diabetesPie} />
            <RiskPie title="Obesity Risk Distribution" data={obesityPie} />
          </>
        )}
      </div>

      {/* Monthly trends line chart */}
      <div className="rounded-xl border border-border bg-card p-5">
        <h2 className="text-sm font-semibold text-foreground mb-1">Monthly Screening Trends</h2>
        <p className="text-xs text-muted-foreground mb-4">Screenings and predictions over the last 6 months</p>
        {trendsLoading ? (
          <Skeleton className="h-52 w-full rounded-lg" />
        ) : trends.length === 0 ? (
          <p className="text-sm text-muted-foreground py-16 text-center">No trend data available yet.</p>
        ) : (
          <ResponsiveContainer width="100%" height={210}>
            <LineChart data={trends} margin={{ left: 0, right: 8, top: 4, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="screenings" stroke="#2563eb" strokeWidth={2} dot={{ r: 3 }} name="Screenings" />
              <Line type="monotone" dataKey="predictions" stroke="#7c3aed" strokeWidth={2} dot={{ r: 3 }} name="Predictions" />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Feature importance */}
      <div className="rounded-xl border border-border bg-card p-5">
        <h2 className="text-sm font-semibold text-foreground mb-1">Global Feature Importance</h2>
        <p className="text-xs text-muted-foreground mb-4">Top predictors in the CatBoost diabetes model</p>
        {fiLoading ? (
          <Skeleton className="h-52 w-full rounded-lg" />
        ) : featureBarData.length === 0 ? (
          <p className="text-sm text-muted-foreground py-16 text-center">Feature importance data unavailable.</p>
        ) : (
          <ResponsiveContainer width="100%" height={Math.max(200, featureBarData.length * 38)}>
            <BarChart data={featureBarData} layout="vertical" margin={{ left: 8, right: 24, top: 4, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11 }} unit="%" domain={[0, 100]} />
              <YAxis type="category" dataKey="feature" tick={{ fontSize: 11 }} width={120} />
              <Tooltip formatter={(v: number) => [`${v}%`, "Importance"]} />
              <Bar dataKey="importance" fill="#2563eb" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* System status */}
      {!statsLoading && (
        <div className="rounded-xl border border-border bg-card p-5">
          <h2 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
            <Database className="h-4 w-4 text-primary" />System Status
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { label: "Database Connection", status: "Stable", ok: true },
              { label: "Risk Model Status", status: fiData ? "Active" : "Checking…", ok: !!fiData },
              { label: "Data Freshness", status: (stats as any)?.last_updated ? `Updated ${new Date((stats as any).last_updated).toLocaleTimeString()}` : "—", ok: true },
            ].map(({ label, status, ok }) => (
              <div key={label} className="flex items-center gap-2 p-3 rounded-lg bg-muted/30 border border-border/50">
                {ok ? <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" /> : <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0" />}
                <div>
                  <p className="text-xs font-medium text-foreground">{label}</p>
                  <p className="text-xs text-muted-foreground">{status}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
