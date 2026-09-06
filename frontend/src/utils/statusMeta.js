export const STATUS_COLORS = {
  NEW: { border: "border-ink/40", text: "text-ink" },
  PENDING: { border: "border-marigold-dark", text: "text-marigold-dark" },
  ASSIGNED: { border: "border-module-schools", text: "text-module-schools" },
  IN_PROGRESS: { border: "border-module-traffic", text: "text-module-traffic" },
  RESOLVED: { border: "border-stamp-teal", text: "text-stamp-teal" },
  REJECTED: { border: "border-stamp-red", text: "text-stamp-red" },
  ESCALATED: { border: "border-stamp-red", text: "text-stamp-red" },
  REQUIRES_ADMIN_REVIEW: { border: "border-ink-faint", text: "text-ink-faint" },
};

export const PRIORITY_COLORS = {
  LOW: "bg-ink/10 text-ink-soft",
  MEDIUM: "bg-marigold/20 text-marigold-dark",
  HIGH: "bg-module-traffic/20 text-module-traffic",
  CRITICAL: "bg-stamp-red/15 text-stamp-red",
};

export const MODULE_COLORS = {
  GOVERNMENT_SCHOOLS: "#2F5FA8",
  AGRICULTURE: "#3F7D3B",
  HEALTHCARE: "#B23A2E",
  TRAFFIC: "#C97A1E",
};

export const MODULE_LABEL_KEYS = {
  GOVERNMENT_SCHOOLS: "schools",
  AGRICULTURE: "agriculture",
  HEALTHCARE: "healthcare",
  TRAFFIC: "traffic",
};

// Hex equivalents of the status/priority Tailwind tokens, for Recharts fills
// (Recharts needs literal color values, not utility classes).
export const STATUS_HEX = {
  NEW: "#1B2A4A",
  PENDING: "#C4832A",
  ASSIGNED: "#2F5FA8",
  IN_PROGRESS: "#C97A1E",
  RESOLVED: "#2F6F62",
  REJECTED: "#B23A2E",
  ESCALATED: "#8B2E24",
  REQUIRES_ADMIN_REVIEW: "#7C86A0",
};

export const PRIORITY_HEX = {
  LOW: "#7C86A0",
  MEDIUM: "#E8A33D",
  HIGH: "#C97A1E",
  CRITICAL: "#B23A2E",
};

export const CATEGORICAL_PALETTE = ["#1B2A4A", "#E8A33D", "#2F6F62", "#B23A2E", "#2F5FA8", "#3F7D3B", "#C97A1E", "#7C86A0"];
