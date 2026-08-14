"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { formatLabel } from "@/lib/utils";

export function CampaignExecutionWorkspace() {
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const list = useQuery({ queryKey: ["campaigns"], queryFn: () => beaconApi.campaigns({ limit: 200 }) });
  const mode = useQuery({ queryKey: ["communication-mode"], queryFn: beaconApi.communicationMode });

  const selected = useMemo(
    () => (list.data?.campaigns ?? []).find((item) => item.id === selectedId) ?? null,
    [list.data, selectedId],
  );

  const [toAddress, setToAddress] = useState("prospect@sandbox.example");

  const approveAndSend = useMutation({
    mutationFn: async () => {
      if (!selected) throw new Error("Select a campaign");
      if (selected.status !== "approved" && selected.status !== "scheduled") {
        await beaconApi.campaignApprove(selected.id, { actor: "founder", notes: "Sprint 18A approve before send" });
      }
      return beaconApi.communicationExecuteCampaign(selected.id, {
        to_address: toAddress,
        subject: selected.steps?.[0]?.subject_preview || `${selected.company_name} outreach`,
        body_text: selected.steps?.[0]?.body_preview || `Personalized outreach for ${selected.company_name}`,
        channel: selected.primary_channel === "whatsapp" ? "whatsapp" : "email",
        company_id: selected.company_id,
        opportunity_id: selected.opportunity_id,
        simulate_reply: true,
        force_sandbox: true,
        actor: "founder",
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["campaigns"] });
      await queryClient.invalidateQueries({ queryKey: ["inbox"] });
      await queryClient.invalidateQueries({ queryKey: ["founder-os"] });
    },
  });

  const sandboxSend = useMutation({
    mutationFn: async () => {
      if (!selected) throw new Error("Select a campaign");
      return beaconApi.communicationSandboxSend({
        channel: selected.primary_channel === "whatsapp" ? "whatsapp" : "email",
        to_address: toAddress,
        subject: selected.steps?.[0]?.subject_preview || `${selected.company_name} outreach`,
        body_text: selected.steps?.[0]?.body_preview || "Sandbox campaign execution",
        campaign_id: selected.id,
        company_id: selected.company_id,
        opportunity_id: selected.opportunity_id,
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["campaigns"] });
      await queryClient.invalidateQueries({ queryKey: ["inbox"] });
    },
  });

  const stop = useMutation({
    mutationFn: async () => {
      if (!selected) throw new Error("Select a campaign");
      return beaconApi.communicationStopCampaign(selected.id, { reason: "manual_stop", actor: "operator" });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["campaigns"] });
    },
  });

  if (list.isLoading) return <Skeleton className="h-64 w-full" />;
  if (list.isError) {
    return <ErrorState description="Campaign execution APIs unavailable." onRetry={() => void list.refetch()} />;
  }

  const campaigns = list.data?.campaigns ?? [];

  return (
    <div className="space-y-6">
      <div>
        <SectionLabel>Execution</SectionLabel>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Campaign Execution</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Founder-approved personalized email via Communication Gateway — sandbox by default, Gmail OAuth when
          production send is explicitly enabled.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Gateway gate</CardTitle>
          <CardDescription>
            Mode {mode.data?.mode ?? "…"} · Sandbox {mode.data?.sandbox ? "on" : "off"} · Production send{" "}
            {mode.data?.allow_production_send ? "enabled" : "disabled"}
          </CardDescription>
        </CardHeader>
      </Card>

      <div className="grid gap-4 lg:grid-cols-[360px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Campaigns</CardTitle>
            <CardDescription>{campaigns.length} plans</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {campaigns.length === 0 ? (
              <EmptyState title="No campaigns" description="Create and approve a campaign first." />
            ) : (
              campaigns.map((campaign) => (
                <button
                  key={campaign.id}
                  type="button"
                  onClick={() => setSelectedId(campaign.id)}
                  className={`w-full rounded-lg border px-3 py-3 text-left ${
                    selectedId === campaign.id ? "border-primary/50 bg-primary/10" : "border-border/60"
                  }`}
                >
                  <p className="text-sm font-medium">{campaign.company_name}</p>
                  <div className="mt-1 flex flex-wrap gap-2">
                    <Badge className="bg-muted text-muted-foreground ring-border">
                      {formatLabel(campaign.status)}
                    </Badge>
                    <Badge className="bg-muted text-muted-foreground ring-border">{campaign.primary_channel}</Badge>
                  </div>
                </button>
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Execute</CardTitle>
            <CardDescription>Founder-approved send → Inbox/Conversation Center on reply</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {!selected ? (
              <EmptyState title="Select a campaign" description="Choose an approved plan to send." />
            ) : (
              <>
                <p className="text-sm text-muted-foreground">{selected.channel_choice_reason}</p>
                <p className="text-sm">{selected.steps?.[0]?.body_preview || "No step preview"}</p>
                <label className="block text-xs text-muted-foreground">
                  Recipient
                  <input
                    className="mt-1 w-full rounded-md border border-border/60 bg-transparent px-3 py-2 text-sm"
                    value={toAddress}
                    onChange={(e) => setToAddress(e.target.value)}
                  />
                </label>
                <div className="flex flex-wrap gap-2">
                  <Button onClick={() => approveAndSend.mutate()} disabled={approveAndSend.isPending}>
                    {approveAndSend.isPending ? "Sending…" : "Approve & send"}
                  </Button>
                  <Button variant="outline" onClick={() => sandboxSend.mutate()} disabled={sandboxSend.isPending}>
                    Sandbox only
                  </Button>
                  <Button variant="outline" onClick={() => stop.mutate()} disabled={stop.isPending}>
                    Manual stop
                  </Button>
                </div>
                {selected.status !== "approved" && selected.status !== "scheduled" ? (
                  <p className="text-xs text-amber-400">Campaign will be approved automatically before send.</p>
                ) : null}
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
