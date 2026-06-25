import { useState } from "react";
import { Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Building2, Badge, Eye, EyeOff, Loader2, Check } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { AuthLayout } from "@/components/layout/AuthLayout";
import { useRegister } from "@/hooks/useAuth";

const schema = z
  .object({
    // Step 1 — Facility
    facility_name: z.string().min(2, "Facility name is required"),
    facility_type: z.string().min(1, "Select a facility type"),
    facility_address: z.string().min(5, "Full address is required"),
    license_number: z.string().min(2, "License / accreditation ID is required"),
    // Step 2 — Admin
    full_name: z.string().min(2, "Full name is required"),
    title: z.string().min(2, "Professional title is required"),
    email: z.string().email("Enter a valid email address"),
    department: z.string().min(2, "Department is required"),
    // Step 3 — Security
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[A-Z]/, "Must contain at least one uppercase letter")
      .regex(/[0-9]/, "Must contain at least one number"),
    confirm_password: z.string(),
    terms: z.literal(true, { errorMap: () => ({ message: "You must accept the Terms of Service" }) }),
    hipaa: z.literal(true, { errorMap: () => ({ message: "HIPAA certification is required" }) }),
  })
  .refine((d) => d.password === d.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

type FormValues = z.infer<typeof schema>;

const STEP_FIELDS: Record<number, Array<keyof FormValues>> = {
  1: ["facility_name", "facility_type", "facility_address", "license_number"],
  2: ["full_name", "title", "email", "department"],
  3: ["password", "confirm_password", "terms", "hipaa"],
};

const STEP_LABELS = ["Facility Info", "Admin Details", "Security"];

function passwordStrength(p: string) {
  let s = 0;
  if (p.length > 5) s++;
  if (p.length > 8) s++;
  if (/[A-Z]/.test(p)) s++;
  if (/[0-9!@#$%^&*]/.test(p)) s++;
  const labels = ["", "Weak", "Fair", "Good", "Strong"];
  const colors = ["", "bg-destructive", "bg-amber-500", "bg-emerald-500", "bg-primary"];
  const textColors = ["", "text-destructive", "text-amber-600", "text-emerald-600", "text-primary"];
  return { score: s, label: labels[s] || "Weak", barColor: colors[s] || colors[1], textColor: textColors[s] || textColors[1] };
}

export default function RegisterPage() {
  const [step, setStep] = useState(1);
  const [showPw, setShowPw] = useState(false);
  const register = useRegister();

  const {
    register: field,
    handleSubmit,
    trigger,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    mode: "onTouched",
    defaultValues: {
      facility_type: "General Hospital",
      terms: false as unknown as true,
      hipaa: false as unknown as true,
    },
  });

  const pwValue = watch("password") ?? "";
  const strength = passwordStrength(pwValue);

  async function goNext() {
    const valid = await trigger(STEP_FIELDS[step]);
    if (valid) setStep((s) => s + 1);
  }

  const onSubmit = (data: FormValues) => {
    register.mutate(
      {
        email: data.email,
        password: data.password,
        full_name: data.full_name,
        clinic_name: data.facility_name,
      },
      { onError: () => toast.error("Registration failed. Please try again.") },
    );
  };

  return (
    <AuthLayout>
      <div className="w-full max-w-2xl">
        {/* Stepper */}
        <div className="mb-8 px-2">
          <div className="relative flex justify-between items-center">
            {/* Background track */}
            <div className="absolute top-5 left-0 w-full h-0.5 bg-border" />
            {/* Active track */}
            <div
              className="absolute top-5 left-0 h-0.5 bg-primary transition-all duration-500"
              style={{ width: `${((step - 1) / 2) * 100}%` }}
            />
            {STEP_LABELS.map((label, i) => {
              const n = i + 1;
              const done = n < step;
              const active = n === step;
              return (
                <div key={label} className="relative z-10 flex flex-col items-center gap-2">
                  <div
                    className={cn(
                      "w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm shadow-sm border-2 transition-all duration-300",
                      done && "bg-emerald-500 border-emerald-500 text-white",
                      active && "bg-primary border-primary text-primary-foreground shadow-md",
                      !done && !active && "bg-card border-border text-muted-foreground",
                    )}
                  >
                    {done ? <Check className="h-4 w-4" /> : n}
                  </div>
                  <span
                    className={cn(
                      "text-xs font-semibold whitespace-nowrap",
                      active ? "text-primary" : done ? "text-emerald-600" : "text-muted-foreground",
                    )}
                  >
                    {label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Card */}
        <div className="glass-card rounded-xl border border-border/50 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-primary" />

          <form onSubmit={handleSubmit(onSubmit)} className="px-8 py-8 space-y-6">
            {/* ─── Step 1: Facility Info ─── */}
            {step === 1 && (
              <div className="space-y-5">
                <div>
                  <h2 className="text-2xl font-semibold text-foreground">Facility Information</h2>
                  <p className="text-sm text-muted-foreground mt-1">Establish your clinical environment on the DSS network.</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-foreground">Facility Name</label>
                    <input
                      {...field("facility_name")}
                      placeholder="e.g. St. Jude Regional Hospital"
                      className="w-full px-4 py-2.5 rounded-lg bg-card border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                    />
                    {errors.facility_name && <p className="text-xs text-destructive">{errors.facility_name.message}</p>}
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-foreground">Facility Type</label>
                    <select
                      {...field("facility_type")}
                      className="w-full px-4 py-2.5 rounded-lg bg-card border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                    >
                      <option>General Hospital</option>
                      <option>Specialized Clinic</option>
                      <option>Research Unit</option>
                      <option>Public Health Agency</option>
                    </select>
                  </div>
                  <div className="md:col-span-2 space-y-1.5">
                    <label className="text-sm font-medium text-foreground">Full Address</label>
                    <input
                      {...field("facility_address")}
                      placeholder="123 Clinical Plaza, Sector 4, Cambridge, MA"
                      className="w-full px-4 py-2.5 rounded-lg bg-card border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                    />
                    {errors.facility_address && <p className="text-xs text-destructive">{errors.facility_address.message}</p>}
                  </div>
                  <div className="md:col-span-2 space-y-1.5">
                    <label className="text-sm font-medium text-foreground">License Number / Accreditation ID</label>
                    <div className="relative">
                      <Badge className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <input
                        {...field("license_number")}
                        placeholder="MD-8829-DSS"
                        className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-card border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                      />
                    </div>
                    {errors.license_number && <p className="text-xs text-destructive">{errors.license_number.message}</p>}
                  </div>
                </div>
              </div>
            )}

            {/* ─── Step 2: Admin Details ─── */}
            {step === 2 && (
              <div className="space-y-5">
                <div>
                  <h2 className="text-2xl font-semibold text-foreground">Administrator Details</h2>
                  <p className="text-sm text-muted-foreground mt-1">The primary contact responsible for clinical decision-making protocols.</p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-foreground">Full Name</label>
                    <input
                      {...field("full_name")}
                      placeholder="Dr. Sarah Chen"
                      className="w-full px-4 py-2.5 rounded-lg bg-card border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                    />
                    {errors.full_name && <p className="text-xs text-destructive">{errors.full_name.message}</p>}
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-foreground">Professional Title</label>
                    <input
                      {...field("title")}
                      placeholder="Chief Medical Officer"
                      className="w-full px-4 py-2.5 rounded-lg bg-card border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                    />
                    {errors.title && <p className="text-xs text-destructive">{errors.title.message}</p>}
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-foreground">Work Email</label>
                    <input
                      {...field("email")}
                      type="email"
                      placeholder="sarah.chen@facility.org"
                      className="w-full px-4 py-2.5 rounded-lg bg-card border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                    />
                    {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-foreground">Department Affiliation</label>
                    <input
                      {...field("department")}
                      placeholder="Endocrinology & Metabolic Health"
                      className="w-full px-4 py-2.5 rounded-lg bg-card border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                    />
                    {errors.department && <p className="text-xs text-destructive">{errors.department.message}</p>}
                  </div>
                </div>
              </div>
            )}

            {/* ─── Step 3: Security ─── */}
            {step === 3 && (
              <div className="space-y-5">
                <div>
                  <h2 className="text-2xl font-semibold text-foreground">Security & Verification</h2>
                  <p className="text-sm text-muted-foreground mt-1">Protect sensitive patient data with enterprise-grade encryption.</p>
                </div>
                <div className="space-y-5">
                  {/* Password */}
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-foreground">Admin Password</label>
                    <div className="relative">
                      <input
                        {...field("password")}
                        type={showPw ? "text" : "password"}
                        placeholder="••••••••"
                        className="w-full px-4 pr-10 py-2.5 rounded-lg bg-card border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPw((v) => !v)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                      >
                        {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                    {/* Strength meter */}
                    {pwValue && (
                      <div className="mt-2 space-y-1">
                        <div className="flex gap-1">
                          {[1, 2, 3, 4].map((i) => (
                            <div
                              key={i}
                              className={cn(
                                "h-1.5 flex-1 rounded-full transition-all duration-300",
                                i <= strength.score ? strength.barColor : "bg-border",
                              )}
                            />
                          ))}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          Security Strength:{" "}
                          <span className={cn("font-semibold", strength.textColor)}>{strength.label}</span>
                        </p>
                      </div>
                    )}
                    {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
                  </div>

                  {/* Confirm password */}
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium text-foreground">Confirm Password</label>
                    <input
                      {...field("confirm_password")}
                      type={showPw ? "text" : "password"}
                      placeholder="••••••••"
                      className="w-full px-4 py-2.5 rounded-lg bg-card border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                    />
                    {errors.confirm_password && <p className="text-xs text-destructive">{errors.confirm_password.message}</p>}
                  </div>

                  {/* Checkboxes */}
                  <div className="space-y-3 pt-2">
                    <label className="flex items-start gap-3 cursor-pointer group">
                      <input
                        {...field("terms")}
                        type="checkbox"
                        className="mt-0.5 h-4 w-4 rounded border-border text-primary focus:ring-primary/30 focus:ring-2"
                      />
                      <span className="text-sm text-muted-foreground group-hover:text-foreground transition-colors leading-relaxed">
                        I agree to the{" "}
                        <a href="#" className="text-primary underline underline-offset-2">Terms of Service</a>
                        {" "}and acknowledge the clinical liability frameworks of the Intelligent DSS.
                      </span>
                    </label>
                    {errors.terms && <p className="text-xs text-destructive">{errors.terms.message}</p>}

                    <label className="flex items-start gap-3 cursor-pointer group">
                      <input
                        {...field("hipaa")}
                        type="checkbox"
                        className="mt-0.5 h-4 w-4 rounded border-border text-primary focus:ring-primary/30 focus:ring-2"
                      />
                      <span className="text-sm text-muted-foreground group-hover:text-foreground transition-colors leading-relaxed">
                        I certify that our facility maintains full{" "}
                        <strong className="text-primary">HIPAA Compliance</strong>{" "}
                        and data protection standards for electronic health records.
                      </span>
                    </label>
                    {errors.hipaa && <p className="text-xs text-destructive">{errors.hipaa.message}</p>}
                  </div>

                  {/* Facility info icon */}
                  <div className="flex items-center gap-2 pt-1">
                    <Building2 className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                    <p className="text-xs text-muted-foreground">
                      Facility data and admin credentials are encrypted in transit using AES-256 standards.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Navigation */}
            <div className="flex justify-between items-center pt-4 border-t border-border/50 mt-6">
              <button
                type="button"
                onClick={() => setStep((s) => s - 1)}
                disabled={step === 1}
                className="px-6 py-2.5 rounded-lg border border-primary text-primary text-sm font-medium hover:bg-primary/5 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
              >
                Back
              </button>
              {step < 3 ? (
                <button
                  type="button"
                  onClick={goNext}
                  className="px-8 py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 shadow-sm transition-all active:scale-95"
                >
                  Next
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={register.isPending}
                  className="px-8 py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 shadow-sm transition-all active:scale-95 disabled:opacity-60 flex items-center gap-2"
                >
                  {register.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                  Complete Registration
                </button>
              )}
            </div>
          </form>
        </div>

        <p className="mt-5 text-center text-sm text-muted-foreground">
          Already registered?{" "}
          <Link to="/login" className="font-medium text-primary hover:text-primary/80 transition-colors">
            Sign in
          </Link>
        </p>
      </div>
    </AuthLayout>
  );
}
