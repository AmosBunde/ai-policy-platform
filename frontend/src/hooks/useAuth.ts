import { useCallback, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { useAuthStore } from "../store/authStore";
import { api } from "../services/api";

interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
  organization?: string;
  role?: string;
}

interface LoginResult {
  redirectTo: string;
}

export function useLogin(returnUrl?: string) {
  const storeLogin = useAuthStore((s) => s.login);
  const navigate = useNavigate();

  return useMutation({
    mutationFn: async ({ email, password }: { email: string; password: string }): Promise<LoginResult> => {
      await storeLogin(email, password);
      return { redirectTo: returnUrl || "/" };
    },
    onSuccess: (data) => {
      navigate(data.redirectTo, { replace: true });
    },
  });
}

export function useRegister() {
  const navigate = useNavigate();

  return useMutation({
    mutationFn: async (payload: RegisterPayload) => {
      const response = await api.post("/auth/register", payload);
      return response.data;
    },
    onSuccess: () => {
      navigate("/login", { replace: true });
    },
  });
}

export function useLogout() {
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();

  return useCallback(() => {
    logout();
    navigate("/login", { replace: true });
  }, [logout, navigate]);
}

// Auto-refresh token before expiry (refresh every 25 minutes for a 30-min token)
const REFRESH_INTERVAL_MS = 25 * 60 * 1000;

export function useAutoRefresh() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const refreshAccessToken = useAuthStore((s) => s.refreshAccessToken);
  const logout = useAuthStore((s) => s.logout);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    intervalRef.current = setInterval(() => {
      refreshAccessToken().catch(() => {
        logout();
      });
    }, REFRESH_INTERVAL_MS);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isAuthenticated, refreshAccessToken, logout]);
}
