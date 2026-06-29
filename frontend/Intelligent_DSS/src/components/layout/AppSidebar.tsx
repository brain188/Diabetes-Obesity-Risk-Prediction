import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Users,
  ClipboardCheck,
  Brain,
  FileText,
  BarChart2,
  Settings,
  UserPlus,
  Building2,
  ShieldCheck,
  ScrollText,
  HelpCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";

const workerNav = [
  { label: "Dashboard", to: "/dashboard", icon: LayoutDashboard },
  { label: "Patients", to: "/patients", icon: Users },
  { label: "Screenings", to: "/screenings", icon: ClipboardCheck },
  { label: "Predictions", to: "/predictions", icon: Brain },
  { label: "Reports", to: "/reports", icon: FileText },
  { label: "Analytics", to: "/analytics", icon: BarChart2 },
  { label: "Settings", to: "/settings", icon: Settings },
  { label: "Help", to: "/help", icon: HelpCircle },
];

const adminNav = [
  { label: "Overview", to: "/admin/dashboard", icon: LayoutDashboard },
  { label: "Users", to: "/admin/users", icon: Users },
  { label: "Facilities", to: "/admin/facilities", icon: Building2 },
  { label: "Audit Trail", to: "/admin/audit", icon: ShieldCheck },
  { label: "System Logs", to: "/admin/logs", icon: ScrollText },
  { label: "AI Report", to: "/admin/ai-report", icon: Brain },
  { label: "System Config", to: "/admin/config", icon: Settings },
];

function NavItem({ item }: { item: { label: string; to: string; icon: typeof LayoutDashboard } }) {
  return (
    <NavLink
      to={item.to}
      end
      className={({ isActive }) =>
        cn(
          "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150",
          isActive
            ? "bg-accent text-primary font-semibold"
            : "text-muted-foreground hover:bg-accent/60 hover:text-foreground",
        )
      }
    >
      <item.icon className="h-4 w-4 shrink-0" />
      {item.label}
    </NavLink>
  );
}

export function AppSidebar() {
  const navigate = useNavigate();

  return (
    <aside className="fixed left-0 top-16 h-[calc(100vh-64px)] w-64 flex flex-col border-r border-border bg-sidebar z-40">
      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-3 space-y-0.5 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
        {workerNav.map((item) => <NavItem key={item.label} item={item} />)}

        <div className="pt-3 pb-1">
          <p className="px-3 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/60">
            Administration
          </p>
        </div>

        {adminNav.map((item) => <NavItem key={item.label} item={item} />)}
      </nav>

      {/* Register patient CTA */}
      <div className="p-3 border-t border-border">
        <button
          onClick={() => navigate("/patients")}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 transition-colors shadow-sm"
        >
          <UserPlus className="h-4 w-4" />
          Register New Patient
        </button>
      </div>
    </aside>
  );
}
