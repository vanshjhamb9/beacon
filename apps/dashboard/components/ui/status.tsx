import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export type StatusTone = "ready" | "info" | "attention" | "blocked" | "inactive";

const TONE_CLASS: Record<StatusTone, string> = {
  ready: "bg-status-ready/15 text-status-ready ring-status-ready/30",
  info: "bg-status-info/15 text-status-info ring-status-info/30",
  attention: "bg-status-attention/15 text-status-attention ring-status-attention/30",
  blocked: "bg-status-blocked/15 text-status-blocked ring-status-blocked/30",
  inactive: "bg-status-inactive/15 text-status-inactive ring-status-inactive/30",
};

const DOT_CLASS: Record<StatusTone, string> = {
  ready: "bg-status-ready",
  info: "bg-status-info",
  attention: "bg-status-attention",
  blocked: "bg-status-blocked",
  inactive: "bg-status-inactive",
};

export function statusFromLabel(label: string | null | undefined): StatusTone {
  const value = (label || "").toLowerCase();
  if (/(ready|won|connected|executing|verified|sent)/.test(value)) return "ready";
  if (/(reply|meeting|contacted|negotiation|info|draft)/.test(value)) return "info";
  if (/(attention|planning|pending|review|needs)/.test(value)) return "attention";
  if (/(blocked|lost|error|offline|failed)/.test(value)) return "blocked";
  return "inactive";
}

export function StatusBadge({
  tone,
  children,
  className,
}: {
  tone: StatusTone;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset",
        TONE_CLASS[tone],
        className,
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", DOT_CLASS[tone])} />
      {children}
    </span>
  );
}
