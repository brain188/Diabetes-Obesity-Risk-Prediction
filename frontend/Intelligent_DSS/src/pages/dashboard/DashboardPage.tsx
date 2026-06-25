import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Users, ClipboardList, Brain, FileText, RefreshCw } from "lucide-react";
import { format } from "date-fns";
import { StatCard } from "./StatCard";
import { RiskDistributionChart } from "./RiskDistributionChart";
import { ActivityFeed } from "./ActivityFeed";
import { QuickActions } from "./QuickActions";
import { RegisterPatientDialog } from "@/components/shared/RegisterPatientDialog";
import { useDashboardStats, useRiskDistribution } from "@/hooks/useAnalytics";

export default function DashboardPage() {
  const [registerOpen, setRegisterOpen] = useState(false);
  const navigate = useNavigate();

  const { data: stats, isLoading: statsLoading, refetch, isFetching } = useDashboardStats();
  const { data: riskData, isLoading: riskLoading } = useRiskDistribution();

  const cards = useMemo(
    () => [
      {
        label: "Total Patients",
        value: stats?.total_patients ?? 0,
        trend: { value: "+5.2%", dir: "up" as const },
        icon: Users,
        accent: "primary" as const,
      },
      {
        label: "Screening Sessions",
        value: stats?.total_screenings ?? 0,
        trend: { value: "+12%", dir: "up" as const },
        icon: ClipboardList,
        accent: "secondary" as const,
      },
      {
        label: "Predictions Run",
        value: stats?.total_predictions ?? 0,
        trend: { value: "0.0%", dir: "flat" as const },
        icon: Brain,
        accent: "tertiary" as const,
      },
      {
        label: "Reports Generated",
        value: stats?.total_reports ?? 0,
        trend: { value: "-2.1%", dir: "down" as const },
        icon: FileText,
        accent: "error" as const,
      },
    ],
    [stats],
  );

  return (
    <>
      {/* Page header */}
      <div className="mb-6 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Overview</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Real-time clinical metrics and patient risk assessments.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="p-1.5 rounded-md text-muted-foreground hover:bg-muted transition-colors disabled:opacity-50"
            title="Refresh"
          >
            <RefreshCw className={`h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
          </button>
          <span className="text-xs font-semibold text-muted-foreground bg-card px-3 py-1.5 rounded-full border border-border/50 shadow-sm">
            {format(new Date(), "MMM d, yyyy · HH:mm")}
          </span>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        {cards.map((card) => (
          <StatCard key={card.label} {...card} loading={statsLoading} />
        ))}
      </div>

      {/* Bento grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Quick Actions — 3 cols */}
        <div className="lg:col-span-3">
          <div className="bg-card rounded-lg border border-border/40 shadow-clinical p-4 h-full">
            <h2 className="text-base font-semibold text-foreground mb-4 pb-2 border-b border-border/20">
              Quick Actions
            </h2>
            <QuickActions onRegisterPatient={() => setRegisterOpen(true)} />
          </div>
        </div>

        {/* Risk Distribution — 5 cols */}
        <div className="lg:col-span-5">
          <div className="bg-card rounded-lg border border-border/40 shadow-clinical p-4 flex flex-col min-h-[360px]">
            <div className="flex justify-between items-center mb-4 pb-2 border-b border-border/20">
              <h2 className="text-base font-semibold text-foreground">Risk Distribution</h2>
              <span className="text-xs text-muted-foreground">T2D · All patients</span>
            </div>
            <RiskDistributionChart data={riskData} loading={riskLoading} />
          </div>
        </div>

        {/* Recent Activity — 4 cols */}
        <div className="lg:col-span-4">
          <div className="bg-card rounded-lg border border-border/40 shadow-clinical p-4 flex flex-col h-full min-h-[360px]">
            <div className="flex justify-between items-center mb-4 pb-2 border-b border-border/20">
              <h2 className="text-base font-semibold text-foreground">Recent Activity</h2>
              <button
                className="text-xs font-medium text-primary hover:underline"
                onClick={() => navigate("/patients")}
              >
                View All
              </button>
            </div>
            <ActivityFeed />
          </div>
        </div>
      </div>

      <RegisterPatientDialog open={registerOpen} onClose={() => setRegisterOpen(false)} />
    </>
  );
}
