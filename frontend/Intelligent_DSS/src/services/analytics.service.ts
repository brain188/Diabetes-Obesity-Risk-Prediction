import api from "@/lib/api";

export const analyticsService = {
  dashboard: () => api.get("/analytics/stats/dashboard").then((r) => r.data),
  predictionsSummary: () => api.get("/analytics/predictions/summary").then((r) => r.data),
  demographics: () => api.get("/analytics/patients/demographics").then((r) => r.data),
  riskDistribution: () => api.get("/analytics/risk-distribution").then((r) => r.data),
  auditSummary: (days = 7) => api.get(`/analytics/audit/summary?days=${days}`).then((r) => r.data),
  recentActivities: (limit = 50) => api.get(`/analytics/audit/activities?limit=${limit}`).then((r) => r.data),
  modelInfo: () => api.get("/analytics/model/info").then((r) => r.data),
  featureImportance: () => api.get("/analytics/feature-importance").then((r) => r.data),
  monthlyTrends: (months = 6) => api.get(`/analytics/stats/trends?months=${months}`).then((r) => r.data),
};
