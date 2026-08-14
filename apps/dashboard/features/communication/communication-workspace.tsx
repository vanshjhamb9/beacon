"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";

export function CommunicationWorkspace() {
  const queryClient = useQueryClient();
  const [toAddress, setToAddress] = useState("prospect@sandbox.example");
  const [subject, setSubject] = useState("Beacon sandbox outreach");
  const [body, setBody] = useState("Hello from Beacon sandbox.");
  const [reply, setReply] = useState("Thanks — interested in a meeting.");
  const [lastResult, setLastResult] = useState<Record<string, unknown> | null>(null);

  const mode = useQuery({ queryKey: ["communication-mode"], queryFn: beaconApi.communicationMode });
  const queues = useQuery({ queryKey: ["communication-queues"], queryFn: beaconApi.communicationQueues });

  const send = useMutation({
    mutationFn: () =>
      beaconApi.communicationSandboxSend({
        channel: "email",
        to_address: toAddress,
        subject,
        body_text: body,
        simulated_reply: reply,
      }),
    onSuccess: async (data) => {
      setLastResult(data);
      await queryClient.invalidateQueries({ queryKey: ["inbox"] });
      await queryClient.invalidateQueries({ queryKey: ["communication-queues"] });
    },
  });

  const meeting = useMutation({
    mutationFn: () =>
      beaconApi.communicationSandboxMeeting({
        title: "Sandbox discovery",
        attendees: [toAddress],
      }),
    onSuccess: async (data) => {
      setLastResult(data);
      await queryClient.invalidateQueries({ queryKey: ["inbox"] });
    },
  });

  if (mode.isLoading || queues.isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }
  if (mode.isError && queues.isError) {
    return (
      <ErrorState
        description="Communication Gateway unavailable."
        onRetry={() => {
          void mode.refetch();
          void queues.refetch();
        }}
      />
    );
  }

  const depths = queues.data?.depths ?? {};

  return (
    <div className="space-y-6">
      <div>
        <SectionLabel>Communication Gateway</SectionLabel>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Communication</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Sandbox-first providers for email, WhatsApp, and calendar. Production send stays disabled until
          explicitly enabled.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Mode</CardTitle>
            <CardDescription>Runtime send gate</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <Badge>{mode.data?.mode ?? "unknown"}</Badge>
            <p className="text-sm text-muted-foreground">
              Sandbox: {mode.data?.sandbox ? "active" : "off"} · Production send:{" "}
              {mode.data?.allow_production_send ? "allowed" : "blocked"}
            </p>
          </CardContent>
        </Card>
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Queue depths</CardTitle>
            <CardDescription>Outgoing, retry, delayed, dead letter, priority, worker</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {Object.entries(depths).map(([name, depth]) => (
              <Badge key={name} className="bg-muted text-muted-foreground ring-border">
                {name}: {depth}
              </Badge>
            ))}
            <Badge className="bg-muted text-muted-foreground ring-border">
              Stopped campaigns: {queues.data?.stopped_campaigns ?? 0}
            </Badge>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Sandbox send</CardTitle>
          <CardDescription>Simulates delivery, reply, and campaign stop rules without production providers</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Input value={toAddress} onChange={(event) => setToAddress(event.target.value)} placeholder="To" />
          <Input value={subject} onChange={(event) => setSubject(event.target.value)} placeholder="Subject" />
          <Input value={body} onChange={(event) => setBody(event.target.value)} placeholder="Body" />
          <Input value={reply} onChange={(event) => setReply(event.target.value)} placeholder="Simulated reply" />
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => send.mutate()} disabled={send.isPending}>
              {send.isPending ? "Sending…" : "Sandbox send + reply"}
            </Button>
            <Button variant="outline" onClick={() => meeting.mutate()} disabled={meeting.isPending}>
              {meeting.isPending ? "Booking…" : "Sandbox meeting"}
            </Button>
          </div>
          {lastResult ? (
            <pre className="overflow-auto rounded-lg bg-muted/40 p-3 text-xs">
              {JSON.stringify(lastResult, null, 2)}
            </pre>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
