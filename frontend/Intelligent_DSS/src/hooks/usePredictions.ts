import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { predictionService } from "@/services/prediction.service";
import type { ScreeningData } from "@/types/patient.types";

export function usePrediction(id: string) {
  return useQuery({
    queryKey: ["prediction", id],
    queryFn: () => predictionService.get(id),
    enabled: !!id,
  });
}

export function usePredictionByVisit(visitId: string) {
  return useQuery({
    queryKey: ["prediction-visit", visitId],
    queryFn: () => predictionService.getByVisit(visitId),
    enabled: !!visitId,
  });
}

export function useRunPrediction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { patient_id: string; visit_id?: string; screening_data?: ScreeningData }) =>
      predictionService.predict(data),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ["prediction-visit", vars.visit_id] });
    },
  });
}
