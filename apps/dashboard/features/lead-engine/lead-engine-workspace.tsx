"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Building2,
  CheckSquare,
  Clock,
  Loader2,
  Play,
  Save,
  Send,
  Sparkles,
  Square,
  Zap,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import {
  beaconApi,
  type LeadEngineLead,
  type LeadEngineRun,
} from "@/lib/api/beacon";
import { cn } from "@/lib/utils";

type Product = "comai" | "inowix" | "cybersecurity" | "cyber";

type IcpDraft = {
  key: string;
  name: string;
  service_match: string;
  lists: string[];
  company_name_contains: string;
  domains: string;
  linkedin_url_required: boolean;
  employee_count_min: number;
  employee_count_max: number;
  industries: string[];
  company_types: string[];
  countries: string[];
  headquarters_cities: string[];
  specialties: string[];
  year_founded_min: number;
  year_founded_max: number;
  technology_stack: string[];
};

const INDUSTRY_OPTIONS = [
  "fashion",
  "beauty",
  "skincare",
  "jewellery",
  "food",
  "home",
  "electronics",
  "saas",
  "software",
  "health",
];

const TECH_OPTIONS = ["shopify", "woocommerce", "whatsapp", "meta ads", "flutter", "ios", "react"];

const CYB_INDUSTRY_OPTIONS = [
  "SaaS", "Fintech", "Healthtech", "Ecommerce", "AI",
  "EdTech", "HRTech", "InsurTech", "LegalTech", "PropTech", "Logistics",
];
const CYB_SERVICE_OPTIONS = [
  "penetration_testing", "vulnerability_assessment", "web_app_security",
  "api_security", "cloud_security", "compliance", "security_audit",
];
const CYB_GEO_TIER1 = [
  "United States", "United Kingdom", "Canada", "Australia", "UAE",
  "Saudi Arabia", "Singapore", "Switzerland", "Netherlands", "Germany",
];
const CYB_GEO_TIER2 = [
  "Ireland", "Sweden", "Norway", "Denmark", "Finland", "France",
  "New Zealand", "Japan", "South Korea", "Israel",
];
const CYB_PRIORITY_OPTIONS = ["P0 only", "P0 + P1", "All"];
const TYPE_OPTIONS = [
  { id: "d2c_brand", label: "D2C brand" },
  { id: "agency_partner", label: "Agency partner" },
  { id: "saas_product", label: "SaaS product" },
];
const CITY_OPTIONS = [
  "Mumbai",
  "Delhi",
  "Bangalore",
  "Hyderabad",
  "Pune",
  "Surat",
  "Ahmedabad",
  "Chennai",
];

function defaultIcp(product: Product): IcpDraft {
  if (product === "cybersecurity") {
    return {
      key: "cybersecurity-lead-engine",
      name: "Cybersecurity Lead Engine",
      service_match: "cybersecurity",
      lists: ["cybersecurity-leads"],
      company_name_contains: "",
      domains: "",
      linkedin_url_required: false,
      employee_count_min: 5,
      employee_count_max: 10000,
      industries: ["SaaS", "Fintech", "Healthtech", "Ecommerce"],
      company_types: ["saas_product"],
      countries: CYB_GEO_TIER1,
      headquarters_cities: [],
      specialties: CYB_SERVICE_OPTIONS,
      year_founded_min: 2015,
      year_founded_max: 2026,
      technology_stack: [],
    };
  }
  if (product === "inowix") {
    return {
      key: "inowix-lead-engine",
      name: "Inowix Lead Engine",
      service_match: "Inowix",
      lists: ["Inowix tiny/mid eng"],
      company_name_contains: "",
      domains: "",
      linkedin_url_required: false,
      employee_count_min: 2,
      employee_count_max: 70,
      industries: ["saas", "software", "artificial intelligence", "mobile apps", "fintech", "healthtech", "ecommerce tooling", "developer tools", "productivity", "marketplace", "design tools", "data tools", "no-code", "analytics", "infrastructure", "devops", "cybersecurity", "edtech", "climate tech"],
      company_types: ["saas_product"],
      countries: ["India", "United States", "United Kingdom", "Germany", "Israel", "Singapore"],
      headquarters_cities: [
        "Bangalore", "Bengaluru", "Mumbai", "Delhi", "Hyderabad", "Pune", "Noida", "Ahmedabad", "Chennai", "Kochi", "Jaipur", "Goa",
        "San Francisco", "New York", "Austin", "Seattle", "Boston", "Los Angeles", "Chicago", "Toronto",
        "London",
        "Cologne", "Berlin", "Munich",
        "Tel Aviv",
        "Amsterdam", "Paris", "Helsinki", "Stockholm", "Copenhagen", "Tallinn", "Lisbon", "Zurich", "Barcelona",
        "Sydney", "Melbourne", "Tokyo", "Dubai", "Seoul", "Taipei", "Bangkok", "Ho Chi Minh City", "Sao Paulo",
      ],
      specialties: ["ai", "mobile"],
      year_founded_min: 2018,
      year_founded_max: 2026,
      technology_stack: ["react", "flutter", "ios"],
    };
  }
  return {
    key: "comai-lead-engine",
    name: "COMAI Lead Engine",
    service_match: "COMAI",
    lists: ["COMAI small/mid D2C"],
    company_name_contains: "",
    domains: "",
    linkedin_url_required: false,
    employee_count_min: 5,
    employee_count_max: 40,
    industries: ["fashion", "beauty", "jewellery", "skincare", "food"],
    company_types: ["d2c_brand"],
    countries: ["India"],
    headquarters_cities: [],
    specialties: ["fashion", "jewellery", "skincare"],
    year_founded_min: 2018,
    year_founded_max: 2026,
    technology_stack: ["shopify", "whatsapp", "meta ads"],
  };
}

function FilterRow({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="border-b border-border/50 py-3">
      <div className="mb-2 flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
      </div>
      {children}
    </div>
  );
}

function ChipMulti({
  options,
  selected,
  onChange,
}: {
  options: string[];
  selected: string[];
  onChange: (next: string[]) => void;
}) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {options.map((opt) => {
        const on = selected.includes(opt);
        return (
          <button
            key={opt}
            type="button"
            onClick={() =>
              onChange(on ? selected.filter((x) => x !== opt) : [...selected, opt])
            }
            className={cn(
              "rounded-md border px-2 py-1 text-[11px] transition",
              on
                ? "border-primary/40 bg-primary/15 text-foreground"
                : "border-border/60 text-muted-foreground hover:bg-muted/40",
            )}
          >
            {opt}
          </button>
        );
      })}
    </div>
  );
}

export function LeadEngineWorkspace() {
  const qc = useQueryClient();
  const [product, setProduct] = useState<Product>("comai");
  const [limit, setLimit] = useState(80);
  const [autoOn, setAutoOn] = useState(false);

  const [icp, setIcp] = useState<IcpDraft>(() => defaultIcp("comai"));
  const [runId, setRunId] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [preview, setPreview] = useState<{
    subject: string;
    body: string;
    company?: string;
    approveMode?: boolean;
  } | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const presets = useQuery({
    queryKey: ["lead-engine-presets"],
    queryFn: beaconApi.leadEnginePresets,
  });

  useEffect(() => {
    const presetKey = product === "cybersecurity" ? "cyber" : product;
    const preset = presets.data?.presets?.[presetKey];
    if (!preset || preset.error) {
      setIcp(defaultIcp(product));
      return;
    }
    const base = defaultIcp(product);
    setIcp({
      ...base,
      key: String(preset.key || presetKey),
      name: String(preset.name || presetKey),
      service_match: product === "comai" ? "COMAI" : product === "cybersecurity" ? "Cybersecurity" : "Inowix",
      // Keep dashboard-friendly bands; YAML min/max can be too wide/narrow for Lead Engine
      employee_count_min: base.employee_count_min,
      employee_count_max: base.employee_count_max,
      industries: base.industries,
      specialties: base.specialties,
      countries: (preset.countries as string[])?.length ? (preset.countries as string[]) : ["India"],
      headquarters_cities: [],
      technology_stack: base.technology_stack,
      company_types: base.company_types,
      lists: (preset.lists as string[]) || base.lists,
    });
  }, [product, presets.data]);

  const runQuery = useQuery({
    queryKey: ["lead-engine-run", runId],
    queryFn: () => beaconApi.leadEngineRun(runId!),
    enabled: Boolean(runId),
    refetchInterval: (q) => {
      const d = q.state.data;
      if (!d) return false;
      if (d.status === "queued" || d.status === "running") return 400;
      if (d.enrich_status === "running") return 400;
      return false;
    },
  });

  const leadsQuery = useQuery({
    queryKey: ["lead-engine-leads", runId],
    queryFn: () => beaconApi.leadEngineLeads(runId!),
    enabled: Boolean(runId) && runQuery.data?.status === "completed",
  });

  const icpPayload = useMemo(
    () => ({
      key: icp.key,
      name: icp.name,
      service_match: icp.service_match,
      employee_count_min: icp.employee_count_min,
      employee_count_max: icp.employee_count_max,
      industries: icp.industries,
      specialties: icp.specialties,
      countries: icp.countries,
      headquarters_cities: icp.headquarters_cities,
      technology_stack: icp.technology_stack,
      company_types: icp.company_types,
      year_founded_min: icp.year_founded_min,
      year_founded_max: icp.year_founded_max,
      linkedin_url_required: icp.linkedin_url_required,
      company_name_contains: icp.company_name_contains
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      domains: icp.domains
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      lists: icp.lists,
    }),
    [icp],
  );

  const saveIcp = useMutation({
    mutationFn: () =>
      beaconApi.createIcp({
        ...icpPayload,
        priority: product === "comai" ? 20 : 15,
      }),
    onSuccess: () => {
      setMessage("ICP saved to Target Account profiles.");
      void qc.invalidateQueries({ queryKey: ["icps"] });
    },
    onError: (e: Error) => setMessage(e.message || "Failed to save ICP"),
  });

  const autoStatus = useQuery({
    queryKey: ["lead-engine-auto"],
    queryFn: beaconApi.leadEngineAutoStatus,
    refetchInterval: 5000,
  });

  useEffect(() => {
    if (autoStatus.data) setAutoOn(Boolean(autoStatus.data.enabled));
  }, [autoStatus.data?.enabled]);

  const startAuto = useMutation({
    mutationFn: () =>
      beaconApi.leadEngineAutoStart({
        product: product === "cybersecurity" ? "cyber" : product,
        limit,
        interval_sec: 600,
        icp: icpPayload,
      }),
    onSuccess: () => {
      setAutoOn(true);
      setMessage("Auto-run ON — fresh discovery every 10 minutes into outreach pool.");
      void qc.invalidateQueries({ queryKey: ["lead-engine-auto"] });
    },
    onError: (e: Error) => setMessage(e.message || "Failed to start auto-run"),
  });

  const stopAuto = useMutation({
    mutationFn: () => beaconApi.leadEngineAutoStop(),
    onSuccess: () => {
      setAutoOn(false);
      setMessage("Auto-run stopped.");
      void qc.invalidateQueries({ queryKey: ["lead-engine-auto"] });
    },
    onError: (e: Error) => setMessage(e.message || "Failed to stop auto-run"),
  });

  const loadPool = useMutation({
    mutationFn: () => beaconApi.leadEnginePoolLoad(limit),
    onSuccess: (run: LeadEngineRun) => {
      setRunId(run.run_id);
      setSelected(new Set());
      setMessage(`Loaded ${run.lead_count ?? run.counts?.scored ?? 0} NEW pooled leads for outreach.`);
      void qc.invalidateQueries({ queryKey: ["lead-engine-run", run.run_id] });
      void qc.invalidateQueries({ queryKey: ["lead-engine-leads", run.run_id] });
      void qc.invalidateQueries({ queryKey: ["lead-engine-auto"] });
    },
    onError: (e: Error) => setMessage(e.message || "Outreach pool empty — run engine / auto first"),
  });

  const startEngine = useMutation({
    mutationFn: () => beaconApi.leadEngineStart({ product: product === "cybersecurity" ? "cyber" : product, limit, icp: icpPayload }),
    onSuccess: (run: LeadEngineRun) => {
      setRunId(run.run_id);
      setSelected(new Set());
      setMessage(`Engine started: ${run.run_id.slice(0, 8)}…`);
      void qc.invalidateQueries({ queryKey: ["lead-engine-run", run.run_id] });
    },
    onError: (e: Error) => setMessage(e.message || "Failed to start engine"),
  });

  const enrich = useMutation({
    mutationFn: () => beaconApi.leadEngineEnrich(runId!, [...selected]),
    onSuccess: () => {
      setMessage("Enrichment started…");
      void qc.invalidateQueries({ queryKey: ["lead-engine-run", runId] });
    },
    onError: (e: Error) => setMessage(e.message || "Enrichment failed"),
  });

  useEffect(() => {
    if (runQuery.data?.enrich_status === "completed") {
      setMessage(runQuery.data.enrich_label || "Enrichment complete.");
      void qc.invalidateQueries({ queryKey: ["lead-engine-leads", runId] });
    }
  }, [runQuery.data?.enrich_status, runQuery.data?.enrich_label, runId, qc]);

  const drafts = useMutation({
    mutationFn: () => beaconApi.leadEngineDrafts(runId!, selected.size ? [...selected] : undefined),
    onSuccess: (r) => {
      setMessage(`Drafted ${r.count} hyperpersonalized emails.`);
      if (r.drafts[0]) {
        setPreview({
          subject: r.drafts[0].subject,
          body: r.drafts[0].body,
          company: r.drafts[0].company,
          approveMode: false,
        });
      }
      void qc.invalidateQueries({ queryKey: ["lead-engine-leads", runId] });
    },
    onError: (e: Error) => setMessage(e.message || "Failed to generate drafts"),
  });

  const prepareOutreach = useMutation({
    mutationFn: async () => {
      if (!runId) throw new Error("Start Engine first");
      if (!selected.size) throw new Error("Select leads to outreach");
      const r = await beaconApi.leadEngineDrafts(runId, [...selected]);
      return r;
    },
    onSuccess: (r) => {
      const first = r.drafts[0];
      setMessage(`Ready to approve ${r.count} drafts (from vansh@inowix.in · dual CC).`);
      setPreview({
        subject: first?.subject || `${r.count} drafts ready`,
        body:
          first?.body ||
          "Drafts generated. Confirm Send approved to deliver selected leads.",
        company: first?.company || `${r.count} selected`,
        approveMode: true,
      });
      void qc.invalidateQueries({ queryKey: ["lead-engine-leads", runId] });
    },
    onError: (e: Error) => setMessage(e.message || "Failed to prepare outreach"),
  });

  const send = useMutation({
    mutationFn: () => {
      if (!selected.size) throw new Error("Select leads to send");
      return beaconApi.leadEngineSend(runId!, [...selected], false);
    },
    onSuccess: (r) => {
      setPreview(null);
      setMessage(`Sent ${r.sent}/${r.attempted} (CC: ${r.cc.join(", ")})`);
      void qc.invalidateQueries({ queryKey: ["lead-engine-leads", runId] });
      void qc.invalidateQueries({ queryKey: ["lead-engine-run", runId] });
    },
    onError: (e: Error) => setMessage(e.message || "Send failed"),
  });

  const leads: LeadEngineLead[] = leadsQuery.data?.leads ?? [];
  const run = runQuery.data;
  const allSelected = leads.length > 0 && selected.size === leads.length;

  if (presets.isLoading) return <Skeleton className="h-64 w-full" />;
  if (presets.isError) {
    return (
      <ErrorState
        description="Lead Engine presets unavailable."
        onRetry={() => void presets.refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <SectionLabel>Revenue Ops</SectionLabel>
          <h1 className="font-display text-3xl font-semibold tracking-tight">Lead Engine</h1>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
            Only NEW high-intent leads (already-contacted excluded). Turn on Auto-run every 10
            minutes to fill the outreach pool, then Load pool → Start Outreach.
            {autoStatus.data?.enabled
              ? ` Auto active · pool ${autoStatus.data.pool_ready} ready · runs ${autoStatus.data.runs_completed}.`
              : ""}
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-xl border border-border/60 bg-card/40 p-1">
          {(["comai", "inowix", "cybersecurity"] as const).map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => { setProduct(p); setIcp(defaultIcp(p)); setRunId(null); setSelected(new Set()); setMessage(null); }}
              className={cn(
                "rounded-lg px-3 py-1.5 text-sm font-medium capitalize transition",
                product === p ? "bg-primary/15 text-foreground" : "text-muted-foreground",
              )}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {message ? (
        <div className="rounded-xl border border-border/60 bg-muted/20 px-4 py-2 text-sm">{message}</div>
      ) : null}

      {/* Mega Extraction Status */}
      <MegaExtractionStatus />

      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        {/* COMPANY filters — Apollo-style */}
        <Card className="h-fit border-border/60 bg-card/50">
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <Building2 className="h-4 w-4 text-muted-foreground" />
              <CardTitle className="text-sm font-semibold uppercase tracking-wide">
                {product === "cybersecurity" ? "Cybersecurity ICP" : "Company"}
              </CardTitle>
            </div>
            <CardDescription>
              {product === "cybersecurity"
                ? "Filter by service needs, industry, geography, and priority level"
                : "Hard filters: mega brands out · unknown headcount out · founder/personal emails preferred"}
            </CardDescription>
          </CardHeader>
          <CardContent className="max-h-[70vh] space-y-0 overflow-y-auto pr-1">
            {product === "cybersecurity" ? (
              <>
                <FilterRow label="Service Needs">
                  <ChipMulti
                    options={CYB_SERVICE_OPTIONS}
                    selected={icp.specialties}
                    onChange={(specialties) => setIcp((s) => ({ ...s, specialties }))}
                  />
                </FilterRow>
                <FilterRow label="Industry">
                  <ChipMulti
                    options={CYB_INDUSTRY_OPTIONS}
                    selected={icp.industries}
                    onChange={(industries) => setIcp((s) => ({ ...s, industries }))}
                  />
                </FilterRow>
                <FilterRow label="Geography (Tier 1)">
                  <ChipMulti
                    options={CYB_GEO_TIER1}
                    selected={icp.countries}
                    onChange={(countries) => setIcp((s) => ({ ...s, countries }))}
                  />
                </FilterRow>
                <FilterRow label="Geography (Tier 2)">
                  <ChipMulti
                    options={CYB_GEO_TIER2}
                    selected={icp.countries.filter((c) => CYB_GEO_TIER2.includes(c))}
                    onChange={(t2) => {
                      const t1 = icp.countries.filter((c) => CYB_GEO_TIER1.includes(c));
                      setIcp((s) => ({ ...s, countries: [...t1, ...t2] }));
                    }}
                  />
                </FilterRow>
                <FilterRow label="Company Size">
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      className="w-full rounded-lg border border-border/60 bg-background px-3 py-2 text-sm"
                      value={icp.employee_count_min}
                      onChange={(e) =>
                        setIcp((s) => ({ ...s, employee_count_min: Number(e.target.value) || 0 }))
                      }
                    />
                    <span className="text-xs text-muted-foreground">to</span>
                    <input
                      type="number"
                      className="w-full rounded-lg border border-border/60 bg-background px-3 py-2 text-sm"
                      value={icp.employee_count_max}
                      onChange={(e) =>
                        setIcp((s) => ({ ...s, employee_count_max: Number(e.target.value) || 0 }))
                      }
                    />
                  </div>
                </FilterRow>
                <FilterRow label="Company Name">
                  <input
                    className="w-full rounded-lg border border-border/60 bg-background px-3 py-2 text-sm"
                    value={icp.company_name_contains}
                    onChange={(e) => setIcp((s) => ({ ...s, company_name_contains: e.target.value }))}
                    placeholder="Contains…"
                  />
                </FilterRow>
              </>
            ) : (
              <>
                <FilterRow label="Lists">
                  <input
                    className="w-full rounded-lg border border-border/60 bg-background px-3 py-2 text-sm"
                    value={icp.lists.join(", ")}
                    onChange={(e) =>
                      setIcp((s) => ({
                        ...s,
                        lists: e.target.value
                          .split(",")
                          .map((x) => x.trim())
                          .filter(Boolean),
                      }))
                    }
                    placeholder="Saved ICP list names"
                  />
                </FilterRow>
                <FilterRow label="Company Name">
                  <input
                    className="w-full rounded-lg border border-border/60 bg-background px-3 py-2 text-sm"
                    value={icp.company_name_contains}
                    onChange={(e) => setIcp((s) => ({ ...s, company_name_contains: e.target.value }))}
                    placeholder="Contains…"
                  />
                </FilterRow>
                <FilterRow label="Domain">
                  <input
                    className="w-full rounded-lg border border-border/60 bg-background px-3 py-2 text-sm"
                    value={icp.domains}
                    onChange={(e) => setIcp((s) => ({ ...s, domains: e.target.value }))}
                    placeholder="brand.com, …"
                  />
                </FilterRow>
                <FilterRow label="Professional Network URL">
                  <label className="flex items-center gap-2 text-sm text-muted-foreground">
                    <input
                      type="checkbox"
                      checked={icp.linkedin_url_required}
                      onChange={(e) => setIcp((s) => ({ ...s, linkedin_url_required: e.target.checked }))}
                    />
                    Prefer LinkedIn-accessible founders
                  </label>
                </FilterRow>
                <FilterRow label="Headcount">
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      className="w-full rounded-lg border border-border/60 bg-background px-3 py-2 text-sm"
                      value={icp.employee_count_min}
                      onChange={(e) =>
                        setIcp((s) => ({ ...s, employee_count_min: Number(e.target.value) || 0 }))
                      }
                    />
                    <span className="text-xs text-muted-foreground">to</span>
                    <input
                      type="number"
                      className="w-full rounded-lg border border-border/60 bg-background px-3 py-2 text-sm"
                      value={icp.employee_count_max}
                      onChange={(e) =>
                        setIcp((s) => ({ ...s, employee_count_max: Number(e.target.value) || 0 }))
                      }
                    />
                  </div>
                </FilterRow>
                <FilterRow label="Industry">
                  <ChipMulti
                    options={INDUSTRY_OPTIONS}
                    selected={icp.industries}
                    onChange={(industries) => setIcp((s) => ({ ...s, industries }))}
                  />
                </FilterRow>
                <FilterRow label="Type">
                  <ChipMulti
                    options={TYPE_OPTIONS.map((t) => t.id)}
                    selected={icp.company_types}
                    onChange={(company_types) => setIcp((s) => ({ ...s, company_types }))}
                  />
                </FilterRow>
                <FilterRow label="Headquarters">
                  <ChipMulti
                    options={CITY_OPTIONS}
                    selected={icp.headquarters_cities}
                    onChange={(headquarters_cities) => setIcp((s) => ({ ...s, headquarters_cities }))}
                  />
                  <p className="mt-2 text-[11px] text-muted-foreground">Country: India (preset)</p>
                </FilterRow>
                <FilterRow label="Specialties">
                  <ChipMulti
                    options={INDUSTRY_OPTIONS}
                    selected={icp.specialties}
                    onChange={(specialties) => setIcp((s) => ({ ...s, specialties }))}
                  />
                </FilterRow>
                <FilterRow label="Year founded">
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      className="w-full rounded-lg border border-border/60 bg-background px-3 py-2 text-sm"
                      value={icp.year_founded_min}
                      onChange={(e) =>
                        setIcp((s) => ({ ...s, year_founded_min: Number(e.target.value) || 2000 }))
                      }
                    />
                    <span className="text-xs text-muted-foreground">to</span>
                    <input
                      type="number"
                      className="w-full rounded-lg border border-border/60 bg-background px-3 py-2 text-sm"
                      value={icp.year_founded_max}
                      onChange={(e) =>
                        setIcp((s) => ({ ...s, year_founded_max: Number(e.target.value) || 2026 }))
                      }
                    />
                  </div>
                </FilterRow>
                <FilterRow label="Technologies">
                  <ChipMulti
                    options={TECH_OPTIONS}
                    selected={icp.technology_stack}
                    onChange={(technology_stack) => setIcp((s) => ({ ...s, technology_stack }))}
                  />
                </FilterRow>
              </>
            )}
          </CardContent>
        </Card>

        {/* Controls + leads */}
        <div className="space-y-4">
          <Card className="border-border/60 bg-card/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Run controls</CardTitle>
              <CardDescription>
                Start engine when ready. Outreach is approve-gated (preview → send).
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap items-center gap-3">
              <label className="flex items-center gap-2 text-sm text-muted-foreground">
                Limit
                <input
                  type="number"
                  min={1}
                  max={150}
                  value={limit}
                  onChange={(e) => setLimit(Math.min(150, Math.max(1, Number(e.target.value) || 80)))}
                  className="w-20 rounded-lg border border-border/60 bg-background px-2 py-1.5 text-sm text-foreground"
                />
              </label>
              <Button
                variant="outline"
                size="sm"
                onClick={() => saveIcp.mutate()}
                disabled={saveIcp.isPending}
              >
                {saveIcp.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                Save ICP
              </Button>
              <Button size="sm" onClick={() => startEngine.mutate()} disabled={startEngine.isPending}>
                {startEngine.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
                Start Engine
              </Button>
              <Button
                variant={autoOn ? "default" : "outline"}
                size="sm"
                disabled={startAuto.isPending || stopAuto.isPending}
                onClick={() => (autoOn ? stopAuto.mutate() : startAuto.mutate())}
              >
                {(startAuto.isPending || stopAuto.isPending) && (
                  <Loader2 className="h-4 w-4 animate-spin" />
                )}
                {autoOn ? "Auto-run ON (10m)" : "Auto-run every 10m"}
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={loadPool.isPending}
                onClick={() => loadPool.mutate()}
              >
                {loadPool.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                Load pool for outreach
                {autoStatus.data?.pool_ready ? ` (${autoStatus.data.pool_ready})` : ""}
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={!runId || !selected.size || enrich.isPending || run?.enrich_status === "running"}
                onClick={() => enrich.mutate()}
              >
                {enrich.isPending || run?.enrich_status === "running" ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="h-4 w-4" />
                )}
                Enrich selected
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={!runId || run?.status !== "completed" || drafts.isPending}
                onClick={() => drafts.mutate()}
              >
                Draft outreach
              </Button>
              <Button
                size="sm"
                disabled={!runId || !selected.size || prepareOutreach.isPending || send.isPending}
                onClick={() => prepareOutreach.mutate()}
              >
                {prepareOutreach.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
                Start Outreach
              </Button>
              {runId && run?.status === "completed" ? (
                <a
                  className="text-xs text-muted-foreground underline-offset-2 hover:underline"
                  href={beaconApi.leadEngineExportUrl(runId)}
                  target="_blank"
                  rel="noreferrer"
                >
                  Export CSV
                </a>
              ) : null}
            </CardContent>
          </Card>

          {run ? (
            <div className="space-y-2">
              <div className="flex flex-wrap gap-2 text-sm">
                <Badge>Volume + ICP strict + Intent</Badge>
                <Badge variant="outline">status: {run.status}</Badge>
                <Badge variant="outline">stage: {run.stage}</Badge>
                <Badge variant="outline">extracted: {run.counts?.extracted ?? 0}</Badge>
                <Badge variant="outline">enriched: {run.counts?.enriched ?? 0}</Badge>
                <Badge variant="outline">scored: {run.counts?.scored ?? 0}</Badge>
                <Badge variant="outline">ready: {run.counts?.ready ?? 0}</Badge>
                {(run.counts?.icp_core ?? 0) > 0 ? (
                  <Badge variant="outline">ICP-core: {run.counts?.icp_core}</Badge>
                ) : null}
                {(run.counts?.icp_adjacent ?? 0) > 0 ? (
                  <Badge variant="outline">adjacent: {run.counts?.icp_adjacent}</Badge>
                ) : null}
                <Badge variant="outline">sent: {run.counts?.sent ?? 0}</Badge>
                {(run.counts?.new_unique ?? 0) > 0 ? (
                  <Badge variant="outline">new unique: {run.counts?.new_unique}</Badge>
                ) : null}
                {(run.counts?.rejected ?? 0) > 0 ? (
                  <Badge variant="outline">rejected by ICP: {run.counts?.rejected}</Badge>
                ) : null}
                {(run.counts?.soft_flagged ?? 0) > 0 ? (
                  <Badge variant="outline">soft flags: {run.counts?.soft_flagged}</Badge>
                ) : null}
              </div>
              {(run.status === "queued" || run.status === "running" || startEngine.isPending) && (
                <div className="rounded-xl border border-border/60 bg-muted/20 p-3">
                  <div className="mb-2 flex items-center justify-between gap-3 text-sm">
                    <span className="flex items-center gap-2 text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      {run.stage_label || `Engine ${run.stage}…`}
                    </span>
                    <span className="font-mono text-xs">{Math.min(100, run.progress_pct ?? 5)}%</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-black/30">
                    <div
                      className="h-full rounded-full bg-primary transition-all duration-500"
                      style={{ width: `${Math.min(100, Math.max(5, run.progress_pct ?? 5))}%` }}
                    />
                  </div>
                  <div className="mt-2 flex flex-wrap gap-3 text-[11px] text-muted-foreground">
                    {["extracting", "enriching", "scoring", "ready"].map((s) => (
                      <span
                        key={s}
                        className={cn(
                          "capitalize",
                          run.stage === s || (s === "ready" && run.status === "completed")
                            ? "text-foreground"
                            : "",
                        )}
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {run.enrich_status === "running" ? (
                <div className="rounded-xl border border-border/60 bg-muted/20 p-3">
                  <div className="mb-2 flex items-center justify-between gap-3 text-sm">
                    <span className="flex items-center gap-2 text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      {run.enrich_label || "Enriching selected leads…"}
                    </span>
                    <span className="font-mono text-xs">
                      {Math.min(100, run.enrich_progress_pct ?? 5)}%
                    </span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-black/30">
                    <div
                      className="h-full rounded-full bg-emerald-500/80 transition-all duration-500"
                      style={{
                        width: `${Math.min(100, Math.max(5, run.enrich_progress_pct ?? 5))}%`,
                      }}
                    />
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}

          {run?.rejects && Object.keys(run.rejects).length > 0 ? (
            <p className="text-xs text-muted-foreground">
              Hard rejects —{" "}
              {Object.entries(run.rejects)
                .filter(([, n]) => Number(n) > 0)
                .map(([k, n]) => `${k}: ${n}`)
                .join(" · ") || "none"}
            </p>
          ) : null}
          {run?.soft_flags && Object.values(run.soft_flags).some((n) => Number(n) > 0) ? (
            <p className="text-xs text-muted-foreground">
              Soft flags (kept) —{" "}
              {Object.entries(run.soft_flags)
                .filter(([, n]) => Number(n) > 0)
                .map(([k, n]) => `${k}: ${n}`)
                .join(" · ") || "none"}
            </p>
          ) : null}

          <Card className="border-border/60 bg-card/50">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <CardTitle className="text-base">
                    {product === "cybersecurity" ? "Cybersecurity Leads" : "High-intent leads"}
                  </CardTitle>
                  <CardDescription>
                    {product === "cybersecurity"
                      ? "Companies with active cybersecurity buying signals · P0/P1 priority · verified contacts"
                      : "Mid D2C · ICP-strict · strong signals (not FAQ-only) · Premkala drafts"}
                  </CardDescription>
                </div>
                {leads.length > 0 ? (
                  <button
                    type="button"
                    className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground"
                    onClick={() =>
                      setSelected(allSelected ? new Set() : new Set(leads.map((l) => l.id)))
                    }
                  >
                    {allSelected ? <CheckSquare className="h-3.5 w-3.5" /> : <Square className="h-3.5 w-3.5" />}
                    {allSelected ? "Clear" : "Select all"}
                  </button>
                ) : null}
              </div>
            </CardHeader>
            <CardContent>
              {!runId ? (
                <EmptyState title="No run yet" description="Set ICP filters and click Start Engine." />
              ) : run?.status === "running" || run?.status === "queued" ? (
                <div className="space-y-3 py-6">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    {run.stage_label || `Engine ${run.stage}…`}
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-black/30">
                    <div
                      className="h-full rounded-full bg-primary transition-all duration-500"
                      style={{ width: `${Math.min(100, Math.max(8, run.progress_pct ?? 8))}%` }}
                    />
                  </div>
                </div>
              ) : leadsQuery.isLoading ? (
                <Skeleton className="h-40 w-full" />
              ) : leads.length === 0 ? (
                <EmptyState
                  title="No leads matched"
                  description="Widen headcount / industries or clear domain filters."
                />
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[720px] text-left text-sm">
                    <thead className="text-xs uppercase text-muted-foreground">
                      <tr className="border-b border-border/50">
                        <th className="py-2 pr-2" />
                        <th className="py-2 pr-3">Company</th>
                        {product === "cybersecurity" ? (
                          <>
                            <th className="py-2 pr-3">Priority</th>
                            <th className="py-2 pr-3">Contact</th>
                            <th className="py-2 pr-3">Services</th>
                            <th className="py-2 pr-3">Score</th>
                            <th className="py-2">Evidence</th>
                          </>
                        ) : (
                          <>
                            <th className="py-2 pr-3">Founder</th>
                            <th className="py-2 pr-3">Email</th>
                            <th className="py-2 pr-3">Phone</th>
                            <th className="py-2 pr-3">Score</th>
                            <th className="py-2">Evidence</th>
                          </>
                        )}
                      </tr>
                    </thead>
                    <tbody>
                      {leads.map((lead) => {
                        const on = selected.has(lead.id);
                        return (
                          <tr key={lead.id} className="border-b border-border/40 align-top">
                            <td className="py-2.5 pr-2">
                              <input
                                type="checkbox"
                                checked={on}
                                onChange={() => {
                                  setSelected((prev) => {
                                    const next = new Set(prev);
                                    if (next.has(lead.id)) next.delete(lead.id);
                                    else next.add(lead.id);
                                    return next;
                                  });
                                }}
                              />
                            </td>
                            <td className="py-2.5 pr-3">
                              <div className="font-medium">{lead.company}</div>
                              <div className="text-xs text-muted-foreground">
                                {lead.category}
                                {lead.city ? ` · ${lead.city}` : ""}
                              </div>
                            </td>
                            {product === "cybersecurity" ? (
                              <>
                                <td className="py-2.5 pr-3">
                                  <Badge variant="outline" className={cn(
                                    "text-[10px]",
                                    lead.signal?.includes("ACTIVE") ? "border-red-500/40 text-red-500" :
                                    lead.signal?.includes("VERIFIED") ? "border-yellow-500/40 text-yellow-500" :
                                    "border-blue-500/40 text-blue-500",
                                  )}>
                                    {lead.signal || lead.grade || "—"}
                                  </Badge>
                                </td>
                                <td className="py-2.5 pr-3">
                                  <div className="text-sm">{lead.founder_name || "—"}</div>
                                  <div className="text-xs text-muted-foreground">{lead.founder_role || ""}</div>
                                  <div className="font-mono text-xs text-muted-foreground">{lead.email}</div>
                                </td>
                                <td className="py-2.5 pr-3">
                                  <div className="max-w-[160px] text-xs text-muted-foreground line-clamp-2">
                                    {lead.why || "—"}
                                  </div>
                                </td>
                                <td className="py-2.5 pr-3">
                                  <Badge variant="outline">{lead.intent_score ?? "—"}</Badge>
                                  <div className="mt-1 text-[10px] text-muted-foreground">{lead.grade}</div>
                                </td>
                                <td className="py-2.5">
                                  <div className="max-w-[220px] text-xs text-muted-foreground line-clamp-2">
                                    {lead.signal || "—"}
                                  </div>
                                </td>
                              </>
                            ) : (
                              <>
                                <td className="py-2.5 pr-3">{lead.founder_name || "—"}</td>
                                <td className="py-2.5 pr-3 font-mono text-xs">{lead.email}</td>
                                <td className="py-2.5 pr-3 text-xs">{lead.phone || "—"}</td>
                                <td className="py-2.5 pr-3">
                                  <Badge variant="outline">{lead.intent_score ?? "—"}</Badge>
                                  <div className="mt-1 text-[10px] text-muted-foreground">{lead.grade}</div>
                                  {lead.already_contacted ? (
                                    <div className="mt-1 text-[10px] text-amber-500">already contacted</div>
                                  ) : null}
                                </td>
                                <td className="py-2.5">
                                  <div className="max-w-[220px] text-xs text-muted-foreground line-clamp-2">
                                    {lead.why || lead.signal || "—"}
                                  </div>
                                  {lead.subject ? (
                                    <button
                                      type="button"
                                      className="mt-1 text-[11px] text-primary hover:underline"
                                      onClick={() =>
                                        setPreview({
                                          subject: lead.subject!,
                                          body: lead.body || "",
                                          company: lead.company,
                                        })
                                      }
                                    >
                                      Preview draft
                                    </button>
                                  ) : null}
                                </td>
                              </>
                            )}
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {preview ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="max-h-[85vh] w-full max-w-xl overflow-y-auto rounded-2xl border border-border bg-[#0f1623] p-5 shadow-xl">
            <div className="mb-3 flex items-start justify-between gap-3">
              <div>
                <p className="text-xs uppercase text-muted-foreground">
                  {preview.approveMode ? "Approve outreach" : "Outreach preview"}
                </p>
                <h3 className="font-display text-lg font-semibold">{preview.company || "Draft"}</h3>
                {preview.approveMode ? (
                  <p className="mt-1 text-xs text-muted-foreground">
                    From vansh@inowix.in · CC vanshjhamb9@gmail.com, ragibali84@gmail.com ·{" "}
                    {selected.size} selected
                  </p>
                ) : null}
              </div>
              <Button variant="outline" size="sm" onClick={() => setPreview(null)}>
                Close
              </Button>
            </div>
            <p className="mb-3 text-sm font-medium">{preview.subject}</p>
            <pre className="whitespace-pre-wrap rounded-xl bg-black/30 p-4 text-sm leading-relaxed text-foreground/90">
              {preview.body}
            </pre>
            {preview.approveMode ? (
              <div className="mt-4 flex justify-end gap-2">
                <Button variant="outline" size="sm" onClick={() => setPreview(null)}>
                  Cancel
                </Button>
                <Button size="sm" disabled={send.isPending} onClick={() => send.mutate()}>
                  {send.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  Send approved
                </Button>
              </div>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function MegaExtractionStatus() {
  const [status, setStatus] = useState<{
    active: boolean;
    schedule: string;
    seen_domains: number;
    total_mega_extracted: number;
    last_extraction: string;
  } | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch("/api/v1/unified-leads/extraction-status");
        if (res.ok) setStatus(await res.json());
      } catch (e) {
        console.error("Failed to fetch extraction status", e);
      }
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  if (!status) return null;

  return (
    <Card className="border-border/60 bg-card/50">
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-muted-foreground" />
          <CardTitle className="text-sm font-semibold uppercase tracking-wide">
            Automated Mega Extraction
          </CardTitle>
          {status.active && (
            <span className="ml-2 flex items-center gap-1.5 rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] text-emerald-400">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
              ACTIVE
            </span>
          )}
        </div>
        <CardDescription>
          Runs every 20 minutes · Extracts CMO/CTO/VC/Founder decision makers
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-4 text-sm">
          <div>
            <span className="text-muted-foreground">Schedule: </span>
            <span className="font-medium">{status.schedule}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Seen domains: </span>
            <span className="font-medium">{status.seen_domains}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Extracted: </span>
            <span className="font-medium text-emerald-400">
              {status.total_mega_extracted}
            </span>
          </div>
          {status.last_extraction && (
            <div>
              <span className="text-muted-foreground">Last run: </span>
              <span className="font-medium">
                {new Date(status.last_extraction).toLocaleString()}
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
