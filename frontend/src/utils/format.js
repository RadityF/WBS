function parseDateValue(value) {
  if (!value) return null;
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value;
  if (typeof value === "number") {
    const dateFromNumber = new Date(value);
    return Number.isNaN(dateFromNumber.getTime()) ? null : dateFromNumber;
  }

  const raw = String(value).trim();
  if (!raw) return null;

  const normalized = raw.includes(" ") ? raw.replace(" ", "T") : raw;
  const hasTimezone = /(?:Z|[+-]\d{2}:\d{2})$/i.test(normalized);
  if (hasTimezone) {
    const dateWithTimezone = new Date(normalized);
    return Number.isNaN(dateWithTimezone.getTime()) ? null : dateWithTimezone;
  }

  const naiveIso = normalized.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2})(?:\.(\d+))?)?$/);
  if (naiveIso) {
    const year = Number(naiveIso[1]);
    const month = Number(naiveIso[2]) - 1;
    const day = Number(naiveIso[3]);
    const hour = Number(naiveIso[4]);
    const minute = Number(naiveIso[5]);
    const second = Number(naiveIso[6] || "0");
    const millis = Number((naiveIso[7] || "").slice(0, 3).padEnd(3, "0"));
    return new Date(Date.UTC(year, month, day, hour, minute, second, millis));
  }

  const utcFallback = new Date(`${normalized}Z`);
  if (!Number.isNaN(utcFallback.getTime())) return utcFallback;

  const localFallback = new Date(normalized);
  return Number.isNaN(localFallback.getTime()) ? null : localFallback;
}

export function formatDate(value) {
  if (!value) return "-";
  const date = parseDateValue(value);
  if (!date) return String(value);
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
