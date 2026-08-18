"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Phone,
  PhoneCall,
  RefreshCw,
  Search,
  Mail,
  Linkedin,
  ExternalLink,
  ArrowUpRight,
  Clock,
  Star,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
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
  clients: string | null;
  client_count: number | null;
  decision_maker: string | null;
  decision_maker_role: string | null;
  email: string | null;
  phone: string | null;
  linkedin: string | null;
  contactability: string | null;
  services: string[];
  tier: string | null;
  client_access_score: number | null;
  comai_fit_score: number | null;
  final_score: number | null;
  why_this_agency: string | null;
  comai_fit: string | null;
  pitch_angle: string | null;
  status: string;
  created_at: string;
};

const API_BASE = "/api/v1/partner-leads";

function tierColor(tier: string | null) {
  switch (tier) {
    case "A":
      return "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
    case "B":
      return "bg-amber-500/15 text-amber-400 border-amber-500/30";
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
    default:
      return "bg-red-500/15 text-red-400 border-red-500/30";
  }
}

function isToday(dateStr: string) {
  const d = new Date(dateStr);
  const now = new Date();
  return (
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  );
}

export default function ColdCallPage() {
  const [leads, setLeads] = useState<PartnerLead[]>([]);
  const [allLeads, setAllLeads] = useState<PartnerLead[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"today" | "new" | "phone" | "high">("phone");

  const fetchLeads = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}?limit=200&status=NEW`);
      const data = await res.json();
      const items = data.items || [];
      setAllLeads(items);
    } catch (e) {
      console.error("Failed to fetch leads", e);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchLeads();
  }, [fetchLeads]);

  useEffect(() => {
    let filtered = allLeads;

    if (search) {
      const q = search.toLowerCase();
      filtered = filtered.filter(
        (l) =>
          l.agency_name.toLowerCase().includes(q) ||
          (l.decision_maker && l.decision_maker.toLowerCase().includes(q)) ||
          (l.city && l.city.toLowerCase().includes(q))
      );
    }

    switch (filter) {
      case "today":
        filtered = filtered.filter((l) => isToday(l.created_at));
        break;
      case "new":
        filtered = filtered.filter((l) => l.status === "NEW");
        break;
      case "phone":
        filtered = filtered.filter((l) => l.phone && l.phone.length > 5);
        break;
      case "high":
        filtered = filtered.filter(
          (l) => l.contactability === "HIGH" && l.phone && l.phone.length > 5
        );
        break;
    }

    filtered.sort((a, b) => (b.final_score || 0) - (a.final_score || 0));
    setLeads(filtered);
  }, [allLeads, search, filter]);

  const todayCount = allLeads.filter((l) => isToday(l.created_at)).length;
  const phoneCount = allLeads.filter((l) => l.phone && l.phone.length > 5).length;
  const highPhoneCount = allLeads.filter(
    (l) => l.contactability === "HIGH" && l.phone && l.phone.length > 5
  ).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <PhoneCall className="h-6 w-6 text-green-400" />
            Cold Call Today
          </h1>
          <p className="text-muted-foreground">
            B2B partner leads ready for cold calling â€” sorted by score
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchLeads}>
          <RefreshCw className="h-4 w-4 mr-1" /> Refresh
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Today&apos;s New</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-400">{todayCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">All NEW Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{allLeads.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-green-500">Have Phone Number</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-400">{phoneCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-emerald-500">High + Phone Ready</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-400">{highPhoneCount}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filter Chips */}
      <div className="flex flex-wrap gap-2">
        {[
          { key: "today" as const, label: "Today's New", icon: Clock, count: todayCount },
          { key: "new" as const, label: "All NEW", icon: Star, count: allLeads.length },
          { key: "phone" as const, label: "Have Phone", icon: Phone, count: phoneCount },
          { key: "high" as const, label: "High + Phone", icon: PhoneCall, count: highPhoneCount },
        ].map((chip) => (
          <button
            key={chip.key}
            onClick={() => setFilter(chip.key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filter === chip.key
                ? "bg-green-500/20 text-green-400 border border-green-500/30"
                : "bg-muted text-muted-foreground hover:bg-muted/80 border border-transparent"
            }`}
          >
            <chip.icon className="h-4 w-4" />
            {chip.label}
            <span className="ml-1 px-1.5 py-0.5 rounded text-xs bg-background/50">{chip.count}</span>
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search by agency, founder, city..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>

      {/* Cold Call Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">#</TableHead>
                <TableHead>Agency</TableHead>
                <TableHead>Tier</TableHead>
                <TableHead>Score</TableHead>
                <TableHead>Founder / Decision Maker</TableHead>
                <TableHead>Phone</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>LinkedIn</TableHead>
                <TableHead>Contact</TableHead>
                <TableHead>Why This Agency</TableHead>
                <TableHead>Pitch Angle</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={11} className="text-center py-8 text-muted-foreground">
                    Loading leads for cold calling...
                  </TableCell>
                </TableRow>
              ) : leads.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={11} className="text-center py-8 text-muted-foreground">
                    No leads match the current filter
                  </TableCell>
                </TableRow>
              ) : (
                leads.map((lead, idx) => (
                  <TableRow key={lead.id} className={lead.phone ? "bg-green-500/5" : ""}>
                    <TableCell className="text-muted-foreground font-mono text-sm">
                      {idx + 1}
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="font-medium">{lead.agency_name}</div>
                        <div className="text-xs text-muted-foreground">
                          {lead.agency_type} {lead.city ? `â€¢ ${lead.city}` : ""}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={tierColor(lead.tier)}>
                        {lead.tier || "C"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <span className="font-mono font-bold text-lg">{lead.final_score || 0}</span>
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="text-sm font-medium">{lead.decision_maker || "â€”"}</div>
                        <div className="text-xs text-muted-foreground">{lead.decision_maker_role || ""}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      {lead.phone ? (
                        <a
                          href={`tel:${lead.phone}`}
                          className="inline-flex items-center gap-1 px-2 py-1 rounded bg-green-500/15 text-green-400 hover:bg-green-500/25 text-sm font-mono"
                        >
                          <Phone className="h-3 w-3" />
                          {lead.phone}
                        </a>
                      ) : (
                        <span className="text-muted-foreground text-sm">â€”</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {lead.email ? (
                        <a href={`mailto:${lead.email}`} className="text-xs text-blue-400 hover:underline flex items-center gap-1">
                          <Mail className="h-3 w-3" /> {lead.email}
                        </a>
                      ) : (
                        "â€”"
                      )}
                    </TableCell>
                    <TableCell>
                      {lead.linkedin ? (
                        <a href={lead.linkedin} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-400 hover:underline flex items-center gap-1">
                          <Linkedin className="h-3 w-3" /> Profile
                        </a>
                      ) : (
                        "â€”"
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={contactColor(lead.contactability)}>
                        {lead.contactability || "â€”"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="text-xs text-muted-foreground max-w-[200px] truncate" title={lead.why_this_agency || ""}>
                        {lead.why_this_agency || "â€”"}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-xs max-w-[200px] truncate" title={lead.pitch_angle || ""}>
                        {lead.pitch_angle || "â€”"}
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Summary */}
      <div className="text-sm text-muted-foreground">
        Showing {leads.length} leads sorted by score (highest first). Click any phone number to start dialing.
      </div>
    </div>
  );
}
