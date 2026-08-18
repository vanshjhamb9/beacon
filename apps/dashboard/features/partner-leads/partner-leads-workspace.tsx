"use client";

import { useCallback, useEffect, useState } from "react";
import { Download, RefreshCw, Search, Users, Mail, Phone, Linkedin, ExternalLink, Star, ArrowUpRight } from "lucide-react";

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

type PartnerLead = {
  id: string;
  agency_name: string;
  agency_url: string | null;
  country: string | null;
  city: string | null;
  agency_type: string | null;
  employees: string | null;
  founded: number | null;
  clients: string | null;
  client_count: number | null;
  revenue_generated: string | null;
  revenue_managed: string | null;
  notable_clients: string[];
  decision_maker: string | null;
  decision_maker_role: string | null;
  email: string | null;
  phone: string | null;
  linkedin: string | null;
  contactability: string | null;
  services: string[];
  certifications: string[];
  tier: string | null;
  client_access_score: number | null;
  comai_fit_score: number | null;
  final_score: number | null;
  why_this_agency: string | null;
  comai_fit: string | null;
  pitch_angle: string | null;
  status: string;
  outreach_sent: boolean;
  response_received: boolean;
  meeting_scheduled: boolean;
  partner_converted: boolean;
  source: string | null;
  lead_source: string | null;
};

type PartnerStats = {
  total: number;
  tier_a: number;
  tier_b: number;
  tier_c: number;
  contacted: number;
  responded: number;
  meetings: number;
  converted: number;
  high_contactability: number;
  by_country: Record<string, number>;
  by_type: Record<string, number>;
  avg_final_score: number;
  avg_client_access_score: number;
  avg_comai_fit_score: number;
};

const API_BASE = "/api/v1/partner-leads";

function tierColor(tier: string | null) {
  switch (tier) {
    case "A":
      return "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
    case "B":
      return "bg-amber-500/15 text-amber-400 border-amber-500/30";
    case "C":
      return "bg-slate-500/15 text-slate-400 border-slate-500/30";
    default:
      return "bg-slate-500/15 text-slate-400 border-slate-500/30";
  }
}

function contactColor(level: string | null) {
  switch (level) {
    case "HIGH":
      return "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
    case "MEDIUM":
      return "bg-amber-500/15 text-amber-400 border-amber-500/30";
    case "LOW":
      return "bg-red-500/15 text-red-400 border-red-500/30";
    default:
      return "bg-slate-500/15 text-slate-400 border-slate-500/30";
  }
}

function statusColor(status: string) {
  switch (status) {
    case "NEW":
      return "bg-blue-500/15 text-blue-400 border-blue-500/30";
    case "CONTACTED":
      return "bg-amber-500/15 text-amber-400 border-amber-500/30";
    case "RESPONSE_RECEIVED":
      return "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
    case "MEETING_SCHEDULED":
      return "bg-purple-500/15 text-purple-400 border-purple-500/30";
    case "PARTNERED":
      return "bg-green-500/15 text-green-400 border-green-500/30";
    case "REJECTED":
      return "bg-red-500/15 text-red-400 border-red-500/30";
    default:
      return "bg-slate-500/15 text-slate-400 border-slate-500/30";
  }
}

export function PartnerLeadsWorkspace() {
  const [leads, setLeads] = useState<PartnerLead[]>([]);
  const [stats, setStats] = useState<PartnerStats | null>(null);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [tierFilter, setTierFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [contactFilter, setContactFilter] = useState("all");
  const [sourceFilter, setSourceFilter] = useState("all");
  const [phoneOnly, setPhoneOnly] = useState(false);
  const [page, setPage] = useState(0);
  const limit = 50;

  const fetchLeads = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.set("search", search);
      if (tierFilter !== "all") params.set("tier", tierFilter);
      if (statusFilter !== "all") params.set("status", statusFilter);
      if (contactFilter !== "all") params.set("contactability", contactFilter);
      if (sourceFilter !== "all") params.set("lead_source", sourceFilter);
      if (phoneOnly) params.set("has_phone", "true");
      params.set("limit", String(limit));
      params.set("offset", String(page * limit));

      const res = await fetch(`${API_BASE}?${params}`);
      const data = await res.json();
      setLeads(data.items || []);
      setTotal(data.total || 0);
    } catch (e) {
      console.error("Failed to fetch partner leads", e);
    }
    setLoading(false);
  }, [search, tierFilter, statusFilter, contactFilter, sourceFilter, phoneOnly, page]);

  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/stats`);
      const data = await res.json();
      setStats(data);
    } catch (e) {
      console.error("Failed to fetch stats", e);
    }
  }, []);

  useEffect(() => {
    fetchLeads();
    fetchStats();
  }, [fetchLeads, fetchStats]);

  const exportCSV = () => {
    const headers = [
      "Agency Name", "Tier", "Country", "City", "Type", "Clients",
      "Decision Maker", "Email", "Phone", "LinkedIn", "Contactability",
      "Final Score", "Status", "Pitch Angle",
    ];
    const rows = leads.map((l) => [
      l.agency_name, l.tier || "", l.country || "", l.city || "",
      l.agency_type || "", l.clients || "", l.decision_maker || "",
      l.email || "", l.phone || "", l.linkedin || "",
      l.contactability || "", String(l.final_score || ""),
      l.status, l.pitch_angle || "",
    ]);
    const csv = [headers, ...rows].map((r) => r.map((c) => `"${c}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "comai_b2b_partner_leads.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">COMAI B2B Partner Leads</h1>
          <p className="text-muted-foreground">
            Distribution partner agencies for WhatsApp commerce platform
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={fetchLeads}>
            <RefreshCw className="h-4 w-4 mr-1" /> Refresh
          </Button>
          <Button variant="outline" size="sm" onClick={exportCSV}>
            <Download className="h-4 w-4 mr-1" /> Export CSV
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Leads</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-emerald-500">Tier A (Hot)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-emerald-400">{stats.tier_a}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-amber-500">Tier B (Potential)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-amber-400">{stats.tier_b}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-blue-500">High Contact</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-400">{stats.high_contactability}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Avg Score</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.avg_final_score}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Pipeline</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm">
                <span className="text-emerald-400">{stats.contacted} contacted</span>
                <span className="text-muted-foreground"> / </span>
                <span className="text-amber-400">{stats.responded} responded</span>
                <span className="text-muted-foreground"> / </span>
                <span className="text-purple-400">{stats.meetings} meetings</span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search agencies..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(0); }}
            className="pl-9"
          />
        </div>
        <Select value={tierFilter} onValueChange={(v) => { setTierFilter(v); setPage(0); }}>
          <SelectTrigger className="w-[130px]">
            <SelectValue placeholder="All Tiers" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Tiers</SelectItem>
            <SelectItem value="A">Tier A (Hot)</SelectItem>
            <SelectItem value="B">Tier B (Potential)</SelectItem>
            <SelectItem value="C">Tier C (Nurture)</SelectItem>
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setPage(0); }}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="All Statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="NEW">New</SelectItem>
            <SelectItem value="CONTACTED">Contacted</SelectItem>
            <SelectItem value="RESPONSE_RECEIVED">Response Received</SelectItem>
            <SelectItem value="MEETING_SCHEDULED">Meeting Scheduled</SelectItem>
            <SelectItem value="PARTNERED">Partnered</SelectItem>
            <SelectItem value="REJECTED">Rejected</SelectItem>
          </SelectContent>
        </Select>
        <Select value={contactFilter} onValueChange={(v) => { setContactFilter(v); setPage(0); }}>
          <SelectTrigger className="w-[150px]">
            <SelectValue placeholder="All Contact" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Contact</SelectItem>
            <SelectItem value="HIGH">High</SelectItem>
            <SelectItem value="MEDIUM">Medium</SelectItem>
            <SelectItem value="LOW">Low</SelectItem>
          </SelectContent>
        </Select>
        <Select value={sourceFilter} onValueChange={(v) => { setSourceFilter(v); setPage(0); }}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="All Sources" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Sources</SelectItem>
            <SelectItem value="comai_b2b">COMAI B2B</SelectItem>
            <SelectItem value="inowix">Inowix</SelectItem>
            <SelectItem value="cyber">Cyber</SelectItem>
          </SelectContent>
        </Select>
        <Button
          variant={phoneOnly ? "default" : "outline"}
          size="sm"
          onClick={() => { setPhoneOnly(!phoneOnly); setPage(0); }}
        >
          <Phone className="h-4 w-4 mr-1" />
          {phoneOnly ? "Phone Only" : "All"}
        </Button>
      </div>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Agency</TableHead>
                <TableHead>Tier</TableHead>
                <TableHead>Score</TableHead>
                <TableHead>Clients</TableHead>
                <TableHead>Decision Maker</TableHead>
                <TableHead>Contact</TableHead>
                <TableHead>Source</TableHead>
                <TableHead>Contactability</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={10} className="text-center py-8 text-muted-foreground">
                    Loading partner leads...
                  </TableCell>
                </TableRow>
              ) : leads.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={10} className="text-center py-8 text-muted-foreground">
                    No partner leads found
                  </TableCell>
                </TableRow>
              ) : (
                leads.map((lead) => (
                  <TableRow key={lead.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{lead.agency_name}</div>
                        <div className="text-xs text-muted-foreground">
                          {lead.agency_type} {lead.city ? `• ${lead.city}` : ""}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={tierColor(lead.tier)}>
                        {lead.tier || "C"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="font-mono text-sm">
                        <span className="font-bold">{lead.final_score || 0}</span>
                        <span className="text-muted-foreground"> / 100</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm max-w-[200px] truncate" title={lead.clients || ""}>
                        {lead.clients || "—"}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="text-sm font-medium">{lead.decision_maker || "—"}</div>
                        <div className="text-xs text-muted-foreground">{lead.decision_maker_role || ""}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col gap-1">
                        {lead.email && (
                          <a href={`mailto:${lead.email}`} className="text-xs text-blue-400 hover:underline flex items-center gap-1">
                            <Mail className="h-3 w-3" /> {lead.email}
                          </a>
                        )}
                        {lead.phone && (
                          <a href={`tel:${lead.phone}`} className="text-xs text-green-400 hover:underline flex items-center gap-1">
                            <Phone className="h-3 w-3" /> {lead.phone}
                          </a>
                        )}
                        {lead.linkedin && (
                          <a href={lead.linkedin} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-400 hover:underline flex items-center gap-1">
                            <Linkedin className="h-3 w-3" /> LinkedIn
                          </a>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">
                        {lead.lead_source === "comai_b2b" ? "B2B" : lead.lead_source || "B2B"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={contactColor(lead.contactability)}>
                        {lead.contactability || "—"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={statusColor(lead.status)}>
                        {lead.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        {lead.agency_url && (
                          <a href={lead.agency_url} target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-foreground">
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Showing {page * limit + 1}-{Math.min((page + 1) * limit, total)} of {total} leads
        </p>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
          >
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage(page + 1)}
            disabled={(page + 1) * limit >= total}
          >
            Next
          </Button>
        </div>
      </div>

      {/* Pipeline Visual */}
      {stats && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Pipeline Overview</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              {[
                { label: "NEW", count: stats.total - stats.contacted, color: "bg-blue-500" },
                { label: "CONTACTED", count: stats.contacted - stats.responded, color: "bg-amber-500" },
                { label: "RESPONDED", count: stats.responded - stats.meetings, color: "bg-emerald-500" },
                { label: "MEETINGS", count: stats.meetings - stats.converted, color: "bg-purple-500" },
                { label: "CONVERTED", count: stats.converted, color: "bg-green-500" },
              ].map((stage, i) => (
                <div key={stage.label} className="flex items-center gap-2 flex-1">
                  <div className="flex-1">
                    <div className="text-xs text-muted-foreground mb-1">{stage.label}</div>
                    <div className={`h-8 rounded-md ${stage.color}/20 flex items-center justify-center`}>
                      <span className="text-sm font-bold">{stage.count}</span>
                    </div>
                  </div>
                  {i < 4 && <span className="text-muted-foreground text-lg">→</span>}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Analytics Breakdown */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">By Agency Type</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {Object.entries(stats.by_type)
                  .sort(([, a], [, b]) => b - a)
                  .slice(0, 8)
                  .map(([type, count]) => (
                    <div key={type} className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground truncate max-w-[200px]">{type}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-2 rounded-full bg-muted overflow-hidden">
                          <div
                            className="h-full bg-primary/60 rounded-full"
                            style={{ width: `${(count / stats.total) * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium w-8 text-right">{count}</span>
                      </div>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Scoring Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-muted-foreground">Avg Final Score</span>
                    <span className="font-medium">{stats.avg_final_score}</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-muted overflow-hidden">
                    <div className="h-full bg-primary/60 rounded-full" style={{ width: `${stats.avg_final_score}%` }} />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-muted-foreground">Avg Client Access Score</span>
                    <span className="font-medium">{stats.avg_client_access_score}</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-muted overflow-hidden">
                    <div className="h-full bg-emerald-500/60 rounded-full" style={{ width: `${stats.avg_client_access_score}%` }} />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-muted-foreground">Avg COMAI Fit Score</span>
                    <span className="font-medium">{stats.avg_comai_fit_score}</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-muted overflow-hidden">
                    <div className="h-full bg-amber-500/60 rounded-full" style={{ width: `${stats.avg_comai_fit_score}%` }} />
                  </div>
                </div>
                <div className="pt-2 border-t">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">High Contactability</span>
                    <span className="font-medium text-emerald-400">{stats.high_contactability} / {stats.total}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
