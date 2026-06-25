import { AlertTriangle, ClipboardCheck, FileText, UserPlus } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { formatDistanceToNow, parseISO } from "date-fns";
import { cn } from "@/lib/utils";
import type { ActivityItem } from "@/types/analytics.types";

const iconMap = {
  prediction_high: { Icon: AlertTriangle, ring: "border-destructive text-destructive", bg: "bg-red-50/50 border border-red-200" },
  screening:       { Icon: ClipboardCheck, ring: "border-border text-emerald-600",     bg: "" },
  report:          { Icon: FileText,        ring: "border-border text-muted-foreground", bg: "" },
  patient:         { Icon: UserPlus,        ring: "border-border text-primary",          bg: "" },
};

function relativeTime(ts: string) {
  try { return formatDistanceToNow(parseISO(ts), { addSuffix: true }); }
  catch { return ts; }
}

function makeFallback(): ActivityItem[] {
  const now = Date.now();
  return [
    { id: "1", type: "prediction_high", description: "High risk prediction flagged for Patient #982-A", timestamp: new Date(now - 12 * 60 * 1000).toISOString() },
    { id: "2", type: "screening",       description: "Routine screening completed by care team",          timestamp: new Date(now - 60 * 60 * 1000).toISOString() },
    { id: "3", type: "report",          description: "Weekly analytical report auto-generated.",           timestamp: new Date(now - 3 * 60 * 60 * 1000).toISOString() },
    { id: "4", type: "patient",         description: "New patient registered via intake portal.",          timestamp: new Date(now - 24 * 60 * 60 * 1000).toISOString() },
  ];
}

interface Props {
  items?: ActivityItem[];
}

export function ActivityFeed({ items }: Props) {
  const navigate = useNavigate();
  const feed = items && items.length > 0 ? items : makeFallback();

  return (
    <ul className="flex flex-col flex-1 relative">
      {/* Timeline vertical line */}
      <div className="absolute left-[15px] top-4 bottom-4 w-px bg-border/40" />

      {feed.map((item, i) => {
        const { Icon, ring, bg } = iconMap[item.type];
        return (
          <li key={item.id} className={cn("flex items-start gap-4 relative z-10", i < feed.length - 1 && "mb-4")}>
            <div className={cn("w-8 h-8 rounded-full bg-card border-2 flex items-center justify-center flex-shrink-0 shadow-sm mt-0.5", ring)}>
              <Icon className="h-3.5 w-3.5" />
            </div>
            <div className={cn("flex-1 p-2 rounded-lg", bg)}>
              <p className="text-sm text-foreground leading-snug">
                {item.description}
                {item.patient_id && (
                  <button
                    className="font-semibold ml-1 hover:text-primary transition-colors"
                    onClick={() => navigate(`/patients/${item.patient_id}`)}
                  >
                    #{item.patient_id.slice(0, 6).toUpperCase()}
                  </button>
                )}
              </p>
              <span className="text-xs text-muted-foreground mt-1 block">{relativeTime(item.timestamp)}</span>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
