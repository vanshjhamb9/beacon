"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { formatDateTime } from "@/lib/utils";

export function InboxWorkspace() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const threads = useQuery({ queryKey: ["inbox"], queryFn: () => beaconApi.inbox(100) });
  const timeline = useQuery({
    queryKey: ["inbox", selectedId],
    queryFn: () => beaconApi.inboxConversation(selectedId!),
    enabled: Boolean(selectedId),
  });

  if (threads.isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }
  if (threads.isError) {
    return <ErrorState description="Inbox unavailable." onRetry={() => void threads.refetch()} />;
  }

  const rows = threads.data ?? [];

  return (
    <div className="space-y-6">
      <div>
        <SectionLabel>Conversation Center</SectionLabel>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Inbox</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Email, WhatsApp, and meeting timelines with unread and AI summaries.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Threads</CardTitle>
            <CardDescription>{rows.length} conversations</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {rows.length === 0 ? (
              <EmptyState title="No conversations yet" description="Sandbox sends populate the inbox." />
            ) : (
              rows.map((thread) => (
                <button
                  key={thread.id}
                  type="button"
                  onClick={() => setSelectedId(thread.id)}
                  className={`w-full rounded-lg border px-3 py-3 text-left transition ${
                    selectedId === thread.id ? "border-primary/50 bg-primary/10" : "border-border/60 hover:bg-muted/40"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <p className="truncate text-sm font-medium">{thread.subject}</p>
                    {thread.unread_count > 0 ? <Badge>{thread.unread_count}</Badge> : null}
                  </div>
                  <p className="mt-1 truncate text-xs text-muted-foreground">
                    {thread.ai_summary || thread.channels.join(", ")}
                  </p>
                  <p className="mt-1 text-[11px] text-muted-foreground">
                    {thread.last_activity_at ? formatDateTime(thread.last_activity_at) : "—"}
                  </p>
                </button>
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Timeline</CardTitle>
            <CardDescription>Messages, replies, notes, and meetings</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {!selectedId ? (
              <EmptyState title="Select a thread" description="Choose a conversation to inspect the timeline." />
            ) : timeline.isLoading ? (
              <Skeleton className="h-40 w-full" />
            ) : (
              (timeline.data ?? []).map((item) => (
                <div key={item.id} className="rounded-lg border border-border/60 px-3 py-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge className="bg-muted text-muted-foreground ring-border">{item.channel}</Badge>
                    <Badge className="bg-muted text-muted-foreground ring-border">{item.item_type}</Badge>
                    <Badge className="bg-muted text-muted-foreground ring-border">{item.direction}</Badge>
                    {item.unread ? <Badge>Unread</Badge> : null}
                  </div>
                  {item.subject ? <p className="mt-2 text-sm font-medium">{item.subject}</p> : null}
                  <p className="mt-1 whitespace-pre-wrap text-sm text-muted-foreground">{item.body}</p>
                  <p className="mt-2 text-[11px] text-muted-foreground">{formatDateTime(item.occurred_at)}</p>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
