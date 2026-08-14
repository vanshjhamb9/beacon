"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";

export function ApprovalCenterWorkspace() {
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState<string[]>([]);

  const queue = useQuery({
    queryKey: ["lre-approval-center"],
    queryFn: () => beaconApi.liveRevenueApprovalCenter(),
  });

  const approve = useMutation({
    mutationFn: (id: string) => beaconApi.campaignApprove(id, { actor: "founder", notes: "approval_center" }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["lre-approval-center"] });
    },
  });
  const reject = useMutation({
    mutationFn: (id: string) => beaconApi.campaignReject(id, { actor: "founder", notes: "approval_center" }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["lre-approval-center"] });
    },
  });
  const bulkApprove = useMutation({
    mutationFn: (ids: string[]) => beaconApi.campaignBulkApprove(ids),
    onSuccess: async () => {
      setSelected([]);
      await queryClient.invalidateQueries({ queryKey: ["lre-approval-center"] });
    },
  });
  const bulkReject = useMutation({
    mutationFn: (ids: string[]) => beaconApi.campaignBulkReject(ids),
    onSuccess: async () => {
      setSelected([]);
      await queryClient.invalidateQueries({ queryKey: ["lre-approval-center"] });
    },
  });

  const cards = useMemo(() => queue.data?.cards ?? [], [queue.data]);

  if (queue.isLoading) return <Skeleton className="h-72 w-full" />;
  if (queue.isError) {
    return <ErrorState description="Approval center unavailable." onRetry={() => void queue.refetch()} />;
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <SectionLabel>Live Revenue Execution</SectionLabel>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Founder Approval Center</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
            Review company, decision maker, pain, email/WhatsApp preview, risk, then approve or reject. Nothing sends without you.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            disabled={!selected.length || bulkReject.isPending}
            onClick={() => bulkReject.mutate(selected)}
          >
            Bulk reject ({selected.length})
          </Button>
          <Button disabled={!selected.length || bulkApprove.isPending} onClick={() => bulkApprove.mutate(selected)}>
            Bulk approve ({selected.length})
          </Button>
        </div>
      </header>

      {cards.length === 0 ? (
        <EmptyState title="No campaigns awaiting approval" description="Create campaigns from Sales Copilot packages first." />
      ) : (
        <div className="space-y-4">
          {cards.map((card) => {
            const id = String(card.campaign_id);
            const email = (card.email_preview ?? {}) as Record<string, unknown>;
            const wa = (card.whatsapp_preview ?? {}) as Record<string, unknown>;
            const checked = selected.includes(id);
            return (
              <Card key={id}>
                <CardHeader className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() =>
                          setSelected((prev) => (checked ? prev.filter((x) => x !== id) : [...prev, id]))
                        }
                      />
                      <CardTitle className="font-display text-xl">{String(card.company_name)}</CardTitle>
                      <Badge>{String(card.priority)}</Badge>
                      <Badge variant="outline">Risk {String(card.risk_score)}</Badge>
                      <Badge variant="outline">Prob {String(card.probability)}</Badge>
                    </div>
                    <CardDescription>
                      DM: {String((card.decision_maker as Record<string, unknown>)?.name ?? "Unknown")} ·{" "}
                      {String((card.decision_maker as Record<string, unknown>)?.title ?? "")}
                    </CardDescription>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button variant="outline" disabled={reject.isPending} onClick={() => reject.mutate(id)}>
                      Reject
                    </Button>
                    <Button disabled={approve.isPending} onClick={() => approve.mutate(id)}>
                      Approve
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="grid gap-4 lg:grid-cols-2">
                  <div>
                    <p className="mb-2 text-xs uppercase tracking-wide text-muted-foreground">Pain points</p>
                    <ul className="space-y-1 text-sm text-muted-foreground">
                      {(card.pain_points as string[] | undefined)?.slice(0, 5).map((p) => (
                        <li key={p}>• {p}</li>
                      )) ?? <li>• None</li>}
                    </ul>
                    <p className="mb-2 mt-4 text-xs uppercase tracking-wide text-muted-foreground">Email preview</p>
                    <p className="text-sm font-medium">{String(email.subject ?? "—")}</p>
                    <p className="mt-1 whitespace-pre-wrap text-sm text-muted-foreground">
                      {String(email.body_text ?? "").slice(0, 420)}
                    </p>
                  </div>
                  <div>
                    <p className="mb-2 text-xs uppercase tracking-wide text-muted-foreground">WhatsApp preview</p>
                    <p className="whitespace-pre-wrap text-sm text-muted-foreground">
                      {String(wa.body_text ?? "No WhatsApp plan")}
                    </p>
                    <p className="mb-2 mt-4 text-xs uppercase tracking-wide text-muted-foreground">Calendly</p>
                    <p className="text-sm text-muted-foreground">{String(card.calendly_preview ?? "—")}</p>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
