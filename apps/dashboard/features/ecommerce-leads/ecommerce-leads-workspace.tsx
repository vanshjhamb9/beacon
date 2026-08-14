"use client";

import { useCallback, useEffect, useState } from "react";
import { Download, RefreshCw, Search, TrendingUp } from "lucide-react";

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

type EcommerceLead = {
  id: string;
  company_name: string;
  website: string;
  platform: string;
  category: string;
  city: string;
  state: string;
  email: string;
  phone: string;
  founder_name: string;
  instagram_url: string;
  linkedin_url: string;
  whatsapp_detected: boolean;
  product_count: number;
  chatbot_detected: boolean;
  comai_score: number;
  lead_priority: string;
  sales_reason: string;
  source: string;
};

type EcommerceStats = {
  total_leads: number;
  hot_leads: number;
  warm_leads: number;
  low_leads: number;
  platforms: Record<string, number>;
  categories: Record<string, number>;
  avg_score: number;
};

const API_BASE = "/api/v1/ecommerce";

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
  const [leads, setLeads] = useState<EcommerceLead[]>([]);
  const [stats, setStats] = useState<EcommerceStats | null>(null);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [discovering, setDiscovering] = useState(false);
  const [search, setSearch] = useState("");
  const [platformFilter, setPlatformFilter] = useState("all");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [page, setPage] = useState(0);
  const pageSize = 50;

  const fetchLeads = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("limit", String(pageSize));
      params.set("offset", String(page * pageSize));
      if (platformFilter !== "all") params.set("platform", platformFilter);
      if (priorityFilter !== "all") params.set("priority", priorityFilter);

      const res = await fetch(`${API_BASE}/leads?${params}`);
      if (res.ok) {
        const data = await res.json();
        setLeads(data.leads);
        setTotal(data.total);
      }
    } catch (e) {
      console.error("Failed to fetch leads", e);
    }
    setLoading(false);
  }, [page, platformFilter, priorityFilter]);

  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/stats`);
      if (res.ok) setStats(await res.json());
    } catch (e) {
      console.error("Failed to fetch stats", e);
    }
  }, []);

  useEffect(() => {
    fetchLeads();
    fetchStats();
  }, [fetchLeads, fetchStats]);

  const handleDiscover = async () => {
    setDiscovering(true);
    try {
      await fetch(`${API_BASE}/discover`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ limit: 500, country: "India" }),
      });
      setTimeout(() => {
        fetchLeads();
        fetchStats();
        setDiscovering(false);
      }, 5000);
    } catch (e) {
      console.error("Discovery failed", e);
      setDiscovering(false);
    }
  };

  const handleExport = () => {
    window.open(`${API_BASE}/export`, "_blank");
  };

  const filteredLeads = leads.filter((l) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      l.company_name.toLowerCase().includes(q) ||
      l.website.toLowerCase().includes(q) ||
      l.category.toLowerCase().includes(q) ||
      l.founder_name.toLowerCase().includes(q) ||
      l.email.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Ecommerce Leads</h1>
          <p className="text-muted-foreground">
            Indian ecommerce businesses for COMAI sales
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleDiscover}
            disabled={discovering}
          >
            <RefreshCw
              className={`mr-2 h-4 w-4 ${discovering ? "animate-spin" : ""}`}
            />
            {discovering ? "Discovering..." : "Discover"}
          </Button>
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="mr-2 h-4 w-4" />
            Export XLSX
          </Button>
        </div>
      </div>

      {stats && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Leads
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_leads.toLocaleString()}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-emerald-500">
                Hot Leads
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-emerald-400">
                {stats.hot_leads.toLocaleString()}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-amber-500">
                Warm Leads
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
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Avg Score
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
                <span className="text-2xl font-bold">{stats.avg_score}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {stats && Object.keys(stats.platforms).length > 0 && (
        <div className="flex flex-wrap gap-2">
          {Object.entries(stats.platforms).map(([platform, count]) => (
            <Badge key={platform} variant="secondary" className="text-xs">
              {platform}: {count}
            </Badge>
          ))}
        </div>
      )}

      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search leads..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={platformFilter} onValueChange={setPlatformFilter}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Platform" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Platforms</SelectItem>
            <SelectItem value="shopify">Shopify</SelectItem>
            <SelectItem value="woocommerce">WooCommerce</SelectItem>
            <SelectItem value="magento">Magento</SelectItem>
          </SelectContent>
        </Select>
        <Select value={priorityFilter} onValueChange={setPriorityFilter}>
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
                <TableHead>Website</TableHead>
                <TableHead>Platform</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>City</TableHead>
                <TableHead>Contact</TableHead>
                <TableHead>Score</TableHead>
                <TableHead>Priority</TableHead>
                <TableHead>Reason</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-8">
                    Loading...
                  </TableCell>
                </TableRow>
              ) : filteredLeads.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                    No leads found. Click &quot;Discover&quot; to start collecting leads.
                  </TableCell>
                </TableRow>
              ) : (
                filteredLeads.map((lead) => (
                  <TableRow key={lead.id}>
                    <TableCell className="font-medium">
                      {lead.company_name}
                    </TableCell>
                    <TableCell>
                      <a
                        href={lead.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:underline truncate max-w-[200px] block"
                      >
                        {lead.website.replace(/^https?:\/\//, "").slice(0, 30)}
                      </a>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">
                        {lead.platform || "unknown"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm">{lead.category}</TableCell>
                    <TableCell className="text-sm">{lead.city}</TableCell>
                    <TableCell className="text-sm">
                      {lead.email || lead.phone || "-"}
                    </TableCell>
                    <TableCell className="font-mono text-sm font-semibold">
                      {lead.comai_score.toFixed(1)}
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
