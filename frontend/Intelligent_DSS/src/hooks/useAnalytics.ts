import { useQuery } from "@tanstack/react-query";
import { analyticsService } from "@/services/analytics.service";
import type { DashboardStats, RiskDistribution } from "@/types/analytics.types";

export function useDashboardStats() {
  return useQuery<DashboardStats>({
    queryKey: ["analytics", "dashboard"],
    queryFn: analyticsService.dashboard,
    staleTime: 1000 * 60 * 2,
  });
}

export function useRiskDistribution() {
  return useQuery<{ distribution: RiskDistribution }>({
    queryKey: ["analytics", "risk-distribution"],
    queryFn: analyticsService.riskDistribution,
    staleTime: 1000 * 60 * 5,
  });
}

export function usePredictionsSummary() {
  return useQuery({
    queryKey: ["analytics", "predictions-summary"],
    queryFn: analyticsService.predictionsSummary,
    staleTime: 1000 * 60 * 5,
  });
}

export function useFeatureImportance() {
  return useQuery({
    queryKey: ["analytics", "feature-importance"],
    queryFn: analyticsService.featureImportance,
    staleTime: 1000 * 60 * 30,
  });
}

export function useMonthlyTrends(months = 6) {
  return useQuery({
    queryKey: ["analytics", "monthly-trends", months],
    queryFn: () => analyticsService.monthlyTrends(months),
    staleTime: 1000 * 60 * 10,
  });
}

export function useRecentActivities(limit = 10) {
  return useQuery({
    queryKey: ["analytics", "recent-activities", limit],
    queryFn: () => analyticsService.recentActivities(limit),
    staleTime: 1000 * 60 * 2,
  });
}
