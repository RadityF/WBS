export function formatDate(value) {
  if (!value) return "-";
  const raw = String(value);
  const hasTimezone = /(?:Z|[+-]\d{2}:\d{2})$/.test(raw);
  const normalized = hasTimezone ? raw : `${raw}Z`;
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat("id-ID", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Jakarta",
  }).format(date);
}

export function statusClass(status) {
  if (!status) return "";
  return `status-${String(status).toLowerCase()}`;
}

export function statusLabel(status) {
  if (!status) return "-";
  const labels = {
    SUBMITTED: "Laporan diterima",
    AI_VALIDATED: "Terverifikasi awal",
    NEEDS_INFO: "Perlu klarifikasi",
    NEEDS_REVIEW: "Menunggu review admin",
    IN_REVIEW: "Sedang ditinjau",
    RESOLVED: "Selesai",
    ARCHIVE: "Diarsipkan",
    AUTO_RESOLVED: "Laporan ditutup",
    REOPENED: "Dibuka kembali",
  };
  return labels[status] || String(status).replaceAll("_", " ");
}
