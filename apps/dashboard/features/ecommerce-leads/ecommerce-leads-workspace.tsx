"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Download,
  Mail,
  Phone,
  RefreshCw,
  Search,
  TrendingUp,
  User,
  Zap,
} from "lucide-react";

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

export function EcommerceLeadsWorkspace() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [page, setPage] = useState(0);
  const pageSize = 50;

  const fetchLeads = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("limit", "500");
      if (search) params.set("search", search);
      if (categoryFilter !== "all") params.set("category", categoryFilter);
      if (priorityFilter !== "all") params.set("priority", priorityFilter);

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
  }, [search, categoryFilter, priorityFilter]);

  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/unified-leads/stats");
      if (res.ok) setStats(await res.json());
    } catch (e) {
      console.error("Failed to fetch stats", e);
    }
  }, []);

  useEffect(() => {
    fetchLeads();
    fetchStats();
    const interval = setInterval(() => {
      fetchLeads();
      fetchStats();
    }, 30000);
    return () => clearInterval(interval);
  }, [fetchLeads, fetchStats]);

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
          <h1 className="text-2xl font-bold tracking-tight">Ecommerce Leads</h1>
          <p className="text-muted-foreground">
            Indian D2C brands with contact details and decision makers
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
              <div className="flex items-center gap-2">
                <Phone className="h-4 w-4 text-emerald-400" />
                <p className="text-[11px] uppercase tracking-wider text-emerald-500">
                  With Phone
                </p>
              </div>
              <p className="mt-1 text-2xl font-bold text-emerald-400">
                {stats.with_phone}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-blue-400" />
                <p className="text-[11px] uppercase tracking-wider text-blue-500">
                  With Email
                </p>
              </div>
              <p className="mt-1 text-2xl font-bold text-blue-400">
                {stats.with_email}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <User className="h-4 w-4 text-amber-400" />
                <p className="text-[11px] uppercase tracking-wider text-amber-500">
                  Decision Makers
                </p>
              </div>
              <p className="mt-1 text-2xl font-bold text-amber-400">
                {stats.with_role}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-purple-400" />
                <p className="text-[11px] uppercase tracking-wider text-purple-500">
                  Avg Score
                </p>
              </div>
              <p className="mt-1 text-2xl font-bold text-purple-400">
                {stats.avg_score}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search company, founder, email..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(0);
            }}
            className="pl-9"
          />
        </div>
        <Select
          value={categoryFilter}
          onValueChange={(v) => {
            setCategoryFilter(v);
            setPage(0);
          }}
        >
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            <SelectItem value="fashion">Fashion</SelectItem>
            <SelectItem value="beauty">Beauty</SelectItem>
            <SelectItem value="jewellery">Jewellery</SelectItem>
            <SelectItem value="food">Food</SelectItem>
            <SelectItem value="home">Home</SelectItem>
            <SelectItem value="electronics">Electronics</SelectItem>
            <SelectItem value="health">Health</SelectItem>
          </SelectContent>
        </Select>
        <Select
          value={priorityFilter}
          onValueChange={(v) => {
            setPriorityFilter(v);
            setPage(0);
          }}
        >
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Priority" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Priorities</SelectItem>
            <SelectItem value="HOT">Hot</SelectItem>
            <SelectItem value="WARM">Warm</SelectItem>
            <SelectItem value="LOW">Low</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Company</TableHead>
                <TableHead>Founder</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Phone</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>City</TableHead>
                <TableHead>Score</TableHead>
                <TableHead>Priority</TableHead>
                <TableHead>Reason</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={10} className="text-center py-8">
                    Loading...
                  </TableCell>
                </TableRow>
              ) : paginatedLeads.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={10}
                    className="text-center py-8 text-muted-foreground"
                  >
                    No leads found.
                  </TableCell>
                </TableRow>
              ) : (
                paginatedLeads.map((lead) => (
                  <TableRow key={lead.id}>
                    <TableCell className="font-medium">
                      <div>{lead.company_name}</div>
                      {lead.website && (
                        <a
                          href={lead.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[11px] text-blue-400 hover:underline"
                        >
                          {lead.domain || lead.website.slice(0, 25)}
                        </a>
                      )}
                    </TableCell>
                    <TableCell className="text-sm">
                      {lead.founder_name || "—"}
                    </TableCell>
                    <TableCell className="text-xs">
                      {lead.decision_maker_role || "—"}
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {lead.phone || (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {lead.email || (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">
                        {lead.category || "—"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm">{lead.city || "—"}</TableCell>
                    <TableCell className="font-mono text-sm font-semibold">
                      {lead.comai_score.toFixed(0)}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={`text-xs ${priorityColor(lead.lead_priority)}`}
                      >
                        {lead.lead_priority}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground max-w-[200px] truncate">
                      {lead.sales_reason}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
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
