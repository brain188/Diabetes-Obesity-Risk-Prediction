import api from "@/lib/api";
import type {
  PredictionResponse,
  PredictionRequest,
  CombinedExplanationResponse,
} from "@/types/prediction.types";

export const predictionService = {
  predict: (data: PredictionRequest) =>
    api.post<PredictionResponse>("/predictions/", data).then((r) => r.data),

  get: (id: string) =>
    api.get<PredictionResponse>(`/predictions/${id}`).then((r) => r.data),

  getExplanations: (id: string) =>
    api.get<CombinedExplanationResponse>(`/predictions/${id}/explanations`).then((r) => r.data),

  getHistory: (patientId: string, limit = 10) =>
    api
      .get<PredictionResponse[]>(`/predictions/patients/${patientId}/history`, { params: { limit } })
      .then((r) => r.data),
};
