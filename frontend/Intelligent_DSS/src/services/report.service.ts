import api from "@/lib/api";

export interface Report {
  report_id: string;
  visit_id: string;
  patient_id: string;
  generated_at: string;
  file_url: string;
}

export interface ReportListItem {
  report_id: string;
  visit_id: string;
  format: string;
  generated_at: string;
  download_count: string;
  file_size_bytes: string | null;
  patient_id: string;
  patient_name: string;
  patient_sex: string;
}

export const reportService = {
  generate: (visitId: string) =>
    api.post<Report>("/reports/generate", { visit_id: visitId }).then((r) => r.data),

  get: (reportId: string) =>
    api.get<Report>(`/reports/${reportId}`).then((r) => r.data),

  getByVisit: (visitId: string) =>
    api.get<Report>(`/reports/visit/${visitId}`).then((r) => r.data),

  listAll: (page = 1, page_size = 50) =>
    api.get<ReportListItem[]>(`/reports/?page=${page}&page_size=${page_size}`).then((r) => r.data),

  download: (reportId: string) =>
    api.get(`/reports/${reportId}/download`, { responseType: "blob" }).then((r) => r.data),

  delete: (reportId: string) =>
    api.delete(`/reports/${reportId}`).then((r) => r.data),
};
