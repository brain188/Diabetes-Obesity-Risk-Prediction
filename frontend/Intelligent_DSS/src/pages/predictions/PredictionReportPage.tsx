import { useParams, useLocation, useNavigate, Link } from "react-router-dom";
import { format, parseISO, differenceInYears } from "date-fns";
import { ChevronRight, Download, Loader2, FileText, AlertTriangle, CheckCircle2, Clock, Stethoscope } from "lucide-react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { usePatient } from "@/hooks/usePatients";
import { useGenerateReport, useDownloadReport } from "@/hooks/useReports";
import { RISK_COLORS } from "@/lib/constants";
import type { PredictionResponse, RiskClass } from "@/types/prediction.types";

function RiskBadge({ risk }: { risk: RiskClass }) {
  const Icon = risk === "Low" ? CheckCircle2 : AlertTriangle;
  return (
    <span className={cn("inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border", RISK_COLORS[risk])}>
      <Icon className="h-3.5 w-3.5" />{risk} Risk
    </span>
  );
}

export default function PredictionReportPage() {
  const { id: patientId = "" } = useParams<{ id: string }>();
  const { state } = useLocation();
  const navigate = useNavigate();

  const prediction = state?.prediction as PredictionResponse | undefined;
  const { data: patient, isLoading } = usePatient(patientId);
  const generate = useGenerateReport();
  const download = useDownloadReport();

  const age = patient ? differenceInYears(new Date(), parseISO(patient.date_of_birth)) : null;

  const handleGenerateAndDownload = async () => {
    if (!prediction?.visit_id) {
      toast.error("No visit ID available to generate a report.");
      return;
    }
    generate.mutate(prediction.visit_id, {
      onSuccess: (report) => {
        download.mutate(report.report_id, {
          onSuccess: () => toast.success("Report downloaded successfully."),
          onError: () => toast.error("Failed to download report."),
        });
      },
      onError: () => toast.error("Failed to generate report. Please try again."),
    });
  };

  const isBusy = generate.isPending || download.isPending;

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-8">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-sm text-muted-foreground">
        <Link to="/patients" className="hover:text-foreground transition-colors">Patients</Link>
        <ChevronRight className="h-3.5 w-3.5" />
        <Link to={`/patients/${patientId}`} className="hover:text-foreground transition-colors">
          {patient?.full_name ?? "Patient"}
        </Link>
        <ChevronRight className="h-3.5 w-3.5" />
        <span className="text-foreground font-medium">Clinical Report</span>
      </nav>

      {/* Report header card */}
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-lg bg-primary/10">
              <FileText className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-foreground">Clinical Prediction Report</h1>
              <p className="text-sm text-muted-foreground">Diabetes & Obesity Risk Assessment</p>
            </div>
          </div>
          <button
            onClick={handleGenerateAndDownload}
            disabled={isBusy || !prediction}
            className="flex items-center gap-2 px-5 py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 shadow-sm transition-all disabled:opacity-60"
          >
            {isBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
            {generate.isPending ? "Generating…" : download.isPending ? "Downloading…" : "Download PDF"}
          </button>
        </div>
      </div>

      {/* Patient info */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="px-6 py-4 border-b border-border/50 bg-muted/20">
          <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <Stethoscope className="h-4 w-4 text-primary" />Patient Information
          </h2>
        </div>
        <div className="px-6 py-5">
          {isLoading ? (
            <Skeleton className="h-16 w-full" />
          ) : patient ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
              <div><p className="text-muted-foreground text-xs mb-0.5">Full Name</p><p className="font-medium text-foreground">{patient.full_name}</p></div>
              <div><p className="text-muted-foreground text-xs mb-0.5">Date of Birth</p><p className="font-medium text-foreground">{format(parseISO(patient.date_of_birth), "MMMM d, yyyy")}</p></div>
              <div><p className="text-muted-foreground text-xs mb-0.5">Age / Sex</p><p className="font-medium text-foreground">{age} years · {patient.sex}</p></div>
              {patient.national_id && <div><p className="text-muted-foreground text-xs mb-0.5">National ID</p><p className="font-medium text-foreground">{patient.national_id}</p></div>}
              {patient.contact_info && <div><p className="text-muted-foreground text-xs mb-0.5">Contact</p><p className="font-medium text-foreground">{patient.contact_info}</p></div>}
              <div><p className="text-muted-foreground text-xs mb-0.5">Patient ID</p><p className="font-mono text-xs text-muted-foreground">{patient.patient_id}</p></div>
            </div>
          ) : null}
        </div>
      </div>

      {/* Prediction summary */}
      {prediction ? (
        <>
          <div className="rounded-xl border border-border bg-card overflow-hidden">
            <div className="px-6 py-4 border-b border-border/50 bg-muted/20 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-foreground">Risk Assessment Results</h2>
              <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Clock className="h-3.5 w-3.5" />
                {format(parseISO(prediction.prediction_date), "MMM d, yyyy · HH:mm")}
              </span>
            </div>
            <div className="px-6 py-5 grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div className="space-y-3">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Diabetes Risk</p>
                <RiskBadge risk={prediction.diabetes.risk_class} />
                <div className="space-y-1 text-sm">
                  <p><span className="text-muted-foreground">Classification: </span><strong>{prediction.diabetes.class_label}</strong></p>
                  <p><span className="text-muted-foreground">Probability: </span><strong>{Math.round(prediction.diabetes.probability * 100)}%</strong></p>
                </div>
              </div>
              <div className="space-y-3">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Obesity Risk</p>
                <RiskBadge risk={prediction.obesity.risk_class} />
                <div className="space-y-1 text-sm">
                  <p><span className="text-muted-foreground">BMI: </span><strong>{prediction.obesity?.bmi != null ? `${prediction.obesity.bmi.toFixed(1)} kg/m²` : "—"}</strong></p>
                  <p><span className="text-muted-foreground">Category: </span><strong>{prediction.obesity.bmi_category}</strong></p>
                  <p><span className="text-muted-foreground">Class: </span><strong>{prediction.obesity.obesity_class}</strong></p>
                </div>
              </div>
            </div>
          </div>

          {/* Recommendation */}
          {prediction.recommendation && (
            <div className="rounded-xl border border-border bg-card overflow-hidden">
              <div className="px-6 py-4 border-b border-border/50 bg-muted/20">
                <h2 className="text-sm font-semibold text-foreground">Clinical Recommendation</h2>
              </div>
              <div className="px-6 py-5 space-y-3">
                <p className="text-sm text-foreground leading-relaxed">{prediction.recommendation.action_text}</p>
                {prediction.recommendation.follow_up_interval_days != null && (
                  <p className="text-sm text-muted-foreground">
                    Follow-up recommended in <strong className="text-foreground">{prediction.recommendation.follow_up_interval_days} days</strong>.
                  </p>
                )}
                {prediction.recommendation.patient_advice && (
                  <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
                    <p className="text-xs font-semibold text-primary mb-1">Patient Advice</p>
                    <p className="text-sm text-foreground whitespace-pre-line">{prediction.recommendation.patient_advice}</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="rounded-xl border border-dashed border-border bg-muted/20 p-10 text-center">
          <FileText className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
          <p className="text-sm font-medium text-foreground">No prediction data</p>
          <p className="text-xs text-muted-foreground mt-1">Navigate here from the prediction results page to generate a report.</p>
          <button
            onClick={() => navigate(`/patients/${patientId}/screening`)}
            className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            Start Screening
          </button>
        </div>
      )}
    </div>
  );
}
