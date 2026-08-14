"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Sheet } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge, statusFromLabel } from "@/components/ui/status";
import { beaconApi } from "@/lib/api/beacon";
import { gmailConnectUrl } from "@/lib/founder";
import { mergeLead } from "@/lib/lead";
import { cn, formatScore } from "@/lib/utils";

type CompanyDrawerProps = {
  open: boolean;
  onClose: () => void;
  companyId?: string | null;
  companyName?: string | null;
  recordId?: string | null;
  seed?: Record<string, unknown> | null;
};

const TABS = ["Overview", "Outreach", "Evidence", "Notes", "Timeline"] as const;

function gmailComposeUrl(to: string, subject: string, body: string): string {
  const params = new URLSearchParams({
    view: "cm",
    fs: "1",
    to,
    su: subject,
    body,
  });
  return `https://mail.google.com/mail/?${params.toString()}`;
}

export function CompanyDrawer({
  open,
  onClose,
  companyId,
  companyName,
  recordId,
  seed,
}: CompanyDrawerProps) {
  const [tab, setTab] = useState<(typeof TABS)[number]>("Overview");
  const [note, setNote] = useState("");
  const qc = useQueryClient();

  const company = useQuery({
    queryKey: ["company-drawer", companyId],
    queryFn: () => beaconApi.company(companyId!),
    enabled: open && Boolean(companyId),
  });

  const workspace = useQuery({
    queryKey: ["ofc-workspace"],
    queryFn: () => beaconApi.ofcWorkspace(),
    enabled: open && !recordId && Boolean(companyId),
  });

  const matchedRecordId = useMemo(() => {
    if (recordId) return recordId;
    const items = ((workspace.data?.items as Array<Record<string, unknown>>) || []) as Array<
      Record<string, unknown>
    >;
    const match = items.find((item) => String(item.company_id) === String(companyId));
    return match ? String(match.id) : null;
  }, [recordId, workspace.data, companyId]);

  const ofc = useQuery({
    queryKey: ["ofc-record", matchedRecordId],
    queryFn: () => beaconApi.ofcRecord(matchedRecordId!),
    enabled: open && Boolean(matchedRecordId),
  });

  const queue = useQuery({
    queryKey: ["rrp-founder-queue-v4"],
    queryFn: () => beaconApi.rrpFounderQueue(),
    enabled: open && Boolean(companyId),
  });

  const oauth = useQuery({
    queryKey: ["gmail-oauth-status"],
    queryFn: () => beaconApi.communicationOauthStatus("gmail"),
    enabled: open,
  });

  const addNote = useMutation({
    mutationFn: (text: string) => {
      if (matchedRecordId) return beaconApi.ofcNote(matchedRecordId, text);
      if (companyId) return beaconApi.clrNotes(companyId, text);
      return Promise.reject(new Error("No target"));
    },
    onSuccess: () => {
      setNote("");
      void qc.invalidateQueries({ queryKey: ["ofc-record", matchedRecordId] });
    },
  });

  const queueItem = ((queue.data?.items as Array<Record<string, unknown>>) || []).find(
    (item) => String(item.company_id) === String(companyId),
  );
  const ofcRecord = (ofc.data as { record?: Record<string, unknown> } | undefined)?.record;
  const ofcListItem = ((workspace.data?.items as Array<Record<string, unknown>>) || []).find(
    (item) => String(item.company_id) === String(companyId) || String(item.id) === String(matchedRecordId),
  );

  const lead = mergeLead(
    seed,
    queueItem,
    ofcListItem,
    ofcRecord,
    company.data
      ? {
          company: company.data.name,
          company_id: company.data.id,
          website: company.data.primary_domain || "",
          industry: company.data.industry || "",
          description: company.data.memory_summary || "",
          attributes: company.data.attributes || {},
          why_now: company.data.attributes?.why_now,
          buying_signals: company.data.attributes?.buying_signals,
          decision_maker: company.data.attributes?.decision_maker,
          business_email:
            company.data.attributes?.business_email ||
            company.data.attributes?.ofc_business_email,
        }
      : null,
  );

  const timeline = ((ofc.data as { timeline?: Array<Record<string, unknown>> })?.timeline ||
    []) as Array<Record<string, unknown>>;
  const notes = ((ofc.data as { notes?: Array<Record<string, unknown>> })?.notes || []) as Array<
    Record<string, unknown>
  >;

  const connected = Boolean(oauth.data?.connected);
  const loading = (company.isLoading && Boolean(companyId)) || (ofc.isLoading && Boolean(matchedRecordId));
  const [emailSubject, setEmailSubject] = useState("");
  const [emailBody, setEmailBody] = useState("");
  const [whatsappBody, setWhatsappBody] = useState("");

  useEffect(() => {
    setEmailSubject(lead.emailSubject || `A note for ${lead.company}`);
    setEmailBody(lead.emailDraft || "");
    setWhatsappBody(lead.whatsappDraft || "");
  }, [lead.companyId, lead.emailSubject, lead.emailDraft, lead.whatsappDraft, open]);

  const recipient = lead.email || lead.dmEmail || "";
  const manualGmailHref = gmailComposeUrl(
    recipient,
    emailSubject || `A note for ${lead.company}`,
    emailBody || lead.emailDraft || "",
  );

  return (
    <Sheet
      open={open}
      onClose={onClose}
      title={companyName || lead.company}
      description={lead.service !== "—" ? lead.service : "Review, edit, and send"}
    >
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <StatusBadge tone={statusFromLabel(lead.status)}>{lead.status}</StatusBadge>
        {lead.confidence > 0 ? (
          <span className="text-xs text-muted-foreground">Score {formatScore(lead.confidence, 0)}</span>
        ) : null}
      </div>

      <div className="mb-4 flex gap-1 overflow-x-auto scrollbar-thin">
        {TABS.map((item) => (
          <button
            key={item}
            type="button"
            onClick={() => setTab(item)}
            className={cn(
              "rounded-lg px-3 py-1.5 text-xs font-medium transition",
              tab === item ? "bg-primary/15 text-foreground" : "text-muted-foreground hover:bg-muted/40",
            )}
          >
            {item}
          </button>
        ))}
      </div>

      {loading ? <Skeleton className="mb-4 h-24 w-full" /> : null}

      {tab === "Overview" ? (
        <div className="space-y-4 text-sm">
          <Field label="Why now" value={lead.whyNow} />
          <Field label="Pain" value={lead.pain} />
          <Field label="Decision maker" value={lead.decisionMaker} />
          <Field label="Email" value={lead.email || lead.dmEmail || "—"} />
          <Field label="Website" value={lead.website || "—"} />
          <Field label="Industry" value={lead.industry} />
          <Field label="Service" value={lead.service} />
          <Field label="Next action" value={lead.nextAction} />
          <div className="flex flex-wrap gap-2 pt-2">
            {!connected ? (
              <Button asChild>
                <a href={gmailConnectUrl()}>Connect Gmail</a>
              </Button>
            ) : (
              <Button asChild>
                <a href="/outreach">Review Email</a>
              </Button>
            )}
            <Button variant="outline" asChild>
              <a href="/outreach">Start Outreach</a>
            </Button>
          </div>
        </div>
      ) : null}

      {tab === "Outreach" ? (
        <div className="space-y-4 text-sm">
          <EditableBlock label="Email Subject" value={emailSubject} onChange={setEmailSubject} minHeight="min-h-12" />
          <EditableBlock label="AI Email" value={emailBody} onChange={setEmailBody} />
          <EditableBlock label="WhatsApp Draft" value={whatsappBody} onChange={setWhatsappBody} />
          <Field label="CTA" value={lead.cta} />
          <Field label="Recipient" value={recipient || "—"} />
          <div className="flex flex-wrap gap-2">
            {recipient ? (
              <Button asChild>
                <a href={manualGmailHref} target="_blank" rel="noreferrer">
                  Send manually via Gmail
                </a>
              </Button>
            ) : (
              <Button disabled>Send manually via Gmail</Button>
            )}
            {connected ? (
              <Button asChild>
                <a href="/outreach">Approve & Send</a>
              </Button>
            ) : (
              <Button asChild>
                <a href={gmailConnectUrl()}>Connect Gmail to send</a>
              </Button>
            )}
          </div>
        </div>
      ) : null}

      {tab === "Evidence" ? (
        <div className="space-y-3 text-sm">
          <Field label="Why now" value={lead.whyNow} />
          <Field label="Confidence" value={formatScore(lead.confidence, 0)} />
          <Field label="Trust" value={formatScore(lead.trust, 0)} />
          <div>
            <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">Evidence</p>
            <ul className="mt-2 space-y-1">
              {lead.evidence.length === 0 ? (
                <li className="text-muted-foreground">No evidence listed.</li>
              ) : (
                lead.evidence.map((item) => (
                  <li key={item} className="rounded-lg border border-border/60 px-3 py-2">
                    {item}
                  </li>
                ))
              )}
            </ul>
          </div>
        </div>
      ) : null}

      {tab === "Notes" ? (
        <div className="space-y-3">
          <textarea
            value={note}
            onChange={(event) => setNote(event.target.value)}
            placeholder="Add a note…"
            className="min-h-24 w-full rounded-xl border border-border/70 bg-card/50 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
          />
          <Button
            size="sm"
            disabled={!note.trim() || addNote.isPending}
            onClick={() => addNote.mutate(note.trim())}
          >
            Save note
          </Button>
          <div className="space-y-2">
            {notes.length === 0 ? (
              <p className="text-sm text-muted-foreground">No notes yet.</p>
            ) : (
              notes.map((row, idx) => (
                <div key={idx} className="rounded-lg border border-border/60 px-3 py-2 text-sm">
                  {String(row.note || row.text || row.body || "")}
                </div>
              ))
            )}
          </div>
        </div>
      ) : null}

      {tab === "Timeline" ? (
        <div className="space-y-2">
          {timeline.length === 0 ? (
            <p className="text-sm text-muted-foreground">No activity yet.</p>
          ) : (
            timeline.map((row, idx) => (
              <div key={idx} className="rounded-lg border border-border/60 px-3 py-2 text-sm">
                <p className="font-medium">{String(row.event_type || row.type || "Event")}</p>
                <p className="text-xs text-muted-foreground">{String(row.created_at || row.at || "")}</p>
              </div>
            ))
          )}
        </div>
      ) : null}
    </Sheet>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-[0.12em] text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm leading-relaxed">{value || "—"}</p>
    </div>
  );
}

function EditableBlock({
  label,
  value,
  onChange,
  minHeight = "min-h-28",
}: {
  label: string;
  value: string;
  onChange?: (value: string) => void;
  minHeight?: string;
}) {
  return (
    <div>
      <p className="mb-1 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">{label}</p>
      <textarea
        value={value}
        onChange={(event) => onChange?.(event.target.value)}
        className={`${minHeight} w-full rounded-xl border border-border/70 bg-card/50 px-3 py-2 text-sm leading-relaxed outline-none focus:ring-2 focus:ring-ring`}
      />
    </div>
  );
}
