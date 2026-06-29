import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { differenceInYears, parseISO, format } from "date-fns";
import {
  ChevronRight, ClipboardPlus, Brain, FileText, Phone, CreditCard,
  Calendar, Activity, AlertTriangle, CheckCircle2, User, MapPin,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { usePatient, usePatientHistory } from "@/hooks/usePatients";
import { usePredictionHistory } from "@/hooks/usePrediction";
import { RISK_COLORS } from "@/lib/constants";
import type { RiskClass } from "@/types/prediction.types";

function getAge(dob: string) {
  try {
    const years = differenceInYears(new Date(), parseISO(dob));
    return isNaN(years) ? "—" : years;
  } catch { return "—"; }
}

function RiskBadge({ risk }: { risk: RiskClass }) {
  const Icon = risk === "Low" ? CheckCircle2 : AlertTriangle;
  return (
    <span className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold border", RISK_COLORS[risk])}>
      <Icon className="h-3 w-3" />{risk}
    </span>
  );
}

export default function PatientProfilePage() {
  const { id: patientId = "" } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [tab, setTab] = useState<"predictions" | "visits">("predictions");

  const { data: patient, isLoading } = usePatient(patientId);
  const { data: history } = usePatientHistory(patientId);
  const { data: predictions } = usePredictionHistory(patientId);

  const age = patient
    ? ((patient as any).age ?? getAge(patient.date_of_birth) ?? "—")
    : null;

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-8">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-sm text-muted-foreground">
        <Link to="/patients" className="hover:text-foreground transition-colors">Patients</Link>
        <ChevronRight className="h-3.5 w-3.5" />
        {isLoading
          ? <Skeleton className="h-4 w-28" />
          : <span className="text-foreground font-medium">{patient?.full_name ?? "Patient"}</span>
        }
      </nav>

      {/* Patient card */}
      {isLoading ? (
        <Skeleton className="h-36 w-full rounded-xl" />
      ) : patient ? (
        <div className="rounded-xl border border-border bg-card p-6">
          <div className="flex flex-col sm:flex-row sm:items-start gap-5">
            <div className="w-16 h-16 rounded-full bg-primary/15 flex items-center justify-center text-primary font-bold text-xl shrink-0">
              {patient.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-3 mb-1.5">
                <h1 className="text-xl font-bold text-foreground">{patient.full_name}</h1>
                <span className={cn(
                  "px-2 py-0.5 rounded-full text-xs font-medium border",
                  patient.is_active
                    ? "text-emerald-700 bg-emerald-50 border-emerald-200"
                    : "text-muted-foreground bg-muted border-border",
                )}>
                  {patient.is_active ? "Active" : "Inactive"}
                </span>
              </div>
              <div className="flex flex-wrap gap-x-5 gap-y-1.5 text-sm text-muted-foreground">
                <span className="flex items-center gap-1.5"><User className="h-3.5 w-3.5" />{patient.sex}, Age {age}</span>
                <span className="flex items-center gap-1.5"><Calendar className="h-3.5 w-3.5" />{format(parseISO(patient.date_of_birth), "MMMM d, yyyy")}</span>
                {patient.contact_info && (
                  <span className="flex items-center gap-1.5"><Phone className="h-3.5 w-3.5" />{patient.contact_info}</span>
                )}
                {patient.national_id && (
                  <span className="flex items-center gap-1.5"><CreditCard className="h-3.5 w-3.5" />{patient.national_id}</span>
                )}
                {patient.last_visit_date && (
                  <span className="flex items-center gap-1.5">
                    <Activity className="h-3.5 w-3.5" />
                    Last visit: {format(parseISO(patient.last_visit_date), "MMM d, yyyy")}
                  </span>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-1.5 font-mono">ID: {patient.patient_id}</p>
            </div>
            <div className="flex flex-wrap gap-2 shrink-0">
              <button
                onClick={() => navigate(`/patients/${patientId}/screening`)}
                className="flex items-center gap-1.5 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors shadow-sm"
              >
                <ClipboardPlus className="h-4 w-4" />New Screening
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="rounded-xl border border-border bg-card p-8 text-center">
          <p className="text-muted-foreground">Patient not found.</p>
          <Link to="/patients" className="mt-3 inline-block text-sm text-primary hover:underline">Back to patients</Link>
        </div>
      )}

      {/* Tab bar */}
      <div className="flex border-b border-border gap-1">
        {(["predictions", "visits"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={cn(
              "px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px",
              tab === t
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            {t === "predictions" ? "Prediction History" : "Screening Visits"}
          </button>
        ))}
      </div>

      {/* Prediction history */}
      {tab === "predictions" && (
        <div className="space-y-3">
          {!predictions || (predictions as any[]).length === 0 ? (
            <div className="rounded-xl border border-dashed border-border bg-muted/20 p-10 text-center">
              <Brain className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
              <p className="text-sm font-medium text-foreground">No predictions yet</p>
              <p className="text-xs text-muted-foreground mt-1">Run a screening to generate the first prediction.</p>
              <button
                onClick={() => navigate(`/patients/${patientId}/screening`)}
                className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
              >
                Start Screening
              </button>
            </div>
          ) : (
            (predictions as any[]).map((p: any) => (
              <div key={p.prediction_id} className="rounded-xl border border-border bg-card p-5 flex flex-wrap items-center gap-4">
                <div className="flex-1 min-w-0 space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs text-muted-foreground">
                      {p.prediction_date ? format(parseISO(p.prediction_date), "MMM d, yyyy · HH:mm") : "—"}
                    </span>
                    {p.model_version && <span className="text-xs bg-muted text-muted-foreground px-1.5 py-0.5 rounded">v{p.model_version}</span>}
                  </div>
                  <div className="flex flex-wrap gap-4">
                    <div className="flex items-center gap-1.5 text-sm">
                      <span className="text-muted-foreground">Diabetes:</span>
                      {p.diabetes?.risk_class ? <RiskBadge risk={p.diabetes.risk_class as RiskClass} /> : <span className="text-muted-foreground text-xs">—</span>}
                      {p.diabetes?.probability != null && (
                        <span className="text-xs text-muted-foreground">({Math.round(p.diabetes.probability * 100)}%)</span>
                      )}
                    </div>
                    <div className="flex items-center gap-1.5 text-sm">
                      <span className="text-muted-foreground">Obesity:</span>
                      {p.obesity?.risk_class ? <RiskBadge risk={p.obesity.risk_class as RiskClass} /> : <span className="text-muted-foreground text-xs">—</span>}
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Link
                    to={`/patients/${patientId}/prediction`}
                    state={{ prediction: p }}
                    className="flex items-center gap-1.5 px-3 py-1.5 border border-border rounded-lg text-xs font-medium text-foreground hover:bg-muted transition-colors"
                  >
                    <Brain className="h-3.5 w-3.5" />Results
                  </Link>
                  <button
                    onClick={() => navigate(`/patients/${patientId}/report`, { state: { prediction: p } })}
                    className="flex items-center gap-1.5 px-3 py-1.5 border border-border rounded-lg text-xs font-medium text-foreground hover:bg-muted transition-colors"
                  >
                    <FileText className="h-3.5 w-3.5" />Report
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Screening visits */}
      {tab === "visits" && (
        <div className="space-y-3">
          {!history || history.length === 0 ? (
            <div className="rounded-xl border border-dashed border-border bg-muted/20 p-10 text-center">
              <MapPin className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
              <p className="text-sm font-medium text-foreground">No screening visits yet</p>
              <p className="text-xs text-muted-foreground mt-1">Visit history will appear here after screenings.</p>
            </div>
          ) : (
            history.map((v) => (
              <div key={v.visit_id} className="rounded-xl border border-border bg-card p-5 flex flex-wrap items-center justify-between gap-4">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-foreground">
                    Visit — {format(parseISO(v.visit_date), "MMMM d, yyyy")}
                  </p>
                  {v.screening_data && (
                    <p className="text-xs text-muted-foreground">
                      BMI {v.screening_data.bmi?.toFixed(1)} · {v.screening_data.bmi_category}
                      {v.screening_data.has_hypertension && " · Hypertension"}
                      {v.screening_data.family_history_diabetes && " · Family Hx DM"}
                    </p>
                  )}
                  {v.notes && <p className="text-xs text-muted-foreground italic">"{v.notes}"</p>}
                </div>
                <span className="text-xs text-muted-foreground font-mono">{v.visit_id.slice(0, 8).toUpperCase()}</span>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
