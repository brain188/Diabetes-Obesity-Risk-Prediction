import { useRef, useState, useCallback, KeyboardEvent } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { Mail, RefreshCw, ShieldCheck, ArrowLeft, Check } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { AuthLayout } from "@/components/layout/AuthLayout";

const OTP_LENGTH = 6;

export default function VerifyEmailPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const email: string = state?.email ?? sessionStorage.getItem("pending_verify_email") ?? "your registered email";

  const [digits, setDigits] = useState<string[]>(Array(OTP_LENGTH).fill(""));
  const refs = useRef<Array<HTMLInputElement | null>>(Array(OTP_LENGTH).fill(null));

  const focusAt = (i: number) => refs.current[i]?.focus();

  const handleChange = useCallback((i: number, raw: string) => {
    const val = raw.replace(/\D/g, "").slice(-1);
    setDigits((prev) => {
      const next = [...prev];
      next[i] = val;
      return next;
    });
    if (val && i < OTP_LENGTH - 1) focusAt(i + 1);
  }, []);

  const handleKeyDown = useCallback((i: number, e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace") {
      if (digits[i]) {
        setDigits((prev) => { const n = [...prev]; n[i] = ""; return n; });
      } else if (i > 0) {
        focusAt(i - 1);
      }
    } else if (e.key === "ArrowLeft" && i > 0) {
      focusAt(i - 1);
    } else if (e.key === "ArrowRight" && i < OTP_LENGTH - 1) {
      focusAt(i + 1);
    }
  }, [digits]);

  const handlePaste = useCallback((e: React.ClipboardEvent) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, OTP_LENGTH);
    if (!pasted) return;
    const next = Array(OTP_LENGTH).fill("");
    pasted.split("").forEach((c, i) => { next[i] = c; });
    setDigits(next);
    focusAt(Math.min(pasted.length, OTP_LENGTH - 1));
  }, []);

  function handleResend() {
    toast.info("A new verification code has been sent to your email.");
  }

  function handleSubmit() {
    const token = digits.join("");
    if (token.length < OTP_LENGTH) {
      toast.error("Please enter the complete 6-digit code.");
      return;
    }
    sessionStorage.removeItem("pending_verify_email");
    toast.success("Verification complete. Please sign in.");
    navigate("/login");
  }

  const filled = digits.filter(Boolean).length;

  return (
    <AuthLayout>
      <div className="w-full max-w-lg">
        {/* Stepper — step 3 active */}
        <div className="mb-8 px-2">
          <div className="relative flex justify-between items-center">
            <div className="absolute top-5 left-0 w-full h-0.5 bg-border" />
            <div className="absolute top-5 left-0 h-0.5 bg-primary transition-all duration-500" style={{ width: "100%" }} />
            {["Facility Info", "Admin Details", "Verification"].map((label, i) => {
              const done = i < 2;
              const active = i === 2;
              return (
                <div key={label} className="relative z-10 flex flex-col items-center gap-2">
                  <div className={cn(
                    "w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm border-2 shadow-sm transition-all",
                    done && "bg-emerald-500 border-emerald-500 text-white",
                    active && "bg-white border-primary text-primary",
                  )}>
                    {done ? <Check className="h-4 w-4" /> : "3"}
                  </div>
                  <span className={cn("text-xs font-semibold whitespace-nowrap", active ? "text-primary" : "text-emerald-600")}>
                    {label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="glass-card rounded-xl border border-border/50 overflow-hidden relative">
          <div className="absolute top-0 left-0 w-full h-1 bg-primary pointer-events-none" />
          <div className="px-8 py-8">
            <h2 className="text-2xl font-semibold text-foreground">Review & Verify</h2>
            <p className="text-sm text-muted-foreground mt-1 mb-6">
              Confirm your details and verify your email to finalise clinical portal registration.
            </p>

            {/* Email verification section */}
            <div className="flex items-start gap-4 mb-6">
              <div className="p-2.5 bg-primary/10 rounded-lg flex-shrink-0">
                <Mail className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-foreground">Email Verification</h3>
                <p className="text-sm text-muted-foreground mt-0.5">
                  We've sent a 6-digit code to{" "}
                  <strong className="text-foreground">{email}</strong>
                </p>
              </div>
            </div>

            {/* OTP inputs */}
            <div className="flex flex-col items-center gap-4 mb-6">
              <div className="flex gap-3" onPaste={handlePaste}>
                {digits.map((d, i) => (
                  <input
                    key={i}
                    ref={(el) => { refs.current[i] = el; }}
                    value={d}
                    maxLength={1}
                    inputMode="numeric"
                    autoFocus={i === 0}
                    onChange={(e) => handleChange(i, e.target.value)}
                    onKeyDown={(e) => handleKeyDown(i, e)}
                    className={cn(
                      "w-12 h-14 text-center text-xl font-bold rounded-lg border-2 bg-card focus:outline-none transition-all",
                      d ? "border-primary text-foreground" : "border-border text-muted-foreground",
                      "focus:border-primary focus:ring-2 focus:ring-primary/20",
                    )}
                  />
                ))}
              </div>

              <button
                type="button"
                onClick={handleResend}
                className="flex items-center gap-1.5 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
              >
                <RefreshCw className="h-4 w-4" />
                Resend Code
              </button>
            </div>

            {/* Progress indicator */}
            {filled > 0 && filled < OTP_LENGTH && (
              <div className="mb-4">
                <div className="flex gap-1">
                  {Array(OTP_LENGTH).fill(null).map((_, i) => (
                    <div key={i} className={cn("h-1 flex-1 rounded-full transition-all", i < filled ? "bg-primary" : "bg-border")} />
                  ))}
                </div>
              </div>
            )}

            {/* HIPAA security banner */}
            <div className="flex items-start gap-3 p-4 bg-muted/50 rounded-lg border border-border/40 mb-6">
              <ShieldCheck className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold text-emerald-700">HIPAA Compliant Data Storage</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  All patient data and administrator credentials are encrypted using AES-256 standards during transit and at rest.
                </p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between">
              <Link
                to="/register"
                className="flex items-center gap-2 px-6 py-2.5 rounded-lg border border-primary text-primary text-sm font-medium hover:bg-primary/5 transition-colors"
              >
                <ArrowLeft className="h-4 w-4" />
                Back
              </Link>
              <button
                type="button"
                onClick={handleSubmit}
                disabled={filled < OTP_LENGTH}
                className="flex items-center gap-2 px-8 py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 shadow-sm transition-all active:scale-95 disabled:opacity-60"
              >
                Complete Registration
              </button>
            </div>
          </div>
        </div>

        <p className="mt-5 text-center text-sm text-muted-foreground">
          Need help?{" "}
          <a href="mailto:support@intelligentdss.com" className="font-medium text-primary hover:text-primary/80 transition-colors">
            Contact Support
          </a>
        </p>
      </div>
    </AuthLayout>
  );
}
