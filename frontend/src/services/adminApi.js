import { http } from "./http";

export async function adminLogin(payload) {
  const { data } = await http.post("/v1/admin/login", payload);
  return data;
}

export async function getAdminCases(status = "") {
  const { data } = await http.get("/v1/admin/cases", {
    params: status ? { status } : undefined,
  });
  return data;
}

export async function getAdminCaseDetail(ticketId) {
  const { data } = await http.get(`/v1/admin/cases/${encodeURIComponent(ticketId)}`);
  return data;
}

export async function updateAdminCaseStatus(ticketId, payload) {
  const { data } = await http.post(`/v1/admin/cases/${encodeURIComponent(ticketId)}/status`, payload);
  return data;
}

export async function triggerKbReindex() {
  const { data } = await http.post("/v1/kb/reindex");
  return data;
}
