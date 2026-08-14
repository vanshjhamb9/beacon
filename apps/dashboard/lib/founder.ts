import { API_BASE_URL } from "@/lib/api/client";

export const FOUNDER_NAME = "Vansh";

export function greetingForNow(date = new Date()): string {
  const hour = date.getHours();
  if (hour < 12) return "Good Morning";
  if (hour < 17) return "Good Afternoon";
  return "Good Evening";
}

export function gmailConnectUrl(provider = "gmail"): string {
  return `${API_BASE_URL}/communication/oauth/authorize?provider=${encodeURIComponent(provider)}`;
}

export function pipelineColumn(status: string | null | undefined): string {
  const value = (status || "READY").toUpperCase();
  if (value === "READY" || value === "READY_TO_SEND") return "Ready";
  if (value === "CONTACTED") return "Contacted";
  if (value.includes("REPL")) return "Replied";
  if (value.includes("MEETING")) return "Meeting";
  if (value.includes("NEGOT") || value.includes("PROPOSAL")) return "Negotiation";
  if (value === "WON") return "Won";
  if (value === "LOST" || value === "PAUSED") return "Lost";
  return "Ready";
}

export const PIPELINE_COLUMNS = [
  "Ready",
  "Contacted",
  "Replied",
  "Meeting",
  "Negotiation",
  "Won",
  "Lost",
] as const;

export const PIPELINE_STATUS_MAP: Record<(typeof PIPELINE_COLUMNS)[number], string> = {
  Ready: "READY",
  Contacted: "CONTACTED",
  Replied: "REPLIED",
  Meeting: "MEETING_BOOKED",
  Negotiation: "NEGOTIATION",
  Won: "WON",
  Lost: "LOST",
};

export function outreachStep(status: string | null | undefined): number {
  const value = (status || "READY").toUpperCase();
  if (value === "READY" || value === "READY_TO_SEND") return 0;
  if (value === "CONTACTED") return 3;
  if (value.includes("REPL")) return 4;
  if (value.includes("MEETING") || value.includes("NEGOT") || value.includes("PROPOSAL")) return 4;
  if (value === "WON") return 5;
  return 1;
}

export const OUTREACH_STEPS = ["Prospect", "Review", "Approve", "Send", "Track", "Won"] as const;
