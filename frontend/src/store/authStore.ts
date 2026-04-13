import { create } from "zustand";
import axios from "axios";

interface UserProfile {
  id: string;
  email: string;
  fullName: string;
  role: string;
  organization: string | null;
}

interface AuthState {
  user: UserProfile | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshAccessToken: () => Promise<void>;
  setUser: (user: UserProfile) => void;
}

const API_URL = import.meta.env.VITE_API_URL || "/api/v1";

// Restore user profile from sessionStorage (NOT tokens)
const savedUser = (() => {
  try {
    const raw = sessionStorage.getItem("regulatorai_user");
    return raw ? (JSON.parse(raw) as UserProfile) : null;
  } catch {
    return null;
  }
})();

export const useAuthStore = create<AuthState>((set, get) => ({
  user: savedUser,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,

  login: async (email: string, password: string) => {
    const response = await axios.post(`${API_URL}/auth/login`, { email, password });
    const { access_token, refresh_token } = response.data as {
      access_token: string;
      refresh_token: string;
    };

    // Fetch user profile
    const profileResp = await axios.get(`${API_URL}/users/me`, {
      headers: { Authorization: `Bearer ${access_token}` },
    });
    const user = profileResp.data as UserProfile;

    sessionStorage.setItem("regulatorai_user", JSON.stringify(user));

    set({
      accessToken: access_token,
      refreshToken: refresh_token,
      user,
      isAuthenticated: true,
    });
  },

  logout: () => {
    const { refreshToken } = get();
    if (refreshToken) {
      axios
        .post(`${API_URL}/auth/logout`, { refresh_token: refreshToken })
        .catch(() => {});
    }
    sessionStorage.removeItem("regulatorai_user");
    set({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
    });
  },

  refreshAccessToken: async () => {
    const { refreshToken } = get();
    if (!refreshToken) throw new Error("No refresh token");

    const response = await axios.post(`${API_URL}/auth/refresh`, {
      refresh_token: refreshToken,
    });
    const { access_token, refresh_token } = response.data as {
      access_token: string;
      refresh_token: string;
    };

    set({ accessToken: access_token, refreshToken: refresh_token });
  },

  setUser: (user: UserProfile) => {
    sessionStorage.setItem("regulatorai_user", JSON.stringify(user));
    set({ user });
  },
}));
