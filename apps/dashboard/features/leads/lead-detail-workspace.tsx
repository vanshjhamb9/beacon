"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Clock,
  Edit,
  ExternalLink,
  Mail,
  MessageSquare,
  RefreshCw,
  Send,
  Trash2,
  X,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { cn, formatScore } from "@/lib/utils";

type LeadDetail = {
  id?: string;
  company_id?: string;
  company_name?: string;
  company?: string;
  score?: number;
  intent_score?: number;
  confidence?: number;
  industry?: string;
  country?: string;
  city?: string;
  source?: string;
  source_url?: string;
  website?: string;
  why_now?: string;
  description?: string;
  requirement?: string;
  founder_name?: string;
  founder_title?: string;
  email?: string;
  phone?: string;
  status?: string;
  stage?: string;
  grade?: string;
  created_at?: string;
  subject?: string;
  body?: string;
  whatsapp_already?: boolean;
  strong_signals?: string[];
  contact_info?: Record<string, unknown>;
};

export function LeadDetailWorkspace({ leadId }: { leadId: string }) {
  const queryClient = useQueryClient();
  const [editingDraft, setEditingDraft] = useState(false);
  const [draftText, setDraftText] = useState("");
  const [draftSubject, setDraftSubject] = useState("");
  const [autoDraftTried, setAutoDraftTried] = useState(false);

  const { data: companyData, isLoading, refetch } = useQuery({
    queryKey: ["workspace-lead", leadId],
    queryFn: () => beaconApi.workspaceLead(leadId),
  });

  const leadData = (companyData || {}) as LeadDetail;
  const score = Number(leadData.intent_score || leadData.score || (leadData.confidence || 0) * 100);
  const email = leadData.email || String(leadData.contact_info?.email || "");
  const phone = leadData.phone || String(leadData.contact_info?.phone || leadData.contact_info?.whatsapp || "");
  const website = leadData.source_url || leadData.website || "";
  const localPart = email.includes("@") ? email.split("@")[0] : "";
  const brandInbox = ["care", "wecare", "hello", "hi", "info", "contact", "support", "help"].includes(localPart);
  const founderDisplay =
    leadData.founder_name ||
    (brandInbox ? "Brand inbox (no named founder found)" : "—");

  const draftMutation = useMutation({
    mutationFn: () => beaconApi.workspaceDraftLead(leadId),
    onSuccess: (res) => {
      setDraftSubject(String(res.subject || ""));
      setDraftText(String(res.body || ""));
      void queryClient.invalidateQueries({ queryKey: ["workspace-lead", leadId] });
      void queryClient.invalidateQueries({ queryKey: ["workspace-outreach"] });
    },
  });

  const transition = useMutation({
    mutationFn: (status: string) => beaconApi.workspaceSetStage(leadId, status),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["workspace-leads"] });
      void queryClient.invalidateQueries({ queryKey: ["workspace-lead", leadId] });
      void queryClient.invalidateQueries({ queryKey: ["workspace-overview"] });
      void queryClient.invalidateQueries({ queryKey: ["workspace-outreach"] });
      void refetch();
    },
  });

  const sendMutation = useMutation({
    mutationFn: () =>
      beaconApi.workspaceSendLead(leadId, {
        subject: draftSubject || undefined,
        body: (editingDraft ? draftText : draftText || leadData.body) || undefined,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["workspace-leads"] });
      void queryClient.invalidateQueries({ queryKey: ["workspace-lead", leadId] });
      void queryClient.invalidateQueries({ queryKey: ["workspace-overview"] });
      void queryClient.invalidateQueries({ queryKey: ["workspace-outreach"] });
      void refetch();
    },
  });

  // Seed draft fields from lead; auto-generate if missing
  useEffect(() => {
    if (!companyData) return;
    const sub = String(leadData.subject || "");
    const bod = String(leadData.body || "");
    if (sub && !draftSubject) setDraftSubject(sub);
    if (bod && !draftText) setDraftText(bod);
    if (!autoDraftTried && email && (!sub || !bod) && !draftMutation.isPending) {
      setAutoDraftTried(true);
      draftMutation.mutate();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [companyData, email]);

  if (isLoading) return <Skeleton className="h-96 w-full" />;

  const displaySubject = draftSubject || leadData.subject || "";
  const displayBody = draftText || leadData.body || "";

  return (
    <div className="mx-auto max-w-[1200px] space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <Link
            href="/leads"
            className="mb-2 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Leads
          </Link>
          <h1 className="font-display text-2xl font-semibold">
            {leadData.company_name || leadData.company || "Unknown Lead"}
          </h1>
          <div className="mt-2 flex flex-wrap items-center gap-3">
            {score > 0 && (
              <span
                className={cn(
                  "rounded-full px-3 py-1 text-sm font-medium",
                  score >= 90
                    ? "bg-green-500/10 text-green-500"
                    : score >= 70
                      ? "bg-yellow-500/10 text-yellow-500"
                      : "bg-muted text-muted-foreground"
                )}
              >
                Score: {formatScore(score, 0)}
              </span>
            )}
            {leadData.grade && (
              <span className="rounded-full bg-primary/10 px-3 py-1 text-sm text-primary">{leadData.grade}</span>
            )}
            {leadData.industry && (
              <span className="rounded-full bg-muted px-3 py-1 text-sm">{leadData.industry}</span>
            )}
            {(leadData.city || leadData.country) && (
              <span className="rounded-full bg-muted px-3 py-1 text-sm">
                {[leadData.city, leadData.country].filter(Boolean).join(", ")}
              </span>
            )}
            {leadData.source && (
              <span className="rounded-full bg-muted px-3 py-1 text-sm">{leadData.source}</span>
            )}
            {leadData.whatsapp_already && (
              <span className="rounded-full bg-orange-500/10 px-3 py-1 text-sm text-orange-400">
                WhatsApp already present
              </span>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => transition.mutate("contacted")} disabled={transition.isPending}>
            Move to Pipeline
          </Button>
          <Button variant="danger" onClick={() => transition.mutate("lost")} disabled={transition.isPending}>
            <Trash2 className="mr-2 h-4 w-4" />
            Reject
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_400px]">
        <div className="space-y-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Requirement</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed text-foreground/90">
                {leadData.requirement || leadData.why_now || leadData.description || "No requirement specified."}
              </p>
              {!!leadData.strong_signals?.length && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {leadData.strong_signals.map((s) => (
                    <span key={s} className="rounded bg-muted px-2 py-0.5 text-[11px] text-muted-foreground">
                      {s}
                    </span>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Founder</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Name</p>
                  <p className="mt-1 text-sm">{founderDisplay}</p>
                </div>
                <div>
                  <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Title</p>
                  <p className="mt-1 text-sm">{leadData.founder_title || (brandInbox ? "Brand inbox" : "Founder")}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-base">Draft Outreach</CardTitle>
              <div className="flex gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => draftMutation.mutate()}
                  disabled={draftMutation.isPending}
                >
                  <RefreshCw className={cn("mr-1 h-4 w-4", draftMutation.isPending && "animate-spin")} />
                  {draftMutation.isPending ? "Generating…" : "Generate"}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    if (editingDraft) setEditingDraft(false);
                    else {
                      setDraftText(displayBody);
                      setEditingDraft(true);
                    }
                  }}
                >
                  {editingDraft ? (
                    <>
                      <X className="mr-1 h-4 w-4" />
                      Cancel
                    </>
                  ) : (
                    <>
                      <Edit className="mr-1 h-4 w-4" />
                      Edit
                    </>
                  )}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {draftMutation.isPending && !displayBody ? (
                <Skeleton className="h-32 w-full" />
              ) : editingDraft ? (
                <div className="space-y-2">
                  <input
                    value={draftSubject}
                    onChange={(e) => setDraftSubject(e.target.value)}
                    placeholder="Subject"
                    className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm"
                  />
                  <textarea
                    value={draftText}
                    onChange={(e) => setDraftText(e.target.value)}
                    className="min-h-[200px] w-full rounded-lg border border-border bg-card p-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                  />
                </div>
              ) : (
                <div className="rounded-lg border border-border/60 bg-muted/20 p-4">
                  {displaySubject && (
                    <p className="mb-2 text-sm font-medium">Subject: {displaySubject}</p>
                  )}
                  <p className="whitespace-pre-wrap text-sm leading-relaxed">
                    {displayBody || "No draft yet — click Generate."}
                  </p>
                </div>
              )}

              <div className="flex flex-wrap gap-2">
                <Button
                  onClick={() => sendMutation.mutate()}
                  disabled={sendMutation.isPending || !email}
                >
                  <Send className="mr-2 h-4 w-4" />
                  {sendMutation.isPending ? "Sending…" : "Send Email"}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => website && window.open(website, "_blank")}
                  disabled={!website}
                >
                  <ExternalLink className="mr-2 h-4 w-4" />
                  Open Website
                </Button>
                <Button
                  variant="outline"
                  onClick={() =>
                    phone && window.open(`https://wa.me/${phone.replace(/[^0-9]/g, "")}`, "_blank")
                  }
                  disabled={!phone}
                >
                  <MessageSquare className="mr-2 h-4 w-4" />
                  Open WhatsApp
                </Button>
              </div>
              {sendMutation.isSuccess && (
                <p className="text-sm text-green-500">Marked as sent and moved to Contacted.</p>
              )}
              {sendMutation.isError && (
                <p className="text-sm text-red-500">{(sendMutation.error as Error)?.message || "Send failed"}</p>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Contact Channels</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center gap-3">
                <Mail className="h-4 w-4 text-muted-foreground" />
                <div className="min-w-0 flex-1">
                  <p className="text-sm">{email || "No email"}</p>
                  {email && <p className="text-[10px] text-muted-foreground">Email</p>}
                </div>
                {email && (
                  <Button size="icon" variant="ghost" className="h-8 w-8" asChild>
                    <a href={`mailto:${email}`}>
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  </Button>
                )}
              </div>

              {phone && (
                <div className="flex items-center gap-3">
                  <MessageSquare className="h-4 w-4 text-muted-foreground" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm">{phone}</p>
                    <p className="text-[10px] text-muted-foreground">Phone / WhatsApp</p>
                  </div>
                </div>
              )}

              {website && (
                <div className="flex items-center gap-3">
                  <ExternalLink className="h-4 w-4 text-muted-foreground" />
                  <div className="min-w-0 flex-1">
                    <a
                      href={website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="truncate text-sm text-primary hover:underline"
                    >
                      {website.replace(/^https?:\/\//, "")}
                    </a>
                    <p className="text-[10px] text-muted-foreground">Website</p>
                  </div>
                </div>
              )}

              <p className="text-xs capitalize text-muted-foreground">
                Stage: {leadData.stage || leadData.status || "new"}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Timeline</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-start gap-3">
                <Clock className="mt-0.5 h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-sm">Discovered</p>
                  <p className="text-xs text-muted-foreground">
                    {leadData.created_at
                      ? new Date(leadData.created_at).toLocaleString()
                      : "Just now"}
                  </p>
                </div>
              </div>
              {website && (
                <div className="flex items-start gap-3">
                  <ExternalLink className="mt-0.5 h-4 w-4 text-muted-foreground" />
                  <div>
                    <p className="text-sm">Source</p>
                    <a
                      href={website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-primary hover:underline"
                    >
                      View website
                    </a>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
