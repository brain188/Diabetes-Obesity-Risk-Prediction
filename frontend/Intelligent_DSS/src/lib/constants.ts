export const RISK_COLORS = {
  Low: "text-emerald-600 bg-emerald-50 border-emerald-200",
  Moderate: "text-amber-600 bg-amber-50 border-amber-200",
  High: "text-red-600 bg-red-50 border-red-200",
} as const;

export const PRIORITY_COLORS = {
  Urgent: "destructive",
  High: "destructive",
  Medium: "default",
  Low: "secondary",
} as const;

export const FEATURE_LABELS: Record<string, string> = {
  age: "Age",
  sex: "Sex",
  is_pregnant: "Pregnancy",
  bmi: "BMI",
  bmi_category: "BMI Category",
  family_history_diabetes: "Family History",
  previous_gdm: "Previous GDM",
  physically_active: "Physical Activity",
  has_hypertension: "Hypertension",
  residence: "Residence",
};

export const PAGE_SIZE = 10;
