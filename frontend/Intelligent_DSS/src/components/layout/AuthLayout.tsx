import { Link } from "react-router-dom";
import { Activity, Lock } from "lucide-react";

export function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="pattern-bg min-h-screen flex flex-col font-sans text-foreground">
      <header className="w-full px-6 py-4 flex items-center justify-between bg-card/80 backdrop-blur-sm border-b border-border/40 sticky top-0 z-50">
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
        <Link to="/help" className="text-xs text-muted-foreground hover:text-primary transition-colors">
          Help
        </Link>
      </header>

      <main className="flex-grow flex items-center justify-center px-4 py-8">
        {children}
      </main>

      <footer className="px-6 py-5 text-center">
        <div className="flex justify-center items-center gap-4 mb-2">
          <a href="#" className="text-xs text-muted-foreground hover:text-primary transition-colors">Privacy Policy</a>
          <span className="text-border">•</span>
          <a href="#" className="text-xs text-muted-foreground hover:text-primary transition-colors">Terms of Service</a>
          <span className="text-border">•</span>
          <a href="#" className="text-xs text-muted-foreground hover:text-primary transition-colors">Security Standards</a>
        </div>
        <div className="flex justify-center items-center gap-1.5 mb-1">
          <Lock className="h-3 w-3 text-muted-foreground/70" />
          <p className="text-xs text-muted-foreground/70">256-bit SSL Secure. © 2025 Intelligent DSS Clinical.</p>
        </div>
      </footer>
    </div>
  );
}
