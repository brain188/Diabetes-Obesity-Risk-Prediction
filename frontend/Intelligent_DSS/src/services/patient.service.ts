import api from "@/lib/api";
import type { Patient, ScreeningVisit } from "@/types/patient.types";
import type { PaginatedResponse } from "@/types/api.types";

export const patientService = {
  list: (params?: { name?: string; page?: number; page_size?: number }) =>
    api.get<PaginatedResponse<Patient>>("/patients", { params }).then((r) => r.data),

  get: (id: string) => api.get<Patient>(`/patients/${id}`).then((r) => r.data),

  create: (data: Partial<Patient>) =>
    api.post<Patient>("/patients", data).then((r) => r.data),

  update: (id: string, data: Partial<Patient>) =>
    api.put<Patient>(`/patients/${id}`, data).then((r) => r.data),

  remove: (id: string) => api.delete(`/patients/${id}`).then((r) => r.data),

  history: (id: string) =>
    api.get<{ items: ScreeningVisit[]; total: number }>(`/screening/patients/${id}/visits`).then((r) => r.data.items),
};
