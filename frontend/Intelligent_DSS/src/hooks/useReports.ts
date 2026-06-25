import { useMutation, useQuery } from "@tanstack/react-query";
import { reportService } from "@/services/report.service";
import type { ReportListItem } from "@/services/report.service";

export function useAllReports(page = 1, pageSize = 50) {
  return useQuery<ReportListItem[]>({
    queryKey: ["reports", "all", page, pageSize],
    queryFn: () => reportService.listAll(page, pageSize),
    staleTime: 1000 * 60,
  });
}

export function useReport(reportId: string) {
  return useQuery({
    queryKey: ["report", reportId],
    queryFn: () => reportService.get(reportId),
    enabled: !!reportId,
  });
}

export function useGenerateReport() {
  return useMutation({
    mutationFn: (visitId: string) => reportService.generate(visitId),
  });
}

export function useDownloadReport() {
  return useMutation({
    mutationFn: async (reportId: string) => {
      const blob = await reportService.download(reportId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `report-${reportId}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    },
  });
}
