import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Badge({
  className,
  tone,
  variant: _variant,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { tone?: string; variant?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset",
        tone === "ready" && "bg-status-ready/15 text-status-ready ring-status-ready/30",
        tone === "info" && "bg-status-info/15 text-status-info ring-status-info/30",
        tone === "attention" && "bg-status-attention/15 text-status-attention ring-status-attention/30",
        tone === "blocked" && "bg-status-blocked/15 text-status-blocked ring-status-blocked/30",
        className,
      )}
      {...props}
    />
  );
}
