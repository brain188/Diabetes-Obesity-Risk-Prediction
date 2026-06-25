import { useQuery } from "@tanstack/react-query";
import {
  Building2, MapPin, Users, Activity, CheckCircle2,
  UserCog, RefreshCw, TrendingUp, Layers,
} from "lucide-react";
import { authService } from "@/services/auth.service";
import { useDashboardStats } from "@/hooks/useAnalytics";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/EmptyState";
import type { User } from "@/types/auth.types";

interface FacilityStats {
  name: string;
  workerCount: number;
  activeWorkers: number;
  adminCount: number;
  workerCount_healthcare: number;
}

const DEPT_COLORS = [
  "from-sky-50 to-sky-100/50 border-sky-200",
  "from-purple-50 to-purple-100/50 border-purple-200",
  "from-emerald-50 to-emerald-100/50 border-emerald-200",
  "from-amber-50 to-amber-100/50 border-amber-200",
  "from-rose-50 to-rose-100/50 border-rose-200",
  "from-indigo-50 to-indigo-100/50 border-indigo-200",
];

const DEPT_ICON_COLORS = [
  "bg-sky-100 text-sky-600",
  "bg-purple-100 text-purple-600",
  "bg-emerald-100 text-emerald-600",
  "bg-amber-100 text-amber-600",
  "bg-rose-100 text-rose-600",
  "bg-indigo-100 text-indigo-600",
];

function buildFacilityStats(users: User[]): FacilityStats[] {
  const map = new Map<string, FacilityStats>();
  for (const u of users) {
    const name = u.clinic_name ?? "Unassigned Unit";
    if (!map.has(name)) {
      map.set(name, { name, workerCount: 0, activeWorkers: 0, adminCount: 0, workerCount_healthcare: 0 });
    }
    const f = map.get(name)!;
    f.workerCount++;
    if (u.is_active) f.activeWorkers++;
    if (u.role === "admin") f.adminCount++;
    else f.workerCount_healthcare++;
  }
  return Array.from(map.values()).sort((a, b) => b.workerCount - a.workerCount);
}

function FacilityCard({ facility, index }: { facility: FacilityStats; index: number }) {
  const colorGrad = DEPT_COLORS[index % DEPT_COLORS.length];
  const iconColor = DEPT_ICON_COLORS[index % DEPT_ICON_COLORS.length];
  const activeRate = facility.workerCount > 0
    ? Math.round((facility.activeWorkers / facility.workerCount) * 100)
    : 0;

  return (
    <div className={`rounded-xl border bg-gradient-to-br ${colorGrad} p-5 hover:shadow-md transition-all`}>
      <div className="flex items-start gap-3 mb-4">
        <div className={`p-2.5 rounded-lg shrink-0 ${iconColor}`}>
          <Building2 className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-semibold text-foreground truncate">{facility.name}</h3>
          <p className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
            <MapPin className="h-3 w-3 shrink-0" /> Clinical Facility Node
          </p>
        </div>
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
          facility.activeWorkers > 0
            ? "bg-emerald-100 text-emerald-700 border-emerald-200"
            : "bg-slate-100 text-slate-500 border-slate-200"
        }`}>
          <span className={`w-1.5 h-1.5 rounded-full ${facility.activeWorkers > 0 ? "bg-emerald-500" : "bg-slate-400"}`} />
          {facility.activeWorkers > 0 ? "Active" : "Inactive"}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-2 mb-4">
        <div className="rounded-lg bg-white/70 border border-white/80 py-2.5 text-center">
          <p className="text-lg font-bold text-foreground">{facility.workerCount}</p>
          <p className="text-[10px] text-muted-foreground">Total Staff</p>
        </div>
        <div className="rounded-lg bg-white/70 border border-white/80 py-2.5 text-center">
          <p className="text-lg font-bold text-emerald-700">{facility.activeWorkers}</p>
          <p className="text-[10px] text-muted-foreground">Active</p>
        </div>
        <div className="rounded-lg bg-white/70 border border-white/80 py-2.5 text-center">
          <p className="text-lg font-bold text-purple-700">{facility.adminCount}</p>
          <p className="text-[10px] text-muted-foreground">Admins</p>
        </div>
      </div>

      {/* Utilisation bar */}
      <div>
        <div className="flex justify-between text-[10px] text-muted-foreground mb-1">
          <span>Staff active rate</span>
          <span className="font-semibold">{activeRate}%</span>
        </div>
        <div className="h-1.5 rounded-full bg-white/60 overflow-hidden">
          <div
            className="h-full rounded-full bg-emerald-500 transition-all"
            style={{ width: `${activeRate}%` }}
          />
        </div>
      </div>
    </div>
  );
}

export default function FacilityManagementPage() {
  const { data: users = [], isLoading, isError, refetch, isFetching } = useQuery<User[]>({
    queryKey: ["admin", "users"],
    queryFn: authService.listUsers,
    retry: false,
  });

  const { data: stats } = useDashboardStats();

  const facilities = buildFacilityStats(users);
  const totalActive = users.filter((u) => u.is_active).length;
  const totalAdmins = users.filter((u) => u.role === "admin").length;

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Facility Management</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Overview of registered clinical nodes, departments, and staffing.
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

      {/* Summary stat strip */}
      {!isLoading && !isError && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="rounded-xl border border-border bg-card px-4 py-3 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-50"><Layers className="h-4 w-4 text-blue-600" /></div>
            <div>
              <p className="text-xl font-bold text-foreground">{facilities.length}</p>
              <p className="text-xs text-muted-foreground">Facility Nodes</p>
            </div>
          </div>
          <div className="rounded-xl border border-border bg-card px-4 py-3 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-50"><Users className="h-4 w-4 text-purple-600" /></div>
            <div>
              <p className="text-xl font-bold text-foreground">{users.length}</p>
              <p className="text-xs text-muted-foreground">Total Staff</p>
            </div>
          </div>
          <div className="rounded-xl border border-border bg-card px-4 py-3 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emerald-50"><Activity className="h-4 w-4 text-emerald-600" /></div>
            <div>
              <p className="text-xl font-bold text-emerald-700">{totalActive}</p>
              <p className="text-xs text-muted-foreground">Active Users</p>
            </div>
          </div>
          <div className="rounded-xl border border-border bg-card px-4 py-3 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-amber-50"><TrendingUp className="h-4 w-4 text-amber-600" /></div>
            <div>
              <p className="text-xl font-bold text-foreground">{stats?.total_screenings ?? 0}</p>
              <p className="text-xs text-muted-foreground">Total Screenings</p>
            </div>
          </div>
        </div>
      )}

      {/* Facility cards */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-52 rounded-xl" />)}
        </div>
      ) : isError ? (
        <EmptyState
          icon={Building2}
          title="Unable to load facilities"
          description="Facility data is derived from user accounts. Ensure the users endpoint is accessible."
        />
      ) : facilities.length === 0 ? (
        <EmptyState
          icon={Building2}
          title="No facilities found"
          description="Facilities appear automatically once users register with a clinic name."
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {facilities.map((f, i) => (
            <FacilityCard key={f.name} facility={f} index={i} />
          ))}
        </div>
      )}

      {/* Access Summary */}
      {!isLoading && !isError && users.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-5">
          <h2 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
            <UserCog className="h-4 w-4 text-primary" />
            Access & Role Distribution
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              {
                label: "Healthcare Workers",
                count: users.filter((u) => u.role !== "admin").length,
                color: "bg-sky-50 border-sky-200 text-sky-700",
                sub: "Clinical access only",
              },
              {
                label: "Administrators",
                count: totalAdmins,
                color: "bg-purple-50 border-purple-200 text-purple-700",
                sub: "Full system access",
              },
              {
                label: "Inactive Accounts",
                count: users.filter((u) => !u.is_active).length,
                color: "bg-slate-50 border-slate-200 text-slate-600",
                sub: "Pending activation",
              },
            ].map(({ label, count, color, sub }) => (
              <div key={label} className={`rounded-lg border px-4 py-3 ${color}`}>
                <p className="text-2xl font-bold">{count}</p>
                <p className="text-sm font-medium mt-0.5">{label}</p>
                <p className="text-xs opacity-70 mt-0.5">{sub}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
