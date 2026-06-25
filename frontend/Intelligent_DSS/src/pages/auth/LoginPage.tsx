import { useState } from "react";
import { Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Activity, Mail, Lock, Eye, EyeOff, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useLogin } from "@/hooks/useAuth";

const schema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
  rememberMe: z.boolean().optional(),
});
type FormValues = z.infer<typeof schema>;

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const login = useLogin();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = (data: FormValues) => {
    login.mutate(
      { email: data.email, password: data.password },
      { onError: () => toast.error("Invalid credentials. Please try again.") },
    );
  };

  return (
    <div className="pattern-bg min-h-screen flex flex-col font-sans text-foreground">
      {/* Header */}
      <header className="w-full px-6 py-4 flex items-center bg-card/80 backdrop-blur-sm border-b border-border/40 sticky top-0 z-50">
        <div className="flex items-center gap-2.5">
          <div className="bg-primary text-primary-foreground p-2 rounded-lg flex items-center justify-center">
            <Activity className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-primary leading-none">Intelligent DSS</h1>
            <p className="text-[10px] font-semibold tracking-widest uppercase text-muted-foreground mt-0.5">
              Risk Prediction System
            </p>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="flex-grow flex items-center justify-center px-4 py-8">
        <div className="glass-card w-full max-w-md rounded-xl border border-border/50 relative overflow-hidden">
          {/* Primary accent top bar */}
          <div className="absolute top-0 left-0 w-full h-1 bg-primary" />

          <div className="px-8 py-8">
            <div className="text-center mb-7">
              <h2 className="text-2xl font-semibold text-foreground">Welcome Back</h2>
              <p className="text-sm text-muted-foreground mt-1">Sign in to access patient analytics</p>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
              {/* Email */}
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-foreground mb-1.5">
                  Corporate Email
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <input
                    {...register("email")}
                    id="email"
                    type="email"
                    placeholder="clinician@hospital.org"
                    autoComplete="email"
                    className="w-full pl-10 pr-4 py-2.5 bg-card border border-border rounded-lg text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                  />
                </div>
                {errors.email && (
                  <p className="mt-1 text-xs text-destructive">{errors.email.message}</p>
                )}
              </div>

              {/* Password */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label htmlFor="password" className="block text-sm font-medium text-foreground">
                    Password
                  </label>
                  <a href="#" className="text-xs font-medium text-primary hover:text-primary/80 transition-colors">
                    Forgot Password?
                  </a>
                </div>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <input
                    {...register("password")}
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    autoComplete="current-password"
                    className="w-full pl-10 pr-10 py-2.5 bg-card border border-border rounded-lg text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {errors.password && (
                  <p className="mt-1 text-xs text-destructive">{errors.password.message}</p>
                )}
              </div>

              {/* Remember me */}
              <div className="flex items-center gap-2">
                <input
                  {...register("rememberMe")}
                  id="remember-me"
                  type="checkbox"
                  className="h-4 w-4 rounded border-border text-primary focus:ring-primary/30 focus:ring-2"
                />
                <label htmlFor="remember-me" className="text-sm text-muted-foreground">
                  Remember me on this device
                </label>
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={login.isPending}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-primary hover:bg-primary/90 disabled:opacity-60 text-primary-foreground rounded-lg text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-primary/30 focus:ring-offset-2"
              >
                {login.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                Sign In
              </button>
            </form>

            <p className="mt-6 text-center text-sm text-muted-foreground">
              New clinician?{" "}
              <Link to="/register" className="font-medium text-primary hover:text-primary/80 transition-colors">
                Register for access
              </Link>
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="px-6 py-5 text-center">
        <div className="flex justify-center items-center gap-4 mb-2">
          <a href="#" className="text-xs text-muted-foreground hover:text-primary transition-colors">Privacy Policy</a>
          <span className="text-border">•</span>
          <a href="#" className="text-xs text-muted-foreground hover:text-primary transition-colors">Terms of Service</a>
          <span className="text-border">•</span>
          <Link to="/help" className="text-xs text-muted-foreground hover:text-primary transition-colors">Help Center</Link>
        </div>
        <p className="text-xs text-muted-foreground/70">© 2025 Intelligent DSS. Secure Clinical Environment.</p>
      </footer>
    </div>
  );
}
