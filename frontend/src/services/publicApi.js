import { http } from "./http";

export async function submitReport({ narrative, attachments }) {
  const formData = new FormData();
  formData.append("narrative", narrative);
  for (const file of attachments || []) {
    formData.append("attachments", file);
  }

  const { data } = await http.post("/v1/reports/submit", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return data;
}

export async function getReportStatus(ticketId, pin) {
  const { data } = await http.get(`/v1/reports/${encodeURIComponent(ticketId)}/status`, {
    params: { pin },
  });
  return data;
}

export async function replyFollowup(ticketId, payload) {
  const { data } = await http.post(`/v1/reports/${encodeURIComponent(ticketId)}/reply`, payload);
  return data;
}
