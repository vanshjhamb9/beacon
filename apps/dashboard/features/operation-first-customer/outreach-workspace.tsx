"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { formatScore } from "@/lib/utils";

const STATUSES = [
  "READY",
  "CONTACTED",
  "REPLIED",
  "MEETING_BOOKED",
  "PROPOSAL_SENT",
  "NEGOTIATION",
  "WON",
  "LOST",
  "PAUSED",
] as const;

const OBJECTIONS = [
  "No Budget",
  "Already using competitor",
  "No Reply",
  "Wrong Contact",
  "Not Priority",
  "Interested",
  "Meeting Scheduled",
] as const;

const TIMELINE_EVENTS = [
  "Email sent",
  "Reply received",
  "Meeting booked",
  "Follow-up",
  "Proposal",
  "Won",
  "Lost",
] as const;

export function OutreachWorkspace() {
  const qc = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [note, setNote] = useState("");

  const workspace = useQuery({
    queryKey: ["ofc-workspace"],
    queryFn: () => beaconApi.ofcWorkspace(),
    refetchInterval: 60_000,
  });

  const detail = useQuery({
    queryKey: ["ofc-record", selectedId],
    queryFn: () => beaconApi.ofcRecord(selectedId!),
    enabled: Boolean(selectedId),
  });

  const sync = useMutation({
    mutationFn: () => beaconApi.ofcSync(),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["ofc-workspace"] }),
  });

  const transition = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => beaconApi.ofcTransition(id, status),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["ofc-workspace"] });
      void qc.invalidateQueries({ queryKey: ["ofc-record", selectedId] });
    },
  });

  const addNote = useMutation({
    mutationFn: ({ id, text }: { id: string; text: string }) => beaconApi.ofcNote(id, text),
    onSuccess: () => {
      setNote("");
      void qc.invalidateQueries({ queryKey: ["ofc-record", selectedId] });
    },
  });

  const objection = useMutation({
    mutationFn: ({ id, label }: { id: string; label: string }) => beaconApi.ofcObjection(id, label),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["ofc-record", selectedId] }),
  });

  const timeline = useMutation({
    mutationFn: ({ id, event_type }: { id: string; event_type: string }) =>
      beaconApi.ofcTimeline(id, event_type),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["ofc-record", selectedId] }),
  });

  const items = useMemo(
    () => ((workspace.data?.items as Array<Record<string, unknown>>) || []) as Array<Record<string, unknown>>,
    [workspace.data],
  );
  const today = (workspace.data?.today_action || {}) as Record<string, unknown>;
  const selected = items.find((i) => String(i.id) === selectedId) || null;
  const brief = ((selected?.brief || (detail.data as { record?: { brief?: Record<string, unknown> } })?.record?.brief || {}) as Record<string, unknown>);
  const timelineRows = ((detail.data as { timeline?: Array<Record<string, unknown>> })?.timeline || []) as Array<
    Record<string, unknown>
  >;
  const notes = ((detail.data as { notes?: Array<Record<string, unknown>> })?.notes || []) as Array<
    Record<string, unknown>
  >;

  if (workspace.isError) {
    return <ErrorState title="Outreach Workspace unavailable" description="API /first-customer/workspace failed." />;
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <SectionLabel>OFC v2 · Operation First Customer</SectionLabel>
          <h1 className="text-2xl font-semibold tracking-tight">Outreach Workspace</h1>
          <p className="text-sm text-muted-foreground">
            Revenue Ready → outreach records. Manual founder control. No GPT. No auto-scoring.
          </p>
        </div>
        <Button onClick={() => sync.mutate()} disabled={sync.isPending}>
          {sync.isPending ? "Syncing…" : "Sync Revenue Ready"}
        </Button>
      </div>

      <Card className="border-emerald-700/40 bg-emerald-950/20">
        <CardHeader className="pb-2">
          <SectionLabel>Morning question</SectionLabel>
          <CardTitle className="text-lg">What should Vansh do today to close the next customer?</CardTitle>
        </CardHeader>
        <CardContent className="space-y-1 text-sm">
          <p className="text-base font-medium">{String(today.action || "Sync Revenue Ready companies to start.")}</p>
          <p className="text-muted-foreground">{String(today.why || "")}</p>
          {today.channel ? (
            <p>
              <span className="text-muted-foreground">Channel · </span>
              {String(today.channel)}
            </p>
          ) : null}
        </CardContent>
      </Card>

      {workspace.isLoading && <Skeleton className="h-40 w-full" />}

      <div className="grid gap-4 lg:grid-cols-[1fr_1.2fr]">
        <div className="space-y-3">
          {items.map((item) => (
            <Card
              key={String(item.id)}
              className={selectedId === String(item.id) ? "ring-2 ring-emerald-600" : "cursor-pointer"}
              onClick={() => setSelectedId(String(item.id))}
            >
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between gap-2">
                  <CardTitle className="text-lg">{String(item.company)}</CardTitle>
                  <Badge variant="outline">{String(item.status)}</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-1 text-sm text-muted-foreground">
                <p>{String((item.brief as Record<string, unknown>)?.why_now || "—")}</p>
                <p>
                  {(item.brief as Record<string, unknown>)?.recommended_service as string} · $
                  {formatScore(Number(item.pipeline_value || 0), 0)}
                </p>
              </CardContent>
            </Card>
          ))}
          {!workspace.isLoading && items.length === 0 && (
            <Card>
              <CardContent className="py-8 text-sm text-muted-foreground">
                No outreach records yet. Click Sync Revenue Ready.
              </CardContent>
            </Card>
          )}
        </div>

        <div className="space-y-4">
          {!selected && (
            <Card>
              <CardContent className="py-10 text-sm text-muted-foreground">
                Select a company to open the Outreach Brief, timeline, notes, and objections.
              </CardContent>
            </Card>
          )}

          {selected && (
            <>
              <Card>
                <CardHeader className="pb-2">
                  <SectionLabel>Outreach Brief</SectionLabel>
                  <CardTitle>{String(selected.company)}</CardTitle>
                </CardHeader>
                <CardContent className="grid gap-1 text-sm">
                  <Row label="Website" value={brief.website} />
                  <Row label="Industry" value={brief.industry} />
                  <Row label="Decision Maker" value={brief.decision_maker} />
                  <Row label="DM Email" value={brief.decision_maker_email} />
                  <Row label="Business Email" value={brief.business_email} />
                  <Row label="Why Now" value={brief.why_now} />
                  <Row label="Service" value={brief.recommended_service} />
                  <Row label="CTA" value={brief.recommended_cta} />
                  <Row
                    label="Score"
                    value={`Conf ${formatScore(Number(brief.confidence || 0), 0)} · Trust ${formatScore(Number(brief.trust || 0), 0)} · RR ${formatScore(Number(brief.revenue_ready_score || 0), 0)}`}
                  />
                  <Row
                    label="Pain"
                    value={(Array.isArray(brief.pain_points) ? brief.pain_points : []).join(" · ") || "—"}
                  />
                  <Row
                    label="Evidence"
                    value={(Array.isArray(brief.evidence) ? brief.evidence : []).slice(0, 4).join(" · ") || "—"}
                  />
                  {brief.first_message_template ? (
                    <p className="mt-2 rounded-md bg-muted/50 p-3 text-xs leading-relaxed">
                      {String(brief.first_message_template)}
                    </p>
                  ) : null}
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">Status</CardTitle>
                </CardHeader>
                <CardContent className="flex flex-wrap gap-2">
                  {STATUSES.map((status) => (
                    <Button
                      key={status}
                      size="sm"
                      variant={String(selected.status) === status ? "default" : "outline"}
                      disabled={transition.isPending}
                      onClick={() => transition.mutate({ id: String(selected.id), status })}
                    >
                      {status}
                    </Button>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">Conversation Timeline</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex flex-wrap gap-2">
                    {TIMELINE_EVENTS.map((event_type) => (
                      <Button
                        key={event_type}
                        size="sm"
                        variant="outline"
                        disabled={timeline.isPending}
                        onClick={() => timeline.mutate({ id: String(selected.id), event_type })}
                      >
                        {event_type}
                      </Button>
                    ))}
                  </div>
                  <div className="space-y-2 text-sm">
                    {timelineRows.map((row) => (
                      <div key={String(row.id)} className="border-l-2 border-muted pl-3">
                        <p className="font-medium">{String(row.event_type)}</p>
                        <p className="text-xs text-muted-foreground">{String(row.created_at || "")}</p>
                      </div>
                    ))}
                    {timelineRows.length === 0 && (
                      <p className="text-muted-foreground">Append-only timeline is empty.</p>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">Founder Notes</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <textarea
                    className="min-h-20 w-full rounded-md border bg-background p-2 text-sm"
                    placeholder="Interested · Budget next quarter · Asked for demo…"
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                  />
                  <Button
                    size="sm"
                    disabled={!note.trim() || addNote.isPending}
                    onClick={() => addNote.mutate({ id: String(selected.id), text: note })}
                  >
                    Save note
                  </Button>
                  <div className="space-y-2 text-sm">
                    {notes.map((n) => (
                      <p key={String(n.id)} className="rounded-md bg-muted/40 p-2">
                        {String(n.note)}
                      </p>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">Objection Analytics</CardTitle>
                </CardHeader>
                <CardContent className="flex flex-wrap gap-2">
                  {OBJECTIONS.map((label) => (
                    <Button
                      key={label}
                      size="sm"
                      variant="outline"
                      disabled={objection.isPending}
                      onClick={() => objection.mutate({ id: String(selected.id), label })}
                    >
                      {label}
                    </Button>
                  ))}
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: unknown }) {
  return (
    <p>
      <span className="text-muted-foreground">{label} · </span>
      {String(value || "—")}
    </p>
  );
}
