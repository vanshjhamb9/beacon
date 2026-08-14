"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { ArrowRight, Download, Filter, RefreshCw, Search, X, Zap } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { cn, formatScore } from "@/lib/utils";

type LeadFilters = {
  industry: string;
  country: string;
  score: string;
  source: string;
  search: string;
};

const INDUSTRIES = ["All", "fashion", "beauty", "jewellery", "lifestyle", "food", "home"];
const COUNTRIES = ["All", "India"];
const SCORES = ["All", "Hot (90-100)", "Warm (70-89)", "Cool (50-69)"];
const SOURCES = ["All", "live_verified_enrichment", "lead_engine"];

export function LeadsWorkspace() {
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState<LeadFilters>({
    industry: "All",
    country: "All",
    score: "All",
    source: "All",
    search: "",
  });
  const [page, setPage] = useState(1);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const limit = 20;

  const { data, isLoading } = useQuery({
    queryKey: ["workspace-leads", filters.search],
    queryFn: () => beaconApi.workspaceLeads({ limit: 300, search: filters.search || undefined }),
    refetchInterval: 20_000,
  });

  const syncMutation = useMutation({
    mutationFn: () => beaconApi.workspaceSync(),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["workspace-leads"] });
      void queryClient.invalidateQueries({ queryKey: ["workspace-overview"] });
    },
  });

  const moveMutation = useMutation({
    mutationFn: async (stage: string) => {
      await Promise.all([...selectedIds].map((id) => beaconApi.workspaceSetStage(id, stage)));
    },
    onSuccess: () => {
      setSelectedIds(new Set());
      void queryClient.invalidateQueries({ queryKey: ["workspace-leads"] });
      void queryClient.invalidateQueries({ queryKey: ["workspace-overview"] });
    },
  });

  const leads = useMemo(() => {
    const items = ((data as Record<string, unknown>)?.items as Array<Record<string, unknown>>) || [];
    return items.filter((lead) => {
      if (filters.industry !== "All") {
        const ind = String(lead.industry || lead.category || "").toLowerCase();
        if (!ind.includes(filters.industry.toLowerCase())) return false;
      }
      if (filters.country !== "All" && String(lead.country || "") !== filters.country) return false;
      if (filters.source !== "All" && String(lead.source || "") !== filters.source) return false;
      if (filters.score !== "All") {
        const score = Number(lead.score || lead.intent_score || 0);
        if (filters.score === "Hot (90-100)" && (score < 90 || score > 100)) return false;
        if (filters.score === "Warm (70-89)" && (score < 70 || score > 89)) return false;
        if (filters.score === "Cool (50-69)" && (score < 50 || score > 69)) return false;
      }
      return true;
    });
  }, [data, filters]);

  const total = leads.length;
  const paginatedLeads = leads.slice((page - 1) * limit, page * limit);
  const totalPages = Math.max(1, Math.ceil(total / limit));

  const toggleSelectAll = () => {
    if (selectedIds.size === paginatedLeads.length) setSelectedIds(new Set());
    else setSelectedIds(new Set(paginatedLeads.map((l) => String(l.id))));
  };

  const clearFilters = () => {
    setFilters({ industry: "All", country: "All", score: "All", source: "All", search: "" });
    setPage(1);
  };

  const hasActiveFilters =
    filters.industry !== "All" ||
    filters.country !== "All" ||
    filters.score !== "All" ||
    filters.source !== "All" ||
    filters.search !== "";

  if (isLoading) return <Skeleton className="h-96 w-full" />;

  return (
    <div className="mx-auto max-w-[1400px] space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-semibold">Leads</h1>
          <p className="text-sm text-muted-foreground">{total} Lead Engine leads ready for outreach</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => syncMutation.mutate()} disabled={syncMutation.isPending}>
            <RefreshCw className={cn("mr-2 h-4 w-4", syncMutation.isPending && "animate-spin")} />
            Sync from Engine
          </Button>
          <Button asChild>
            <Link href="/lead-engine">
              <Zap className="mr-2 h-4 w-4" />
              Open Lead Engine
            </Link>
          </Button>
          <Button variant="outline" size="sm" asChild>
            <a href="/api/v1/lead-engine/pool?limit=100" target="_blank" rel="noreferrer">
              <Download className="mr-2 h-4 w-4" />
              Export Pool
            </a>
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Filter className="h-4 w-4" />
              Filters
            </div>
            <div className="relative flex-1 sm:max-w-xs">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search leads..."
                value={filters.search}
                onChange={(e) => {
                  setFilters({ ...filters, search: e.target.value });
                  setPage(1);
                }}
                className="h-9 pl-9"
              />
            </div>
            {(
              [
                ["industry", INDUSTRIES],
                ["country", COUNTRIES],
                ["score", SCORES],
                ["source", SOURCES],
              ] as const
            ).map(([key, opts]) => (
              <select
                key={key}
                value={filters[key]}
                onChange={(e) => {
                  setFilters({ ...filters, [key]: e.target.value });
                  setPage(1);
                }}
                className="h-9 rounded-md border border-border bg-card px-3 text-sm"
              >
                {opts.map((o) => (
                  <option key={o} value={o}>
                    {key[0].toUpperCase() + key.slice(1)}: {o}
                  </option>
                ))}
              </select>
            ))}
            {hasActiveFilters && (
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                <X className="mr-1 h-4 w-4" />
                Clear
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {selectedIds.size > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-3 rounded-lg border border-primary/30 bg-primary/5 p-3"
        >
          <span className="text-sm font-medium">{selectedIds.size} selected</span>
          <Button size="sm" onClick={() => moveMutation.mutate("contacted")} disabled={moveMutation.isPending}>
            Mark Contacted
          </Button>
          <Button size="sm" variant="outline" onClick={() => moveMutation.mutate("lost")}>
            Reject
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setSelectedIds(new Set())}>
            Cancel
          </Button>
        </motion.div>
      )}

      <Card>
        <CardContent className="p-0">
          {paginatedLeads.length === 0 ? (
            <div className="p-8 text-center">
              <Search className="mx-auto h-12 w-12 text-muted-foreground/50" />
              <p className="mt-4 text-muted-foreground">No leads found. Run Lead Engine or Sync from Engine.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b border-border/60 bg-muted/30 text-left text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
                  <tr>
                    <th className="w-10 px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selectedIds.size === paginatedLeads.length && paginatedLeads.length > 0}
                        onChange={toggleSelectAll}
                        className="rounded border-border"
                      />
                    </th>
                    <th className="px-4 py-3 font-medium">Company</th>
                    <th className="px-4 py-3 font-medium">Industry</th>
                    <th className="px-4 py-3 font-medium">Country</th>
                    <th className="px-4 py-3 font-medium">Email</th>
                    <th className="px-4 py-3 font-medium">Score</th>
                    <th className="px-4 py-3 font-medium">Stage</th>
                    <th className="w-10 px-4 py-3"></th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedLeads.map((lead, idx) => {
                    const leadId = String(lead.id || idx);
                    return (
                      <tr key={leadId} className="border-b border-border/40 hover:bg-muted/20">
                        <td className="px-4 py-3">
                          <input
                            type="checkbox"
                            checked={selectedIds.has(leadId)}
                            onChange={() => {
                              const next = new Set(selectedIds);
                              if (next.has(leadId)) next.delete(leadId);
                              else next.add(leadId);
                              setSelectedIds(next);
                            }}
                            className="rounded border-border"
                          />
                        </td>
                        <td className="px-4 py-3 font-medium">{String(lead.company_name || "Unknown")}</td>
                        <td className="px-4 py-3 text-muted-foreground">{String(lead.industry || "—")}</td>
                        <td className="px-4 py-3 text-muted-foreground">{String(lead.country || "—")}</td>
                        <td className="px-4 py-3 text-muted-foreground">{String(lead.email || "—")}</td>
                        <td className="px-4 py-3">
                          <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                            {formatScore(Number(lead.intent_score || lead.score || 0), 0)}
                          </span>
                        </td>
                        <td className="px-4 py-3 capitalize text-muted-foreground">{String(lead.stage || "new")}</td>
                        <td className="px-4 py-3">
                          <Link href={`/leads/${leadId}`} className="text-primary hover:underline">
                            <ArrowRight className="h-4 w-4" />
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Prev
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {page} / {totalPages}
          </span>
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
