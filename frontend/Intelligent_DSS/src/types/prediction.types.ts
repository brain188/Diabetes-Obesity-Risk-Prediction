export type RiskClass = "Low" | "Moderate" | "High";
export type DiabetesClassLabel = "Normal" | "Prediabetes" | "Diabetic";
export type Priority = "Urgent" | "High" | "Medium" | "Low";

export interface FeatureContribution {
  feature_name: string;
  value: number;
  shap_value: number;
  impact_direction: "Positive" | "Negative";
  importance_abs: number;
}

export interface SHAPExplanationResponse {
  explanation_id: string;
  prediction_id: string;
  base_value: number;
  final_probability: number;
  feature_contributions: FeatureContribution[];
  top_positive_features: FeatureContribution[];
  top_negative_features: FeatureContribution[];
}

export interface LIMEExplanationResponse {
  explanation_id: string;
  prediction_id: string;
  feature_contributions: FeatureContribution[];
  top_positive_features: FeatureContribution[];
  top_negative_features: FeatureContribution[];
}

export interface GlobalFeatureImportanceResponse {
  model_version: string;
  feature_importance: Record<string, number>;
  sorted_features: string[];
  updated_at: string;
}

export interface ClinicalGuidance {
  diabetes_guidance: string;
  obesity_guidance: string;
  patient_advice?: string;
}

export interface RecommendationResponse {
  recommendation_id: string;
  prediction_id: string;
  priority: Priority;
  action_text: string;
  patient_advice?: string | null;
  follow_up_interval_days?: number | null;
  referral_required?: string | null;
  clinical_guidance?: ClinicalGuidance | null;
}

export interface DiabetesPrediction {
  probability: number;
  risk_class: RiskClass;
  risk_color: string;
  class_label: DiabetesClassLabel;
}

export interface ObesityPrediction {
  bmi: number;
  bmi_category: string;
  risk_class: RiskClass;
  risk_color: string;
  obesity_class: string;
  probability?: number;
}

export interface PredictionResponse {
  prediction_id: string;
  visit_id: string;
  patient_id: string;
  diabetes: DiabetesPrediction;
  obesity: ObesityPrediction;
  model_version: string;
  prediction_date: string;
  latency_ms?: number | null;
  shap_explanation?: SHAPExplanationResponse | null;
  lime_explanation?: LIMEExplanationResponse | null;
  global_feature_importance?: GlobalFeatureImportanceResponse | null;
  recommendation?: RecommendationResponse | null;
}

export interface CombinedExplanationResponse {
  prediction_id: string;
  shap: SHAPExplanationResponse | null;
  lime: LIMEExplanationResponse | null;
  global_feature_importance: GlobalFeatureImportanceResponse | null;
}

export interface ScreeningDataRequest {
  weight: number;
  height: number;
  physical_activity: boolean;
  family_history_diabetes: boolean;
  previous_gdm: boolean;
  has_hypertension: boolean;
  is_pregnant: boolean;
  residence: "Urban" | "Rural";
  notes?: string;
}

export interface PredictionRequest {
  patient_id: string;
  visit_id?: string;
  screening_data?: ScreeningDataRequest;
}

export type PredictionResult = PredictionResponse;
