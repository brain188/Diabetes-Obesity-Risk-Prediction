import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { authService } from "@/services/auth.service";
import { useAuthStore } from "@/store/auth.store";

export function useLogin() {
  const { setAuth } = useAuthStore();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: authService.login,
    onSuccess: (response) => {
      setAuth(response.user, response.access_token);
      navigate(response.user.role === "admin" ? "/admin/dashboard" : "/dashboard");
    },
  });
}

export function useRegister() {
  const navigate = useNavigate();

  return useMutation({
    mutationFn: authService.register,
    onSuccess: () => {
      toast.success("Account created! Please sign in.");
      navigate("/login");
    },
  });
}

export function useLogout() {
  const { clearAuth } = useAuthStore();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: authService.logout,
    onSettled: () => {
      clearAuth();
      navigate("/login");
    },
  });
}

export function useCurrentUser() {
  const { accessToken } = useAuthStore();
  return useQuery({
    queryKey: ["me"],
    queryFn: authService.me,
    enabled: !!accessToken,
  });
}
