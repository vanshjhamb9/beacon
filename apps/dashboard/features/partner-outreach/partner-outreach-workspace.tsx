"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Inbox,
  Loader2,
  OctagonX,
  Play,
  RefreshCw,
  Send,
  Trash2,
  Upload,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  partnerOutreachApi,
  type PartnerOutreachCampaign,
  type PartnerOutreachLead,
} from "@/lib/api/beacon";

const PIPELINE_ORDER = [
  "drafted",
  "queued",
  "sent",
  "replied",
  "interested",
  "meeting",
  "partner_onboarded",
  "nurture",
  "lost",
  "failed",
];

export function PartnerOutreachWorkspace() {
  const [campaigns, setCampaigns] = useState<PartnerOutreachCampaign[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [leads, setLeads] = useState<PartnerOutreachLead[]>([]);
  const [pipeline, setPipeline] = useState<Record<string, number>>({});
  const [inbox, setInbox] = useState<Array<Record<string, unknown>>>([]);
  const [metrics, setMetrics] = useState<Record<string, unknown> | null>(null);
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [previewLead, setPreviewLead] = useState<PartnerOutreachLead | null>(null);
  const [tab, setTab] = useState<"leads" | "pipeline" | "inbox">("leads");
  const [error, setError] = useState<string | null>(null);

  const selected = useMemo(
    () => campaigns.find((c) => c.id === selectedId) || null,
    [campaigns, selectedId],
  );

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [cRes, mRes, hRes, pRes, iRes] = await Promise.all([
        partnerOutreachApi.listCampaigns(),
        partnerOutreachApi.metrics(),
        partnerOutreachApi.health(),
        partnerOutreachApi.pipeline(),
        partnerOutreachApi.inbox(50),
      ]);
      setCampaigns(cRes.campaigns || []);
      setMetrics(mRes);
      setHealth(hRes);
      setPipeline((pRes.counts as Record<string, number>) || {});
      setInbox(iRes.items || []);
      const nextId = selectedId || cRes.campaigns?.[0]?.id || null;
      if (nextId) {
        setSelectedId(nextId);
        const leadsRes = await partnerOutreachApi.getLeads(nextId);
        setLeads(leadsRes.leads || []);
      } else {
        setLeads([]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load partner outreach");
    }
    setLoading(false);
  }, [selectedId]);

  useEffect(() => {
    void refresh();
    const t = setInterval(() => void refresh(), 20000);
    return () => clearInterval(t);
  }, [refresh]);

  async function onUpload(file: File | null) {
    if (!file) return;
    setUploading(true);
    setError(null);
    setStatusMsg(`Validating leads in ${file.name}…`);
    try {
      const res = await partnerOutreachApi.uploadCampaign(file);
      setSelectedId(res.campaign.id);
      const processed = (res as { process?: { sent?: number; message?: string } }).process;
      setStatusMsg(
        `Validated ${res.valid_rows} lead(s), skipped ${res.skipped_rows}. ` +
          (processed?.message
            ? processed.message
            : res.dry_run
              ? "Dry-run ON — queue will simulate sends."
              : "Auto-processing started."),
      );
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
      setStatusMsg(null);
    }
    setUploading(false);
  }

  async function onKill() {
    if (!selectedId) return;
    await partnerOutreachApi.killCampaign(selectedId);
    await refresh();
  }

  async function onResume() {
    if (!selectedId) return;
    await partnerOutreachApi.resumeCampaign(selectedId);
    await refresh();
  }

  async function onProcess() {
    if (!selectedId) return;
    setProcessing(true);
    setError(null);
    setStatusMsg("Processing queue…");
    try {
      const result = await partnerOutreachApi.processCampaign(selectedId, 100);
      setStatusMsg(result.message || `Processed: sent ${result.sent}, held ${result.held ?? 0}`);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Process failed");
      setStatusMsg(null);
    }
    setProcessing(false);
  }

  async function onClearHistory() {
    if (
      !window.confirm(
        "Clear all partner outreach campaigns? This removes previous uploads and dry-run history.",
      )
    ) {
      return;
    }
    setUploading(true);
    setError(null);
    try {
      const res = await partnerOutreachApi.clearCampaigns();
      setSelectedId(null);
      setLeads([]);
      setStatusMsg(`Cleared ${res.campaigns_removed} campaign(s). Upload a fresh list when ready.`);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Clear failed");
    }
    setUploading(false);
  }

  async function selectCampaign(id: string) {
    setSelectedId(id);
    const leadsRes = await partnerOutreachApi.getLeads(id);
    setLeads(leadsRes.leads || []);
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">COMAI Partner Outreach</h1>
          <p className="text-muted-foreground">
            Upload agency/freelancer leads → hyperpersonalized partnership emails with video CTA →
            auto-send, replies, and follow-ups.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" onClick={() => void refresh()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => void onClearHistory()}
            disabled={uploading || processing}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Clear history
          </Button>
          <label className="inline-flex cursor-pointer items-center">
            <input
              type="file"
              accept=".csv,.xlsx,.txt"
              className="hidden"
              onChange={(e) => {
                void onUpload(e.target.files?.[0] || null);
                e.currentTarget.value = "";
              }}
            />
            <span className="inline-flex h-9 items-center justify-center gap-2 rounded-md bg-primary px-3 text-sm font-medium text-primary-foreground hover:bg-primary/90">
              {uploading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Validating leads…
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4" />
                  Upload Excel/CSV
                </>
              )}
            </span>
          </label>
        </div>
      </div>

      {error ? (
        <div className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-300">
          {error}
        </div>
      ) : null}

      {statusMsg || uploading || processing ? (
        <div className="flex items-center gap-2 rounded-md border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-100">
          {(uploading || processing) && <Loader2 className="h-4 w-4 shrink-0 animate-spin" />}
          <span>
            {uploading
              ? "Validating leads — parsing file, checking emails, drafting intros…"
              : processing
                ? "Processing queue…"
                : statusMsg}
          </span>
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm">
            <div>
              Enabled:{" "}
              <Badge variant={health?.enabled ? "default" : "secondary"}>
                {String(health?.enabled ?? false)}
              </Badge>
            </div>
            <div>
              Dry-run:{" "}
              <Badge variant={health?.dry_run ? "secondary" : "default"}>
                {String(health?.dry_run ?? true)}
              </Badge>
            </div>
            <div className="truncate text-muted-foreground">
              Video: {String(health?.video_url || "—")}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Sent</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">
            {String(metrics?.sent ?? 0)}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Reply rate</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">
            {(((metrics?.reply_rate as number) || 0) * 100).toFixed(1)}%
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Interested / meetings</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">
            {String(metrics?.interested ?? 0)} / {String(metrics?.meetings ?? 0)}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Campaigns</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {loading && !campaigns.length ? (
              <div className="text-sm text-muted-foreground">Loading…</div>
            ) : null}
            {!campaigns.length && !loading ? (
              <div className="text-sm text-muted-foreground">
                No campaigns yet. Upload a CSV/XLSX of partner leads.
              </div>
            ) : null}
            {campaigns.map((c) => (
              <button
                key={c.id}
                type="button"
                onClick={() => void selectCampaign(c.id)}
                className={`w-full rounded-md border px-3 py-2 text-left text-sm transition ${
                  selectedId === c.id
                    ? "border-emerald-500/50 bg-emerald-500/10"
                    : "border-border hover:bg-muted/40"
                }`}
              >
                <div className="font-medium line-clamp-1">{c.name}</div>
                <div className="mt-1 flex flex-wrap gap-1 text-xs text-muted-foreground">
                  <Badge variant="outline">{c.status}</Badge>
                  <span>
                    {c.sent}/{c.valid_rows} sent
                  </span>
                </div>
              </button>
            ))}
          </CardContent>
        </Card>

        <div className="space-y-4">
          {selected ? (
            <Card>
              <CardHeader className="flex flex-row items-center justify-between gap-2">
                <div>
                  <CardTitle className="text-base">{selected.name}</CardTitle>
                  <p className="text-sm text-muted-foreground">
                    Valid {selected.valid_rows} · Skipped {selected.skipped_rows} · Sent{" "}
                    {selected.sent} · Failed {selected.failed}
                  </p>
                  {selected.valid_rows === 0 && (selected.row_errors?.length || 0) > 0 ? (
                    <div className="mt-2 rounded-md border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-xs text-amber-200">
                      <div className="font-medium">Nothing to process — all rows skipped</div>
                      <ul className="mt-1 list-disc pl-4">
                        {(selected.row_errors || []).slice(0, 5).map((err, i) => (
                          <li key={i}>
                            {String(err.error || "error")}
                            {err.hint ? ` — ${String(err.hint)}` : ""}
                            {err.email ? ` (${String(err.email)})` : ""}
                          </li>
                        ))}
                      </ul>
                      <p className="mt-1 opacity-80">
                        Tip: CSV needs email / founder_email / general_email / emails + company_name
                      </p>
                    </div>
                  ) : null}
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={processing || uploading}
                    onClick={() => void onProcess()}
                  >
                    {processing ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="mr-2 h-4 w-4" />
                    )}
                    {processing ? "Processing…" : "Process queue"}
                  </Button>
                  {selected.kill_flag || selected.status === "killed" ? (
                    <Button size="sm" onClick={() => void onResume()}>
                      <Play className="mr-2 h-4 w-4" />
                      Resume
                    </Button>
                  ) : (
                    <Button size="sm" variant="destructive" onClick={() => void onKill()}>
                      <OctagonX className="mr-2 h-4 w-4" />
                      Kill switch
                    </Button>
                  )}
                </div>
              </CardHeader>
            </Card>
          ) : null}

          <div className="flex gap-2">
            {(["leads", "pipeline", "inbox"] as const).map((t) => (
              <Button
                key={t}
                size="sm"
                variant={tab === t ? "default" : "outline"}
                onClick={() => setTab(t)}
              >
                {t === "inbox" ? <Inbox className="mr-2 h-4 w-4" /> : null}
                {t}
              </Button>
            ))}
          </div>

          {tab === "pipeline" ? (
            <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-5">
              {PIPELINE_ORDER.map((stage) => (
                <Card key={stage}>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm capitalize">{stage.replaceAll("_", " ")}</CardTitle>
                  </CardHeader>
                  <CardContent className="text-2xl font-semibold">
                    {pipeline[stage] || 0}
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : null}

          {tab === "inbox" ? (
            <Card>
              <CardContent className="pt-6">
                {!inbox.length ? (
                  <p className="text-sm text-muted-foreground">No replies ingested yet.</p>
                ) : (
                  <div className="space-y-3">
                    {inbox.map((item) => (
                      <div
                        key={String(item.id)}
                        className="rounded-md border border-border p-3 text-sm"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-medium">{String(item.subject || "(no subject)")}</span>
                          <Badge variant="outline">{String(item.reply_class || "reply")}</Badge>
                        </div>
                        <p className="mt-2 whitespace-pre-wrap text-muted-foreground">
                          {String(item.body_text || "").slice(0, 320)}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ) : null}

          {tab === "leads" ? (
            <Card>
              <CardContent className="pt-6">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Agency</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Stage</TableHead>
                      <TableHead>Step</TableHead>
                      <TableHead></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {leads.map((lead) => (
                      <TableRow key={lead.id}>
                        <TableCell className="font-medium">{lead.agency_name}</TableCell>
                        <TableCell>{lead.email}</TableCell>
                        <TableCell>{lead.agency_type || "—"}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{lead.stage}</Badge>
                        </TableCell>
                        <TableCell>{lead.sequence_step || "—"}</TableCell>
                        <TableCell>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => setPreviewLead(lead)}
                          >
                            Preview
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {!leads.length ? (
                  <p className="py-6 text-center text-sm text-muted-foreground">
                    Select a campaign or upload leads to begin.
                  </p>
                ) : null}
              </CardContent>
            </Card>
          ) : null}
        </div>
      </div>

      {previewLead ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="max-h-[85vh] w-full max-w-2xl overflow-auto rounded-lg border border-border bg-background p-5 shadow-xl">
            <div className="mb-4 flex items-start justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold">{previewLead.agency_name}</h2>
                <p className="text-sm text-muted-foreground">{previewLead.subject}</p>
              </div>
              <Button variant="outline" size="sm" onClick={() => setPreviewLead(null)}>
                Close
              </Button>
            </div>
            <div className="mb-3">
              <Input value={previewLead.email} readOnly />
            </div>
            <pre className="whitespace-pre-wrap rounded-md bg-muted/40 p-4 text-sm leading-relaxed">
              {previewLead.body_text}
            </pre>
          </div>
        </div>
      ) : null}
    </div>
  );
}
