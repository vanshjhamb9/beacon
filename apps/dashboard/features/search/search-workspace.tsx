"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { EmptyState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { formatLabel, formatScore, priorityTone } from "@/lib/utils";

export function SearchWorkspace() {
  const params = useSearchParams();
  const initial = params.get("q") || "";
  const [query, setQuery] = useState(initial);

  const companies = useQuery({
    queryKey: ["companies", "search"],
    queryFn: () => beaconApi.companies({ limit: 200 }),
  });
  const revenue = useQuery({
    queryKey: ["revenue-opportunities", "search"],
    queryFn: () => beaconApi.revenueOpportunities({ limit: 200 }),
  });
  const opportunities = useQuery({
    queryKey: ["opportunities", "search"],
    queryFn: () => beaconApi.opportunities({ limit: 200 }),
  });

  const q = query.trim().toLowerCase();

  const results = useMemo(() => {
    if (!q) return { companies: [], services: [], pains: [], industries: [], opportunities: [] };

    const companyHits = (companies.data?.companies ?? []).filter((company) =>
      [company.name, company.industry, company.primary_domain, company.memory_summary]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q),
    );

    const revenueItems = revenue.data?.opportunities ?? [];
    const serviceHits = revenueItems.filter((item) =>
      [item.recommended_service, item.secondary_service, item.business_pain, item.company.name]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q),
    );

    const opportunityHits = (opportunities.data?.opportunities ?? []).filter((item) =>
      [item.company_name, item.narrative, item.status, item.recommendation].join(" ").toLowerCase().includes(q),
    );

    const industries = [
      ...new Set(
        [...companyHits, ...serviceHits.map((item) => ({ industry: item.company.industry }))]
          .map((item) => ("industry" in item ? item.industry : null))
          .filter(Boolean) as string[],
      ),
    ].filter((industry) => industry.toLowerCase().includes(q));

    const pains = [
      ...new Set(serviceHits.map((item) => item.business_pain).filter(Boolean) as string[]),
    ].filter((pain) => pain.toLowerCase().includes(q));

    return {
      companies: companyHits.slice(0, 12),
      services: serviceHits.slice(0, 12),
      pains: pains.slice(0, 12),
      industries: industries.slice(0, 12),
      opportunities: opportunityHits.slice(0, 12),
    };
  }, [q, companies.data, revenue.data, opportunities.data]);

  const loading = companies.isLoading || revenue.isLoading || opportunities.isLoading;

  return (
    <div className="mx-auto flex max-w-[1100px] flex-col gap-6">
      <header className="space-y-2">
        <SectionLabel>Universal Search</SectionLabel>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Search</h1>
        <p className="text-sm text-muted-foreground">
          Companies, services, pains, industries, and opportunities — client-side over live API data.
        </p>
      </header>

      <Input
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Try company, Shopify, automation, funding…"
        className="h-11"
        autoFocus
      />

      {!q ? (
        <EmptyState title="Start typing" description="Search across Beacon entities without leaving the workspace." />
      ) : loading ? (
        <div className="space-y-3">
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          <ResultGroup title="Companies">
            {results.companies.map((company) => (
              <ResultLink key={company.id} href={`/companies/${company.id}`} title={company.name} meta={company.industry || "—"} />
            ))}
          </ResultGroup>
          <ResultGroup title="Recommended Services">
            {results.services.map((item) => (
              <ResultLink
                key={item.solution_match_id}
                href={`/companies/${item.company.id}`}
                title={item.recommended_service}
                meta={`${item.company.name} · ${formatLabel(item.priority)}`}
                badge={
                  <Badge className={priorityTone(item.priority)}>{formatScore(item.opportunity_score, 0)}</Badge>
                }
              />
            ))}
          </ResultGroup>
          <ResultGroup title="Opportunities">
            {results.opportunities.map((item) => (
              <ResultLink
                key={item.id}
                href={`/opportunities/${item.id}`}
                title={item.company_name}
                meta={`${formatLabel(item.status)} · score ${formatScore(item.opportunity_score, 0)}`}
              />
            ))}
          </ResultGroup>
          <ResultGroup title="Pains & Industries">
            {results.pains.map((pain) => (
              <div key={pain} className="rounded-lg border border-border/50 px-3 py-2 text-sm">
                Pain: {pain}
              </div>
            ))}
            {results.industries.map((industry) => (
              <div key={industry} className="rounded-lg border border-border/50 px-3 py-2 text-sm">
                Industry: {industry}
              </div>
            ))}
            {results.pains.length === 0 && results.industries.length === 0 ? (
              <p className="text-sm text-muted-foreground">No pain/industry matches.</p>
            ) : null}
          </ResultGroup>
        </div>
      )}
    </div>
  );
}

function ResultGroup({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">{children}</CardContent>
    </Card>
  );
}

function ResultLink({
  href,
  title,
  meta,
  badge,
}: {
  href: string;
  title: string;
  meta: string;
  badge?: React.ReactNode;
}) {
  return (
    <Link href={href} className="flex items-center justify-between gap-3 rounded-lg border border-border/50 px-3 py-2 transition hover:border-primary/30">
      <div className="min-w-0">
        <p className="truncate text-sm font-medium">{title}</p>
        <p className="truncate text-xs text-muted-foreground">{meta}</p>
      </div>
      {badge}
    </Link>
  );
}
