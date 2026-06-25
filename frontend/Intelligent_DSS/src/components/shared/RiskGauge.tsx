import { cn } from "@/lib/utils";

interface Props {
  probability: number;
  label: string;
  className?: string;
}

export function RiskGauge({ probability, label, className }: Props) {
  const pct = Math.round(probability * 100);
  const color = pct >= 55 ? "#ef4444" : pct >= 35 ? "#f59e0b" : "#10b981";
  const circumference = 2 * Math.PI * 45;
  const offset = circumference - (pct / 100) * (circumference / 2);

  return (
    <div className={cn("flex flex-col items-center gap-1", className)}>
      <svg width={120} height={70} viewBox="0 0 120 70">
        <path
          d="M 10 60 A 50 50 0 0 1 110 60"
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={10}
          strokeLinecap="round"
        />
        <path
          d="M 10 60 A 50 50 0 0 1 110 60"
          fill="none"
          stroke={color}
          strokeWidth={10}
          strokeLinecap="round"
          strokeDasharray={circumference / 2}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
        <text x="60" y="56" textAnchor="middle" fontSize="18" fontWeight="700" fill={color}>
          {pct}%
        </text>
      </svg>
      <p className="text-xs text-muted-foreground font-medium">{label}</p>
    </div>
  );
}
