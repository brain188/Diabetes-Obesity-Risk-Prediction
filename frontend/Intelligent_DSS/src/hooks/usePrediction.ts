import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { predictionService } from "@/services/prediction.service";
import type { PredictionRequest } from "@/types/prediction.types";

export function usePredict() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: PredictionRequest) => predictionService.predict(data),
    onSuccess: (result) => {
      qc.setQueryData(["prediction", result.prediction_id], result);
    },
  });
}

export function usePrediction(id: string) {
  return useQuery({
    queryKey: ["prediction", id],
    queryFn: () => predictionService.get(id),
    enabled: !!id,
  });
}

export function useExplanations(predictionId: string) {
  return useQuery({
    queryKey: ["explanations", predictionId],
    queryFn: () => predictionService.getExplanations(predictionId),
    enabled: !!predictionId,
  });
}

export function usePredictionHistory(patientId: string) {
  return useQuery({
    queryKey: ["prediction-history", patientId],
    queryFn: () => predictionService.getHistory(patientId),
    enabled: !!patientId,
  });
}
