export function formatDate(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat("id-ID", {
    dateStyle: "medium",
    timeStyle: "short",
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
    AUTO_RESOLVED: "Dialihkan / bukan kategori WBS",
  };
  return labels[status] || String(status).replaceAll("_", " ");
}
