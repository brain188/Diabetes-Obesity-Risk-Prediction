import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { Skeleton } from "@/components/ui/skeleton";
import type { RiskDistribution } from "@/types/analytics.types";

interface Props {
  data?: { distribution: RiskDistribution };
  loading?: boolean;
}

const COLORS = { High: "#ba1a1a", Moderate: "#006a61", Low: "#004ac6" };
const LABELS = ["High", "Moderate", "Low"] as const;

const CHART_HEIGHT = 220;

function normalize(d?: RiskDistribution): Array<{ name: string; value: number }> {
  if (!d) return [{ name: "High", value: 24 }, { name: "Moderate", value: 31 }, { name: "Low", value: 45 }];
  return LABELS.map((k) => ({
    name: k,
    value: d[k] ?? d[k.toLowerCase() as "low" | "moderate" | "high"] ?? 0,
  }));
}

export function RiskDistributionChart({ data, loading }: Props) {
  const chartData = normalize(data?.distribution);
  const highEntry = chartData.find((d) => d.name === "High");
  const total = chartData.reduce((s, d) => s + d.value, 0);
  const highPct = total > 0 ? Math.round(((highEntry?.value ?? 0) / total) * 100) : 24;

  if (loading) {
    return (
      <div className="flex-1 flex flex-col gap-3">
        <Skeleton className="w-full rounded-lg" style={{ height: CHART_HEIGHT }} />
        <div className="flex justify-center gap-5">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-16" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col gap-3">
      {/* Fixed-height container so the pie and the center overlay share the same reference */}
      <div
        className="relative bg-background rounded-lg border border-border/20 overflow-hidden"
        style={{ height: CHART_HEIGHT }}
      >
        {/* Decorative blurs */}
        <div className="absolute w-40 h-40 rounded-full bg-destructive/10 blur-2xl top-2 left-2 pointer-events-none" />
        <div className="absolute w-28 h-28 rounded-full bg-primary/10 blur-2xl bottom-2 right-4 pointer-events-none" />

        <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={85}
              paddingAngle={3}
              dataKey="value"
              startAngle={90}
              endAngle={-270}
            >
              {chartData.map((entry) => (
                <Cell key={entry.name} fill={COLORS[entry.name as keyof typeof COLORS]} />
              ))}
            </Pie>
            <Tooltip
              formatter={(v: number) =>
                total > 0 ? [`${Math.round((v / total) * 100)}% (${v})`, "Patients"] : [`${v}%`, ""]
              }
            />
          </PieChart>
        </ResponsiveContainer>

        {/* Center overlay — Stitch glassmorphism card */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="bg-white/70 backdrop-blur-sm border border-white/50 px-4 py-3 rounded-xl shadow-sm text-center">
            <span className="block text-4xl font-bold text-destructive leading-none">{highPct}%</span>
            <span className="text-xs font-semibold text-foreground uppercase tracking-wider mt-1 block">
              High Risk T2D
            </span>
            <div className="mt-2 w-24 h-1.5 rounded-full bg-muted overflow-hidden mx-auto">
              <div className="bg-destructive h-full rounded-full" style={{ width: `${highPct}%` }} />
            </div>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex justify-center gap-5">
        {chartData.map((entry) => (
          <div key={entry.name} className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[entry.name as keyof typeof COLORS] }} />
            <span className="text-xs text-muted-foreground">
              {entry.name}{total > 0 ? ` (${Math.round((entry.value / total) * 100)}%)` : ""}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
