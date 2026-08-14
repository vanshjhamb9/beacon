import type { HTMLAttributes, ReactNode } from "react";
import { AlertCircle, Inbox } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function EmptyState({
  title,
  description,
  action,
  className,
}: {
  title: string;
  description: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-border/80 bg-card/40 px-6 py-16 text-center",
        className,
      )}
    >
      <div className="rounded-full bg-muted p-3 text-muted-foreground">
        <Inbox className="h-5 w-5" />
      </div>
      <div className="space-y-1">
        <h3 className="font-display text-base font-semibold">{title}</h3>
        <p className="max-w-md text-sm text-muted-foreground">{description}</p>
      </div>
      {action}
    </div>
  );
}

export function ErrorState({
  title = "Something went wrong",
  description,
  onRetry,
  className,
}: {
  title?: string;
  description: string;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 rounded-xl border border-rose-500/20 bg-rose-500/5 px-6 py-12 text-center",
        className,
      )}
      role="alert"
    >
      <AlertCircle className="h-5 w-5 text-rose-300" />
      <div className="space-y-1">
        <h3 className="font-display text-base font-semibold text-rose-100">{title}</h3>
        <p className="max-w-md text-sm text-rose-100/70">{description}</p>
      </div>
      {onRetry ? (
        <Button variant="outline" size="sm" onClick={onRetry}>
          Try again
        </Button>
      ) : null}
    </div>
  );
}

export function SectionLabel({ children, className, ...props }: HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={cn("text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground", className)} {...props}>
      {children}
    </p>
  );
}
