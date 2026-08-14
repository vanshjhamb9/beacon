"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status";
import { beaconApi } from "@/lib/api/beacon";
import { cn, formatDateTime } from "@/lib/utils";

const CHANNELS = ["All", "Email", "WhatsApp", "LinkedIn"] as const;

export function ConversationsWorkspace() {
  const [channel, setChannel] = useState<(typeof CHANNELS)[number]>("All");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const threads = useQuery({ queryKey: ["inbox"], queryFn: () => beaconApi.inbox(100) });
  const timeline = useQuery({
    queryKey: ["inbox", selectedId],
    queryFn: () => beaconApi.inboxConversation(selectedId!),
    enabled: Boolean(selectedId),
  });

  const rows = useMemo(() => {
    const all = threads.data ?? [];
    if (channel === "All") return all;
    return all.filter((thread) =>
      thread.channels.some((item) => item.toLowerCase().includes(channel.toLowerCase())),
    );
  }, [channel, threads.data]);

  if (threads.isLoading) return <Skeleton className="h-72 w-full" />;
  if (threads.isError) {
    return <ErrorState description="Conversations unavailable." onRetry={() => void threads.refetch()} />;
  }

  return (
    <div className="space-y-5">
      <header className="space-y-2">
        <p className="text-sm text-muted-foreground">Unified inbox · Email, WhatsApp, LinkedIn</p>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Conversations</h1>
      </header>

      <div className="flex gap-2 overflow-x-auto scrollbar-thin">
        {CHANNELS.map((item) => (
          <button
            key={item}
            type="button"
            onClick={() => setChannel(item)}
            className={cn(
              "rounded-lg px-3 py-1.5 text-sm transition",
              channel === item ? "bg-primary/15 text-foreground" : "text-muted-foreground hover:bg-muted/40",
            )}
          >
            {item}
            {item === "LinkedIn" ? (
              <span className="ml-1 text-[10px] text-muted-foreground">Soon</span>
            ) : null}
          </button>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-[340px_1fr]">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Inbox</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {rows.length === 0 ? (
              <EmptyState title="No conversations" description="Replies will appear here after you send." />
            ) : (
              rows.map((thread) => (
                <button
                  key={thread.id}
                  type="button"
                  onClick={() => setSelectedId(thread.id)}
                  className={cn(
                    "w-full rounded-lg border px-3 py-3 text-left transition",
                    selectedId === thread.id ? "border-primary/40 bg-primary/10" : "border-border/60 hover:bg-muted/30",
                  )}
                >
                  <div className="flex items-center justify-between gap-2">
                    <p className="truncate text-sm font-medium">{thread.subject}</p>
                    {thread.unread_count > 0 ? <Badge className="bg-status-info/15 text-status-info ring-status-info/30">{thread.unread_count}</Badge> : null}
                  </div>
                  <p className="mt-1 truncate text-xs text-muted-foreground">
                    {thread.ai_summary || thread.channels.join(" · ")}
                  </p>
                </button>
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Thread</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {!selectedId ? (
              <EmptyState title="Select a conversation" description="Choose a thread to reply." />
            ) : timeline.isLoading ? (
              <Skeleton className="h-40 w-full" />
            ) : (
              (timeline.data ?? []).map((item) => (
                <div key={item.id} className="rounded-lg border border-border/60 px-3 py-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge tone="info">{item.channel}</StatusBadge>
                    <span className="text-[11px] text-muted-foreground">{formatDateTime(item.occurred_at)}</span>
                  </div>
                  {item.subject ? <p className="mt-2 text-sm font-medium">{item.subject}</p> : null}
                  <p className="mt-1 whitespace-pre-wrap text-sm text-muted-foreground">{item.body}</p>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
