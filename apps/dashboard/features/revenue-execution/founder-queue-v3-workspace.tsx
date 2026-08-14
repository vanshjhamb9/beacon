"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { formatScore } from "@/lib/utils";

function Field({ label, value }: { label: string; value: unknown }) {
  const text = value == null || value === "" || value === "UNKNOWN" ? null : String(value);
  if (!text) return null;
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="font-medium">{text}</p>
    </div>
  );
}

export function FounderQueueV3Workspace() {
  const queue = useQuery({
    queryKey: ["rev-founder-queue-v3"],
    queryFn: () => beaconApi.revFounderQueue(),
    refetchInterval: 60_000,
  });
  const acceptance = useQuery({
    queryKey: ["rev-acceptance"],
    queryFn: () => beaconApi.revAcceptance(),
    refetchInterval: 60_000,
  });

  if (queue.isError) {
    return <ErrorState title="Founder Queue unavailable" description="API /revenue-execution-validation/founder-queue failed." />;
  }

  const items = ((queue.data?.items as Array<Record<string, unknown>>) || []) as Array<Record<string, unknown>>;
  const locked = !acceptance.data?.production_unlocked;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <SectionLabel>Top 10 only</SectionLabel>
        <h1 className="text-2xl font-semibold tracking-tight">Founder Queue</h1>
        <p className="text-sm text-muted-foreground">
          Revenue Ready companies you can contact today. Send is {locked ? "LOCKED" : "unlocked"}.
        </p>
      </div>

      {queue.isLoading && <Skeleton className="h-40 w-full" />}

      {!queue.isLoading && items.length === 0 && (
        <Card>
          <CardContent className="py-8 text-sm text-muted-foreground">
            No Revenue Ready companies yet. Production outreach stays locked.
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4">
        {items.slice(0, 10).map((card, idx) => {
          const email = String(card.verified_email || "");
          const canSend = !locked && Boolean(email) && email !== "UNKNOWN";
          return (
            <Card key={`${card.company_id}-${idx}`} className="border-border/70">
              <CardHeader className="pb-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <SectionLabel>#{idx + 1}</SectionLabel>
                    <CardTitle className="text-xl">{String(card.company)}</CardTitle>
                  </div>
                  <Badge variant="outline">
                    Reply {formatScore(Math.min(95, Number(card.confidence || 0) * 0.85), 0)}%
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="grid gap-3 text-sm sm:grid-cols-2">
                <Field label="Why today" value={card.why_now} />
                <Field label="Buyer" value={card.decision_maker} />
                <Field label="Email" value={email} />
                <Field label="Service" value={card.service_match} />
                <div className="sm:col-span-2">
                  <p className="text-xs text-muted-foreground">Evidence</p>
                  <p className="text-muted-foreground">
                    {Array.isArray(card.evidence) ? (card.evidence as string[]).slice(0, 6).join(" · ") : "—"}
                  </p>
                </div>
                <div className="sm:col-span-2 flex flex-wrap gap-2">
                  <Button asChild variant="outline" size="sm">
                    <Link href={String(card.dossier_url || `/companies/${card.company_id}`)}>Open company</Link>
                  </Button>
                  <Button size="sm" disabled={!canSend}>
                    {locked ? "Send Email (LOCKED)" : "Send Email"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
