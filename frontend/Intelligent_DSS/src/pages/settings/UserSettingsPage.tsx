import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  User, Mail, Building2, Lock, Eye, EyeOff, Loader2,
  CheckCircle2, Bell, Globe, Laptop, Sun, Moon, Shield,
  LogOut, AlertTriangle, Monitor,
} from "lucide-react";
import { toast } from "sonner";
import { useAuthStore } from "@/store/auth.store";
import { authService } from "@/services/auth.service";
import { useTheme } from "@/components/theme-provider";
import { cn } from "@/lib/utils";

/* ── Password schema ── */
const passwordSchema = z.object({
  current_password: z.string().min(1, "Required"),
  new_password: z
    .string()
    .min(8, "At least 8 characters")
    .regex(/[A-Z]/, "Must contain an uppercase letter")
    .regex(/[0-9]/, "Must contain a number"),
  confirm_password: z.string(),
}).refine((d) => d.new_password === d.confirm_password, {
  message: "Passwords do not match",
  path: ["confirm_password"],
});
type PasswordForm = z.infer<typeof passwordSchema>;

function passwordStrength(pw: string): { label: string; color: string; width: string } {
  if (!pw) return { label: "", color: "", width: "0%" };
  let score = 0;
  if (pw.length >= 8) score++;
  if (pw.length >= 12) score++;
  if (/[A-Z]/.test(pw)) score++;
  if (/[0-9]/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  if (score <= 1) return { label: "Weak", color: "bg-red-500", width: "25%" };
  if (score === 2) return { label: "Fair", color: "bg-amber-500", width: "50%" };
  if (score === 3) return { label: "Good", color: "bg-yellow-400", width: "65%" };
  if (score === 4) return { label: "Strong", color: "bg-emerald-500", width: "85%" };
  return { label: "Very Strong", color: "bg-emerald-600", width: "100%" };
}

function PasswordInput({ id, label, reg, error, watch }: {
  id: string; label: string; reg: any; error?: string; watch?: string;
}) {
  const [show, setShow] = useState(false);
  const strength = watch ? passwordStrength(watch) : null;
  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="text-sm font-medium text-foreground">{label}</label>
      <div className="relative">
        <input
          id={id}
          {...reg}
          type={show ? "text" : "password"}
          className="w-full px-3 py-2 pr-9 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
        />
        <button type="button" onClick={() => setShow(!show)} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
          {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
        </button>
      </div>
      {strength && watch && (
        <div className="space-y-1">
          <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
            <div className={`h-full rounded-full transition-all ${strength.color}`} style={{ width: strength.width }} />
          </div>
          {strength.label && <p className={`text-xs font-medium ${strength.color.replace("bg-", "text-")}`}>{strength.label}</p>}
        </div>
      )}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
        checked ? "bg-primary" : "bg-muted"
      }`}
    >
      <span className={`inline-block h-4 w-4 rounded-full bg-white shadow transition-transform ${checked ? "translate-x-4" : "translate-x-0"}`} />
    </button>
  );
}

type Tab = "account" | "preferences" | "sessions";

export default function UserSettingsPage() {
  const { user } = useAuthStore();
  const { theme, setTheme } = useTheme();
  const [tab, setTab] = useState<Tab>("account");
  const [pwSuccess, setPwSuccess] = useState(false);
  const [language, setLanguage] = useState("en");
  const [emailNotif, setEmailNotif] = useState(true);
  const [systemAlerts, setSystemAlerts] = useState(true);

  const { register, handleSubmit, reset, watch, formState: { errors, isSubmitting } } = useForm<PasswordForm>({
    resolver: zodResolver(passwordSchema),
  });
  const newPwValue = watch("new_password", "");

  const onChangePassword = async (data: PasswordForm) => {
    try {
      await authService.changePassword({ current_password: data.current_password, new_password: data.new_password });
      setPwSuccess(true);
      reset();
      toast.success("Password changed successfully.");
      setTimeout(() => setPwSuccess(false), 4000);
    } catch {
      toast.error("Failed to change password. Check your current password and try again.");
    }
  };

  const initials = user?.full_name?.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase() ?? "??";

  return (
    <div className="max-w-2xl mx-auto space-y-0 pb-8">
      {/* Profile banner */}
      <div className="rounded-xl border border-border bg-card overflow-hidden mb-6">
        <div className="bg-gradient-to-r from-primary/10 to-primary/5 px-6 pt-6 pb-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xl font-bold shrink-0 ring-4 ring-background">
              {initials}
            </div>
            <div className="min-w-0">
              <p className="text-lg font-bold text-foreground">{user?.full_name ?? "—"}</p>
              <p className="text-sm text-muted-foreground capitalize">{user?.role?.replace("_", " ") ?? "—"}</p>
              {user?.clinic_name && (
                <p className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                  <Building2 className="h-3 w-3" />{user.clinic_name}
                </p>
              )}
            </div>
          </div>
        </div>
        {/* Tabs */}
        <div className="flex border-b border-border bg-background/50">
          {(["account", "preferences", "sessions"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-5 py-3 text-sm font-medium capitalize border-b-2 transition-colors ${
                tab === t
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* ── ACCOUNT TAB ── */}
      {tab === "account" && (
        <div className="space-y-4">
          {/* Account info */}
          <div className="rounded-xl border border-border bg-card overflow-hidden">
            <div className="px-6 py-4 border-b border-border/50 bg-muted/20 flex items-center gap-2">
              <User className="h-4 w-4 text-primary" />
              <h2 className="text-sm font-semibold text-foreground">Account Information</h2>
            </div>
            <div className="px-6 py-5 space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/30 border border-border/50">
                  <Mail className="h-4 w-4 text-muted-foreground shrink-0" />
                  <div className="min-w-0">
                    <p className="text-xs text-muted-foreground">Email</p>
                    <p className="text-sm font-medium text-foreground truncate">{user?.email ?? "—"}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/30 border border-border/50">
                  <Building2 className="h-4 w-4 text-muted-foreground shrink-0" />
                  <div className="min-w-0">
                    <p className="text-xs text-muted-foreground">Department / Clinic</p>
                    <p className="text-sm font-medium text-foreground truncate">{user?.clinic_name ?? "Not set"}</p>
                  </div>
                </div>
              </div>
              {/* System usage badge */}
              <div className="flex items-center gap-3 p-3 rounded-lg bg-primary/5 border border-primary/20">
                <div className="p-2 rounded-lg bg-primary/10 shrink-0">
                  <CheckCircle2 className="h-4 w-4 text-primary" />
                </div>
                <div>
                  <p className="text-xs font-semibold text-primary">Active Clinician</p>
                  <p className="text-xs text-muted-foreground">Account is active and in good standing</p>
                </div>
              </div>
            </div>
          </div>

          {/* Security */}
          <div className="rounded-xl border border-border bg-card overflow-hidden">
            <div className="px-6 py-4 border-b border-border/50 bg-muted/20 flex items-center gap-2">
              <Shield className="h-4 w-4 text-primary" />
              <h2 className="text-sm font-semibold text-foreground">Security Settings</h2>
            </div>
            <form onSubmit={handleSubmit(onChangePassword)} className="px-6 py-5 space-y-4">
              <PasswordInput id="current_password" label="Current Password" reg={register("current_password")} error={errors.current_password?.message} />
              <PasswordInput id="new_password" label="New Password" reg={register("new_password")} error={errors.new_password?.message} watch={newPwValue} />
              <PasswordInput id="confirm_password" label="Confirm New Password" reg={register("confirm_password")} error={errors.confirm_password?.message} />
              <div className="flex items-center gap-3 pt-1">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex items-center gap-2 px-5 py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-60"
                >
                  {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Lock className="h-4 w-4" />}
                  Update Password
                </button>
                {pwSuccess && (
                  <span className="flex items-center gap-1.5 text-sm text-emerald-600">
                    <CheckCircle2 className="h-4 w-4" />Password updated
                  </span>
                )}
              </div>
            </form>
          </div>

          {/* Danger zone */}
          <div className="rounded-xl border border-red-200 bg-red-50/50 px-6 py-4 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-red-700 flex items-center gap-2"><AlertTriangle className="h-4 w-4" />Deactivate Account</p>
              <p className="text-xs text-red-600 mt-0.5">Permanently disable your account. This cannot be undone.</p>
            </div>
            <button className="px-4 py-2 rounded-lg border border-red-300 text-red-700 text-sm font-medium hover:bg-red-100 transition-colors">
              Deactivate
            </button>
          </div>
        </div>
      )}

      {/* ── PREFERENCES TAB ── */}
      {tab === "preferences" && (
        <div className="space-y-4">
          {/* Theme */}
          <div className="rounded-xl border border-border bg-card overflow-hidden">
            <div className="px-6 py-4 border-b border-border/50 bg-muted/20 flex items-center gap-2">
              <Sun className="h-4 w-4 text-primary" />
              <h2 className="text-sm font-semibold text-foreground">Interface Theme</h2>
            </div>
            <div className="px-6 py-5">
              <div className="grid grid-cols-3 gap-3">
                {(["light", "dark", "system"] as const).map((t) => {
                  const Icon = t === "light" ? Sun : t === "dark" ? Moon : Monitor;
                  return (
                    <button
                      key={t}
                      onClick={() => setTheme(t)}
                      className={`flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all ${
                        theme === t ? "border-primary bg-primary/5" : "border-border hover:border-border/80"
                      }`}
                    >
                      <Icon className={`h-5 w-5 ${theme === t ? "text-primary" : "text-muted-foreground"}`} />
                      <span className={`text-xs font-medium capitalize ${theme === t ? "text-primary" : "text-muted-foreground"}`}>{t}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Language */}
          <div className="rounded-xl border border-border bg-card overflow-hidden">
            <div className="px-6 py-4 border-b border-border/50 bg-muted/20 flex items-center gap-2">
              <Globe className="h-4 w-4 text-primary" />
              <h2 className="text-sm font-semibold text-foreground">System Language</h2>
            </div>
            <div className="px-6 py-5">
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full px-3 py-2.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
              >
                <option value="en">English (US)</option>
                <option value="es">Spanish (ES)</option>
                <option value="fr">French (FR)</option>
                <option value="de">German (DE)</option>
              </select>
            </div>
          </div>

          {/* Notifications */}
          <div className="rounded-xl border border-border bg-card overflow-hidden">
            <div className="px-6 py-4 border-b border-border/50 bg-muted/20 flex items-center gap-2">
              <Bell className="h-4 w-4 text-primary" />
              <h2 className="text-sm font-semibold text-foreground">Communication Preferences</h2>
            </div>
            <div className="px-6 py-5 space-y-4">
              {[
                { label: "Email Notifications", sub: "Daily summary of patient risks", val: emailNotif, set: setEmailNotif },
                { label: "System Alerts", sub: "High-risk threshold triggers", val: systemAlerts, set: setSystemAlerts },
              ].map(({ label, sub, val, set }) => (
                <div key={label} className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-sm font-medium text-foreground">{label}</p>
                    <p className="text-xs text-muted-foreground">{sub}</p>
                  </div>
                  <Toggle checked={val} onChange={set} />
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-3">
            <button
              onClick={() => toast.success("Preferences saved.")}
              className="px-5 py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
            >
              Save Preferences
            </button>
          </div>
        </div>
      )}

      {/* ── SESSIONS TAB ── */}
      {tab === "sessions" && (
        <div className="space-y-4">
          <div className="rounded-xl border border-border bg-card overflow-hidden">
            <div className="px-6 py-4 border-b border-border/50 bg-muted/20 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <Laptop className="h-4 w-4 text-primary" />Active Sessions
              </h2>
              <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full">1 active</span>
            </div>
            <div className="divide-y divide-border/50">
              <div className="px-6 py-4 flex items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <Monitor className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">Current Session</p>
                    <p className="text-xs text-muted-foreground">This browser · Active now</p>
                  </div>
                </div>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />Active
                </span>
              </div>
            </div>
            <div className="px-6 py-4 border-t border-border/50">
              <button
                onClick={() => toast.info("All other sessions logged out.")}
                className="flex items-center gap-2 text-sm text-red-600 hover:text-red-700 font-medium"
              >
                <LogOut className="h-4 w-4" />Logout from all devices
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
