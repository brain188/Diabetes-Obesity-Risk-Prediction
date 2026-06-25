import { useState, useDeferredValue } from "react";
import { useQuery } from "@tanstack/react-query";
import { format, parseISO } from "date-fns";
import {
  Search, Users, CheckCircle2, XCircle, ShieldCheck, UserRound,
  RefreshCw, Lock, Eye, Pencil, UserCog, Filter,
} from "lucide-react";
import { authService } from "@/services/auth.service";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/EmptyState";
import type { User } from "@/types/auth.types";

const ROLE_PERMISSIONS: Record<string, string[]> = {
  admin: [
    "View & manage all patients",
    "Run AI predictions",
    "Generate & download reports",
    "Access analytics dashboard",
    "Manage users & facilities",
    "View system logs & audit trail",
    "Configure system settings",
  ],
  healthcare_worker: [
    "View & manage assigned patients",
    "Run AI predictions",
    "Generate & download reports",
    "View own analytics",
  ],
};

function RoleBadge({ role }: { role: string }) {
  const isAdmin = role === "admin";
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${
      isAdmin
        ? "bg-purple-50 text-purple-700 border-purple-200"
        : "bg-sky-50 text-sky-700 border-sky-200"
    }`}>
      {isAdmin ? <ShieldCheck className="h-3 w-3" /> : <UserRound className="h-3 w-3" />}
      {isAdmin ? "Admin" : "Healthcare Worker"}
    </span>
  );
}

function StatusDot({ active }: { active: boolean }) {
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${active ? "text-emerald-600" : "text-slate-400"}`}>
      <span className={`w-2 h-2 rounded-full ${active ? "bg-emerald-500 animate-pulse" : "bg-slate-300"}`} />
      {active ? "Active" : "Inactive"}
    </span>
  );
}

function UserRow({ user }: { user: User }) {
  const initials = user.full_name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  return (
    <div className="flex items-center gap-4 p-4 hover:bg-muted/30 transition-colors border-b border-border/40 last:border-0">
      {/* Avatar */}
      <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary text-sm font-bold shrink-0">
        {initials}
      </div>

      {/* Name & Email */}
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold text-foreground truncate">{user.full_name}</p>
        <p className="text-xs text-muted-foreground truncate">{user.email}</p>
      </div>

      {/* Clinic */}
      <div className="hidden md:block w-36 shrink-0">
        <p className="text-xs font-medium text-foreground truncate">{user.clinic_name ?? "—"}</p>
        <p className="text-[10px] text-muted-foreground">Facility</p>
      </div>

      {/* Last login */}
      <div className="hidden lg:block w-32 shrink-0">
        {user.last_login_at ? (
          <>
            <p className="text-xs text-foreground">{format(parseISO(user.last_login_at), "MMM d, yyyy")}</p>
            <p className="text-[10px] text-muted-foreground">Last login</p>
          </>
        ) : (
          <p className="text-xs text-muted-foreground">Never logged in</p>
        )}
      </div>

      {/* Role */}
      <div className="shrink-0">
        <RoleBadge role={user.role} />
      </div>

      {/* Status */}
      <div className="shrink-0 w-20 text-right">
        <StatusDot active={user.is_active} />
      </div>
    </div>
  );
}

type RoleFilter = "all" | "admin" | "healthcare_worker";

export default function UserManagementPage() {
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState<RoleFilter>("all");
  const deferred = useDeferredValue(search);

  const { data: users = [], isLoading, isError, refetch, isFetching } = useQuery<User[]>({
    queryKey: ["admin", "users"],
    queryFn: authService.listUsers,
    retry: false,
  });

  const filtered = users.filter((u) => {
    if (roleFilter !== "all" && u.role !== roleFilter) return false;
    if (deferred) {
      const q = deferred.toLowerCase();
      if (
        !u.full_name.toLowerCase().includes(q) &&
        !u.email.toLowerCase().includes(q) &&
        !(u.clinic_name ?? "").toLowerCase().includes(q)
      ) return false;
    }
    return true;
  });

  const adminCount = users.filter((u) => u.role === "admin").length;
  const workerCount = users.filter((u) => u.role !== "admin").length;
  const activeCount = users.filter((u) => u.is_active).length;

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">User Management</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage healthcare workers and administrators across all facilities.
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

      {/* Summary tiles */}
      {!isLoading && !isError && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="rounded-xl border border-border bg-card px-4 py-3">
            <p className="text-2xl font-bold text-foreground">{users.length}</p>
            <p className="text-xs text-muted-foreground mt-0.5 flex items-center gap-1">
              <Users className="h-3 w-3" /> Total Users
            </p>
          </div>
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3">
            <p className="text-2xl font-bold text-emerald-700">{activeCount}</p>
            <p className="text-xs text-emerald-600 mt-0.5 flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3" /> Active
            </p>
          </div>
          <div className="rounded-xl border border-sky-200 bg-sky-50 px-4 py-3">
            <p className="text-2xl font-bold text-sky-700">{workerCount}</p>
            <p className="text-xs text-sky-600 mt-0.5 flex items-center gap-1">
              <UserRound className="h-3 w-3" /> Clinicians
            </p>
          </div>
          <div className="rounded-xl border border-purple-200 bg-purple-50 px-4 py-3">
            <p className="text-2xl font-bold text-purple-700">{adminCount}</p>
            <p className="text-xs text-purple-600 mt-0.5 flex items-center gap-1">
              <ShieldCheck className="h-3 w-3" /> Admins
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* User table */}
        <div className="lg:col-span-2 space-y-3">
          {/* Search & filter bar */}
          <div className="flex flex-wrap gap-3 items-center">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by name, email, clinic…"
                className="w-full pl-9 pr-3 py-2 bg-card border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>
            <div className="flex items-center gap-1.5">
              <Filter className="h-3.5 w-3.5 text-muted-foreground" />
              {(["all", "admin", "healthcare_worker"] as RoleFilter[]).map((r) => (
                <button
                  key={r}
                  onClick={() => setRoleFilter(r)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                    roleFilter === r
                      ? "bg-primary text-primary-foreground border-primary"
                      : "border-border text-muted-foreground hover:bg-muted"
                  }`}
                >
                  {r === "all" ? "All" : r === "admin" ? "Admins" : "Clinicians"}
                </button>
              ))}
            </div>
          </div>

          {/* Table */}
          <div className="rounded-xl border border-border bg-card overflow-hidden">
            {/* Table header */}
            <div className="hidden md:flex items-center gap-4 px-4 py-2 bg-muted/30 border-b border-border/50 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              <div className="w-10 shrink-0" />
              <div className="flex-1">Name</div>
              <div className="w-36 shrink-0">Facility</div>
              <div className="hidden lg:block w-32 shrink-0">Last Login</div>
              <div className="shrink-0">Role</div>
              <div className="w-20 shrink-0 text-right">Status</div>
            </div>

            {isLoading ? (
              <div className="p-4 space-y-2">
                {Array.from({ length: 6 }).map((_, i) => (
                  <Skeleton key={i} className="h-14 rounded-lg" />
                ))}
              </div>
            ) : isError ? (
              <div className="p-6">
                <EmptyState
                  icon={Users}
                  title="Unable to load users"
                  description="The users endpoint may require admin-level access."
                />
              </div>
            ) : filtered.length === 0 ? (
              <div className="p-6">
                <EmptyState
                  icon={Users}
                  title="No users found"
                  description={search ? `No results for "${search}"` : "No registered users yet."}
                />
              </div>
            ) : (
              <div>
                {filtered.map((u) => <UserRow key={u.worker_id} user={u} />)}
              </div>
            )}
          </div>

          {!isLoading && filtered.length > 0 && (
            <p className="text-xs text-muted-foreground text-right">
              Showing {filtered.length} of {users.length} users
            </p>
          )}
        </div>

        {/* Access Control Panel */}
        <div className="space-y-4">
          <div className="rounded-xl border border-border bg-card p-5">
            <h2 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
              <Lock className="h-4 w-4 text-primary" /> Access Control Policies
            </h2>
            <div className="space-y-3">
              {[
                { label: "Multi-Factor Auth", status: "Enforced", ok: true },
                { label: "Session Timeout", status: "8 hours", ok: true },
                { label: "Password Policy", status: "Min 8 chars", ok: true },
                { label: "Login Attempts", status: "5 max", ok: true },
              ].map(({ label, status, ok }) => (
                <div key={label} className="flex items-center justify-between py-2 border-b border-border/30 last:border-0">
                  <div className="flex items-center gap-2 text-xs text-foreground">
                    {ok
                      ? <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                      : <XCircle className="h-3.5 w-3.5 text-red-500 shrink-0" />}
                    {label}
                  </div>
                  <span className="text-xs font-medium text-muted-foreground">{status}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-xl border border-border bg-card p-5">
            <h2 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
              <UserCog className="h-4 w-4 text-primary" /> Role Permissions
            </h2>
            <div className="space-y-4">
              {(["admin", "healthcare_worker"] as const).map((role) => {
                const isAdmin = role === "admin";
                return (
                  <div key={role}>
                    <p className={`text-xs font-semibold mb-2 flex items-center gap-1 ${isAdmin ? "text-purple-700" : "text-sky-700"}`}>
                      {isAdmin ? <ShieldCheck className="h-3 w-3" /> : <UserRound className="h-3 w-3" />}
                      {isAdmin ? "Administrator" : "Healthcare Worker"}
                    </p>
                    <ul className="space-y-1">
                      {ROLE_PERMISSIONS[role].map((perm) => (
                        <li key={perm} className="flex items-start gap-1.5 text-[11px] text-muted-foreground">
                          <CheckCircle2 className={`h-3 w-3 shrink-0 mt-0.5 ${isAdmin ? "text-purple-400" : "text-sky-400"}`} />
                          {perm}
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Security Notice */}
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
            <div className="flex items-start gap-2">
              <ShieldCheck className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <p className="text-xs font-semibold text-amber-800">Security Notice</p>
                <p className="text-xs text-amber-700 mt-1">
                  Users with inactive accounts cannot access the system. Review and update access
                  regularly for compliance.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
