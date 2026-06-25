import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { patientService } from "@/services/patient.service";

export function usePatients(params?: { name?: string; page?: number }) {
  return useQuery({
    queryKey: ["patients", params],
    queryFn: () => patientService.list(params),
  });
}

export function usePatient(id: string) {
  return useQuery({
    queryKey: ["patient", id],
    queryFn: () => patientService.get(id),
    enabled: !!id,
  });
}

export function useCreatePatient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: patientService.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["patients"] }),
  });
}

export function usePatientHistory(id: string) {
  return useQuery({
    queryKey: ["patient-history", id],
    queryFn: () => patientService.history(id),
    enabled: !!id,
  });
}
