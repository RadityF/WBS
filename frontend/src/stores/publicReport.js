import { defineStore } from "pinia";
import { getReportStatus, replyFollowup, submitReport } from "../services/publicApi";
import { extractApiError } from "../services/http";

export const usePublicReportStore = defineStore("public-report", {
  state: () => ({
    submitLoading: false,
    submitError: "",
    submitResult: null,

    statusLoading: false,
    statusError: "",
    statusResult: null,

    replyLoading: false,
    replyError: "",
    replyMessage: "",

    sessionTicketId: "",
    sessionPin: "",
  }),
  actions: {
    setSession(ticketId, pin) {
      this.sessionTicketId = ticketId || "";
      this.sessionPin = pin || "";
    },
    clearSession() {
      this.sessionTicketId = "";
      this.sessionPin = "";
    },
    async submit(payload) {
      this.submitLoading = true;
      this.submitError = "";
      this.submitResult = null;
      try {
        const data = await submitReport(payload);
        this.submitResult = data;
        this.setSession(data.ticket_id, data.pin);
        return data;
      } catch (error) {
        this.submitError = extractApiError(error, "Gagal submit laporan");
        return null;
      } finally {
        this.submitLoading = false;
      }
    },
    async fetchStatus(ticketId, pin) {
      this.statusLoading = true;
      this.statusError = "";
      this.statusResult = null;
      try {
        const data = await getReportStatus(ticketId, pin);
        this.statusResult = data;
        this.setSession(ticketId, pin);
        return data;
      } catch (error) {
        this.statusError = extractApiError(error, "Gagal mengambil status laporan");
        return null;
      } finally {
        this.statusLoading = false;
      }
    },
    async sendReply(ticketId, pin, message) {
      this.replyLoading = true;
      this.replyError = "";
      this.replyMessage = "";
      try {
        const data = await replyFollowup(ticketId, { pin, message });
        this.replyMessage = data.message || "Balasan terkirim";
        return data;
      } catch (error) {
        this.replyError = extractApiError(error, "Gagal mengirim balasan");
        return null;
      } finally {
        this.replyLoading = false;
      }
    },
  },
});
