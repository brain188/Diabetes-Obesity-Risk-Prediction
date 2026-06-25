import { useQuery } from "@tanstack/react-query";
import { Settings, Brain, Cpu, CheckCircle2, XCircle, RefreshCw, Database } from "lucide-react";
import { analyticsService } from "@/services/analytics.service";
import { Skeleton } from "@/components/ui/skeleton";

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-border/40 last:border-0 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium text-foreground text-right">{value}</span>
    </div>
  );
}

export default function FacilitySettingsPage() {
  const { data: modelInfo, isLoading, refetch, isFetching } = useQuery({
    queryKey: ["admin", "model-info"],
    queryFn: analyticsService.modelInfo,
    retry: false,
  });

  const metrics = modelInfo?.test_metrics ?? {};
  const thresholds = modelInfo?.thresholds ?? {};

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">System Settings</h1>
          <p className="text-sm text-muted-foreground mt-1">ML model configuration and node health information.</p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border text-sm text-muted-foreground hover:bg-muted transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Model status */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="px-6 py-4 border-b border-border/50 bg-muted/20 flex items-center gap-2">
          <Brain className="h-4 w-4 text-primary" />
          <h2 className="text-sm font-semibold text-foreground">ML Model</h2>
          {modelInfo && (
            <span className={`ml-auto inline-flex items-center gap-1 text-xs font-medium ${modelInfo.is_loaded ? "text-emerald-600" : "text-red-500"}`}>
              {modelInfo.is_loaded ? <CheckCircle2 className="h-3.5 w-3.5" /> : <XCircle className="h-3.5 w-3.5" />}
              {modelInfo.is_loaded ? "Loaded" : "Not loaded"}
            </span>
          )}
        </div>
        <div className="px-6 py-4">
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-8 w-full" />)}
            </div>
          ) : modelInfo ? (
            <>
              <InfoRow label="Model name" value={modelInfo.model_name ?? "—"} />
              <InfoRow label="Version" value={modelInfo.model_version ?? "—"} />
              <InfoRow label="Features" value={modelInfo.n_features ?? "—"} />
              <InfoRow label="Feature names" value={
                <span className="text-xs text-muted-foreground max-w-xs truncate">
                  {(modelInfo.feature_names ?? []).join(", ")}
                </span>
              } />
            </>
          ) : (
            <p className="text-sm text-muted-foreground py-4">Model info unavailable.</p>
          )}
        </div>
      </div>

      {/* Model performance */}
      {!isLoading && Object.keys(metrics).length > 0 && (
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          <div className="px-6 py-4 border-b border-border/50 bg-muted/20 flex items-center gap-2">
            <Cpu className="h-4 w-4 text-primary" />
            <h2 className="text-sm font-semibold text-foreground">Model Performance (Test Set)</h2>
          </div>
          <div className="px-6 py-4 grid grid-cols-2 sm:grid-cols-3 gap-3">
            {Object.entries(metrics).map(([key, val]) => (
              <div key={key} className="rounded-lg bg-muted/30 border border-border px-3 py-2.5">
                <p className="text-base font-bold text-foreground">
                  {typeof val === "number" ? (val < 1 ? `${(val * 100).toFixed(1)}%` : val) : String(val)}
                </p>
                <p className="text-xs text-muted-foreground capitalize">{key.replace(/_/g, " ")}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Thresholds */}
      {!isLoading && Object.keys(thresholds).length > 0 && (
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          <div className="px-6 py-4 border-b border-border/50 bg-muted/20 flex items-center gap-2">
            <Settings className="h-4 w-4 text-primary" />
            <h2 className="text-sm font-semibold text-foreground">Risk Thresholds</h2>
          </div>
          <div className="px-6 py-4">
            {Object.entries(thresholds).map(([key, val]) => (
              <InfoRow key={key} label={key.replace(/_/g, " ")} value={String(val)} />
            ))}
          </div>
        </div>
      )}

      {/* System info */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="px-6 py-4 border-b border-border/50 bg-muted/20 flex items-center gap-2">
          <Database className="h-4 w-4 text-primary" />
          <h2 className="text-sm font-semibold text-foreground">Node Configuration</h2>
        </div>
        <div className="px-6 py-4">
          <InfoRow label="API base URL" value={<span className="font-mono text-xs">{import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1"}</span>} />
          <InfoRow label="Environment" value={import.meta.env.MODE ?? "—"} />
          <InfoRow label="Version" value="1.0.0" />
        </div>
      </div>
    </div>
  );
}
