import { useState, useDeferredValue } from "react";
import { useNavigate } from "react-router-dom";
import { format, differenceInYears, parseISO } from "date-fns";
import { UserPlus, Search, Eye, Pencil, ListFilter, ChevronLeft, ChevronRight, Users } from "lucide-react";
import { usePatients } from "@/hooks/usePatients";
import { RegisterPatientDialog } from "@/components/shared/RegisterPatientDialog";
import { EmptyState } from "@/components/shared/EmptyState";
import { Skeleton } from "@/components/ui/skeleton";
import type { Patient } from "@/types/patient.types";
import { PAGE_SIZE } from "@/lib/constants";

function getAge(dob: string) {
  try { return differenceInYears(new Date(), parseISO(dob)); } catch { return "—"; }
}

function formatDate(dateStr?: string) {
  if (!dateStr) return "No visits";
  try { return format(parseISO(dateStr), "MMM d, yyyy"); } catch { return "—"; }
}

function initials(name: string) {
  return name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);
}

type StatusFilter = "" | "active" | "inactive";
type SexFilter = "" | "Male" | "Female";

export default function PatientManagementPage() {
  const navigate = useNavigate();
  const [registerOpen, setRegisterOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("");
  const [sexFilter, setSexFilter] = useState<SexFilter>("");
  const [page, setPage] = useState(1);

  const deferredSearch = useDeferredValue(search);

  const { data, isLoading, isError } = usePatients({
    name: deferredSearch || undefined,
    page,
    page_size: PAGE_SIZE,
  });

  const patients: Patient[] = (data?.items ?? []).filter((p) => {
    if (statusFilter === "active" && !p.is_active) return false;
    if (statusFilter === "inactive" && p.is_active) return false;
    if (sexFilter && p.sex !== sexFilter) return false;
    return true;
  });

  const totalPages = data?.pages ?? 1;
  const total = data?.total ?? 0;
  const start = (page - 1) * PAGE_SIZE + 1;
  const end = Math.min(page * PAGE_SIZE, total);

  return (
    <>
      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Patients</h1>
          <p className="text-sm text-muted-foreground mt-0.5">Manage and monitor patient clinical data</p>
        </div>
        <button
          onClick={() => setRegisterOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 transition-colors shadow-sm whitespace-nowrap"
        >
          <UserPlus className="h-4 w-4" />
          Register New Patient
        </button>
      </div>

      {/* Filter bar */}
      <div className="bg-card rounded-lg shadow-clinical border border-border/40 p-4 mb-5 flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-96">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/70" />
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search ID or Name…"
            className="w-full pl-9 pr-4 py-2 bg-background border border-border rounded-md text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          {/* Status */}
          <div className="relative">
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value as StatusFilter); setPage(1); }}
              className="appearance-none bg-background border border-border rounded-md pl-3 pr-7 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
            >
              <option value="">Status: All</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
            <ChevronRight className="absolute right-2 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground rotate-90 pointer-events-none" />
          </div>

          {/* Sex */}
          <div className="relative">
            <select
              value={sexFilter}
              onChange={(e) => { setSexFilter(e.target.value as SexFilter); setPage(1); }}
              className="appearance-none bg-background border border-border rounded-md pl-3 pr-7 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
            >
              <option value="">Sex: All</option>
              <option value="Male">Male</option>
              <option value="Female">Female</option>
            </select>
            <ChevronRight className="absolute right-2 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground rotate-90 pointer-events-none" />
          </div>

          <button
            onClick={() => { setSearch(""); setStatusFilter(""); setSexFilter(""); setPage(1); }}
            className="p-2 border border-border rounded-md text-muted-foreground hover:bg-muted transition-colors"
            title="Reset filters"
          >
            <ListFilter className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-card rounded-lg shadow-clinical border border-border/40 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-muted/60 border-b border-border/50">
                {["Patient ID", "Full Name", "Age", "Sex", "Last Visit", "Status", "Actions"].map((h) => (
                  <th
                    key={h}
                    className={`px-4 py-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider ${h === "Actions" ? "text-right" : ""}`}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="text-sm divide-y divide-border/30">
              {isLoading && (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 7 }).map((_, j) => (
                      <td key={j} className="px-4 py-3">
                        <Skeleton className="h-4 w-full" />
                      </td>
                    ))}
                  </tr>
                ))
              )}

              {!isLoading && isError && (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-sm text-muted-foreground">
                    Failed to load patients. Please check your connection.
                  </td>
                </tr>
              )}

              {!isLoading && !isError && patients.length === 0 && (
                <tr>
                  <td colSpan={7}>
                    <EmptyState
                      icon={Users}
                      title="No patients found"
                      description={search ? `No results for "${search}"` : "Register your first patient to get started."}
                      action={
                        <button
                          onClick={() => setRegisterOpen(true)}
                          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 transition-colors"
                        >
                          <UserPlus className="h-4 w-4" /> Register Patient
                        </button>
                      }
                    />
                  </td>
                </tr>
              )}

              {!isLoading && patients.map((patient, i) => (
                <PatientRow
                  key={patient.patient_id}
                  patient={patient}
                  striped={i % 2 === 0}
                  onView={() => navigate(`/patients/${patient.patient_id}`)}
                />
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {total > 0 && (
          <div className="px-4 py-3 border-t border-border/40 bg-card flex items-center justify-between">
            <span className="text-sm text-muted-foreground">
              Showing {start}–{end} of {total} results
            </span>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-1.5 rounded text-muted-foreground hover:bg-muted disabled:opacity-40 transition-colors"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>

              {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                const p = i + 1;
                return (
                  <button
                    key={p}
                    onClick={() => setPage(p)}
                    className={`w-8 h-8 rounded text-sm font-medium transition-colors ${
                      page === p
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:bg-muted"
                    }`}
                  >
                    {p}
                  </button>
                );
              })}

              {totalPages > 5 && <span className="text-muted-foreground px-1">…</span>}

              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-1.5 rounded text-muted-foreground hover:bg-muted disabled:opacity-40 transition-colors"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      <RegisterPatientDialog open={registerOpen} onClose={() => setRegisterOpen(false)} />
    </>
  );
}

function PatientRow({
  patient,
  striped,
  onView,
}: {
  patient: Patient;
  striped: boolean;
  onView: () => void;
}) {
  const navigate = useNavigate();

  return (
    <tr
      className={`group transition-colors hover:bg-accent/40 ${striped ? "bg-card" : "bg-background"}`}
      style={{ boxShadow: undefined }}
    >
      <td className="px-4 py-3 font-medium text-foreground">
        #{patient.patient_id.slice(0, 8).toUpperCase()}
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-accent text-primary flex items-center justify-center text-xs font-semibold shrink-0">
            {initials(patient.full_name)}
          </div>
          <span className="text-foreground font-medium">{patient.full_name}</span>
        </div>
      </td>
      <td className="px-4 py-3 text-muted-foreground">{getAge(patient.date_of_birth)}</td>
      <td className="px-4 py-3 text-muted-foreground">{patient.sex === "Male" ? "M" : "F"}</td>
      <td className="px-4 py-3 text-muted-foreground">
        {formatDate(patient.last_visit_date ?? patient.updated_at)}
      </td>
      <td className="px-4 py-3">
        {patient.is_active ? (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            Active
          </span>
        ) : (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-red-50 text-red-700 border border-red-200">
            Inactive
          </span>
        )}
      </td>
      <td className="px-4 py-3 text-right">
        <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={onView}
            title="View patient"
            className="p-1.5 text-primary hover:bg-accent rounded-md transition-colors"
          >
            <Eye className="h-4 w-4" />
          </button>
          <button
            onClick={() => navigate(`/patients/${patient.patient_id}`)}
            title="Edit patient"
            className="p-1.5 text-muted-foreground hover:bg-muted rounded-md transition-colors"
          >
            <Pencil className="h-4 w-4" />
          </button>
        </div>
      </td>
    </tr>
  );
}
