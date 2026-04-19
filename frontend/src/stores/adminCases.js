import { defineStore } from "pinia";
import { getAdminCaseDetail, getAdminCases, triggerKbReindex, updateAdminCaseStatus } from "../services/adminApi";
import { extractApiError } from "../services/http";
import { useAdminAuthStore } from "./adminAuth";

export const useAdminCasesStore = defineStore("admin-cases", {
  state: () => ({
    loadingList: false,
    listError: "",
    cases: [],
    selectedStatus: "",

    loadingDetail: false,
    detailError: "",
    detail: null,

    updateLoading: false,
    updateError: "",
    updateMessage: "",

    reindexLoading: false,
    reindexError: "",
    reindexResult: null,
  }),
  getters: {
    filteredCases(state) {
      if (!state.selectedStatus) return state.cases;
      return state.cases.filter((item) => item.status === state.selectedStatus);
    },
  },
  actions: {
    handleAuthError(error) {
      if (error?.response?.status === 401) {
        const auth = useAdminAuthStore();
        auth.handleUnauthorized();
      }
    },
    async fetchCases(status = "") {
      this.loadingList = true;
      this.listError = "";
      this.selectedStatus = status;
      try {
        const data = await getAdminCases(status);
        this.cases = data;
        return data;
      } catch (error) {
        this.handleAuthError(error);
        this.listError = extractApiError(error, "Gagal mengambil daftar kasus");
        return [];
      } finally {
        this.loadingList = false;
      }
    },
    async fetchCaseDetail(ticketId) {
      this.loadingDetail = true;
      this.detailError = "";
      this.updateMessage = "";
      try {
        const data = await getAdminCaseDetail(ticketId);
        this.detail = data;
        return data;
      } catch (error) {
        this.handleAuthError(error);
        this.detailError = extractApiError(error, "Gagal mengambil detail kasus");
        return null;
      } finally {
        this.loadingDetail = false;
      }
    },
    async updateStatus(ticketId, payload) {
      this.updateLoading = true;
      this.updateError = "";
      this.updateMessage = "";
      try {
        const data = await updateAdminCaseStatus(ticketId, payload);
        this.updateMessage = data.message || "Status diperbarui";
        return true;
      } catch (error) {
        this.handleAuthError(error);
        this.updateError = extractApiError(error, "Gagal memperbarui status");
        return false;
      } finally {
        this.updateLoading = false;
      }
    },
    async reindexKb() {
      this.reindexLoading = true;
      this.reindexError = "";
      try {
        const data = await triggerKbReindex();
        this.reindexResult = data;
        return data;
      } catch (error) {
        this.handleAuthError(error);
        this.reindexError = extractApiError(error, "Gagal reindex KB");
        return null;
      } finally {
        this.reindexLoading = false;
      }
    },
  },
});
