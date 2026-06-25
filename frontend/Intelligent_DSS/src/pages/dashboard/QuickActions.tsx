import { UserPlus, Microscope, FolderOpen, BarChart2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import type { LucideIcon } from "lucide-react";

type Action =
  | { kind: "register"; label: string; icon: LucideIcon; iconBg: string }
  | { kind: "navigate"; label: string; icon: LucideIcon; iconBg: string; to: string };

const actions: Action[] = [
  { kind: "register",  label: "New Patient Registration", icon: UserPlus,   iconBg: "bg-accent text-primary" },
  { kind: "navigate",  label: "Start Screening",          icon: Microscope,  iconBg: "bg-emerald-50 text-emerald-700", to: "/patients" },
  { kind: "navigate",  label: "View Reports",             icon: FolderOpen,  iconBg: "bg-muted text-muted-foreground",  to: "/reports" },
  { kind: "navigate",  label: "Analytics Dashboard",      icon: BarChart2,   iconBg: "bg-violet-50 text-violet-700",    to: "/analytics" },
];

interface Props {
  onRegisterPatient?: () => void;
}

export function QuickActions({ onRegisterPatient }: Props) {
  const navigate = useNavigate();

  function handleClick(action: Action) {
    if (action.kind === "register") {
      onRegisterPatient?.();
    } else {
      navigate(action.to);
    }
  }

  return (
    <div className="flex flex-col gap-2">
      {actions.map((action) => (
        <button
          key={action.label}
          onClick={() => handleClick(action)}
          className="w-full flex items-center gap-4 p-3 rounded-lg bg-background hover:bg-muted border border-border/50 transition-colors text-left group"
        >
          <div className={`w-8 h-8 rounded flex items-center justify-center flex-shrink-0 transition-transform group-hover:scale-105 ${action.iconBg}`}>
            <action.icon className="h-4 w-4" />
          </div>
          <span className="text-sm font-medium text-foreground">{action.label}</span>
        </button>
      ))}
    </div>
  );
}
