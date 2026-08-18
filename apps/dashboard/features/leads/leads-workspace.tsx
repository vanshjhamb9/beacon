"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { ArrowRight, Download, Filter, RefreshCw, Search, X, Zap } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useMemo, useState, useEffect } from "react";

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
  status: string;
  search: string;
};

const INDUSTRIES = ["All", "fashion", "beauty", "jewellery", "lifestyle", "food", "home", "saas", "fintech", "software"];
const COUNTRIES = ["All", "India", "United States", "United Kingdom", "Canada", "Australia"];
const SCORES = ["All", "Hot (90-100)", "Warm (70-89)", "Cool (50-69)"];
const SOURCES = ["All", "live_verified_enrichment", "lead_engine", "cyber_discovery", "comai_b2b", "inowix", "cyber"];

const STATUS_CHIPS: { id: string; label: string }[] = [
  { id: "all", label: "All" },
  { id: "new", label: "New leads" },
  { id: "not_contacted", label: "Not contacted" },
  { id: "contacted", label: "Contacted" },
  { id: "with_data", label: "With data" },
  { id: "b2b", label: "COMAI B2B Partners" },
  { id: "today", label: "Today's New" },
];

export function LeadsWorkspace() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialStatus = searchParams.get("status") || "all";
  const [filters, setFilters] = useState<LeadFilters>({
    industry: "All",
    country: "All",
    score: "All",
    source: "All",
    status: initialStatus,
    search: "",
  });
  const [page, setPage] = useState(1);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const limit = 20;

  const setStatus = (status: string) => {
    setFilters({ ...filters, status });
    setPage(1);
    const next = new URLSearchParams(searchParams.toString());
    if (status === "all") next.delete("status");
    else next.set("status", status);
    router.replace(`/leads${next.toString() ? `?${next.toString()}` : ""}`, { scroll: false });
  };

  const [partnerLeads, setPartnerLeads] = useState<Array<Record<string, unknown>>>([]);

  const { data, isLoading } = useQuery({
    queryKey: ["workspace-leads", filters.search, filters.status],
    queryFn: async () => {
      if (filters.status === "b2b" || filters.status === "today") {
        return { items: [], filter_counts: {} };
      }
      return beaconApi.workspaceLeads({
        limit: 300,
        search: filters.search || undefined,
        status: filters.status,
      });
    },
    refetchInterval: 20_000,
  });

  useEffect(() => {
    if (filters.status === "b2b" || filters.status === "today") {
      fetch("/api/v1/partner-leads?limit=200")
        .then((r) => r.json())
        .then((d) => setPartnerLeads(d.items || []))
        .catch(() => setPartnerLeads([]));
    } else {
      setPartnerLeads([]);
    }
  }, [filters.status]);

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

  const filterCounts = useMemo(() => {
    const base = (data?.filter_counts || {}) as Record<string, number>;
    return {
      ...base,
      b2b: partnerLeads.length,
      today: partnerLeads.filter((l) => {
        const d = new Date(l.created_at as string);
        const now = new Date();
        return (
          d.getFullYear() === now.getFullYear() &&
          d.getMonth() === now.getMonth() &&
          d.getDate() === now.getDate()
        );
      }).length,
    };
  }, [data, partnerLeads]);

  const leads = useMemo(() => {
    if (filters.status === "b2b" || filters.status === "today") {
      let items = partnerLeads.map((l) => ({
        ...l,
        company_name: l.agency_name,
        industry: l.agency_type,
        score: l.final_score,
        stage: l.status?.toLowerCase() || "new",
        has_contact_data: Boolean(l.email || l.phone),
        is_b2b: true,
      }));
      if (filters.search) {
        const q = filters.search.toLowerCase();
        items = items.filter(
          (l) =>
            String(l.company_name || "").toLowerCase().includes(q) ||
            String(l.city || "").toLowerCase().includes(q) ||
            String(l.decision_maker || "").toLowerCase().includes(q)
        );
      }
      if (filters.status === "today") {
        const now = new Date();
        items = items.filter((l) => {
          const d = new Date(l.created_at as string);
          return (
            d.getFullYear() === now.getFullYear() &&
            d.getMonth() === now.getMonth() &&
            d.getDate() === now.getDate()
          );
        });
      }
      return items;
    }
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
    setFilters({ industry: "All", country: "All", score: "All", source: "All", status: "all", search: "" });
    setPage(1);
    router.replace("/leads", { scroll: false });
  };

  const hasActiveFilters =
    filters.industry !== "All" ||
    filters.country !== "All" ||
    filters.score !== "All" ||
    filters.source !== "All" ||
    filters.status !== "all" ||
    filters.search !== "";

  if (isLoading) return <Skeleton className="h-96 w-full" />;

  return (
    <div className="mx-auto max-w-[1400px] space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-semibold">Leads</h1>
          <p className="text-sm text-muted-foreground">
            {filters.status === "b2b"
              ? `${total} COMAI B2B partner leads`
              : filters.status === "today"
                ? `${total} leads added today`
                : `${total} Lead Engine leads ready for outreach`}
          </p>
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

      <div className="flex flex-wrap gap-2">
        {STATUS_CHIPS.map((chip) => {
          const count = chip.id === "all" ? filterCounts.all : filterCounts[chip.id];
          const active = filters.status === chip.id;
          return (
            <button
              key={chip.id}
              type="button"
              onClick={() => setStatus(chip.id)}
              className={cn(
                "rounded-full border px-3 py-1.5 text-sm font-medium transition",
                active
                  ? "border-primary bg-primary/15 text-foreground"
                  : "border-border/70 bg-card text-muted-foreground hover:text-foreground",
              )}
            >
              {chip.label}
              {typeof count === "number" ? <span className="ml-1.5 text-xs opacity-70">{count}</span> : null}
            </button>
          );
        })}
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
          <Button size="sm" variant="outline" onClick={() => moveMutation.mutate("new")}>
            Mark New
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
                    {filters.status === "b2b" || filters.status === "today" ? (
                      <>
                        <th className="px-4 py-3 font-medium">Tier</th>
                        <th className="px-4 py-3 font-medium">Score</th>
                        <th className="px-4 py-3 font-medium">Decision Maker</th>
                        <th className="px-4 py-3 font-medium">Phone</th>
                        <th className="px-4 py-3 font-medium">Email</th>
                        <th className="px-4 py-3 font-medium">Contact</th>
                        <th className="px-4 py-3 font-medium">Pitch Angle</th>
                      </>
                    ) : (
                      <>
                        <th className="px-4 py-3 font-medium">Industry</th>
                        <th className="px-4 py-3 font-medium">City</th>
                        <th className="px-4 py-3 font-medium">Email</th>
                        <th className="px-4 py-3 font-medium">Phone</th>
                        <th className="px-4 py-3 font-medium">Score</th>
                        <th className="px-4 py-3 font-medium">Stage</th>
                      </>
                    )}
                    <th className="w-10 px-4 py-3"></th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedLeads.map((lead, idx) => {
                    const leadId = String(lead.id || idx);
                    const complete = Boolean(lead.has_contact_data);
                    const isB2B = Boolean(lead.is_b2b);
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
                        <td className="px-4 py-3 font-medium">
                          {String(lead.company_name || "Unknown")}
                          {isB2B && (
                            <span className="ml-2 rounded bg-blue-500/10 px-1.5 py-0.5 text-[10px] text-blue-400">
                              B2B
                            </span>
                          )}
                          {complete && !isB2B ? (
                            <span className="ml-2 rounded bg-emerald-500/10 px-1.5 py-0.5 text-[10px] text-emerald-400">
                              data
                            </span>
                          ) : null}
                        </td>
                        {isB2B ? (
                          <>
                            <td className="px-4 py-3">
                              <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                                lead.tier === "A" ? "bg-emerald-500/15 text-emerald-400" :
                                lead.tier === "B" ? "bg-amber-500/15 text-amber-400" :
                                "bg-slate-500/15 text-slate-400"
                              }`}>
                                {String(lead.tier || "C")}
                              </span>
                            </td>
                            <td className="px-4 py-3">
                              <span className="font-mono font-bold">{formatScore(Number(lead.score || 0), 0)}</span>
                            </td>
                            <td className="px-4 py-3 text-sm">
                              <div>{String(lead.decision_maker || "—")}</div>
                              <div className="text-xs text-muted-foreground">{String(lead.decision_maker_role || "")}</div>
                            </td>
                            <td className="px-4 py-3">
                              {lead.phone ? (
                                <a href={`tel:${lead.phone}`} className="text-green-400 hover:underline text-sm font-mono">
                                  {String(lead.phone)}
                                </a>
                              ) : "—"}
                            </td>
                            <td className="px-4 py-3 text-muted-foreground text-sm">{String(lead.email || "—")}</td>
                            <td className="px-4 py-3">
                              <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                                lead.contactability === "HIGH" ? "bg-emerald-500/15 text-emerald-400" :
                                lead.contactability === "MEDIUM" ? "bg-amber-500/15 text-amber-400" :
                                "bg-red-500/15 text-red-400"
                              }`}>
                                {String(lead.contactability || "—")}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-xs text-muted-foreground max-w-[180px] truncate" title={String(lead.pitch_angle || "")}>
                              {String(lead.pitch_angle || "—")}
                            </td>
                          </>
                        ) : (
                          <>
                            <td className="px-4 py-3 text-muted-foreground">{String(lead.industry || "—")}</td>
                            <td className="px-4 py-3 text-muted-foreground">{String(lead.city || "—")}</td>
                            <td className="px-4 py-3 text-muted-foreground">{String(lead.email || "—")}</td>
                            <td className="px-4 py-3 text-muted-foreground">{String(lead.phone || "—")}</td>
                            <td className="px-4 py-3">
                              <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                                {formatScore(Number(lead.intent_score || lead.score || 0), 0)}
                              </span>
                            </td>
                            <td className="px-4 py-3 capitalize text-muted-foreground">{String(lead.stage || "new")}</td>
                          </>
                        )}
                        <td className="px-4 py-3">
                          <Link href={isB2B ? `/partner-leads` : `/leads/${leadId}`} className="text-primary hover:underline">
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
