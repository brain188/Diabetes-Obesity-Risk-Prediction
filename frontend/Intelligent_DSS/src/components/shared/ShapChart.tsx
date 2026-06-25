import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { FEATURE_LABELS } from "@/lib/constants";
import type { FeatureContribution } from "@/types/prediction.types";

interface Props {
  contributions: FeatureContribution[];
  maxItems?: number;
}

export function ShapChart({ contributions, maxItems = 8 }: Props) {
  const data = [...contributions]
    .sort((a, b) => b.importance_abs - a.importance_abs)
    .slice(0, maxItems)
    .map((c) => ({
      feature: FEATURE_LABELS[c.feature_name] ?? c.feature_name,
      value: c.shap_value,
      direction: c.impact_direction,
    }));

  return (
    <ResponsiveContainer width="100%" height={Math.max(200, data.length * 36)}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 40, top: 4, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e5e7eb" />
        <XAxis
          type="number"
          tick={{ fontSize: 11 }}
          tickFormatter={(v: number) => v.toFixed(2)}
          domain={["auto", "auto"]}
        />
        <YAxis dataKey="feature" type="category" width={130} tick={{ fontSize: 12 }} />
        <Tooltip
          formatter={(v: number) => [v.toFixed(4), "SHAP Value"]}
          labelFormatter={(label) => `Feature: ${label}`}
        />
        <Bar dataKey="value" radius={[0, 4, 4, 0]}>
          {data.map((entry, i) => (
            <Cell key={i} fill={entry.direction === "Positive" ? "#ef4444" : "#10b981"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
