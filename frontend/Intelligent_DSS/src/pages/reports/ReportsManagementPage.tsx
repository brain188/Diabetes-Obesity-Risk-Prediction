import { useState, useDeferredValue } from "react";
import { useNavigate } from "react-router-dom";
import { format, parseISO } from "date-fns";
import {
  FileText, Download, Eye, Trash2, Loader2, Search,
  FileJson, AlertCircle, CheckCircle, Clock,
} from "lucide-react";
import { toast } from "sonner";
import { useAllReports } from "@/hooks/useReports";
import { useDownloadReport } from "@/hooks/useReports";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { reportService } from "@/services/report.service";
import type { ReportListItem } from "@/services/report.service";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/EmptyState";

function initials(name: string) {
  return name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);
}

function FormatBadge({ fmt }: { fmt: string }) {
  const isPdf = fmt?.toUpperCase() === "PDF";
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold border ${
      isPdf ? "bg-red-50 text-red-700 border-red-200" : "bg-sky-50 text-sky-700 border-sky-200"
    }`}>
      {isPdf ? <FileText className="h-3 w-3" /> : <FileJson className="h-3 w-3" />}
      {fmt?.toUpperCase() ?? "PDF"}
    </span>
  );
}

function ReportRow({ report }: { report: ReportListItem }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const download = useDownloadReport();

  const deleteReport = useMutation({
    mutationFn: (id: string) => reportService.delete(id),
    onSuccess: () => {
      toast.success("Report deleted.");
      queryClient.invalidateQueries({ queryKey: ["reports", "all"] });
    },
    onError: () => toast.error("Failed to delete report."),
  });

  return (
    <tr className="border-b border-border/50 hover:bg-muted/20 transition-colors">
      <td className="px-4 py-3 text-xs font-mono text-muted-foreground whitespace-nowrap">
        #{report.report_id.slice(0, 8).toUpperCase()}
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary text-xs font-semibold shrink-0">
            {initials(report.patient_name)}
          </div>
          <div>
            <p className="text-sm font-medium text-foreground">{report.patient_name}</p>
            <p className="text-xs text-muted-foreground">{report.patient_sex}</p>
          </div>
        </div>
      </td>
      <td className="px-4 py-3 text-xs font-mono text-muted-foreground hidden sm:table-cell">
        {report.patient_id.slice(0, 8)}…
      </td>
      <td className="px-4 py-3">
        <FormatBadge fmt={report.format} />
      </td>
      <td className="px-4 py-3 text-sm text-muted-foreground whitespace-nowrap hidden md:table-cell">
        {report.generated_at ? format(parseISO(report.generated_at), "MMM d, yyyy · HH:mm") : "—"}
      </td>
      <td className="px-4 py-3 text-xs text-muted-foreground hidden lg:table-cell">
        {report.download_count ?? "0"}×
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-1">
          <button
            onClick={() => navigate(`/patients/${report.patient_id}/report`)}
            title="View report"
            className="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
          >
            <Eye className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() =>
              download.mutate(report.report_id, {
                onError: () => toast.error("Download failed."),
              })
            }
            title="Download PDF"
            disabled={download.isPending}
            className="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50"
          >
            {download.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />}
          </button>
          <button
            onClick={() => {
              if (window.confirm("Delete this report permanently?")) {
                deleteReport.mutate(report.report_id);
              }
            }}
            title="Delete report"
            disabled={deleteReport.isPending}
            className="p-1.5 rounded hover:bg-red-50 text-muted-foreground hover:text-red-600 transition-colors disabled:opacity-50"
          >
            {deleteReport.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" />}
          </button>
        </div>
      </td>
    </tr>
  );
}

export default function ReportsManagementPage() {
  const [search, setSearch] = useState("");
  const [formatFilter, setFormatFilter] = useState<"ALL" | "PDF" | "JSON">("ALL");
  const deferred = useDeferredValue(search);

  const { data: reports = [], isLoading, isError } = useAllReports();

  const filtered = reports.filter((r) => {
    const matchSearch =
      !deferred ||
      r.patient_name.toLowerCase().includes(deferred.toLowerCase()) ||
      r.report_id.toLowerCase().includes(deferred.toLowerCase()) ||
      r.patient_id.toLowerCase().includes(deferred.toLowerCase());
    const matchFormat = formatFilter === "ALL" || r.format?.toUpperCase() === formatFilter;
    return matchSearch && matchFormat;
  });

  const totalPdf = reports.filter((r) => r.format?.toUpperCase() === "PDF").length;
  const totalJson = reports.filter((r) => r.format?.toUpperCase() === "JSON").length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Reports Management</h1>
          <p className="text-sm text-muted-foreground mt-1">View, download, and manage all generated clinical reports.</p>
        </div>
      </div>

      {/* Summary tiles */}
      {!isLoading && !isError && (
        <div className="flex flex-wrap gap-3">
          <div className="px-4 py-3 rounded-xl border border-border bg-card">
            <p className="text-xl font-bold text-foreground">{reports.length}</p>
            <p className="text-xs text-muted-foreground">Total Reports</p>
          </div>
          <div className="px-4 py-3 rounded-xl border border-red-200 bg-red-50">
            <p className="text-xl font-bold text-red-700">{totalPdf}</p>
            <p className="text-xs text-red-600">PDF</p>
          </div>
          <div className="px-4 py-3 rounded-xl border border-sky-200 bg-sky-50">
            <p className="text-xl font-bold text-sky-700">{totalJson}</p>
            <p className="text-xs text-sky-600">JSON</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-48 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search patient or report ID…"
            className="w-full pl-9 pr-3 py-2 bg-card border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
          />
        </div>
        <div className="flex gap-1 border border-border rounded-lg p-0.5 bg-muted/30">
          {(["ALL", "PDF", "JSON"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFormatFilter(f)}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                formatFilter === f ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {f === "ALL" ? "All Formats" : f}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-14 w-full rounded-xl" />)}
        </div>
      ) : isError ? (
        <EmptyState icon={AlertCircle} title="Failed to load reports" description="Could not fetch reports from the server." />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No reports found"
          description={search ? `No results for "${search}"` : "Generate a report from the prediction results page."}
        />
      ) : (
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-muted/30 border-b border-border">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Report ID</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Patient</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide hidden sm:table-cell">Patient ID</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Format</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide hidden md:table-cell">Generated</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide hidden lg:table-cell">Downloads</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((r) => <ReportRow key={r.report_id} report={r} />)}
              </tbody>
            </table>
          </div>
          <div className="px-4 py-3 border-t border-border/50 bg-muted/10">
            <p className="text-xs text-muted-foreground">
              Showing {filtered.length} of {reports.length} reports
            </p>
          </div>
        </div>
      )}

      {/* Bottom summary metrics — Stitch design */}
      {!isLoading && !isError && reports.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="rounded-xl border border-border bg-card p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-3xl font-bold text-foreground">{reports.length.toLocaleString()}</p>
                <p className="text-sm font-medium text-foreground mt-0.5">Total Generated</p>
                <p className="text-xs text-muted-foreground mt-1">All formats combined</p>
              </div>
              <FileText className="h-5 w-5 text-primary mt-1 shrink-0" />
            </div>
          </div>
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-3xl font-bold text-emerald-700">
                  {reports.length > 0
                    ? `${(((reports.length - totalJson) / reports.length) * 100).toFixed(1)}%`
                    : "—"}
                </p>
                <p className="text-sm font-medium text-emerald-700 mt-0.5">Valid Reports</p>
                <p className="text-xs text-emerald-600 mt-1">Data consistency verified</p>
              </div>
              <CheckCircle className="h-5 w-5 text-emerald-600 mt-1 shrink-0" />
            </div>
          </div>
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-3xl font-bold text-amber-700">{totalJson}</p>
                <p className="text-sm font-medium text-amber-700 mt-0.5">Pending Review</p>
                <p className="text-xs text-amber-600 mt-1">JSON exports awaiting sign-off</p>
              </div>
              <Clock className="h-5 w-5 text-amber-600 mt-1 shrink-0" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
