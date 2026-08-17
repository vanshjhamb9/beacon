"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  CheckCircle,
  Clock,
  MessageSquare,
  RefreshCw,
  Send,
  XCircle,
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { cn } from "@/lib/utils";

type Campaign = {
  id: string;
  company_id?: string;
  company_name?: string;
  email?: string;
  status?: string;
  channel?: string;
  subject?: string;
  body?: string;
  created_at?: string;
  sent_at?: string;
  intent_score?: number;
  grade?: string;
  department?: string;
};

export function OutreachWorkspace() {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<"all" | "pending" | "sent" | "replied">("all");
  const [deptFilter, setDeptFilter] = useState<"all" | "comai" | "inowix" | "cyber">("all");

  const { data, isLoading } = useQuery({
    queryKey: ["workspace-outreach"],
    queryFn: () => beaconApi.workspaceOutreach(100),
    refetchInterval: 20_000,
  });

  const syncMutation = useMutation({
    mutationFn: () => beaconApi.workspaceSync(),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["workspace-outreach"] });
      void queryClient.invalidateQueries({ queryKey: ["workspace-overview"] });
    },
  });

  const approveMutation = useMutation({
    mutationFn: (campaignId: string) => beaconApi.workspaceApproveOutreach(campaignId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["workspace-outreach"] });
      void queryClient.invalidateQueries({ queryKey: ["workspace-leads"] });
      void queryClient.invalidateQueries({ queryKey: ["workspace-overview"] });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: (campaignId: string) => beaconApi.workspaceRejectOutreach(campaignId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["workspace-outreach"] });
      void queryClient.invalidateQueries({ queryKey: ["workspace-leads"] });
    },
  });

  const campaigns = (data?.campaigns || []) as Campaign[];
  const stats = [
    { label: "Pending", value: String(data?.pending || 0), icon: Clock, color: "text-yellow-500" },
    { label: "Sent", value: String(data?.sent || 0), icon: Send, color: "text-blue-500" },
    { label: "Delivered", value: String(data?.delivered || 0), icon: CheckCircle, color: "text-green-500" },
    { label: "Replied", value: String(data?.replied || 0), icon: MessageSquare, color: "text-purple-500" },
    { label: "Bounced", value: String(data?.bounced || 0), icon: XCircle, color: "text-red-500" },
  ];

  const filteredCampaigns = campaigns.filter((c) => {
    if (filter === "pending") {
      if (c.status !== "pending" && c.status !== "draft") return false;
    } else if (filter === "sent") {
      if (c.status !== "sent" && c.status !== "delivered") return false;
    } else if (filter === "replied") {
      if (c.status !== "replied") return false;
    }
    if (deptFilter === "all") return true;
    const dept = String(c.department || "").toLowerCase();
    if (deptFilter === "cyber") return dept.includes("cyber");
    if (deptFilter === "inowix") return dept.startsWith("inowix");
    return dept.startsWith("comai");
  });

  if (isLoading) return <Skeleton className="h-96 w-full" />;

  return (
    <div className="mx-auto max-w-[1400px] space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-semibold">Outreach</h1>
          <p className="text-sm text-muted-foreground">
            Lead Engine + Cyber queue — approve drafts here. Sending is still a separate confirm.
          </p>
        </div>
        <Button variant="outline" onClick={() => syncMutation.mutate()} disabled={syncMutation.isPending}>
          <RefreshCw className={cn("mr-2 h-4 w-4", syncMutation.isPending && "animate-spin")} />
          Refresh Queue
        </Button>
      </div>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {stats.map((stat, idx) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 * idx, duration: 0.3 }}
          >
            <Card className="border-border/60 bg-card/60">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">{stat.label}</p>
                    <p className="mt-1 font-display text-2xl font-semibold">{stat.value}</p>
                  </div>
                  <stat.icon className={cn("h-6 w-6 opacity-50", stat.color)} />
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </section>

      <div className="flex gap-2">
        {(["all", "pending", "sent", "replied"] as const).map((f) => (
          <Button key={f} variant={filter === f ? "default" : "outline"} size="sm" onClick={() => setFilter(f)}>
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </Button>
        ))}
        {(["all", "comai", "inowix", "cyber"] as const).map((d) => (
          <Button key={d} variant={deptFilter === d ? "default" : "outline"} size="sm" onClick={() => setDeptFilter(d)}>
            {d === "all" ? "All lanes" : d.toUpperCase()}
          </Button>
        ))}
      </div>

      <Card>
        <CardContent className="p-0">
          {filteredCampaigns.length === 0 ? (
            <div className="p-8 text-center">
              <Send className="mx-auto h-12 w-12 text-muted-foreground/50" />
              <p className="mt-4 text-muted-foreground">
                No outreach items yet. Run Lead Engine, then Refresh Queue.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-border/50">
              {filteredCampaigns.map((campaign, idx) => (
                <motion.div
                  key={campaign.id || idx}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.02 * idx }}
                  className="flex items-center gap-4 px-4 py-3 hover:bg-muted/20"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <Link
                        href={`/leads/${campaign.company_id}`}
                        className="font-medium hover:text-primary"
                      >
                        {campaign.company_name || "Unknown"}
                      </Link>
                      <span
                        className={cn(
                          "rounded-full px-2 py-0.5 text-xs font-medium",
                          campaign.status === "sent" || campaign.status === "delivered"
                            ? "bg-blue-500/10 text-blue-500"
                            : campaign.status === "replied"
                              ? "bg-purple-500/10 text-purple-500"
                              : "bg-yellow-500/10 text-yellow-500"
                        )}
                      >
                        {campaign.status || "pending"}
                      </span>
                      {!!campaign.grade && (
                        <span className="rounded-full bg-muted px-2 py-0.5 text-xs">{campaign.grade}</span>
                      )}
                    </div>
                    <p className="mt-1 truncate text-sm text-muted-foreground">
                      {campaign.subject || "Draft subject"}
                    </p>
                    <p className="mt-0.5 text-xs text-muted-foreground">{campaign.email}</p>
                  </div>
                  <div className="flex shrink-0 gap-2">
                    {(campaign.status === "pending" || campaign.status === "draft") && (
                      <>
                        <Button
                          size="sm"
                          onClick={() => approveMutation.mutate(campaign.id)}
                          disabled={approveMutation.isPending}
                        >
                          Approve / Sent
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => rejectMutation.mutate(campaign.id)}
                          disabled={rejectMutation.isPending}
                        >
                          Reject
                        </Button>
                      </>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
