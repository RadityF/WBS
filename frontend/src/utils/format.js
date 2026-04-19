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
  return String(status).replaceAll("_", " ");
}
