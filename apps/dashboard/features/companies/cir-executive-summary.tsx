"use client";

import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { formatScore } from "@/lib/utils";

function Field({ label, value }: { label: string; value?: unknown }) {
  const display = value == null || value === "" || value === "UNKNOWN" ? "UNKNOWN" : String(value);
  return (
    <div>
      <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm font-medium leading-snug">{display}</p>
    </div>
  );
}

export function CirExecutiveSummary({ companyId }: { companyId: string }) {
  const cir = useQuery({
    queryKey: ["cir-company", companyId],
    queryFn: () => beaconApi.cirCompany(companyId),
    retry: false,
  });

  if (cir.isLoading) return <Skeleton className="h-72 w-full" />;
  const card = (cir.data?.founder_card || {}) as Record<string, unknown>;
  if (cir.isError || !cir.data || cir.data.status === "not_found") {
    return (
      <EmptyState
        title="Company intelligence not reconstructed"
        description="CIR runs only after EROWD admits a verified official website."
      />
    );
  }
  if (cir.data.status === "not_reconstructed" && !card.company) {
    return (
      <EmptyState
        title="Awaiting reconstruction"
        description="Worker company_intelligence.process_verified runs every 120 seconds."
      />
    );
  }

  const signals = Array.isArray(card.buying_signals) ? (card.buying_signals as string[]) : [];
  const dms = Array.isArray(card.decision_makers) ? (card.decision_makers as string[]) : [];
  const evidence = Array.isArray(card.evidence) ? (card.evidence as string[]) : [];
  const timeline = Array.isArray(card.timeline) ? (card.timeline as string[]) : [];

  return (
    <Card className="border-border/70 bg-card/80 shadow-soft">
      <CardHeader className="pb-3">
        <SectionLabel>Executive Summary</SectionLabel>
        <div className="flex flex-wrap items-center gap-2">
          <CardTitle className="text-xl">{String(card.company || "Company")}</CardTitle>
          <Badge>{String(card.revenue_readiness || "UNKNOWN")}</Badge>
          <Badge variant="outline">Score {formatScore(Number(card.readiness_score || 0), 0)}</Badge>
        </div>
        <CardDescription>One page. Evidence only. What you need before the first email.</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Field label="Industry" value={card.industry} />
        <Field label="Website" value={card.website} />
        <Field label="Country" value={card.country} />
        <Field label="Employees" value={card.employees} />
        <Field label="Primary Product" value={card.primary_product} />
        <Field label="Primary Opportunity" value={card.primary_opportunity} />
        <Field label="Best Service" value={card.best_service} />
        <Field label="Business Email" value={card.business_email} />
        <Field label="Phone" value={card.phone} />
        <div className="sm:col-span-2 lg:col-span-3">
          <Field label="Buying Signals" value={signals.length ? signals.join(" · ") : "UNKNOWN"} />
        </div>
        <div className="sm:col-span-2 lg:col-span-3">
          <Field label="Decision Makers" value={dms.length ? dms.join(" · ") : "UNKNOWN"} />
        </div>
        <div className="sm:col-span-2 lg:col-span-3">
          <Field label="Evidence" value={evidence.length ? evidence.slice(0, 8).join(" · ") : "UNKNOWN"} />
        </div>
        <div className="sm:col-span-2 lg:col-span-3">
          <Field label="Timeline" value={timeline.length ? timeline.slice(0, 5).join(" · ") : "UNKNOWN"} />
        </div>
        <div className="sm:col-span-2 lg:col-span-3">
          <Field label="Recommended Action" value={card.recommended_action} />
        </div>
      </CardContent>
    </Card>
  );
}
