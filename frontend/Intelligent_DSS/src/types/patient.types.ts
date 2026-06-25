export type Sex = "Male" | "Female";
export type Residence = "Urban" | "Rural";
export type BmiCategory = "Normal" | "Overweight" | "Obese I" | "Obese II+";

export interface Patient {
  patient_id: string;
  full_name: string;
  date_of_birth: string;
  sex: Sex;
  contact_info?: string;
  national_id?: string;
  is_active: boolean;
  worker_id: string;
  last_visit_date?: string;
  created_at: string;
  updated_at: string;
}

export interface ScreeningData {
  weight: number;
  height: number;
  bmi: number;
  bmi_category: BmiCategory;
  physical_activity: boolean;
  family_history_diabetes: boolean;
  previous_gdm: boolean;
  has_hypertension: boolean;
  residence: Residence;
  is_pregnant: boolean;
}

export interface ScreeningVisit {
  visit_id: string;
  patient_id: string;
  visit_date: string;
  notes?: string;
  screening_data?: ScreeningData;
}
