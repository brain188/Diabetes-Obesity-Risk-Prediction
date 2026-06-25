import api from "@/lib/api";
import type { ScreeningData, ScreeningVisit } from "@/types/patient.types";

export const screeningService = {
  createVisit: (data: { patient_id: string; notes?: string }) =>
    api.post<ScreeningVisit>("/screening/visits", data).then((r) => r.data),

  saveData: (visitId: string, data: ScreeningData) =>
    api.post(`/screening/visits/${visitId}/data`, data).then((r) => r.data),

  getVisit: (visitId: string) =>
    api.get<ScreeningVisit>(`/screening/visits/${visitId}`).then((r) => r.data),
};
