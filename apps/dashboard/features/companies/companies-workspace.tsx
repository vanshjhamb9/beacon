"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { EmptyState, ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { formatRelativeTime } from "@/lib/utils";

export function CompaniesWorkspace() {
  const [search, setSearch] = useState("");
  const companies = useQuery({
    queryKey: ["companies", "list"],
    queryFn: () => beaconApi.companies({ limit: 200 }),
  });

  const rows = useMemo(() => {
    const q = search.trim().toLowerCase();
    return (companies.data?.companies ?? []).filter((company) => {
      if (!q) return true;
      return [company.name, company.industry, company.primary_domain, company.memory_summary]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q);
    });
  }, [companies.data, search]);

  if (companies.isError) {
    return <ErrorState description="Failed to load companies." onRetry={() => void companies.refetch()} />;
  }

  return (
    <div className="mx-auto flex max-w-[1200px] flex-col gap-6">
      <header className="space-y-2">
        <SectionLabel>Directory</SectionLabel>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Companies</h1>
        <p className="text-sm text-muted-foreground">Open a company workspace for DNA, timeline, and revenue fit.</p>
      </header>

      <Input
        placeholder="Filter companies…"
        value={search}
        onChange={(event) => setSearch(event.target.value)}
        className="max-w-md"
      />

      {companies.isLoading ? (
        <div className="grid gap-3 md:grid-cols-2">
          {Array.from({ length: 6 }).map((_, index) => (
            <Skeleton key={index} className="h-28" />
          ))}
        </div>
      ) : rows.length === 0 ? (
        <EmptyState title="No companies" description="Companies appear after Intelligence resolves entities." />
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {rows.map((company) => (
            <Link key={company.id} href={`/companies/${company.id}`}>
              <Card className="h-full transition hover:border-primary/30">
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg">{company.name}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex flex-wrap gap-2">
                    <Badge className="bg-muted text-muted-foreground ring-border">
                      {company.industry || "Unknown industry"}
                    </Badge>
                    <Badge className="bg-muted text-muted-foreground ring-border">
                      {company.signal_frequency} signals
                    </Badge>
                  </div>
                  <p className="line-clamp-2 text-sm text-muted-foreground">
                    {company.memory_summary || "No memory summary."}
                  </p>
                  <p className="text-xs text-muted-foreground">Last seen {formatRelativeTime(company.last_seen_at)}</p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
