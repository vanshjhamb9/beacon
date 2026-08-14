"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Building2, Globe, Users, Zap } from "lucide-react";
import { useMemo, useState } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { cn } from "@/lib/utils";

export function UniverseWorkspace() {
  const [searchQuery, setSearchQuery] = useState("");
  const [sourceFilter, setSourceFilter] = useState<string>("all");

  const universe = useQuery({
    queryKey: ["company-universe"],
    queryFn: () => beaconApi.companyUniverse(),
    refetchInterval: 60_000,
  });

  const companies = useMemo(
    () => ((universe.data?.items as Array<Record<string, unknown>>) || []) as Array<Record<string, unknown>>,
    [universe.data]
  );

  const filteredCompanies = useMemo(() => {
    return companies.filter((company) => {
      const name = String(company.company_name || "").toLowerCase();
      const domain = String(company.domain || "").toLowerCase();
      const matchesSearch =
        searchQuery === "" ||
        name.includes(searchQuery.toLowerCase()) ||
        domain.includes(searchQuery.toLowerCase());
      const matchesSource = sourceFilter === "all" || company.source === sourceFilter;
      return matchesSearch && matchesSource;
    });
  }, [companies, searchQuery, sourceFilter]);

  const sources = useMemo(() => {
    const sourceSet = new Set(companies.map((c) => String(c.source || "")));
    return Array.from(sourceSet).filter(Boolean);
  }, [companies]);

  if (universe.isLoading) return <Skeleton className="h-96 w-full" />;

  return (
    <div className="mx-auto max-w-[1400px] space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold">Company Universe</h1>
          <p className="text-sm text-muted-foreground">
            {companies.length} companies discovered from raw events (not sales leads)
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <input
          type="text"
          placeholder="Search companies..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="rounded-lg border border-border/60 bg-background px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
        />
        <select
          value={sourceFilter}
          onChange={(e) => setSourceFilter(e.target.value)}
          className="rounded-lg border border-border/60 bg-background px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
        >
          <option value="all">All Sources</option>
          {sources.map((source) => (
            <option key={source} value={source}>
              {source}
            </option>
          ))}
        </select>
      </div>

      {/* Info Banner */}
      <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 p-4">
        <p className="text-sm text-blue-400">
          <strong>Company Universe</strong> is a database of companies we know about. 
          This is NOT a sales pipeline. Companies only enter the sales pipeline when they have verified buying events.
        </p>
      </div>

      {/* Company Grid */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filteredCompanies.length === 0 ? (
          <div className="col-span-full rounded-lg border border-dashed border-border/50 p-8 text-center">
            <Building2 className="mx-auto h-12 w-12 text-muted-foreground/30" />
            <p className="mt-4 text-sm text-muted-foreground">
              No companies found matching your search criteria.
            </p>
          </div>
        ) : (
          filteredCompanies.slice(0, 100).map((company, idx) => (
            <motion.div
              key={String(company.id || idx)}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.02 * idx }}
              className="rounded-lg border border-border/60 bg-card p-4 transition-colors hover:border-primary/50"
            >
              <div className="flex items-start justify-between gap-2">
                <h3 className="font-medium">{String(company.company_name || "Unknown")}</h3>
                {Boolean(company.has_buying_event) && (
                  <span className="rounded-full bg-green-500/10 px-2 py-0.5 text-xs font-medium text-green-500">
                    Has Buying Event
                  </span>
                )}
              </div>

              {String(company.domain || "") && (
                <div className="mt-2 flex items-center gap-1 text-sm text-muted-foreground">
                  <Globe className="h-3 w-3" />
                  <span>{String(company.domain || "")}</span>
                </div>
              )}

              {String(company.employees || "") && (
                <div className="mt-1 flex items-center gap-1 text-sm text-muted-foreground">
                  <Users className="h-3 w-3" />
                  <span>{String(company.employees || "")} employees</span>
                </div>
              )}

              <div className="mt-2 flex flex-wrap gap-1">
                <span className="rounded bg-muted/50 px-1.5 py-0.5 text-[10px] text-muted-foreground">
                  {String(company.source || "unknown")}
                </span>
                {String(company.industry || "") && (
                  <span className="rounded bg-muted/50 px-1.5 py-0.5 text-[10px] text-muted-foreground">
                    {String(company.industry || "")}
                  </span>
                )}
                {Number(company.icp_match_score || 0) > 0 && (
                  <span className={cn(
                    "rounded px-1.5 py-0.5 text-[10px] font-medium",
                    Number(company.icp_match_score || 0) >= 80
                      ? "bg-green-500/10 text-green-500"
                      : Number(company.icp_match_score || 0) >= 60
                        ? "bg-yellow-500/10 text-yellow-500"
                        : "bg-muted text-muted-foreground"
                  )}>
                    ICP: {Number(company.icp_match_score || 0).toFixed(0)}%
                  </span>
                )}
              </div>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
}
