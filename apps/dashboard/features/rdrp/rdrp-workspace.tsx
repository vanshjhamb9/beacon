"use client";

import { useEffect, useState } from "react";
import { Activity, CheckCircle, XCircle, AlertTriangle, Shield, Database, Zap, BarChart3 } from "lucide-react";

const TABS = ["Overview", "Verification", "Technology", "Contacts", "Evidence", "Integrity", "Reliability", "Readiness", "Companies", "Analytics"] as const;

type Tab = (typeof TABS)[number];

const STAGE_COLORS: Record<string, string> = {
  DISCOVERED: "bg-gray-500",
  NORMALIZED: "bg-blue-500",
  COMPANY_VERIFIED: "bg-green-500",
  TECH_VERIFIED: "bg-purple-500",
  DNA_VERIFIED: "bg-yellow-500",
  CONTACT_VERIFIED: "bg-orange-500",
  ICP_VERIFIED: "bg-cyan-500",
  ARIE_ANALYZED: "bg-pink-500",
  RICVP_CALIBRATED: "bg-indigo-500",
  SALES_READY: "bg-emerald-500",
  OUTREACH_READY: "bg-amber-500",
};

export function RdrpWorkspace() {
  const [tab, setTab] = useState<Tab>("Overview");
  const [dashboard, setDashboard] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/rdrp/dashboard")
      .then((r) => r.json())
      .then((d) => { setDashboard(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p className="text-sm text-muted-foreground">Loading RDRP...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Revenue Data Reliability Platform</h1>
          <p className="text-sm text-muted-foreground">Sprint 42.5 — Data trust over data volume</p>
        </div>
        <div className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-emerald-500" />
          <span className="text-sm font-medium text-emerald-500">RDRP Active</span>
        </div>
      </div>

      <div className="flex gap-1 overflow-x-auto border-b">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`whitespace-nowrap px-4 py-2 text-sm font-medium transition ${
              tab === t ? "border-b-2 border-primary text-foreground" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "Overview" && <OverviewTab dashboard={dashboard} />}
      {tab === "Verification" && <VerificationTab />}
      {tab === "Technology" && <TechnologyTab />}
      {tab === "Contacts" && <ContactsTab />}
      {tab === "Evidence" && <EvidenceTab />}
      {tab === "Integrity" && <IntegrityTab />}
      {tab === "Reliability" && <ReliabilityTab />}
      {tab === "Readiness" && <ReadinessTab />}
      {tab === "Companies" && <CompaniesTab />}
      {tab === "Analytics" && <AnalyticsTab />}
    </div>
  );
}

function StatCard({ label, value, icon: Icon, color = "text-primary" }: { label: string; value: string | number; icon: any; color?: string }) {
  return (
    <div className="rounded-xl border bg-card p-4">
      <div className="flex items-center gap-3">
        <div className={`rounded-lg bg-muted p-2`}>
          <Icon className={`h-4 w-4 ${color}`} />
        </div>
        <div>
          <p className="text-xs text-muted-foreground">{label}</p>
          <p className="text-lg font-bold">{value}</p>
        </div>
      </div>
    </div>
  );
}

function OverviewTab({ dashboard }: { dashboard: any }) {
  const stages = dashboard?.stages || {};
  const engines = dashboard?.engines || {};
  const evidenceByType = dashboard?.evidence_by_type || {};

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Companies Tracked" value={dashboard?.total_companies || 0} icon={Database} />
        <StatCard label="Evidence Collected" value={dashboard?.evidence_collected || 0} icon={CheckCircle} color="text-emerald-500" />
        <StatCard label="Engines Active" value={dashboard?.engines_active || 10} icon={Zap} color="text-purple-500" />
        <StatCard label="Pipeline Stages" value={11} icon={BarChart3} color="text-blue-500" />
      </div>

      <div className="rounded-xl border bg-card p-6">
        <h3 className="mb-4 text-lg font-semibold">Readiness Pipeline</h3>
        <div className="flex flex-wrap gap-2">
          {["DISCOVERED", "NORMALIZED", "COMPANY_VERIFIED", "TECH_VERIFIED", "DNA_VERIFIED", "CONTACT_VERIFIED", "ICP_VERIFIED", "ARIE_ANALYZED", "RICVP_CALIBRATED", "SALES_READY", "OUTREACH_READY"].map((stage) => (
            <div key={stage} className="flex items-center gap-2">
              <div className={`h-3 w-3 rounded-full ${STAGE_COLORS[stage] || "bg-gray-400"}`} />
              <span className="text-xs text-muted-foreground">{stage}</span>
              <span className="text-xs font-bold">{stages[stage] || 0}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
        <div className="rounded-xl border bg-card p-4">
          <h4 className="mb-3 text-sm font-semibold">Evidence by Type</h4>
          {Object.entries(evidenceByType).map(([type, count]) => (
            <div key={type} className="flex justify-between py-1">
              <span className="text-xs text-muted-foreground">{type}</span>
              <span className="text-xs font-bold">{count as number}</span>
            </div>
          ))}
        </div>
        <div className="rounded-xl border bg-card p-4">
          <h4 className="mb-3 text-sm font-semibold">Engines Status</h4>
          {Object.entries(engines).map(([name, status]) => (
            <div key={name} className="flex justify-between py-1">
              <span className="text-xs text-muted-foreground">{name.replace(/_/g, " ")}</span>
              <span className={`text-xs font-bold ${status === "active" ? "text-emerald-500" : "text-red-500"}`}>{status as string}</span>
            </div>
          ))}
        </div>
        <div className="rounded-xl border bg-card p-4">
          <h4 className="mb-3 text-sm font-semibold">10 Modules</h4>
          {["Company Verification", "Technology Verification", "DNA Validation", "Decision Maker Reliability", "Contact Verification", "Evidence Engine", "Confidence Engine", "Data Integrity", "Lead Readiness", "Revenue Reliability Score"].map((m) => (
            <div key={m} className="flex justify-between py-1">
              <span className="text-xs text-muted-foreground">{m}</span>
              <CheckCircle className="h-3 w-3 text-emerald-500" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function VerificationTab() {
  return (
    <div className="rounded-xl border bg-card p-6">
      <h3 className="mb-4 text-lg font-semibold">Company Verification Engine</h3>
      <p className="mb-4 text-sm text-muted-foreground">20+ checks: HTTPS, homepage, about, contact, products, checkout, policies, GST, ecommerce, mobile responsive</p>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {["Website Alive", "HTTPS Valid", "Homepage Loads", "About Page", "Contact Page", "Products", "Checkout", "Privacy Policy", "Refund Policy", "Terms", "Shipping Policy", "GST Info", "Active Ecommerce", "Mobile Responsive", "Domain Age", "Store Language", "Store Currency", "Country Detection", "Server Header", "Last Update"].map((check) => (
          <div key={check} className="flex items-center gap-2 rounded-lg border p-2">
            <AlertTriangle className="h-3 w-3 text-yellow-500" />
            <span className="text-xs">{check}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function TechnologyTab() {
  return (
    <div className="rounded-xl border bg-card p-6">
      <h3 className="mb-4 text-lg font-semibold">Technology Verification Engine</h3>
      <p className="mb-4 text-sm text-muted-foreground">18 technologies detected: Shopify, WooCommerce, Magento, Klaviyo, Judge.me, Yotpo, Recharge, Shiprocket, Gorgias, Zendesk, Freshchat, GA4, Meta Pixel, GTM, Razorpay, Stripe, Shopify Plus, and more</p>
      <div className="grid grid-cols-3 gap-3 md:grid-cols-6">
        {["shopify", "woocommerce", "magento", "klaviyo", "judge_me", "yotpo", "recharge", "shiprocket", "gorgias", "zendesk", "freshchat", "ga4", "meta_pixel", "gtm", "razorpay", "stripe", "shopify_plus", "bigcommerce"].map((tech) => (
          <div key={tech} className="flex flex-col items-center gap-1 rounded-lg border p-3">
            <Zap className="h-4 w-4 text-purple-500" />
            <span className="text-xs font-medium">{tech.replace(/_/g, " ")}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ContactsTab() {
  return (
    <div className="rounded-xl border bg-card p-6">
      <h3 className="mb-4 text-lg font-semibold">Contact Verification Engine</h3>
      <p className="mb-4 text-sm text-muted-foreground">Email: format, MX, SMTP, disposable, role-based, catch-all, corporate. Phone: country, WhatsApp, mobile/landline, duplicates, format, reachability</p>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h4 className="mb-2 text-sm font-semibold">Email Checks</h4>
          {["Format Valid", "MX Found", "SMTP Valid", "Disposable", "Role-based", "Catch-all", "Corporate", "Risk Level", "Deliverability"].map((c) => (
            <div key={c} className="flex items-center gap-2 py-1"><CheckCircle className="h-3 w-3 text-emerald-500" /><span className="text-xs">{c}</span></div>
          ))}
        </div>
        <div>
          <h4 className="mb-2 text-sm font-semibold">Phone Checks</h4>
          {["Country Detection", "WhatsApp Detection", "Mobile/Landline", "Format Valid", "Duplicate Detection", "Reachability Score", "Placeholder Detection"].map((c) => (
            <div key={c} className="flex items-center gap-2 py-1"><CheckCircle className="h-3 w-3 text-emerald-500" /><span className="text-xs">{c}</span></div>
          ))}
        </div>
      </div>
    </div>
  );
}

function EvidenceTab() {
  return (
    <div className="rounded-xl border bg-card p-6">
      <h3 className="mb-4 text-lg font-semibold">Evidence Engine</h3>
      <p className="text-sm text-muted-foreground">Every field in Beacon must contain evidence. Every recommendation must explain WHY. Evidence types: HTML, header, script, URL, screenshot. SHA-256 hashed for immutability.</p>
    </div>
  );
}

function IntegrityTab() {
  return (
    <div className="rounded-xl border bg-card p-6">
      <h3 className="mb-4 text-lg font-semibold">Data Integrity Engine</h3>
      <p className="mb-4 text-sm text-muted-foreground">Auto-detect: duplicate phones, duplicate emails, broken domains, redirect chains, wrong TLD, parent company mismatch, marketplace companies, enterprise leakage, inactive companies, dead stores, missing products, placeholder values</p>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {["Duplicate Phone", "Duplicate Email", "Placeholder Phone", "Placeholder Email", "TLD Mismatch", "HTTP Redirect", "Enterprise Leakage", "No Products", "Broken Domain", "Redirect Chain", "Wrong TLD", "Parent Mismatch"].map((c) => (
          <div key={c} className="flex items-center gap-2 rounded-lg border p-2">
            <Shield className="h-3 w-3 text-blue-500" />
            <span className="text-xs">{c}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ReliabilityTab() {
  return (
    <div className="rounded-xl border bg-card p-6">
      <h3 className="mb-4 text-lg font-semibold">Revenue Reliability Score</h3>
      <p className="mb-4 text-sm text-muted-foreground">0-100 score. Components: Company Trust (20%), Technology Trust (20%), Contact Trust (15%), Evidence Trust (15%), Freshness (10%), Data Completeness (10%), Verification Success (10%)</p>
      <div className="grid grid-cols-4 gap-3">
        {[{ grade: "Reliable", min: 85, color: "text-emerald-500" }, { grade: "Likely Reliable", min: 70, color: "text-blue-500" }, { grade: "Needs Review", min: 50, color: "text-yellow-500" }, { grade: "Reject", min: 0, color: "text-red-500" }].map((g) => (
          <div key={g.grade} className="rounded-lg border p-3 text-center">
            <p className={`text-lg font-bold ${g.color}`}>{g.min}+</p>
            <p className="text-xs text-muted-foreground">{g.grade}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function ReadinessTab() {
  return (
    <div className="rounded-xl border bg-card p-6">
      <h3 className="mb-4 text-lg font-semibold">Lead Readiness Engine</h3>
      <p className="mb-4 text-sm text-muted-foreground">Strict pipeline. Nothing skips stages. DISCOVERED → NORMALIZED → COMPANY_VERIFIED → TECH_VERIFIED → DNA_VERIFIED → CONTACT_VERIFIED → ICP_VERIFIED → ARIE_ANALYZED → RICVP_CALIBRATED → SALES_READY → OUTREACH_READY</p>
      <div className="flex flex-wrap gap-2">
        {["DISCOVERED", "NORMALIZED", "COMPANY_VERIFIED", "TECH_VERIFIED", "DNA_VERIFIED", "CONTACT_VERIFIED", "ICP_VERIFIED", "ARIE_ANALYZED", "RICVP_CALIBRATED", "SALES_READY", "OUTREACH_READY"].map((s, i) => (
          <div key={s} className="flex items-center gap-2">
            <div className={`h-6 w-6 rounded-full flex items-center justify-center text-xs font-bold text-white ${STAGE_COLORS[s]}`}>{i + 1}</div>
            <span className="text-xs">{s}</span>
            {i < 10 && <span className="text-muted-foreground">→</span>}
          </div>
        ))}
      </div>
    </div>
  );
}

function CompaniesTab() {
  return (
    <div className="rounded-xl border bg-card p-6">
      <h3 className="mb-4 text-lg font-semibold">Verified Companies</h3>
      <p className="text-sm text-muted-foreground">Companies will appear here after RDRP verification. Each company shows: Verification %, Technology %, Evidence %, Confidence %, Reliability %, Sales Ready %</p>
    </div>
  );
}

function AnalyticsTab() {
  return (
    <div className="rounded-xl border bg-card p-6">
      <h3 className="mb-4 text-lg font-semibold">RDRP Analytics</h3>
      <p className="text-sm text-muted-foreground">Analytics and metrics will be available after processing companies through the RDRP pipeline.</p>
    </div>
  );
}
