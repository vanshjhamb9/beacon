"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Calendar,
  Download,
  Filter,
  Phone,
  Mail,
  RefreshCw,
  Search,
  User,
  X,
  Zap,
} from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type Lead = {
  id: string;
  company_name: string;
  founder_name: string;
  decision_maker_role: string;
  email: string;
  phone: string;
  website: string;
  domain: string;
  platform: string;
  category: string;
  industry: string;
  city: string;
  country: string;
  lead_priority: string;
  comai_score: number;
  sales_reason: string;
  source: string;
  linkedin_url: string;
  created_at: string;
  stage: string;
};

type Stats = {
  total: number;
  with_phone: number;
  with_email: number;
  with_both: number;
  hot: number;
  warm: number;
  low: number;
  with_founder: number;
  with_role: number;
  avg_score: number;
};

const CATEGORIES = [
  "All",
  "fashion",
  "beauty",
  "jewellery",
  "food",
  "home",
  "electronics",
  "health",
];
const PRIORITIES = ["All", "HOT", "WARM", "LOW"];
const SOURCES = ["All", "mega_extraction", "import"];

function priorityColor(priority: string) {
  switch (priority) {
    case "HOT":
      return "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
    case "WARM":
      return "bg-amber-500/15 text-amber-400 border-amber-500/30";
    default:
      return "bg-slate-500/15 text-slate-400 border-slate-500/30";
  }
}

function roleIcon(role: string) {
  const r = role.toUpperCase();
  if (r.includes("FOUNDER") || r.includes("CEO"))
    return <User className="h-3 w-3 text-emerald-400" />;
  if (r.includes("CTO") || r.includes("CMO") || r.includes("CFO"))
    return <Zap className="h-3 w-3 text-amber-400" />;
  return <User className="h-3 w-3 text-muted-foreground" />;
}

export function LeadsWorkspace() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("All");
  const [priorityFilter, setPriorityFilter] = useState("All");
  const [sourceFilter, setSourceFilter] = useState("All");
  const [page, setPage] = useState(0);
  const pageSize = 25;

  const fetchLeads = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("limit", "500");
      if (search) params.set("search", search);
      if (categoryFilter !== "All") params.set("category", categoryFilter);
      if (priorityFilter !== "All") params.set("priority", priorityFilter);
      if (sourceFilter !== "All") params.set("source", sourceFilter);

      const res = await fetch(`/api/v1/unified-leads/all?${params}`);
      if (res.ok) {
        const data = await res.json();
        setLeads(data.leads);
        setTotal(data.total);
        setStats(data.stats);
      }
    } catch (e) {
      console.error("Failed to fetch leads", e);
    }
    setLoading(false);
  }, [search, categoryFilter, priorityFilter, sourceFilter]);

  useEffect(() => {
    fetchLeads();
    const interval = setInterval(fetchLeads, 30000);
    return () => clearInterval(interval);
  }, [fetchLeads]);

  const filteredLeads = leads;
  const paginatedLeads = filteredLeads.slice(
    page * pageSize,
    (page + 1) * pageSize
  );
  const totalPages = Math.max(1, Math.ceil(filteredLeads.length / pageSize));

  const handleExport = () => {
    window.open("/api/v1/ecommerce/export", "_blank");
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">All Leads</h1>
          <p className="text-muted-foreground">
            {total} leads tracked across the entire pipeline
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={fetchLeads}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="mr-2 h-4 w-4" />
            Export XLSX
          </Button>
          <Button size="sm" asChild>
            <Link href="/lead-engine">
              <Zap className="mr-2 h-4 w-4" />
              Lead Engine
            </Link>
          </Button>
        </div>
      </div>

      {stats && (
        <div className="grid gap-4 md:grid-cols-5">
          <Card>
            <CardContent className="p-4">
              <p className="text-[11px] uppercase tracking-wider text-muted-foreground">
                Total Leads
              </p>
              <p className="mt-1 text-2xl font-bold">{stats.total}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-[11px] uppercase tracking-wider text-emerald-500">
                With Phone
              </p>
              <p className="mt-1 text-2xl font-bold text-emerald-400">
                {stats.with_phone}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-[11px] uppercase tracking-wider text-blue-500">
                With Email
              </p>
              <p className="mt-1 text-2xl font-bold text-blue-400">
                {stats.with_email}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-[11px] uppercase tracking-wider text-amber-500">
                Decision Makers
              </p>
              <p className="mt-1 text-2xl font-bold text-amber-400">
                {stats.with_role}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-[11px] uppercase tracking-wider text-purple-500">
                Avg Score
              </p>
              <p className="mt-1 text-2xl font-bold text-purple-400">
                {stats.avg_score}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

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
                placeholder="Search company, founder, email..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(0);
                }}
                className="h-9 pl-9"
              />
            </div>
            <Select
              value={categoryFilter}
              onValueChange={(v) => {
                setCategoryFilter(v);
                setPage(0);
              }}
            >
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                {CATEGORIES.map((c) => (
                  <SelectItem key={c} value={c}>
                    {c === "All" ? "All Categories" : c}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select
              value={priorityFilter}
              onValueChange={(v) => {
                setPriorityFilter(v);
                setPage(0);
              }}
            >
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Priority" />
              </SelectTrigger>
              <SelectContent>
                {PRIORITIES.map((p) => (
                  <SelectItem key={p} value={p}>
                    {p === "All" ? "All Priorities" : p}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select
              value={sourceFilter}
              onValueChange={(v) => {
                setSourceFilter(v);
                setPage(0);
              }}
            >
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Source" />
              </SelectTrigger>
              <SelectContent>
                {SOURCES.map((s) => (
                  <SelectItem key={s} value={s}>
                    {s === "All" ? "All Sources" : s.replace("_", " ")}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center text-muted-foreground">
              Loading leads...
            </div>
          ) : paginatedLeads.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              No leads found.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b border-border/60 bg-muted/30 text-left text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
                  <tr>
                    <th className="px-4 py-3 font-medium">Company</th>
                    <th className="px-4 py-3 font-medium">Founder</th>
                    <th className="px-4 py-3 font-medium">Role</th>
                    <th className="px-4 py-3 font-medium">Phone</th>
                    <th className="px-4 py-3 font-medium">Email</th>
                    <th className="px-4 py-3 font-medium">Category</th>
                    <th className="px-4 py-3 font-medium">City</th>
                    <th className="px-4 py-3 font-medium">Score</th>
                    <th className="px-4 py-3 font-medium">Priority</th>
                    <th className="px-4 py-3 font-medium">Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedLeads.map((lead, idx) => (
                    <motion.tr
                      key={lead.id}
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.01 * idx }}
                      className="border-b border-border/40 hover:bg-muted/20"
                    >
                      <td className="px-4 py-3 font-medium">
                        <div>{lead.company_name}</div>
                        {lead.website && (
                          <a
                            href={lead.website}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-[11px] text-blue-400 hover:underline"
                          >
                            {lead.domain || lead.website.slice(0, 30)}
                          </a>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {lead.founder_name || (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {lead.decision_maker_role ? (
                          <div className="flex items-center gap-1.5">
                            {roleIcon(lead.decision_maker_role)}
                            <span className="text-xs">
                              {lead.decision_maker_role}
                            </span>
                          </div>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {lead.phone ? (
                          <div className="flex items-center gap-1.5">
                            <Phone className="h-3 w-3 text-emerald-400" />
                            <span className="font-mono text-xs">
                              {lead.phone}
                            </span>
                          </div>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {lead.email ? (
                          <div className="flex items-center gap-1.5">
                            <Mail className="h-3 w-3 text-blue-400" />
                            <span className="font-mono text-xs">
                              {lead.email}
                            </span>
                          </div>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="outline" className="text-xs">
                          {lead.category || "—"}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {lead.city || "—"}
                      </td>
                      <td className="px-4 py-3">
                        <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                          {lead.comai_score.toFixed(0)}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <Badge
                          variant="outline"
                          className={`text-xs ${priorityColor(lead.lead_priority)}`}
                        >
                          {lead.lead_priority}
                        </Badge>
                      </td>
                      <td className="max-w-[200px] truncate px-4 py-3 text-xs text-muted-foreground">
                        {lead.sales_reason}
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {page * pageSize + 1}-
            {Math.min((page + 1) * pageSize, filteredLeads.length)} of{" "}
            {filteredLeads.length}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page === 0}
              onClick={() => setPage((p) => p - 1)}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages - 1}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
