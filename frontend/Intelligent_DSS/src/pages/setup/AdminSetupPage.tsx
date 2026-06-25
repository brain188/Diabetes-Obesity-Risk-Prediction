import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ShieldCheck, Check } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { AuthLayout } from "@/components/layout/AuthLayout";
import { useAuthStore } from "@/store/auth.store";

const schema = z.object({
  full_name: z.string().min(2, "Full name is required"),
  title: z.enum(["cmo", "dept_head", "it_admin", "clinic_manager"], {
    errorMap: () => ({ message: "Select your clinical role" }),
  }),
  email: z.string().email("Enter a valid email address"),
  employee_id: z.string().optional(),
  phone: z.string().optional(),
});
type FormValues = z.infer<typeof schema>;

const TITLE_LABELS: Record<string, string> = {
  cmo: "Chief Medical Officer",
  dept_head: "Department Head",
  it_admin: "IT Administrator",
  clinic_manager: "Clinic Manager",
};

const STEPPER = ["Facility Info", "Admin Details", "Verification"];

export default function AdminSetupPage() {
  const navigate = useNavigate();
  const { user, setAuth, accessToken } = useAuthStore();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { full_name: user?.full_name ?? "", email: user?.email ?? "" },
  });

  const onSubmit = (data: FormValues) => {
    if (user && accessToken) {
      setAuth({ ...user, full_name: data.full_name }, accessToken);
    }
    toast.success("Profile setup complete. Welcome to Intelligent DSS.");
    navigate(user?.role === "admin" ? "/admin/dashboard" : "/dashboard");
  };

  return (
    <AuthLayout>
      <div className="w-full max-w-xl">
        {/* Stepper — step 2 active */}
        <div className="mb-8 px-2">
          <div className="relative flex justify-between items-center">
            <div className="absolute top-5 left-0 w-full h-0.5 bg-border" />
            <div className="absolute top-5 left-0 h-0.5 bg-primary transition-all duration-500" style={{ width: "50%" }} />
            {STEPPER.map((label, i) => {
              const done = i < 1;
              const active = i === 1;
              const pending = i > 1;
              return (
                <div key={label} className="relative z-10 flex flex-col items-center gap-2">
                  <div className={cn(
                    "w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm border-2 shadow-sm transition-all",
                    done && "bg-primary border-primary text-primary-foreground",
                    active && "bg-primary border-primary text-primary-foreground ring-4 ring-primary/20",
                    pending && "bg-card border-border text-muted-foreground",
                  )}>
                    {done ? <Check className="h-4 w-4" /> : i + 1}
                  </div>
                  <span className={cn(
                    "text-xs font-semibold whitespace-nowrap",
                    active ? "text-primary" : done ? "text-primary/80" : "text-muted-foreground",
                  )}>
                    {label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Card */}
        <div className="glass-card rounded-xl border border-border/50 overflow-hidden">
          {/* Form header */}
          <div className="px-8 pt-8 pb-5 border-b border-border/40 bg-muted/20">
            <h2 className="text-2xl font-semibold text-foreground">Administrative Setup</h2>
            <p className="text-sm text-muted-foreground mt-1">
              Provide contact information for the primary clinical administrator.
            </p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="px-8 py-6 space-y-5">
            {/* Full Name */}
            <div className="space-y-1.5">
              <label htmlFor="full_name" className="text-sm font-medium text-foreground">Full Name</label>
              <input
                {...register("full_name")}
                id="full_name"
                placeholder="e.g., Dr. Sarah Smith"
                className="w-full px-4 py-2.5 rounded-lg bg-card border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
              />
              {errors.full_name && <p className="text-xs text-destructive">{errors.full_name.message}</p>}
            </div>

            {/* Professional Role */}
            <div className="space-y-1.5">
              <label htmlFor="title" className="text-sm font-medium text-foreground">Professional Role</label>
              <select
                {...register("title")}
                id="title"
                className="w-full px-4 py-2.5 rounded-lg bg-card border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all appearance-none"
              >
                <option value="">Select clinical role</option>
                <option value="cmo">Chief Medical Officer</option>
                <option value="dept_head">Department Head</option>
                <option value="it_admin">IT Administrator</option>
                <option value="clinic_manager">Clinic Manager</option>
              </select>
              {errors.title && <p className="text-xs text-destructive">{errors.title.message}</p>}
            </div>

            {/* Email & Employee ID */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div className="space-y-1.5">
                <label htmlFor="email" className="text-sm font-medium text-foreground">Professional Email</label>
                <input
                  {...register("email")}
                  id="email"
                  type="email"
                  placeholder="sarah.smith@facility.com"
                  className="w-full px-4 py-2.5 rounded-lg bg-card border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                />
                {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
              </div>
              <div className="space-y-1.5">
                <label htmlFor="employee_id" className="text-sm font-medium text-foreground">
                  Employee ID / NPI
                  <span className="ml-1 text-xs text-muted-foreground">(optional)</span>
                </label>
                <input
                  {...register("employee_id")}
                  id="employee_id"
                  placeholder="10-digit NPI number"
                  className="w-full px-4 py-2.5 rounded-lg bg-card border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                />
              </div>
            </div>

            {/* Phone */}
            <div className="space-y-1.5">
              <label htmlFor="phone" className="text-sm font-medium text-foreground">
                Phone Number
                <span className="ml-1 text-xs text-muted-foreground">(optional)</span>
              </label>
              <input
                {...register("phone")}
                id="phone"
                type="tel"
                placeholder="+1 (555) 000-0000"
                className="w-full px-4 py-2.5 rounded-lg bg-card border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
              />
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between pt-4 border-t border-border/50">
              <button
                type="button"
                onClick={() => navigate(-1)}
                className="px-6 py-2.5 rounded-lg border border-primary text-primary text-sm font-medium hover:bg-primary/5 transition-colors"
              >
                Back
              </button>
              <button
                type="submit"
                className="flex items-center gap-2 px-8 py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 shadow-sm transition-all active:scale-95"
              >
                Complete Setup
              </button>
            </div>
          </form>

          {/* HIPAA footer */}
          <div className="flex items-start gap-3 px-8 py-4 bg-muted/30 border-t border-border/40">
            <ShieldCheck className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
            <p className="text-sm text-muted-foreground">
              <strong className="text-primary">HIPAA Secure:</strong>{" "}
              All administrative data is encrypted in transit and at rest using AES-256 standards.
            </p>
          </div>
        </div>
      </div>
    </AuthLayout>
  );
}
