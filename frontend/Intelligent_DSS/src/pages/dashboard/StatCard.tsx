import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

type TrendDir = "up" | "down" | "flat";

interface Props {
  label: string;
  value: number | string;
  trend?: { value: string; dir: TrendDir };
  icon: LucideIcon;
  accent: "primary" | "secondary" | "tertiary" | "error";
  loading?: boolean;
}

const accentStyles = {
  primary:   { blob: "bg-primary/5",   iconRing: "text-primary",   iconHover: "group-hover:bg-primary group-hover:text-primary-foreground" },
  secondary: { blob: "bg-emerald-500/5", iconRing: "text-emerald-600", iconHover: "group-hover:bg-emerald-600 group-hover:text-white" },
  tertiary:  { blob: "bg-violet-500/5", iconRing: "text-violet-600", iconHover: "group-hover:bg-violet-600 group-hover:text-white" },
  error:     { blob: "bg-destructive/5", iconRing: "text-destructive", iconHover: "group-hover:bg-destructive group-hover:text-white" },
};

const trendStyles: Record<TrendDir, { text: string; bg: string }> = {
  up:   { text: "text-emerald-700", bg: "bg-emerald-50" },
  flat: { text: "text-muted-foreground", bg: "bg-muted" },
  down: { text: "text-destructive",  bg: "bg-red-50" },
};

export function StatCard({ label, value, trend, icon: Icon, accent, loading }: Props) {
  const a = accentStyles[accent];
  const t = trend ? trendStyles[trend.dir] : null;

  if (loading) {
    return (
      <div className="bg-card rounded-lg p-4 border border-border/40 shadow-clinical h-32 flex flex-col justify-between">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-8 w-20 mt-2" />
      </div>
    );
  }

  return (
    <div className="bg-card rounded-lg p-4 border border-border/40 shadow-clinical hover:shadow-md hover:border-primary/30 transition-all group flex flex-col justify-between h-32 relative overflow-hidden">
      {/* Decorative blob */}
      <div className={cn("absolute top-0 right-0 w-16 h-16 rounded-bl-full -mr-4 -mt-4 transition-transform group-hover:scale-110", a.blob)} />

      <div className="flex justify-between items-start relative z-10">
        <span className="text-sm font-medium text-muted-foreground">{label}</span>
        <div className={cn("w-8 h-8 rounded-full bg-muted flex items-center justify-center transition-colors", a.iconRing, a.iconHover)}>
          <Icon className="h-4 w-4" />
        </div>
      </div>

      <div className="flex items-end gap-2 relative z-10">
        <span className="text-3xl font-bold text-foreground leading-none">
          {typeof value === "number" ? value.toLocaleString() : value}
        </span>
        {t && trend && (
          <span className={cn("flex items-center gap-0.5 text-xs font-semibold px-1.5 py-0.5 rounded", t.text, t.bg)}>
            {trend.dir === "up" && <TrendingUp className="h-3 w-3" />}
            {trend.dir === "down" && <TrendingDown className="h-3 w-3" />}
            {trend.dir === "flat" && <Minus className="h-3 w-3" />}
            {trend.value}
          </span>
        )}
      </div>
    </div>
  );
}
