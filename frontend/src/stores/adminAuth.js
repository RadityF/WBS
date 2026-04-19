import { defineStore } from "pinia";
import { adminLogin } from "../services/adminApi";
import { extractApiError, TOKEN_KEY } from "../services/http";

export const useAdminAuthStore = defineStore("admin-auth", {
  state: () => ({
    token: "",
    initialized: false,
    loading: false,
    error: "",
    username: "",
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token),
  },
  actions: {
    initialize() {
      if (this.initialized) return;
      const saved = localStorage.getItem(TOKEN_KEY);
      if (saved) {
        this.token = saved;
      }
      this.initialized = true;
    },
    async login(payload) {
      this.loading = true;
      this.error = "";
      try {
        const data = await adminLogin(payload);
        this.token = data.access_token;
        this.username = payload.username;
        localStorage.setItem(TOKEN_KEY, this.token);
        return true;
      } catch (error) {
        this.error = extractApiError(error, "Gagal login admin");
        return false;
      } finally {
        this.loading = false;
      }
    },
    logout() {
      this.token = "";
      this.username = "";
      localStorage.removeItem(TOKEN_KEY);
    },
    handleUnauthorized() {
      this.logout();
      this.error = "Sesi habis. Silakan login kembali.";
    },
  },
});
