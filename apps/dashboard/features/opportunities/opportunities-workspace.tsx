"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useMemo, useRef, useState } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { EmptyState, ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { formatLabel, formatScore, scoreTone } from "@/lib/utils";

type SreRow = Record<string, any>;

export function OpportunitiesWorkspace() {
  const parentRef = useRef<HTMLDivElement>(null);
  const [search, setSearch] = useState("");
  const [salesReadyOnly, setSalesReadyOnly] = useState(true);
  const [enterpriseOnly, setEnterpriseOnly] = useState(false);
  const [intent, setIntent] = useState("all");
  const [dealSize, setDealSize] = useState("all");
  const [emailOnly, setEmailOnly] = useState(false);
  const [phoneOnly, setPhoneOnly] = useState(false);
  const [industry, setIndustry] = useState("all");
  const [country, setCountry] = useState("all");
  const [hiringAi, setHiringAi] = useState(false);
  const [automation, setAutomation] = useState(false);
  const [funding, setFunding] = useState(false);

  const sre = useQuery({
    queryKey: ["buying-events-opportunities", salesReadyOnly, enterpriseOnly],
    queryFn: async () => {
      return beaconApi.buyingEvents({
        limit: 200,
        status: salesReadyOnly ? "verified" : undefined,
      });
    },
  });

  const rows = useMemo(() => {
    const items = (sre.data?.items ?? []) as SreRow[];
    const q = search.trim().toLowerCase();
    return items.filter((item) => {
      const classification = String(item.classification ?? "");
      const ind = String(item.industry ?? "");
      const ctry = String(item.country ?? "");
      const confidence = Number(item.confidence ?? 0) * 100;
      const contactType = String(item.contact_type ?? "");
      if (intent !== "all" && classification.toLowerCase() !== intent) return false;
      if (industry !== "all" && ind.toLowerCase() !== industry) return false;
      if (country !== "all" && ctry.toLowerCase() !== country) return false;
      if (emailOnly && !["DECISION_MAKER_DIRECT", "VERIFIED_WORK_EMAIL"].includes(contactType)) return false;
      if (!q) return true;
      return String(item.company_name ?? "")
        .toLowerCase()
        .includes(q);
    });
  }, [sre.data, search, intent, industry, country, emailOnly]);

  const industries = unique(rows.map((r) => String(r.identity?.fields?.industry?.value || "Unknown")));
  const countries = unique(rows.map((r) => String(r.identity?.fields?.country?.value || "Unknown")));

  const virtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 56,
    overscan: 12,
  });

  if (sre.isError) {
    return <ErrorState description="Failed to load sales-ready opportunities." onRetry={() => void sre.refetch()} />;
  }

  return (
    <div className="mx-auto flex max-w-[1600px] flex-col gap-6">
      <header className="space-y-2">
        <SectionLabel>Sales readiness</SectionLabel>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Opportunities</h1>
        <p className="text-sm text-muted-foreground">
          Founder-facing list from SRE — NOT READY / RESEARCH REQUIRED never appear when Sales Ready Only is on.
        </p>
      </header>

      <Card>
        <CardHeader className="gap-4">
          <CardTitle>Filters</CardTitle>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <Input placeholder="Search company…" value={search} onChange={(e) => setSearch(e.target.value)} />
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              <input type="checkbox" checked={salesReadyOnly} onChange={(e) => setSalesReadyOnly(e.target.checked)} />
              Sales Ready Only
            </label>
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              <input type="checkbox" checked={enterpriseOnly} onChange={(e) => setEnterpriseOnly(e.target.checked)} />
              Enterprise Ready
            </label>
            <Select
              value={intent}
              onChange={setIntent}
              options={["all", "very high", "high", "medium", "low"]}
              labelAll="All intent levels"
            />
            <Select value={dealSize} onChange={setDealSize} options={["all", "small", "medium", "large", "enterprise"]} labelAll="All deal sizes" />
            <Select value={industry} onChange={setIndustry} options={["all", ...industries]} labelAll="All industries" />
            <Select value={country} onChange={setCountry} options={["all", ...countries]} labelAll="All countries" />
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              <input type="checkbox" checked={emailOnly} onChange={(e) => setEmailOnly(e.target.checked)} />
              Verified Email
            </label>
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              <input type="checkbox" checked={phoneOnly} onChange={(e) => setPhoneOnly(e.target.checked)} />
              Verified Phone
            </label>
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              <input type="checkbox" checked={hiringAi} onChange={(e) => setHiringAi(e.target.checked)} />
              Hiring AI
            </label>
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              <input type="checkbox" checked={automation} onChange={(e) => setAutomation(e.target.checked)} />
              Automation
            </label>
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              <input type="checkbox" checked={funding} onChange={(e) => setFunding(e.target.checked)} />
              Funding
            </label>
          </div>
        </CardHeader>
        <CardContent>
          {sre.isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 8 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : rows.length === 0 ? (
            <EmptyState title="No actionable opportunities" description="Run sales_readiness.process_pending or loosen filters." />
          ) : (
            <div className="overflow-hidden rounded-xl border border-border/70">
              <div className="grid grid-cols-[1.2fr_0.8fr_0.7fr_0.7fr_0.7fr_0.7fr] gap-2 border-b border-border/70 bg-muted/30 px-3 py-2 text-[10px] uppercase tracking-[0.1em] text-muted-foreground">
                <span>Company</span>
                <span>Classification</span>
                <span>Confidence</span>
                <span>Contact</span>
                <span>Solution</span>
                <span>Problem</span>
              </div>
              <div ref={parentRef} className="scrollbar-thin h-[640px] overflow-auto">
                <div style={{ height: virtualizer.getTotalSize(), position: "relative" }}>
                  {virtualizer.getVirtualItems().map((virtualRow) => {
                    const item = rows[virtualRow.index];
                    const confidence = Number(item.confidence ?? 0) * 100;
                    return (
                      <div
                        key={String(item.id)}
                        className="absolute left-0 top-0 grid w-full grid-cols-[1.2fr_0.8fr_0.7fr_0.7fr_0.7fr_0.7fr] items-center gap-2 border-b border-border/40 px-3 text-xs"
                        style={{ height: virtualRow.size, transform: `translateY(${virtualRow.start}px)` }}
                      >
                        <Link href={`/leads/${item.id}`} className="truncate font-medium hover:text-primary">
                          {String(item.company_name)}
                        </Link>
                        <Badge variant="outline">{formatLabel(String(item.classification ?? "UNKNOWN"))}</Badge>
                        <span className={`tabular-nums ${scoreTone(confidence)}`}>
                          {formatScore(confidence, 0)}
                        </span>
                        <span className="truncate text-muted-foreground">{String(item.contact_type ?? "UNKNOWN")}</span>
                        <span className="truncate text-muted-foreground">{String(item.solution_match ?? "UNKNOWN")}</span>
                        <span className="truncate text-muted-foreground">{String(item.problem ?? "UNKNOWN")}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function Select({
  value,
  onChange,
  options,
  labelAll,
}: {
  value: string;
  onChange: (value: string) => void;
  options: string[];
  labelAll: string;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="h-9 rounded-lg border border-border bg-background/60 px-3 text-sm"
    >
      {options.map((option) => (
        <option key={option} value={option}>
          {option === "all" ? labelAll : formatLabel(option)}
        </option>
      ))}
    </select>
  );
}

function unique(values: string[]) {
  return [...new Set(values.filter(Boolean).map((v) => v.toLowerCase()))].sort((a, b) => a.localeCompare(b));
}
