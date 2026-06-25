import { useState } from "react";
import { useLocation, useParams, useNavigate, Link } from "react-router-dom";
import { format, parseISO, differenceInYears } from "date-fns";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import {
  ChevronRight, AlertTriangle, CheckCircle2, TrendingUp,
  FileText, History, Stethoscope, Brain, Info, Clock, PhoneCall, Cpu,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { RiskGauge } from "@/components/shared/RiskGauge";
import { usePatient } from "@/hooks/usePatients";
import { usePrediction } from "@/hooks/usePrediction";
import { FEATURE_LABELS } from "@/lib/constants";
import type { PredictionResponse, FeatureContribution, RiskClass, Priority } from "@/types/prediction.types";

// ── helpers ─────────────────────────────────────────────────────────────────

const RISK_PILL: Record<RiskClass, string> = {
  Low:      "text-emerald-700 bg-emerald-50 border-emerald-200",
  Moderate: "text-amber-700   bg-amber-50   border-amber-200",
  High:     "text-red-700     bg-red-50     border-red-200",
};

const RISK_ICON: Record<RiskClass, typeof CheckCircle2> = {
  Low:      CheckCircle2,
  Moderate: AlertTriangle,
  High:     AlertTriangle,
};

const PRIORITY_PILL: Record<Priority, string> = {
  Urgent: "text-red-700     bg-red-50     border-red-300",
  High:   "text-orange-700  bg-orange-50  border-orange-200",
  Medium: "text-amber-700   bg-amber-50   border-amber-200",
  Low:    "text-emerald-700 bg-emerald-50 border-emerald-200",
};

function featureLabel(name: string) {
  return FEATURE_LABELS[name] ?? name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

// ── Contribution chart (shared by SHAP + LIME) ────────────────────────────

function ContributionChart({ contributions, maxItems = 8 }: { contributions: FeatureContribution[]; maxItems?: number }) {
  const data = [...contributions]
    .sort((a, b) => b.importance_abs - a.importance_abs)
    .slice(0, maxItems)
    .map((c) => ({
      feature: featureLabel(c.feature_name),
      value: parseFloat(c.shap_value.toFixed(4)),
      direction: c.impact_direction,
      raw: c.value,
    }));

  if (!data.length) return <p className="text-sm text-muted-foreground py-8 text-center">No contribution data available.</p>;

  return (
    <ResponsiveContainer width="100%" height={Math.max(220, data.length * 40)}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 56, top: 4, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e5e7eb" />
        <XAxis
          type="number"
          tick={{ fontSize: 11 }}
          tickFormatter={(v: number) => v.toFixed(2)}
          domain={["auto", "auto"]}
        />
        <YAxis dataKey="feature" type="category" width={130} tick={{ fontSize: 12 }} />
        <Tooltip
          content={({ active, payload }) => {
            if (!active || !payload?.[0]) return null;
            const d = payload[0].payload as typeof data[0];
            return (
              <div className="bg-card border border-border rounded-lg px-3 py-2 shadow-lg text-xs space-y-1">
                <p className="font-semibold text-foreground">{d.feature}</p>
                <p className="text-muted-foreground">Patient value: <span className="text-foreground font-medium">{typeof d.raw === "boolean" ? (d.raw ? "Yes" : "No") : d.raw}</span></p>
                <p className={d.direction === "Positive" ? "text-red-600" : "text-emerald-600"}>
                  Contribution: {d.value > 0 ? "+" : ""}{d.value.toFixed(4)}
                </p>
              </div>
            );
          }}
        />
        <Bar dataKey="value" radius={[0, 4, 4, 0]} label={{ position: "right", fontSize: 10, formatter: (v: number) => (v > 0 ? `+${v.toFixed(3)}` : v.toFixed(3)) }}>
          {data.map((entry, i) => (
            <Cell key={i} fill={entry.direction === "Positive" ? "#ef4444" : "#10b981"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// ── Feature Importance chart ────────────────────────────────────────────────

function ImportanceChart({ importance, sorted }: { importance: Record<string, number>; sorted: string[] }) {
  const data = sorted.slice(0, 10).map((key) => ({
    feature: featureLabel(key),
    value: parseFloat((importance[key] ?? 0).toFixed(4)),
  }));

  if (!data.length) return <p className="text-sm text-muted-foreground py-8 text-center">No importance data available.</p>;

  return (
    <ResponsiveContainer width="100%" height={Math.max(220, data.length * 40)}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 56, top: 4, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e5e7eb" />
        <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={(v: number) => v.toFixed(2)} />
        <YAxis dataKey="feature" type="category" width={130} tick={{ fontSize: 12 }} />
        <Tooltip formatter={(v: number) => [v.toFixed(4), "Importance"]} />
        <Bar dataKey="value" radius={[0, 4, 4, 0]} fill="#2563eb"
          label={{ position: "right", fontSize: 10, formatter: (v: number) => v.toFixed(3) }} />
      </BarChart>
    </ResponsiveContainer>
  );
}

// ── Risk card ───────────────────────────────────────────────────────────────

function RiskCard({
  title, icon: Icon, riskClass, probability, label, detail,
}: {
  title: string;
  icon: typeof Stethoscope;
  riskClass: RiskClass;
  probability: number;
  label: string;
  detail: string;
}) {
  const RiskIcon = RISK_ICON[riskClass];
  return (
    <div className={cn(
      "rounded-xl border bg-card p-6 flex flex-col items-center gap-4 text-center shadow-sm",
      riskClass === "High" ? "border-red-200" : riskClass === "Moderate" ? "border-amber-200" : "border-emerald-200",
    )}>
      <div className={cn(
        "p-2.5 rounded-lg",
        riskClass === "High" ? "bg-red-50" : riskClass === "Moderate" ? "bg-amber-50" : "bg-emerald-50",
      )}>
        <Icon className={cn(
          "h-5 w-5",
          riskClass === "High" ? "text-red-600" : riskClass === "Moderate" ? "text-amber-600" : "text-emerald-600",
        )} />
      </div>
      <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">{title}</h3>
      <RiskGauge probability={probability} label={`${Math.round(probability * 100)}% Probability`} />
      <div className="space-y-1.5">
        <div className="flex items-center justify-center gap-1.5">
          <RiskIcon className={cn(
            "h-4 w-4",
            riskClass === "High" ? "text-red-600" : riskClass === "Moderate" ? "text-amber-600" : "text-emerald-600",
          )} />
          <span className={cn("px-3 py-1 rounded-full text-xs font-bold border uppercase tracking-wide", RISK_PILL[riskClass])}>
            {riskClass} Risk
          </span>
        </div>
        <p className="text-base font-semibold text-foreground">{label}</p>
        <p className="text-xs text-muted-foreground">{detail}</p>
      </div>
    </div>
  );
}

// ── Main page ───────────────────────────────────────────────────────────────

export default function PredictionResultsPage() {
  const { id: patientId = "" } = useParams<{ id: string }>();
  const { state } = useLocation();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("shap");

  const { data: patient } = usePatient(patientId);

  const predictionFromState = state?.prediction as PredictionResponse | undefined;
  const predictionIdFromState = predictionFromState?.prediction_id;

  const { data: fetchedPrediction, isLoading } = usePrediction(
    predictionIdFromState ? "" : "",
  );

  const prediction: PredictionResponse | undefined = predictionFromState ?? fetchedPrediction;

  const age = patient ? differenceInYears(new Date(), parseISO(patient.date_of_birth)) : null;

  if (isLoading && !prediction) {
    return (
      <div className="max-w-5xl mx-auto space-y-6">
        <Skeleton className="h-6 w-64" />
        <Skeleton className="h-20 w-full rounded-xl" />
        <div className="grid grid-cols-2 gap-5">
          <Skeleton className="h-64 rounded-xl" />
          <Skeleton className="h-64 rounded-xl" />
        </div>
        <Skeleton className="h-80 rounded-xl" />
      </div>
    );
  }

  if (!prediction) {
    return (
      <div className="max-w-5xl mx-auto flex flex-col items-center justify-center py-24 gap-4 text-center">
        <AlertTriangle className="h-12 w-12 text-muted-foreground" />
        <h2 className="text-lg font-semibold text-foreground">No prediction data found</h2>
        <p className="text-sm text-muted-foreground max-w-sm">
          This page requires a prediction result. Start a new screening to generate one.
        </p>
        <button
          onClick={() => navigate(`/patients/${patientId}/screening`)}
          className="mt-2 px-6 py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          Start Screening
        </button>
      </div>
    );
  }

  const { diabetes, obesity, shap_explanation, lime_explanation, global_feature_importance, recommendation, prediction_date, model_version } = prediction;

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-8">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-sm text-muted-foreground">
        <Link to="/patients" className="hover:text-foreground transition-colors">Patients</Link>
        <ChevronRight className="h-3.5 w-3.5" />
        <Link to={`/patients/${patientId}`} className="hover:text-foreground transition-colors">
          {patient?.full_name ?? "Patient"}
        </Link>
        <ChevronRight className="h-3.5 w-3.5" />
        <span className="text-foreground font-medium">Prediction Results</span>
      </nav>

      {/* Patient header bar */}
      <div className="rounded-xl border border-border bg-card px-5 py-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary/15 flex items-center justify-center text-primary font-bold text-sm">
            {patient?.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase() ?? "??"}
          </div>
          <div>
            <p className="text-sm font-semibold text-foreground">{patient?.full_name ?? "Patient"}</p>
            <p className="text-xs text-muted-foreground">#{patientId.slice(0, 8).toUpperCase()}</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-4 text-sm">
          {age && <span className="text-muted-foreground">Age: <strong className="text-foreground">{age}</strong></span>}
          {patient?.sex && <span className="text-muted-foreground">Sex: <strong className="text-foreground">{patient.sex}</strong></span>}
          {obesity?.bmi != null && (
            <span className="text-muted-foreground">BMI: <strong className="text-foreground">{obesity.bmi.toFixed(1)}</strong>
              <span className="ml-1 px-1.5 py-0.5 rounded text-xs bg-muted text-muted-foreground">{obesity.bmi_category}</span>
            </span>
          )}
          <span className="flex items-center gap-1 text-muted-foreground">
            <Clock className="h-3.5 w-3.5" />
            {format(parseISO(prediction_date), "MMM d, yyyy · HH:mm")}
          </span>
        </div>
        <span className="flex items-center gap-1.5 text-xs text-muted-foreground px-2.5 py-1 rounded-full border border-border bg-muted/30">
          <Cpu className="h-3 w-3" />
          Model v{model_version}
        </span>
      </div>

      {/* ── Risk Overview Cards ── */}
      <div>
        <h2 className="text-base font-semibold text-foreground mb-4">Risk Assessment Overview</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <RiskCard
            title="Diabetes Risk"
            icon={Stethoscope}
            riskClass={diabetes.risk_class}
            probability={diabetes.probability}
            label={diabetes.class_label}
            detail={`T2D risk classification based on metabolic biomarkers`}
          />
          <RiskCard
            title="Obesity Risk"
            icon={TrendingUp}
            riskClass={obesity.risk_class}
            probability={obesity.probability ?? (obesity.risk_class === "High" ? 0.75 : obesity.risk_class === "Moderate" ? 0.45 : 0.15)}
            label={obesity.obesity_class}
            detail={obesity?.bmi != null ? `BMI ${obesity.bmi.toFixed(1)} · ${obesity.bmi_category}` : obesity.bmi_category ?? "—"}
          />
        </div>
      </div>

      {/* ── AI Explanation Tabs ── */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="px-6 py-4 border-b border-border/50 bg-muted/20 flex items-center gap-2">
          <Brain className="h-4 w-4 text-primary" />
          <h2 className="text-sm font-semibold text-foreground">AI Explainability</h2>
          <div className="ml-auto flex items-center gap-1.5 text-xs text-muted-foreground">
            <div className="flex items-center gap-1"><div className="w-2.5 h-2.5 rounded-sm bg-red-400" /> Risk-increasing</div>
            <div className="flex items-center gap-1"><div className="w-2.5 h-2.5 rounded-sm bg-emerald-500" /> Risk-decreasing</div>
            <div className="ml-1 flex items-center gap-1"><div className="w-2.5 h-2.5 rounded-sm bg-blue-500" /> Feature weight</div>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <div className="px-6 pt-4">
            <TabsList className="bg-muted/40 h-9">
              <TabsTrigger value="shap" className="text-xs font-medium">SHAP</TabsTrigger>
              <TabsTrigger value="lime" className="text-xs font-medium">LIME</TabsTrigger>
              <TabsTrigger value="importance" className="text-xs font-medium">Feature Importance</TabsTrigger>
            </TabsList>
          </div>

          {/* SHAP */}
          <TabsContent value="shap" className="px-6 pb-6 pt-4 space-y-4">
            <div className="flex items-start gap-3 p-3 rounded-lg bg-blue-50 border border-blue-100">
              <Info className="h-4 w-4 text-blue-500 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-blue-700">
                <strong>SHAP</strong> (SHapley Additive exPlanations) shows how each feature pushed the prediction away from the baseline probability of{" "}
                <strong>{shap_explanation ? `${(shap_explanation.base_value * 100).toFixed(1)}%` : "—"}</strong>.
                Red bars increase risk; green bars decrease it.
              </p>
            </div>
            {shap_explanation ? (
              <>
                <ContributionChart contributions={shap_explanation.feature_contributions} />
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                  {shap_explanation.top_positive_features.length > 0 && (
                    <div className="rounded-lg border border-red-100 bg-red-50/50 p-4">
                      <p className="text-xs font-semibold text-red-700 mb-2 uppercase tracking-wide">Top Risk Factors</p>
                      <ul className="space-y-1.5">
                        {shap_explanation.top_positive_features.slice(0, 3).map((f) => (
                          <li key={f.feature_name} className="flex items-center justify-between text-xs">
                            <span className="text-foreground">{featureLabel(f.feature_name)}</span>
                            <span className="font-semibold text-red-600">+{f.shap_value.toFixed(4)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {shap_explanation.top_negative_features.length > 0 && (
                    <div className="rounded-lg border border-emerald-100 bg-emerald-50/50 p-4">
                      <p className="text-xs font-semibold text-emerald-700 mb-2 uppercase tracking-wide">Protective Factors</p>
                      <ul className="space-y-1.5">
                        {shap_explanation.top_negative_features.slice(0, 3).map((f) => (
                          <li key={f.feature_name} className="flex items-center justify-between text-xs">
                            <span className="text-foreground">{featureLabel(f.feature_name)}</span>
                            <span className="font-semibold text-emerald-600">{f.shap_value.toFixed(4)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <p className="text-sm text-muted-foreground py-8 text-center">SHAP explanation not available for this prediction.</p>
            )}
          </TabsContent>

          {/* LIME */}
          <TabsContent value="lime" className="px-6 pb-6 pt-4 space-y-4">
            <div className="flex items-start gap-3 p-3 rounded-lg bg-purple-50 border border-purple-100">
              <Info className="h-4 w-4 text-purple-500 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-purple-700">
                <strong>LIME</strong> (Local Interpretable Model-agnostic Explanations) approximates the model locally around this patient's data point to identify which features most influenced this specific prediction.
              </p>
            </div>
            {lime_explanation ? (
              <>
                <ContributionChart contributions={lime_explanation.feature_contributions} />
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                  {lime_explanation.top_positive_features.length > 0 && (
                    <div className="rounded-lg border border-red-100 bg-red-50/50 p-4">
                      <p className="text-xs font-semibold text-red-700 mb-2 uppercase tracking-wide">Top Risk Factors</p>
                      <ul className="space-y-1.5">
                        {lime_explanation.top_positive_features.slice(0, 3).map((f) => (
                          <li key={f.feature_name} className="flex items-center justify-between text-xs">
                            <span className="text-foreground">{featureLabel(f.feature_name)}</span>
                            <span className="font-semibold text-red-600">+{f.shap_value.toFixed(4)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {lime_explanation.top_negative_features.length > 0 && (
                    <div className="rounded-lg border border-emerald-100 bg-emerald-50/50 p-4">
                      <p className="text-xs font-semibold text-emerald-700 mb-2 uppercase tracking-wide">Protective Factors</p>
                      <ul className="space-y-1.5">
                        {lime_explanation.top_negative_features.slice(0, 3).map((f) => (
                          <li key={f.feature_name} className="flex items-center justify-between text-xs">
                            <span className="text-foreground">{featureLabel(f.feature_name)}</span>
                            <span className="font-semibold text-emerald-600">{f.shap_value.toFixed(4)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <p className="text-sm text-muted-foreground py-8 text-center">LIME explanation not available for this prediction.</p>
            )}
          </TabsContent>

          {/* Feature Importance */}
          <TabsContent value="importance" className="px-6 pb-6 pt-4 space-y-4">
            <div className="flex items-start gap-3 p-3 rounded-lg bg-blue-50 border border-blue-100">
              <Info className="h-4 w-4 text-blue-500 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-blue-700">
                <strong>Global Feature Importance</strong> reflects the overall contribution of each feature across the entire training dataset — not specific to this patient. Longer bars represent features the model relies on most.
                {global_feature_importance && (
                  <span className="ml-1">Model version: <strong>{global_feature_importance.model_version}</strong></span>
                )}
              </p>
            </div>
            {global_feature_importance ? (
              <ImportanceChart
                importance={global_feature_importance.feature_importance}
                sorted={global_feature_importance.sorted_features}
              />
            ) : (
              <p className="text-sm text-muted-foreground py-8 text-center">Feature importance data not available.</p>
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* ── Clinical Recommendation ── */}
      {recommendation && (
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          <div className="px-6 py-4 border-b border-border/50 bg-muted/20 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Stethoscope className="h-4 w-4 text-primary" />
              <h2 className="text-sm font-semibold text-foreground">Clinical Recommendation</h2>
            </div>
            <span className={cn("px-3 py-1 rounded-full text-xs font-bold border uppercase tracking-wide", PRIORITY_PILL[recommendation.priority])}>
              {recommendation.priority} Priority
            </span>
          </div>
          <div className="px-6 py-5 space-y-5">
            <p className="text-sm text-foreground leading-relaxed">{recommendation.action_text}</p>

            {recommendation.clinical_guidance && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {recommendation.clinical_guidance.diabetes_guidance && (
                  <div className="p-4 rounded-lg bg-muted/30 border border-border/50 space-y-1">
                    <p className="text-xs font-semibold text-foreground uppercase tracking-wide">Diabetes Guidance</p>
                    <p className="text-xs text-muted-foreground leading-relaxed">{recommendation.clinical_guidance.diabetes_guidance}</p>
                  </div>
                )}
                {recommendation.clinical_guidance.obesity_guidance && (
                  <div className="p-4 rounded-lg bg-muted/30 border border-border/50 space-y-1">
                    <p className="text-xs font-semibold text-foreground uppercase tracking-wide">Obesity Guidance</p>
                    <p className="text-xs text-muted-foreground leading-relaxed">{recommendation.clinical_guidance.obesity_guidance}</p>
                  </div>
                )}
              </div>
            )}

            <div className="flex flex-wrap gap-4 pt-1">
              {recommendation.follow_up_interval_days != null && (
                <div className="flex items-center gap-2 text-sm">
                  <div className="p-1.5 rounded bg-primary/10">
                    <Clock className="h-3.5 w-3.5 text-primary" />
                  </div>
                  <span className="text-muted-foreground">Follow-up in</span>
                  <strong className="text-foreground">{recommendation.follow_up_interval_days} days</strong>
                </div>
              )}
              {recommendation.referral_required && (
                <div className="flex items-center gap-2 text-sm">
                  <div className="p-1.5 rounded bg-amber-50">
                    <PhoneCall className="h-3.5 w-3.5 text-amber-600" />
                  </div>
                  <span className="text-muted-foreground">Referral:</span>
                  <strong className="text-foreground">{recommendation.referral_required}</strong>
                </div>
              )}
            </div>

            {recommendation.patient_advice && (
              <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
                <p className="text-xs font-semibold text-primary mb-1.5">Patient Advice</p>
                <p className="text-sm text-foreground">{recommendation.patient_advice}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Actions ── */}
      <div className="flex flex-wrap items-center gap-3 pt-2">
        <button
          onClick={() => navigate(`/patients/${patientId}`)}
          className="flex items-center gap-2 px-5 py-2.5 rounded-lg border border-border text-sm font-medium text-muted-foreground hover:text-foreground hover:border-foreground/30 transition-colors"
        >
          <History className="h-4 w-4" />
          Patient Profile
        </button>
        <button
          onClick={() => navigate(`/patients/${patientId}/screening`)}
          className="flex items-center gap-2 px-5 py-2.5 rounded-lg border border-primary text-primary text-sm font-medium hover:bg-primary/5 transition-colors"
        >
          New Screening
        </button>
        <Link
          to={`/patients/${patientId}/report`}
          state={{ prediction }}
          className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 shadow-sm transition-all"
        >
          <FileText className="h-4 w-4" />
          Generate Report
        </Link>
      </div>
    </div>
  );
}
