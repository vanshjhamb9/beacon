"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Download,
  RefreshCw,
  Search,
  Users,
  Mail,
  Phone,
  Linkedin,
  Sparkles,
  AlertTriangle,
  Target,
  TrendingUp,
  Zap,
  Clock,
  ChevronDown,
  ChevronUp,
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

type TechnologyProfile = {
  platform: string;
  support_tools: string[];
  chatbot_tool: string;
  has_whatsapp_widget: boolean;
  has_live_chat: boolean;
  comai_fit_score: number;
  integration_opportunities: string[];
};

type PainPoint = {
  category: string;
  description: string;
  severity: string;
  comai_solution: string;
  confidence: number;
};

type OpportunityScore = {
  total_score: number;
  classification: string;
  confidence: number;
  score_breakdown: Record<string, number>;
};

type SalesSummary = {
  why_comai: string;
  biggest_pain_point: string;
  recommended_pitch: string;
  pitch_angle: string;
  expected_business_value: string;
  competitive_position: string;
  urgency: string;
  target_person: string;
};

type CallPreparation = {
  thirty_second_opener: string;
  likely_objections: Array<{ objection: string; response: string }>;
  demo_angle: string;
  recommended_features: string[];
  meeting_objective: string;
};

type SalesAccount = {
  id: string;
  company_name: string;
  website: string;
  domain: string;
  platform: string;
  category: string;
  status: string;
  city: string;
  primary_decision_maker: string;
  primary_email: string;
  primary_phone: string;
  primary_linkedin: string;
  account_score: number;
  completeness_pct: number;
  pain_score: number;
  probability_to_buy: number;
  decision_makers: Array<{ name: string; normalized_role: string; confidence: number }>;
  contact_channels: Array<{ kind: string; value: string; confidence: number }>;
  evidence_count: number;
  technology_profile: TechnologyProfile;
  pain_analysis: { pain_points: PainPoint[]; total_pain_score: number; top_pain: string; recommended_module: string };
  opportunity_score: OpportunityScore;
  sales_summary: SalesSummary;
  call_preparation: CallPreparation;
};

type DashboardStats = {
  total_accounts: number;
  sales_ready: number;
  needs_enrichment: number;
  manual_review: number;
  avg_score: number;
  hot_leads: number;
  warm_leads: number;
  cold_leads: number;
};

const API_BASE = "/api/v1/accounts";

function statusColor(status: string) {
  switch (status) {
    case "SALES_READY":
      return "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
    case "NEEDS_ENRICHMENT":
      return "bg-amber-500/15 text-amber-400 border-amber-500/30";
    case "MANUAL_REVIEW":
      return "bg-orange-500/15 text-orange-400 border-orange-500/30";
    default:
      return "bg-slate-500/15 text-slate-400 border-slate-500/30";
  }
}

function classificationColor(classification: string) {
  switch (classification) {
    case "hot":
      return "bg-red-500/15 text-red-400 border-red-500/30";
    case "warm":
      return "bg-amber-500/15 text-amber-400 border-amber-500/30";
    case "cold":
      return "bg-blue-500/15 text-blue-400 border-blue-500/30";
    default:
      return "bg-slate-500/15 text-slate-400 border-slate-500/30";
  }
}

function severityColor(severity: string) {
  switch (severity) {
    case "high":
      return "bg-red-500/15 text-red-400 border-red-500/30";
    case "medium":
      return "bg-amber-500/15 text-amber-400 border-amber-500/30";
    case "low":
      return "bg-blue-500/15 text-blue-400 border-blue-500/30";
    default:
      return "bg-slate-500/15 text-slate-400 border-slate-500/30";
  }
}

export function SalesAccountsWorkspace() {
  const [accounts, setAccounts] = useState<SalesAccount[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [classificationFilter, setClassificationFilter] = useState("all");
  const [page, setPage] = useState(0);
  const [selectedAccount, setSelectedAccount] = useState<SalesAccount | null>(null);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});
  const pageSize = 50;

  const fetchAccounts = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("limit", String(pageSize));
      params.set("offset", String(page * pageSize));
      if (statusFilter !== "all") params.set("status", statusFilter);

      const res = await fetch(`${API_BASE}?${params}`);
      if (res.ok) {
        const data = await res.json();
        setAccounts(data.accounts);
        setTotal(data.total);
      }
    } catch (e) {
      console.error("Failed to fetch accounts", e);
    }
    setLoading(false);
  }, [page, statusFilter]);

  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/dashboard`);
      if (res.ok) setStats(await res.json());
    } catch (e) {
      console.error("Failed to fetch stats", e);
    }
  }, []);

  useEffect(() => {
    fetchAccounts();
    fetchStats();
  }, [fetchAccounts, fetchStats]);

  const handleBulkRefresh = async () => {
    setRefreshing(true);
    try {
      await fetch(`${API_BASE}/bulk-refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lead_ids: [] }),
      });
      setTimeout(() => {
        fetchAccounts();
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

  const toggleSection = (key: string) => {
    setExpandedSections((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const filtered = accounts.filter((a) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      a.company_name.toLowerCase().includes(q) ||
      a.domain.toLowerCase().includes(q) ||
      a.primary_decision_maker.toLowerCase().includes(q) ||
      a.primary_email.toLowerCase().includes(q)
    );
  }).filter((a) => {
    if (classificationFilter === "all") return true;
    return a.opportunity_score?.classification === classificationFilter;
  });

  // Get today's best leads (top 10 by opportunity score)
  const todayBestLeads = [...filtered]
    .sort((a, b) => (b.opportunity_score?.total_score || 0) - (a.opportunity_score?.total_score || 0))
    .slice(0, 10);

  // Get HOT leads
  const hotLeads = filtered.filter((a) => a.opportunity_score?.classification === "hot");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Sales Intelligence Dashboard</h1>
          <p className="text-muted-foreground">
            AI-powered leads with real contact data, pain points, and call preparation
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleBulkRefresh} disabled={refreshing}>
            <RefreshCw className={`mr-2 h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
            {refreshing ? "Building..." : "Build Accounts"}
          </Button>
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="mr-2 h-4 w-4" />
            Export XLSX
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Leads</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_accounts.toLocaleString()}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-red-500">HOT Leads</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Zap className="h-4 w-4 text-red-400" />
                <span className="text-2xl font-bold text-red-400">{stats.hot_leads || hotLeads.length}</span>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-amber-500">Warm Leads</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-amber-400">{stats.warm_leads || 0}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-emerald-500">Sales Ready</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-emerald-400">{stats.sales_ready}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Needs Enrichment</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-amber-400">{stats.needs_enrichment}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Avg Score</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.avg_score}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Today's Best Leads */}
      {todayBestLeads.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-yellow-400" />
              Today&apos;s Best Leads
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-5">
              {todayBestLeads.slice(0, 5).map((lead) => (
                <div
                  key={lead.id}
                  className="p-3 rounded-lg border bg-card hover:bg-accent/50 cursor-pointer transition-colors"
                  onClick={() => setSelectedAccount(lead)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm truncate">{lead.company_name}</span>
                    <Badge variant="outline" className={`text-xs ${classificationColor(lead.opportunity_score?.classification)}`}>
                      {lead.opportunity_score?.total_score?.toFixed(0)}
                    </Badge>
                  </div>
                  <div className="text-xs text-muted-foreground mb-2">{lead.category || lead.platform}</div>
                  <div className="text-xs text-muted-foreground line-clamp-2">
                    {lead.sales_summary?.pitch_angle?.substring(0, 80)}...
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by company, domain, or contact..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="SALES_READY">Sales Ready</SelectItem>
            <SelectItem value="NEEDS_ENRICHMENT">Needs Enrichment</SelectItem>
            <SelectItem value="MANUAL_REVIEW">Manual Review</SelectItem>
          </SelectContent>
        </Select>
        <Select value={classificationFilter} onValueChange={setClassificationFilter}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Classification" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Classes</SelectItem>
            <SelectItem value="hot">HOT</SelectItem>
            <SelectItem value="warm">WARM</SelectItem>
            <SelectItem value="cold">COLD</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Main Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Company</TableHead>
                <TableHead>Platform</TableHead>
                <TableHead>Decision Maker</TableHead>
                <TableHead>Contact</TableHead>
                <TableHead>Opportunity</TableHead>
                <TableHead>Top Pain Point</TableHead>
                <TableHead>Status</TableHead>
                <TableHead></TableHead>
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
                  <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                    No accounts found. Click &quot;Build Accounts&quot; to generate from ecommerce leads.
                  </TableCell>
                </TableRow>
              ) : (
                filtered.map((account) => (
                  <TableRow
                    key={account.id}
                    className="cursor-pointer hover:bg-accent/50"
                    onClick={() => setSelectedAccount(selectedAccount?.id === account.id ? null : account)}
                  >
                    <TableCell className="font-medium">
                      <div>
                        <div>{account.company_name}</div>
                        <div className="text-xs text-muted-foreground truncate max-w-[200px]">
                          {account.domain}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">
                        {account.platform || "unknown"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm">
                      {account.primary_decision_maker || (
                        <span className="text-muted-foreground">Unknown</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col gap-1">
                        {account.primary_email && (
                          <div className="flex items-center gap-1 text-xs">
                            <Mail className="h-3 w-3" />
                            <span className="truncate max-w-[150px]">{account.primary_email}</span>
                          </div>
                        )}
                        {account.primary_phone && (
                          <div className="flex items-center gap-1 text-xs">
                            <Phone className="h-3 w-3" />
                            <span>{account.primary_phone}</span>
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Badge
                          variant="outline"
                          className={`text-xs ${classificationColor(account.opportunity_score?.classification)}`}
                        >
                          {account.opportunity_score?.classification?.toUpperCase()}
                        </Badge>
                        <span className="text-sm font-mono font-semibold">
                          {account.opportunity_score?.total_score?.toFixed(0)}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="text-xs max-w-[200px] truncate">
                      {account.pain_analysis?.top_pain || "N/A"}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={`text-xs ${statusColor(account.status)}`}
                      >
                        {account.status.replace("_", " ")}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {selectedAccount?.id === account.id ? (
                        <ChevronUp className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Expanded Detail Panel */}
      {selectedAccount && (
        <Card className="border-primary/20">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                {selectedAccount.company_name} - Sales Intelligence
              </CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setSelectedAccount(null)}>
                Close
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Why COMAI */}
            <div className="p-4 rounded-lg bg-primary/5 border border-primary/10">
              <h3 className="font-semibold mb-2 flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-yellow-400" />
                Why COMAI
              </h3>
              <p className="text-sm">{selectedAccount.sales_summary?.why_comai}</p>
            </div>

            {/* Pain Points */}
            <div>
              <h3 className="font-semibold mb-3 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-400" />
                Pain Points ({selectedAccount.pain_analysis?.pain_points?.length || 0})
              </h3>
              <div className="grid gap-2 md:grid-cols-2">
                {selectedAccount.pain_analysis?.pain_points?.map((pain, i) => (
                  <div key={i} className="p-3 rounded-lg border bg-card">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium">{pain.category.replace(/_/g, " ")}</span>
                      <Badge variant="outline" className={`text-xs ${severityColor(pain.severity)}`}>
                        {pain.severity}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mb-1">{pain.description}</p>
                    <p className="text-xs text-primary">{pain.comai_solution}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Call Preparation */}
            <div>
              <h3 className="font-semibold mb-3 flex items-center gap-2">
                <Phone className="h-4 w-4 text-blue-400" />
                Call Preparation
              </h3>
              <div className="p-4 rounded-lg border bg-card space-y-4">
                <div>
                  <span className="text-xs font-medium text-muted-foreground">30-Second Opener:</span>
                  <p className="text-sm mt-1">{selectedAccount.call_preparation?.thirty_second_opener}</p>
                </div>
                <div>
                  <span className="text-xs font-medium text-muted-foreground">Demo Angle:</span>
                  <p className="text-sm mt-1">{selectedAccount.call_preparation?.demo_angle}</p>
                </div>
                <div>
                  <span className="text-xs font-medium text-muted-foreground">Recommended Features:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedAccount.call_preparation?.recommended_features?.map((feat, i) => (
                      <Badge key={i} variant="secondary" className="text-xs">{feat}</Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <span className="text-xs font-medium text-muted-foreground">Top Objections:</span>
                  {selectedAccount.call_preparation?.likely_objections?.slice(0, 2).map((obj, i) => (
                    <div key={i} className="mt-2 p-2 rounded bg-muted/50">
                      <p className="text-xs font-medium">Q: {obj.objection}</p>
                      <p className="text-xs text-muted-foreground">A: {obj.response}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Technology & Fit */}
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <h3 className="font-semibold mb-3">Technology Stack</h3>
                <div className="p-4 rounded-lg border bg-card space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Platform:</span>
                    <Badge variant="outline">{selectedAccount.technology_profile?.platform || "Unknown"}</Badge>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Chatbot:</span>
                    <span>{selectedAccount.technology_profile?.chatbot_tool || "None"}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Support Tools:</span>
                    <span>{selectedAccount.technology_profile?.support_tools?.join(", ") || "None"}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>COMAI Fit:</span>
                    <span className="font-mono font-semibold">{selectedAccount.technology_profile?.comai_fit_score?.toFixed(0)}/100</span>
                  </div>
                </div>
              </div>
              <div>
                <h3 className="font-semibold mb-3">Opportunity Breakdown</h3>
                <div className="p-4 rounded-lg border bg-card space-y-2">
                  {selectedAccount.opportunity_score?.score_breakdown && Object.entries(selectedAccount.opportunity_score.score_breakdown).map(([key, value]) => (
                    <div key={key} className="flex justify-between text-sm">
                      <span className="capitalize">{key.replace(/_/g, " ")}:</span>
                      <div className="flex items-center gap-2">
                        <div className="w-20 h-1.5 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary rounded-full"
                            style={{ width: `${Math.min(100, value)}%` }}
                          />
                        </div>
                        <span className="font-mono text-xs w-8 text-right">{value.toFixed(0)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Pagination */}
      {total > pageSize && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {page * pageSize + 1}-{Math.min((page + 1) * pageSize, total)} of {total}
          </p>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
              Previous
            </Button>
            <Button variant="outline" size="sm" disabled={(page + 1) * pageSize >= total} onClick={() => setPage((p) => p + 1)}>
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
