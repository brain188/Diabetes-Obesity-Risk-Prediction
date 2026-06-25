import { useState, useDeferredValue } from "react";
import { useNavigate } from "react-router-dom";
import { differenceInYears, parseISO } from "date-fns";
import { Search, Brain, Activity } from "lucide-react";
import { usePatients } from "@/hooks/usePatients";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/EmptyState";
import { PAGE_SIZE } from "@/lib/constants";
import type { Patient } from "@/types/patient.types";

function getAge(dob: string) {
  try { return differenceInYears(new Date(), parseISO(dob)); } catch { return "—"; }
}

function initials(name: string) {
  return name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);
}

export default function PredictionsListPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const deferredSearch = useDeferredValue(search);

  const { data, isLoading, isError } = usePatients({
    name: deferredSearch || undefined,
    page: 1,
    page_size: PAGE_SIZE,
  });

  const patients: Patient[] = data?.items ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">Predictions</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Select a patient to view their diabetes and obesity risk prediction history.
        </p>
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search patients…"
          className="w-full pl-9 pr-3 py-2 bg-card border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
        />
      </div>

      {/* Patient list */}
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full rounded-xl" />
          ))}
        </div>
      ) : isError ? (
        <EmptyState
          icon={Activity}
          title="Failed to load patients"
          description="Unable to fetch patient list. Please refresh the page."
        />
      ) : patients.length === 0 ? (
        <EmptyState
          icon={Brain}
          title="No patients found"
          description={search ? `No patients matching "${search}"` : "Register a patient to generate a prediction."}
        />
      ) : (
        <div className="space-y-2">
          {patients.map((patient) => (
            <div
              key={patient.patient_id}
              className="flex items-center justify-between p-4 bg-card border border-border rounded-xl hover:border-primary/40 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-accent flex items-center justify-center text-primary text-sm font-semibold shrink-0">
                  {initials(patient.full_name)}
                </div>
                <div>
                  <p className="text-sm font-medium text-foreground">{patient.full_name}</p>
                  <p className="text-xs text-muted-foreground">
                    {patient.sex} · Age {getAge(patient.date_of_birth)} · ID {patient.patient_id.slice(0, 8)}…
                  </p>
                </div>
              </div>
              <button
                onClick={() => navigate(`/patients/${patient.patient_id}`)}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-primary text-primary-foreground rounded-lg text-xs font-medium hover:bg-primary/90 transition-colors"
              >
                <Brain className="h-3.5 w-3.5" />
                View History
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
