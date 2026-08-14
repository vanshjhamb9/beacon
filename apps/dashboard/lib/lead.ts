/** Normalize lead/company payloads from OFC, CLR, and Revenue Ready APIs. */

export type LeadView = {
  id?: string;
  recordId?: string;
  companyId: string;
  company: string;
  status: string;
  website: string;
  whyNow: string;
  decisionMaker: string;
  email: string;
  dmEmail: string;
  service: string;
  industry: string;
  confidence: number;
  trust: number;
  pain: string;
  evidence: string[];
  cta: string;
  emailSubject: string;
  emailDraft: string;
  whatsappDraft: string;
  pipelineValue: number;
  nextAction: string;
  qualityScore?: number;
  qualityGrade?: string;
  raw: Record<string, unknown>;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function asList(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value
      .map((item) => {
        if (typeof item === "string") return item.trim();
        if (item && typeof item === "object") {
          const row = item as Record<string, unknown>;
          return String(row.label || row.reason || row.signal || row.text || row.value || "").trim();
        }
        return String(item || "").trim();
      })
      .filter(Boolean);
  }
  if (typeof value === "string" && value.trim()) return [value.trim()];
  return [];
}

function num(value: unknown): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function pickFirstText(...values: unknown[]): string {
  for (const value of values) {
    const text = String(value || "").trim();
    if (text) return text;
  }
  return "";
}

function firstNameFromDecisionMaker(decisionMaker: string): string {
  return (
    String(decisionMaker || "")
      .split(/[\s(]/)
      .filter(Boolean)[0] || "there"
  );
}

function normalizeSentence(value: string): string {
  const text = (value || "").trim();
  if (!text) return "";
  const out = text.replace(/\s+/g, " ").trim();
  return /[.!?]$/.test(out) ? out : `${out}.`;
}

function cleanSnippet(value: string, max = 180): string {
  const text = value.replace(/\s+/g, " ").trim();
  if (!text) return "";
  return text.length > max ? `${text.slice(0, max - 1).trim()}…` : text;
}

function hashSeed(input: string): number {
  let h = 0;
  for (let i = 0; i < input.length; i += 1) h = (h * 31 + input.charCodeAt(i)) >>> 0;
  return h;
}

function pickVariant<T>(seed: string, options: T[]): T {
  return options[hashSeed(seed) % options.length]!;
}

function domainHint(website: string): string {
  return website
    .replace(/^https?:\/\//, "")
    .replace(/^www\./, "")
    .split("/")[0]
    .toLowerCase();
}

function detectAngle(input: {
  company: string;
  industry: string;
  service: string;
  whyNow: string;
  vision: string;
  pain: string;
  evidence: string[];
  description: string;
  buyingSignals: string[];
}): {
  hook: string;
  opportunity: string;
  buildPlan: string[];
  outcomes: string[];
  meetingAsk: string;
  subject: string;
} {
  const blob = [
    input.company,
    input.industry,
    input.service,
    input.whyNow,
    input.vision,
    input.pain,
    input.description,
    ...input.evidence,
    ...input.buyingSignals,
  ]
    .join(" ")
    .toLowerCase();

  const hiring = /hir(e|ing)|job|career|recruit|headcount|talent/.test(blob);
  const funding = /fund|raised|seed|series|yc|y combinator|portfolio|invest/.test(blob);
  const launch = /launch|product hunt|shipping|release|beta|new product|announc/.test(blob);
  const sales = /sales|pipeline|crm|outbound|lead|conversion|revenue/.test(blob);
  const support = /support|ticket|customer success|onboarding|helpdesk|inbox/.test(blob);
  const ops = /ops|operation|workflow|manual|automat|internal tool|process/.test(blob);
  const ai = /ai|llm|agent|model|copilot|gpt/.test(blob);
  const marketplace = /marketplace|platform|saas|b2b|developer|api/.test(blob);

  const specificSignal =
    cleanSnippet(input.buyingSignals[0] || input.evidence[0] || input.whyNow || input.vision || input.description) ||
    `${input.company} is moving with clear market momentum`;

  const visionLine =
    cleanSnippet(input.vision || input.description || input.whyNow) ||
    `building a stronger ${input.industry && input.industry !== "—" ? input.industry.toLowerCase() : "product"} motion`;

  const serviceLabel =
    input.service && input.service !== "—" ? input.service : ai ? "AI workflow automation" : "revenue operations automation";
  const serviceArticle = /^[aeiou]/i.test(serviceLabel) ? "an" : "a";

  if (hiring) {
    return {
      subject: pickVariant(input.company, [
        `${input.company}: scale output without proportional headcount`,
        `Re: hiring at ${input.company} — keep quality while you grow`,
        `${input.company} hiring signal → execution capacity idea`,
      ]),
      hook: `Your hiring signal stood out — ${specificSignal}. That usually means ${input.company} is pushing growth faster than current systems can absorb.`,
      opportunity: `While you add people, Inowix can help stand up ${serviceArticle} ${serviceLabel} layer so new capacity compounds instead of creating process debt.`,
      buildPlan: [
        `Map the 1-2 workflows your new hires will touch most (onboarding, delivery, or customer response).`,
        `Automate handoffs, reminders, and status reporting so managers stay unblocked.`,
        `Give leadership a live view of throughput so hiring ROI is visible in week one.`,
      ],
      outcomes: [
        `Faster ramp for new teammates`,
        `Fewer dropped tasks during growth`,
        `Clear capacity signal before the next hire`,
      ],
      meetingAsk: `Would you be open to a brief 15-minute working session this week to outline the first automation for ${input.company}?`,
    };
  }

  if (funding) {
    return {
      subject: pickVariant(input.company, [
        `${input.company}: turn funding momentum into measurable execution`,
        `An execution idea for ${input.company} post-funding`,
        `${input.company} — converting capital into operating speed`,
      ]),
      hook: `I noticed the funding and growth momentum around ${input.company}: ${specificSignal}.`,
      opportunity: `As capital lands, operating leverage becomes the story. A focused ${serviceLabel} build can turn that momentum into repeatable throughput.`,
      buildPlan: [
        `Instrument the revenue or delivery path that must improve first.`,
        `Ship a 14-day automation that removes the heaviest manual bottleneck.`,
        `Package a simple KPI board so progress is board-ready.`,
      ],
      outcomes: [
        `Faster cycle time on the funded priority`,
        `Less founder time in status chasing`,
        `Cleaner story for the next milestone update`,
      ],
      meetingAsk: `Would a short call be useful to map a 30-day execution plan aligned to ${input.company}'s funded priorities?`,
    };
  }

  if (launch) {
    return {
      subject: pickVariant(input.company, [
        `${input.company}: convert launch attention into booked conversations`,
        `${input.company}'s launch — a practical conversion idea`,
        `${input.company} launch window: capture demand while it is warm`,
      ]),
      hook: `Your recent launch activity is timely: ${specificSignal}.`,
      opportunity: `Launch windows close quickly. We can help ${input.company} convert attention into qualified conversations with ${serviceArticle} ${serviceLabel} follow-up system.`,
      buildPlan: [
        `Capture inbound intent from the launch channels you are already on.`,
        `Route hot leads to the right owner with a personalized first touch.`,
        `Trigger a tight follow-up sequence so warm interest does not go cold.`,
      ],
      outcomes: [
        `More meetings from the same launch traffic`,
        `Consistent first-response quality`,
        `A reusable playbook for the next release`,
      ],
      meetingAsk: `May we book 15 minutes to design the conversion path for ${input.company}'s current launch window?`,
    };
  }

  if (sales) {
    return {
      subject: pickVariant(input.company, [
        `${input.company}: tighten the path from signal to meeting`,
        `A pipeline idea for ${input.company}`,
        `${input.company} — fewer leaks between interest and booked calls`,
      ]),
      hook: `Looking at ${input.company}, the commercial direction is clear: ${visionLine}`,
      opportunity: `The opportunity I see is speed-to-conversation. A tailored ${serviceLabel} flow can turn your strongest signals into booked meetings.`,
      buildPlan: [
        `Prioritize accounts by intent, not volume alone.`,
        `Generate precise outreach from each account's public signals.`,
        `Close the loop with follow-ups and meeting booking in one workflow.`,
      ],
      outcomes: [
        `Higher reply quality`,
        `Shorter time-to-first-meeting`,
        `A pipeline view leadership can trust`,
      ],
      meetingAsk: `Would you be open to a brief call to walk through a signal-to-meeting workflow for ${input.company}?`,
    };
  }

  if (support) {
    return {
      subject: pickVariant(input.company, [
        `${input.company}: protect customer experience while you scale`,
        `A support and ops idea for ${input.company}`,
        `${input.company} — reduce response drag without adding headcount`,
      ]),
      hook: `From what I can see at ${input.company}, customer and operations load is becoming strategic: ${specificSignal}.`,
      opportunity: `We can implement ${serviceLabel} so response quality stays high even as volume grows.`,
      buildPlan: [
        `Identify the top repetitive customer or operations requests.`,
        `Automate triage, routing, and first-response drafts.`,
        `Add an escalation path so humans only handle judgment calls.`,
      ],
      outcomes: [
        `Faster first response`,
        `Lower manual load on the team`,
        `Better visibility into recurring customer friction`,
      ],
      meetingAsk: `Would a short call this week help map the first customer-experience automation for ${input.company}?`,
    };
  }

  if (ops || marketplace || ai) {
    return {
      subject: pickVariant(input.company, [
        `${input.company}: making “${cleanSnippet(visionLine, 42)}” operational`,
        `An execution idea for ${input.company}'s current direction`,
        `${input.company} — from vision to a weekly operating system`,
      ]),
      hook: `I have been reviewing ${input.company}${input.industry && input.industry !== "—" ? ` (${input.industry})` : ""}, and the direction reads as: ${visionLine}`,
      opportunity: `To make that real, ${input.company} likely needs a practical ${serviceLabel} layer — not another slide deck.`,
      buildPlan: [
        `Translate the vision into one flagship workflow with clear owners.`,
        `Automate the repetitive middle so your team stays on high-judgment work.`,
        `Ship a measurable pilot in two weeks, then expand only what proves ROI.`,
      ],
      outcomes: [
        `Visible weekly progress against the vision`,
        `Less manual coordination overhead`,
        `A foundation you can extend without rework`,
      ],
      meetingAsk: `If useful, I can bring a 30/60/90 draft for ${input.company} to a short call — would you be open to connecting?`,
    };
  }

  const painLine = cleanSnippet(input.pain);
  return {
    subject: pickVariant(input.company, [
      `${input.company}: a practical next step on your current priority`,
      `A concise idea for ${input.company}`,
      `${input.company} — worth a brief 15-minute working session?`,
    ]),
    hook: `I reviewed ${input.company}${input.industry && input.industry !== "—" ? ` in ${input.industry}` : ""} and one theme stood out: ${specificSignal}.`,
    opportunity: painLine
      ? `That pairs with the friction I inferred (${painLine}). A focused ${serviceLabel} engagement can remove that drag and create a cleaner path to meetings and delivery.`
      : `A focused ${serviceLabel} engagement can help ${input.company} move from signal to execution with less manual work.`,
    buildPlan: [
      `Lock the single highest-leverage workflow for the next 14 days.`,
      `Automate the handoffs that currently slow response and follow-up.`,
      `Measure one outcome leaders care about (speed, conversion, or capacity).`,
    ],
    outcomes: [
      `Faster follow-through on hot opportunities`,
      `Less founder and ops time in repetitive work`,
      `A concrete pilot you can expand with confidence`,
    ],
    meetingAsk: `Would you be open to a 15-minute call to pressure-test this for ${input.company} and see if a working session makes sense?`,
  };
}

function inowixGlimpse(company: string, service: string, vision: string): string {
  const focus =
    service && service !== "—"
      ? service
      : "AI automation, revenue operations, and custom workflow systems";
  const visionBit = cleanSnippet(vision, 90);
  const article = /^[aeiou]/i.test(focus) ? "an" : "a";
  return `At Inowix Technologies, we help growing teams turn ambition into working systems — ${article} ${focus} layer that removes manual drag and makes execution repeatable.

For ${company}, that means taking your direction${visionBit ? ` (“${visionBit.replace(/\.$/, "")}”)` : ""} and turning it into a live operating layer: the workflows, outreach, and follow-through that bring the vision to life — so your team spends time on judgment, not busywork.`;
}

function emailSignature(): string {
  return `Best,
Vansh Jhamb
vansh@inowix.in
Founder
Inowix Technologies
https://www.inowix.in/`;
}

function buildHyperPersonalEmail(input: {
  firstName: string;
  company: string;
  website: string;
  industry: string;
  service: string;
  whyNow: string;
  vision: string;
  pain: string;
  evidence: string[];
  description: string;
  buyingSignals: string[];
  cta: string;
}): { subject: string; body: string; whatsapp: string } {
  const angle = detectAngle(input);
  const domain = domainHint(input.website);
  const evidenceLines = (input.buyingSignals.length ? input.buyingSignals : input.evidence)
    .map((item) => cleanSnippet(item, 140))
    .filter(Boolean)
    .slice(0, 3);
  const uniqueEvidence =
    evidenceLines.length > 0
      ? evidenceLines.map((line) => `- ${line}`).join("\n")
      : `- Recent public activity and growth context around ${input.company}`;

  const greeting = pickVariant(input.company, [
    `Dear ${input.firstName},`,
    `Hello ${input.firstName},`,
    `Hi ${input.firstName},`,
  ]);

  const body = `${greeting}

${angle.hook}${domain ? ` I came across this via ${domain}.` : ""}

${angle.opportunity}

${inowixGlimpse(input.company, input.service, input.vision)}

How we would support ${input.company}
${angle.buildPlan.map((line) => `- ${line}`).join("\n")}

What you should expect in the first 2–3 weeks
${angle.outcomes.map((line) => `- ${line}`).join("\n")}

Context I used
${uniqueEvidence}

${angle.meetingAsk}
If a time this week works, reply with two options and I will send a calendar link.

${emailSignature()}`;

  const whatsapp = pickVariant(input.company, [
    `Hi ${input.firstName}, I noticed ${input.company}'s momentum: ${cleanSnippet(input.whyNow || input.vision || input.evidence[0] || "strong growth signal", 90)}. Inowix helps teams turn vision into working automation and cleaner execution. Open to a short 15-min call? — Vansh, Inowix (https://www.inowix.in/)`,
    `Hello ${input.firstName} — ${input.company} stood out because ${cleanSnippet(input.buyingSignals[0] || input.evidence[0] || input.whyNow || "of the current direction", 80)}. Happy to share how Inowix can help bring that to life. Worth a quick chat? — Vansh Jhamb, Founder, Inowix`,
  ]);

  return { subject: angle.subject, body, whatsapp };
}

export function formatMoney(value: number): string {
  if (!Number.isFinite(value) || value === 0) return "$0";
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${Math.round(value).toLocaleString()}`;
  return `$${Math.round(value)}`;
}

export function normalizeLead(input: Record<string, unknown> | null | undefined): LeadView {
  const row = asRecord(input);
  const brief = asRecord(row.brief);
  const attrs = asRecord(row.attributes);
  const source = { ...attrs, ...brief, ...row };

  const painPoints = [
    ...asList(source.pain_points),
    ...asList(attrs.pain_points),
  ];
  const buyingSignals = [
    ...asList(source.buying_signals),
    ...asList(attrs.buying_signals),
    ...asList(source.signals),
  ];
  const evidence = [
    ...asList(source.evidence),
    ...asList(attrs.evidence),
    ...buyingSignals,
  ].filter((item, index, arr) => arr.indexOf(item) === index);

  const company = String(source.company || source.company_name || source.name || "Company");
  const firstName = firstNameFromDecisionMaker(String(source.decision_maker || attrs.decision_maker || ""));

  const whyNow = pickFirstText(
    source.why_now,
    source.why_today,
    source.why,
    painPoints[0],
    source.reason,
    buyingSignals[0],
  );
  const description = pickFirstText(
    source.description,
    attrs.description,
    source.product_description,
    source.summary,
  );
  const vision = pickFirstText(
    source.vision,
    source.mission,
    source.company_goal,
    source.goal,
    source.long_term_goal,
    source.product_vision,
    description,
    whyNow,
  );
  const service = String(source.recommended_service || source.service || attrs.recommended_service || "AI Automation");
  const industry = String(source.industry || attrs.industry || "");
  const website = String(source.website || source.primary_domain || attrs.official_website || "").replace(
    /^https?:\/\//,
    "",
  );
  const cta = String(
    source.recommended_cta || source.next_action || source.suggested_next_step || "Book a short working session",
  );
  const pain = painPoints.join(" · ") || whyNow || "";

  const generated = buildHyperPersonalEmail({
    firstName,
    company,
    website,
    industry,
    service,
    whyNow,
    vision,
    pain,
    evidence,
    description,
    buyingSignals,
    cta,
  });

  // Prefer our hyper-personalized draft. Only keep an upstream template if it
  // clearly contains company-specific content beyond a generic opener.
  const upstreamTemplate = String(
    source.first_message_template || source.email_draft || source.email_body || "",
  )
    .replaceAll("{first_name}", firstName)
    .trim();
  const upstreamLooksGeneric =
    !upstreamTemplate ||
    upstreamTemplate.length < 80 ||
    (!upstreamTemplate.toLowerCase().includes(company.toLowerCase()) &&
      !evidence.some((item) => upstreamTemplate.toLowerCase().includes(item.toLowerCase().slice(0, 24))));

  const emailDraft = upstreamLooksGeneric
    ? generated.body
    : `${normalizeSentence(upstreamTemplate)}

${generated.body}`;

  const personalizedSubject = pickFirstText(
    // Ignore generic upstream subjects that only swap company names poorly
    source.email_subject && String(source.email_subject).toLowerCase().includes("bringing your")
      ? ""
      : source.email_subject,
    source.subject,
    generated.subject,
  );

  const companyId = String(source.company_id || "");
  const maybeRecordId = String(source.record_id || source.id || "");
  const recordId =
    maybeRecordId && companyId && maybeRecordId !== companyId
      ? maybeRecordId
      : source.record_id
        ? String(source.record_id)
        : undefined;

  return {
    id: maybeRecordId || undefined,
    recordId,
    companyId,
    company,
    status: String(source.status || (source.revenue_ready ? "READY TO SEND" : "READY")),
    website: String(source.website || source.primary_domain || ""),
    whyNow: whyNow || "Open to review why this company is next.",
    decisionMaker: String(source.decision_maker || attrs.decision_maker || "—"),
    email: String(source.business_email || source.email || source.decision_maker_email || source.channel || ""),
    dmEmail: String(source.decision_maker_email || ""),
    service: String(source.recommended_service || source.service || "—"),
    industry: String(source.industry || "—"),
    confidence: num(source.confidence ?? source.revenue_ready_score ?? source.trust),
    trust: num(source.trust ?? source.confidence),
    pain: pain || "—",
    evidence: evidence.length ? evidence : whyNow ? [whyNow] : [],
    cta,
    emailSubject: personalizedSubject,
    emailDraft: emailDraft || "Draft will appear after sync.",
    whatsappDraft: String(source.whatsapp_draft || source.whatsapp || generated.whatsapp),
    pipelineValue: num(source.pipeline_value),
    nextAction: String(
      source.next_action ||
        source.next_step ||
        source.suggested_next_step ||
        source.recommended_cta ||
        "Book a short working session",
    ),
    qualityScore: num(source.quality_score),
    qualityGrade: String(source.quality_grade || ""),
    raw: source,
  };
}

export function mergeLead(...parts: Array<Record<string, unknown> | null | undefined>): LeadView {
  const merged: Record<string, unknown> = {};
  for (const part of parts) {
    const row = asRecord(part);
    const brief = asRecord(row.brief);
    const attrs = asRecord(row.attributes);
    Object.assign(merged, attrs, brief, row);
    if (Object.keys(brief).length) merged.brief = brief;
    if (Object.keys(attrs).length) merged.attributes = attrs;
  }
  return normalizeLead(merged);
}

export function indexByCompanyId(rows: Array<Record<string, unknown>>): Map<string, Record<string, unknown>> {
  const map = new Map<string, Record<string, unknown>>();
  for (const row of rows) {
    const id = String(row.company_id || "");
    if (id) map.set(id, row);
  }
  return map;
}

export function funnelCount(funnel: Array<Record<string, unknown>> | undefined, name: string): number {
  const row = (funnel || []).find((item) => String(item.name).toLowerCase() === name.toLowerCase());
  return num(row?.count);
}
