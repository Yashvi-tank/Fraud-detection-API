import { create } from "zustand";
import { apiClient } from "@/lib/api-client";

interface UserProfile {
  id: string;
  username: string;
  created_at: string;
}

interface AuthState {
  token: string | null;
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  register: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  loadUser: () => Promise<void>;
  loginAsDemo: () => Promise<boolean>;
  clearError: () => void;
}

export const useAuth = create<AuthState>((set, get) => ({
  token: typeof window !== "undefined" ? localStorage.getItem("fraud_access_token") : null,
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  clearError: () => set({ error: null }),

  login: async (username, password) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.post("/auth/login", { username, password });
      const { access_token } = response.data;
      
      localStorage.setItem("fraud_access_token", access_token);
      set({ token: access_token, isAuthenticated: true });
      
      // Fetch profile
      await get().loadUser();
      set({ isLoading: false });
      return true;
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      const errMsg = axiosErr.response?.data?.detail || "Login failed. Please verify credentials.";
      set({ error: errMsg, isLoading: false, isAuthenticated: false, token: null });
      return false;
    }
  },

  register: async (username, password) => {
    set({ isLoading: true, error: null });
    try {
      await apiClient.post("/auth/register", { username, password });
      set({ isLoading: false });
      return true;
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      const errMsg = axiosErr.response?.data?.detail || "Registration failed. Username may already exist.";
      set({ error: errMsg, isLoading: false });
      return false;
    }
  },

  logout: () => {
    localStorage.removeItem("fraud_access_token");
    set({ token: null, user: null, isAuthenticated: false, error: null });
  },

  loadUser: async () => {
    const token = get().token;
    if (!token) return;

    set({ isLoading: true });
    try {
      const response = await apiClient.get("/auth/me");
      set({ user: response.data, isAuthenticated: true, isLoading: false });
    } catch {
      // Token invalid or expired — clear session
      localStorage.removeItem("fraud_access_token");
      set({ token: null, user: null, isAuthenticated: false, isLoading: false });
    }
  },

  loginAsDemo: async () => {
    // Try demo auto-login credentials
    return get().login("demo", "demo-password");
  },
}));
