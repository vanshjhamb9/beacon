"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Download,
  RefreshCw,
  Search,
  Target,
  TrendingUp,
  AlertTriangle,
  Flame,
  BarChart3,
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

type RevenueIntelligence = {
  id: string;
  ecommerce_lead_id: string;
  company_name: string;
  website: string;
  domain: string;
  pain_score: number;
  growth_score: number;
  buying_intent: number;
  technology_gap: number;
  support_gap: number;
  traffic_score: number;
  probability_to_buy: number;
  priority: string;
  why_comai: string;
  recommended_pitch: string;
  revenue_potential: number;
  analyzed_at: string;
};

type DashboardStats = {
  total_analyzed: number;
  hot_leads: number;
  warm_leads: number;
  low_leads: number;
  rejected: number;
  avg_probability: number;
};

const API_BASE = "/api/v1/revenue-intelligence";

function priorityColor(priority: string) {
  switch (priority) {
    case "URGENT":
      return "bg-red-500/15 text-red-400 border-red-500/30";
    case "HOT":
      return "bg-orange-500/15 text-orange-400 border-orange-500/30";
    case "WARM":
      return "bg-amber-500/15 text-amber-400 border-amber-500/30";
    case "NURTURE":
      return "bg-blue-500/15 text-blue-400 border-blue-500/30";
    case "LOW":
      return "bg-slate-500/15 text-slate-400 border-slate-500/30";
    case "REJECT":
      return "bg-gray-500/15 text-gray-400 border-gray-500/30";
    default:
      return "bg-slate-500/15 text-slate-400 border-slate-500/30";
  }
}

function priorityIcon(priority: string) {
  switch (priority) {
    case "URGENT":
    case "HOT":
      return <Flame className="h-4 w-4" />;
    case "WARM":
      return <TrendingUp className="h-4 w-4" />;
    case "NURTURE":
      return <Target className="h-4 w-4" />;
    default:
      return <BarChart3 className="h-4 w-4" />;
  }
}

export function RevenueIntelligenceWorkspace() {
  const [leads, setLeads] = useState<RevenueIntelligence[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [page, setPage] = useState(0);
  const pageSize = 50;

  const fetchLeads = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("limit", String(pageSize));
      params.set("offset", String(page * pageSize));
      if (priorityFilter !== "all") params.set("priority", priorityFilter);

      const res = await fetch(`${API_BASE}/leads?${params}`);
      if (res.ok) {
        const data = await res.json();
        setLeads(data.leads);
        setTotal(data.total);
      }
    } catch (e) {
      console.error("Failed to fetch revenue intelligence", e);
    }
    setLoading(false);
  }, [page, priorityFilter]);

  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/dashboard`);
      if (res.ok) setStats(await res.json());
    } catch (e) {
      console.error("Failed to fetch stats", e);
    }
  }, []);

  useEffect(() => {
    fetchLeads();
    fetchStats();
  }, [fetchLeads, fetchStats]);

  const handleBulkRefresh = async () => {
    setRefreshing(true);
    try {
      await fetch(`${API_BASE}/analyze`, {
        method: "POST",
      });
      setTimeout(() => {
        fetchLeads();
        fetchStats();
        setRefreshing(false);
      }, 5000);
    } catch (e) {
      console.error("Refresh failed", e);
      setRefreshing(false);
    }
  };

  const handleExport = () => {
    window.open(`${API_BASE}/export`, "_blank");
  };

  const filtered = leads.filter((l) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      l.company_name.toLowerCase().includes(q) ||
      l.domain.toLowerCase().includes(q) ||
      l.why_comai.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Revenue Intelligence
          </h1>
          <p className="text-muted-foreground">
            AI-powered scoring and prioritization for cold calling outreach
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleBulkRefresh}
            disabled={refreshing}
          >
            <RefreshCw
              className={`mr-2 h-4 w-4 ${refreshing ? "animate-spin" : ""}`}
            />
            {refreshing ? "Analyzing..." : "Analyze Leads"}
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
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Analyzed
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats.total_analyzed.toLocaleString()}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-orange-500">
                Hot + Urgent
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Flame className="h-4 w-4 text-orange-400" />
                <span className="text-2xl font-bold text-orange-400">
                  {stats.hot_leads.toLocaleString()}
                </span>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-amber-500">
                Warm
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-amber-400">
                {stats.warm_leads.toLocaleString()}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-slate-500">
                Low + Rejected
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-slate-400">
                {(stats.low_leads + stats.rejected).toLocaleString()}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Avg Probability
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats.avg_probability}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search companies..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={priorityFilter} onValueChange={setPriorityFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Priority" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Priorities</SelectItem>
            <SelectItem value="URGENT">Urgent</SelectItem>
            <SelectItem value="HOT">Hot</SelectItem>
            <SelectItem value="WARM">Warm</SelectItem>
            <SelectItem value="NURTURE">Nurture</SelectItem>
            <SelectItem value="LOW">Low</SelectItem>
            <SelectItem value="REJECT">Reject</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Company</TableHead>
                <TableHead>Priority</TableHead>
                <TableHead>Probability</TableHead>
                <TableHead>Pain</TableHead>
                <TableHead>Growth</TableHead>
                <TableHead>Intent</TableHead>
                <TableHead>Pitch</TableHead>
                <TableHead>Potential</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8">
                    Loading...
                  </TableCell>
                </TableRow>
              ) : filtered.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={8}
                    className="text-center py-8 text-muted-foreground"
                  >
                    No leads found. Click &quot;Analyze Leads&quot; to run
                    revenue intelligence analysis.
                  </TableCell>
                </TableRow>
              ) : (
                filtered.map((lead) => (
                  <TableRow key={lead.id}>
                    <TableCell className="font-medium">
                      <div>
                        <div>{lead.company_name}</div>
                        <div className="text-xs text-muted-foreground truncate max-w-[200px]">
                          {lead.domain}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={`text-xs ${priorityColor(lead.priority)}`}
                      >
                        <span className="flex items-center gap-1">
                          {priorityIcon(lead.priority)}
                          {lead.priority}
                        </span>
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono text-sm font-semibold">
                      {lead.probability_to_buy}
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {lead.pain_score}
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {lead.growth_score}
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {lead.buying_intent}
                    </TableCell>
                    <TableCell
                      className="text-xs max-w-[200px] truncate"
                      title={lead.recommended_pitch}
                    >
                      {lead.recommended_pitch}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">
                        {lead.revenue_potential}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {total > pageSize && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {page * pageSize + 1}-
            {Math.min((page + 1) * pageSize, total)} of {total}
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
              disabled={(page + 1) * pageSize >= total}
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
