export interface DashboardStats {
  total_patients: number;
  active_patients?: number;
  total_screenings: number;
  total_predictions: number;
  total_reports: number;
  high_risk_count?: number;
  moderate_risk_count?: number;
  low_risk_count?: number;
}

export interface RiskDistribution {
  Low?: number;
  Moderate?: number;
  High?: number;
  low?: number;
  moderate?: number;
  high?: number;
}

export interface ActivityItem {
  id: string;
  type: "prediction_high" | "screening" | "report" | "patient";
  description: string;
  timestamp: string;
  patient_id?: string;
}
