import { useMemo } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { differenceInYears, parseISO, format } from "date-fns";
import {
  Activity, AlertCircle, ChevronRight, Loader2,
  Scale, Ruler, HeartPulse, Home, ClipboardList,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Skeleton } from "@/components/ui/skeleton";
import { usePatient } from "@/hooks/usePatients";
import { usePredict } from "@/hooks/usePrediction";

const schema = z.object({
  weight: z
    .number({ invalid_type_error: "Enter a valid weight" })
    .min(20, "Minimum 20 kg")
    .max(300, "Maximum 300 kg"),
  height: z
    .number({ invalid_type_error: "Enter a valid height" })
    .min(1.0, "Minimum 1.0 m")
    .max(2.5, "Maximum 2.5 m"),
  physical_activity: z.boolean(),
  family_history_diabetes: z.boolean(),
  previous_gdm: z.boolean(),
  has_hypertension: z.boolean(),
  is_pregnant: z.boolean(),
  residence: z.enum(["Urban", "Rural"]),
  notes: z.string().max(1000).optional(),
});

type FormValues = z.infer<typeof schema>;

function calcBmi(weight: number, height: number) {
  if (!weight || !height || height <= 0) return null;
  return weight / (height * height);
}

function bmiCategory(bmi: number) {
  if (bmi < 18.5) return { label: "Underweight", color: "text-blue-600 bg-blue-50 border-blue-200" };
  if (bmi < 25)   return { label: "Normal Weight", color: "text-emerald-600 bg-emerald-50 border-emerald-200" };
  if (bmi < 30)   return { label: "Overweight", color: "text-amber-600 bg-amber-50 border-amber-200" };
  if (bmi < 35)   return { label: "Obese Class I", color: "text-orange-600 bg-orange-50 border-orange-200" };
  return              { label: "Obese Class II+", color: "text-red-600 bg-red-50 border-red-200" };
}

function ToggleField({
  id, label, description, checked, onChange, disabled,
}: {
  id: string; label: string; description?: string;
  checked: boolean; onChange: (v: boolean) => void; disabled?: boolean;
}) {
  return (
    <div className={cn(
      "flex items-center justify-between gap-4 p-4 rounded-lg border transition-colors",
      checked ? "border-primary/40 bg-primary/5" : "border-border bg-card",
      disabled && "opacity-40 cursor-not-allowed",
    )}>
      <div className="space-y-0.5">
        <Label htmlFor={id} className={cn("text-sm font-medium", disabled ? "cursor-not-allowed" : "cursor-pointer")}>
          {label}
        </Label>
        {description && <p className="text-xs text-muted-foreground">{description}</p>}
      </div>
      <Switch
        id={id}
        checked={checked}
        onCheckedChange={onChange}
        disabled={disabled}
        className="data-[state=checked]:bg-primary"
      />
    </div>
  );
}

export default function ScreeningDataEntryPage() {
  const { id: patientId = "" } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: patient, isLoading: patientLoading } = usePatient(patientId);
  const predict = usePredict();

  const age = patient ? differenceInYears(new Date(), parseISO(patient.date_of_birth)) : null;

  const {
    register,
    handleSubmit,
    control,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      physical_activity: false,
      family_history_diabetes: false,
      previous_gdm: false,
      has_hypertension: false,
      is_pregnant: false,
      residence: "Rural",
    },
  });

  const weight = watch("weight");
  const height = watch("height");
  const bmi = useMemo(() => calcBmi(Number(weight), Number(height)), [weight, height]);
  const bmiInfo = bmi ? bmiCategory(bmi) : null;

  const onSubmit = (data: FormValues) => {
    predict.mutate(
      {
        patient_id: patientId,
        screening_data: {
          weight: data.weight,
          height: data.height,
          physical_activity: data.physical_activity,
          family_history_diabetes: data.family_history_diabetes,
          previous_gdm: data.previous_gdm,
          has_hypertension: data.has_hypertension,
          is_pregnant: data.is_pregnant,
          residence: data.residence,
          notes: data.notes || undefined,
        },
      },
      {
        onSuccess: (prediction) => {
          toast.success("Prediction complete.");
          navigate(`/patients/${patientId}/prediction`, { state: { prediction } });
        },
        onError: () => toast.error("Prediction failed. Please check the data and try again."),
      },
    );
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-sm text-muted-foreground">
        <Link to="/patients" className="hover:text-foreground transition-colors">Patients</Link>
        <ChevronRight className="h-3.5 w-3.5" />
        {patientLoading ? (
          <Skeleton className="h-4 w-24" />
        ) : (
          <Link to={`/patients/${patientId}`} className="hover:text-foreground transition-colors">
            {patient?.full_name ?? "Patient"}
          </Link>
        )}
        <ChevronRight className="h-3.5 w-3.5" />
        <span className="text-foreground font-medium">Screening Data Entry</span>
      </nav>

      {/* Page title */}
      <div className="flex items-start gap-3">
        <div className="p-2.5 rounded-lg bg-primary/10">
          <ClipboardList className="h-5 w-5 text-primary" />
        </div>
        <div>
          <h1 className="text-xl font-semibold text-foreground">Clinical Screening Entry</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Enter clinical measurements to generate a T2D and obesity risk prediction.
          </p>
        </div>
      </div>

      {/* Patient context */}
      {patientLoading ? (
        <Skeleton className="h-20 w-full rounded-xl" />
      ) : patient ? (
        <div className="rounded-xl border border-border bg-card px-5 py-4 flex flex-wrap items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-primary/15 flex items-center justify-center text-primary font-bold text-sm">
              {patient.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()}
            </div>
            <div>
              <p className="text-sm font-semibold text-foreground">{patient.full_name}</p>
              <p className="text-xs text-muted-foreground">#{patient.patient_id.slice(0, 8).toUpperCase()}</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-5 text-sm">
            <span className="text-muted-foreground">Age: <strong className="text-foreground">{age ?? "—"}</strong></span>
            <span className="text-muted-foreground">Sex: <strong className="text-foreground">{patient.sex}</strong></span>
            {patient.last_visit_date && (
              <span className="text-muted-foreground">
                Last visit: <strong className="text-foreground">{format(parseISO(patient.last_visit_date), "MMM d, yyyy")}</strong>
              </span>
            )}
          </div>
        </div>
      ) : null}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        {/* ── Anthropometric Measurements ── */}
        <section className="rounded-xl border border-border bg-card overflow-hidden">
          <div className="px-6 py-4 border-b border-border/50 bg-muted/20 flex items-center gap-2">
            <Scale className="h-4 w-4 text-primary" />
            <h2 className="text-sm font-semibold text-foreground">Anthropometric Measurements</h2>
          </div>
          <div className="px-6 py-5 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-foreground">
                  Weight <span className="text-muted-foreground font-normal">(kg)</span>
                  <span className="text-destructive ml-0.5">*</span>
                </label>
                <input
                  {...register("weight", { valueAsNumber: true })}
                  type="number"
                  step="0.1"
                  placeholder="e.g. 72.5"
                  className="w-full px-4 py-2.5 rounded-lg bg-background border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                />
                {errors.weight && (
                  <p className="text-xs text-destructive flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />{errors.weight.message}
                  </p>
                )}
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-medium text-foreground">
                  Height <span className="text-muted-foreground font-normal">(m)</span>
                  <span className="text-destructive ml-0.5">*</span>
                </label>
                <input
                  {...register("height", { valueAsNumber: true })}
                  type="number"
                  step="0.01"
                  placeholder="e.g. 1.72"
                  className="w-full px-4 py-2.5 rounded-lg bg-background border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                />
                {errors.height && (
                  <p className="text-xs text-destructive flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />{errors.height.message}
                  </p>
                )}
              </div>
            </div>

            {bmi && bmiInfo && (
              <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/40 border border-border/50">
                <Ruler className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                <div className="flex items-center gap-3 text-sm">
                  <span className="text-muted-foreground">Calculated BMI:</span>
                  <strong className="text-foreground text-base">{bmi.toFixed(1)}</strong>
                  <span className={cn("px-2.5 py-0.5 rounded-full text-xs font-semibold border", bmiInfo.color)}>
                    {bmiInfo.label}
                  </span>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* ── Clinical Risk Factors ── */}
        <section className="rounded-xl border border-border bg-card overflow-hidden">
          <div className="px-6 py-4 border-b border-border/50 bg-muted/20 flex items-center gap-2">
            <HeartPulse className="h-4 w-4 text-primary" />
            <h2 className="text-sm font-semibold text-foreground">Clinical Risk Factors</h2>
          </div>
          <div className="px-6 py-5 space-y-3">
            <Controller
              control={control}
              name="family_history_diabetes"
              render={({ field }) => (
                <ToggleField
                  id="family_history_diabetes"
                  label="Family History of Diabetes"
                  description="First-degree relative (parent or sibling) diagnosed with T2D"
                  checked={field.value}
                  onChange={field.onChange}
                />
              )}
            />
            <Controller
              control={control}
              name="has_hypertension"
              render={({ field }) => (
                <ToggleField
                  id="has_hypertension"
                  label="Has Hypertension"
                  description="Currently diagnosed or under treatment for high blood pressure"
                  checked={field.value}
                  onChange={field.onChange}
                />
              )}
            />
            <Controller
              control={control}
              name="is_pregnant"
              render={({ field }) => (
                <ToggleField
                  id="is_pregnant"
                  label="Currently Pregnant"
                  description="Patient is currently pregnant"
                  checked={field.value}
                  onChange={field.onChange}
                />
              )}
            />
            <Controller
              control={control}
              name="previous_gdm"
              render={({ field }) => (
                <ToggleField
                  id="previous_gdm"
                  label="Previous Gestational Diabetes (GDM)"
                  description="History of gestational diabetes in a prior pregnancy"
                  checked={field.value}
                  onChange={field.onChange}
                />
              )}
            />
          </div>
        </section>

        {/* ── Lifestyle Factors ── */}
        <section className="rounded-xl border border-border bg-card overflow-hidden">
          <div className="px-6 py-4 border-b border-border/50 bg-muted/20 flex items-center gap-2">
            <Activity className="h-4 w-4 text-primary" />
            <h2 className="text-sm font-semibold text-foreground">Lifestyle Factors</h2>
          </div>
          <div className="px-6 py-5 space-y-5">
            <Controller
              control={control}
              name="physical_activity"
              render={({ field }) => (
                <ToggleField
                  id="physical_activity"
                  label="Physically Active"
                  description="Engages in at least 150 minutes of moderate activity per week"
                  checked={field.value}
                  onChange={field.onChange}
                />
              )}
            />

            <div className="space-y-2.5">
              <label className="text-sm font-medium text-foreground flex items-center gap-2">
                <Home className="h-4 w-4 text-muted-foreground" />
                Residence Type
                <span className="text-destructive ml-0.5">*</span>
              </label>
              <Controller
                control={control}
                name="residence"
                render={({ field }) => (
                  <RadioGroup
                    value={field.value}
                    onValueChange={field.onChange}
                    className="flex gap-3"
                  >
                    {(["Urban", "Rural"] as const).map((v) => (
                      <label
                        key={v}
                        htmlFor={`residence-${v}`}
                        className={cn(
                          "flex items-center gap-2.5 px-5 py-3 rounded-lg border cursor-pointer transition-all text-sm font-medium flex-1 justify-center",
                          field.value === v
                            ? "border-primary bg-primary/5 text-primary"
                            : "border-border bg-card text-muted-foreground hover:border-primary/40",
                        )}
                      >
                        <RadioGroupItem value={v} id={`residence-${v}`} className="sr-only" />
                        {v === "Urban" ? "🏙" : "🌾"} {v}
                      </label>
                    ))}
                  </RadioGroup>
                )}
              />
            </div>
          </div>
        </section>

        {/* ── Clinical Notes ── */}
        <section className="rounded-xl border border-border bg-card overflow-hidden">
          <div className="px-6 py-4 border-b border-border/50 bg-muted/20">
            <h2 className="text-sm font-semibold text-foreground">Clinical Notes <span className="text-muted-foreground font-normal">(optional)</span></h2>
          </div>
          <div className="px-6 py-5">
            <textarea
              {...register("notes")}
              rows={3}
              placeholder="e.g. Patient reports increased thirst and fatigue over the past 2 weeks..."
              className="w-full px-4 py-3 rounded-lg bg-background border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all resize-none"
            />
          </div>
        </section>

        {/* ── Actions ── */}
        <div className="flex items-center justify-between pt-2 pb-6">
          <button
            type="button"
            onClick={() => navigate(`/patients/${patientId}`)}
            className="px-6 py-2.5 rounded-lg border border-border text-sm font-medium text-muted-foreground hover:text-foreground hover:border-foreground/30 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={predict.isPending}
            className="flex items-center gap-2 px-8 py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary/90 shadow-sm transition-all active:scale-95 disabled:opacity-60"
          >
            {predict.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Running Prediction…
              </>
            ) : (
              <>
                <Activity className="h-4 w-4" />
                Save &amp; Run Prediction
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
