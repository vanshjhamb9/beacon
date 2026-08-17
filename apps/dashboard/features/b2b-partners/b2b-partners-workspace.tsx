"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Building2,
  Globe,
  Mail,
  Phone,
  RefreshCw,
  Search,
  Target,
  TrendingUp,
  Users,
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

type Partner = {
  id: string;
  agency_name: string;
  agency_url: string;
  domain: string;
  agency_type: string;
  country: string;
  city: string;
  founder_name: string;
  founder_role: string;
  services: string[];
  client_count_evidence: number;
  partner_intent: string;
  client_access_score: number;
  comai_partner_fit: number;
  email: string;
  phone: string;
  contactability: string;
  partner_tier: string;
  final_verdict: string;
  recommended_pitch_angle: string;
  why_this_agency: string;
};

type Stats = {
  total: number;
  tier_a: number;
  tier_b: number;
  tier_c: number;
  with_email: number;
  with_phone: number;
  contactable: number;
  avg_client_score: number;
  avg_fit_score: number;
  explicit_intent: number;
  high_potential: number;
  by_type: Record<string, number>;
  by_country: Record<string, number>;
  by_intent: Record<string, number>;
};

function tierColor(tier: string) {
  switch (tier) {
    case "A":
      return "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
    case "B":
      return "bg-amber-500/15 text-amber-400 border-amber-500/30";
    default:
      return "bg-slate-500/15 text-slate-400 border-slate-500/30";
  }
}

function intentColor(intent: string) {
  switch (intent) {
    case "EXPLICIT":
      return "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
    case "HIGH_POTENTIAL":
      return "bg-blue-500/15 text-blue-400 border-blue-500/30";
    case "MEDIUM":
      return "bg-amber-500/15 text-amber-400 border-amber-500/30";
    default:
      return "bg-slate-500/15 text-slate-400 border-slate-500/30";
  }
}

function typeIcon(type: string) {
  switch (type) {
    case "marketing":
      return <TrendingUp className="h-3 w-3 text-blue-400" />;
    case "technology":
      return <Zap className="h-3 w-3 text-purple-400" />;
    case "creative":
      return <Building2 className="h-3 w-3 text-pink-400" />;
    default:
      return <Users className="h-3 w-3 text-orange-400" />;
  }
}

export function B2BPartnersWorkspace() {
  const [partners, setPartners] = useState<Partner[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [tierFilter, setTierFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [countryFilter, setCountryFilter] = useState("all");
  const [page, setPage] = useState(0);
  const pageSize = 25;

  const fetchPartners = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("limit", "500");
      if (search) params.set("search", search);
      if (tierFilter !== "all") params.set("tier", tierFilter);
      if (typeFilter !== "all") params.set("agency_type", typeFilter);
      if (countryFilter !== "all") params.set("country", countryFilter);

      const res = await fetch(`/api/v1/b2b-partners/all?${params}`);
      if (res.ok) {
        const data = await res.json();
        setPartners(data.partners);
        setTotal(data.total);
        setStats(data.stats);
      }
    } catch (e) {
      console.error("Failed to fetch partners", e);
    }
    setLoading(false);
  }, [search, tierFilter, typeFilter, countryFilter]);

  useEffect(() => {
    fetchPartners();
    const interval = setInterval(fetchPartners, 30000);
    return () => clearInterval(interval);
  }, [fetchPartners]);

  const filteredPartners = partners;
  const paginatedPartners = filteredPartners.slice(
    page * pageSize,
    (page + 1) * pageSize
  );
  const totalPages = Math.max(1, Math.ceil(filteredPartners.length / pageSize));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            COMAI B2B Partner Pipeline
          </h1>
          <p className="text-muted-foreground">
            {total} agencies, consultants, and service providers for COMAI partner program
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={fetchPartners}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button variant="outline" size="sm" asChild>
            <a href="/api/v1/b2b-partners/export" target="_blank" rel="noreferrer">
              Export Report
            </a>
          </Button>
        </div>
      </div>

      {stats && (
        <div className="grid gap-4 md:grid-cols-4 lg:grid-cols-8">
          <Card>
            <CardContent className="p-3">
              <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
                Total
              </p>
              <p className="text-xl font-bold">{stats.total}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-3">
              <p className="text-[10px] uppercase tracking-wider text-emerald-500">
                Tier A (HOT)
              </p>
              <p className="text-xl font-bold text-emerald-400">{stats.tier_a}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-3">
              <p className="text-[10px] uppercase tracking-wider text-amber-500">
                Tier B (HIGH)
              </p>
              <p className="text-xl font-bold text-amber-400">{stats.tier_b}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-3">
              <p className="text-[10px] uppercase tracking-wider text-slate-500">
                Tier C (NURTURE)
              </p>
              <p className="text-xl font-bold text-slate-400">{stats.tier_c}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-3">
              <p className="text-[10px] uppercase tracking-wider text-blue-500">
                With Email
              </p>
              <p className="text-xl font-bold text-blue-400">{stats.with_email}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-3">
              <p className="text-[10px] uppercase tracking-wider text-emerald-500">
                With Phone
              </p>
              <p className="text-xl font-bold text-emerald-400">{stats.with_phone}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-3">
              <p className="text-[10px] uppercase tracking-wider text-purple-500">
                Explicit Intent
              </p>
              <p className="text-xl font-bold text-purple-400">{stats.explicit_intent}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-3">
              <p className="text-[10px] uppercase tracking-wider text-orange-500">
                Avg Client Score
              </p>
              <p className="text-xl font-bold text-orange-400">{stats.avg_client_score}</p>
            </CardContent>
          </Card>
        </div>
      )}

      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Search className="h-4 w-4" />
              Filters
            </div>
            <div className="relative flex-1 sm:max-w-xs">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search agency, founder, email..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(0);
                }}
                className="h-9 pl-9"
              />
            </div>
            <Select
              value={tierFilter}
              onValueChange={(v) => {
                setTierFilter(v);
                setPage(0);
              }}
            >
              <SelectTrigger className="w-[130px]">
                <SelectValue placeholder="Tier" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Tiers</SelectItem>
                <SelectItem value="A">Tier A (HOT)</SelectItem>
                <SelectItem value="B">Tier B (HIGH)</SelectItem>
                <SelectItem value="C">Tier C (NURTURE)</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={typeFilter}
              onValueChange={(v) => {
                setTypeFilter(v);
                setPage(0);
              }}
            >
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="marketing">Marketing</SelectItem>
                <SelectItem value="technology">Technology</SelectItem>
                <SelectItem value="creative">Creative</SelectItem>
                <SelectItem value="consultant">Consultant</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={countryFilter}
              onValueChange={(v) => {
                setCountryFilter(v);
                setPage(0);
              }}
            >
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Country" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Countries</SelectItem>
                <SelectItem value="India">India</SelectItem>
                <SelectItem value="USA">USA</SelectItem>
                <SelectItem value="UK">UK</SelectItem>
                <SelectItem value="UAE">UAE</SelectItem>
                <SelectItem value="Australia">Australia</SelectItem>
                <SelectItem value="Canada">Canada</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center text-muted-foreground">
              Loading partners...
            </div>
          ) : paginatedPartners.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              No partners found.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b border-border/60 bg-muted/30 text-left text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
                  <tr>
                    <th className="px-4 py-3 font-medium">Agency</th>
                    <th className="px-4 py-3 font-medium">Type</th>
                    <th className="px-4 py-3 font-medium">Location</th>
                    <th className="px-4 py-3 font-medium">Founder</th>
                    <th className="px-4 py-3 font-medium">Services</th>
                    <th className="px-4 py-3 font-medium">Clients</th>
                    <th className="px-4 py-3 font-medium">Client Score</th>
                    <th className="px-4 py-3 font-medium">COMAI Fit</th>
                    <th className="px-4 py-3 font-medium">Intent</th>
                    <th className="px-4 py-3 font-medium">Tier</th>
                    <th className="px-4 py-3 font-medium">Contact</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedPartners.map((partner, idx) => (
                    <motion.tr
                      key={partner.id}
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.01 * idx }}
                      className="border-b border-border/40 hover:bg-muted/20"
                    >
                      <td className="px-4 py-3">
                        <div className="font-medium">{partner.agency_name}</div>
                        {partner.agency_url && (
                          <a
                            href={partner.agency_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-[11px] text-blue-400 hover:underline"
                          >
                            {partner.domain || partner.agency_url.slice(0, 30)}
                          </a>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1.5">
                          {typeIcon(partner.agency_type)}
                          <span className="text-xs capitalize">
                            {partner.agency_type}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                          <Globe className="h-3 w-3" />
                          {partner.city && `${partner.city}, `}
                          {partner.country}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-xs">
                        {partner.founder_name || (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1">
                          {partner.services.slice(0, 3).map((s) => (
                            <Badge
                              key={s}
                              variant="outline"
                              className="text-[10px]"
                            >
                              {s}
                            </Badge>
                          ))}
                          {partner.services.length > 3 && (
                            <Badge variant="outline" className="text-[10px]">
                              +{partner.services.length - 3}
                            </Badge>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-xs font-medium">
                        {partner.client_count_evidence}+
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-2 rounded-full bg-muted/30 overflow-hidden">
                            <div
                              className="h-full rounded-full bg-blue-500"
                              style={{
                                width: `${Math.min(100, partner.client_access_score)}%`,
                              }}
                            />
                          </div>
                          <span className="text-xs font-medium">
                            {partner.client_access_score}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-2 rounded-full bg-muted/30 overflow-hidden">
                            <div
                              className="h-full rounded-full bg-emerald-500"
                              style={{
                                width: `${Math.min(100, partner.comai_partner_fit)}%`,
                              }}
                            />
                          </div>
                          <span className="text-xs font-medium">
                            {partner.comai_partner_fit}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge
                          variant="outline"
                          className={`text-[10px] ${intentColor(partner.partner_intent)}`}
                        >
                          {partner.partner_intent.replace("_", " ")}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        <Badge
                          variant="outline"
                          className={`text-[10px] ${tierColor(partner.partner_tier)}`}
                        >
                          Tier {partner.partner_tier}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        {partner.email ? (
                          <div className="flex items-center gap-1.5">
                            <Mail className="h-3 w-3 text-blue-400" />
                            <span className="font-mono text-[10px] truncate max-w-[120px]">
                              {partner.email}
                            </span>
                          </div>
                        ) : partner.phone ? (
                          <div className="flex items-center gap-1.5">
                            <Phone className="h-3 w-3 text-emerald-400" />
                            <span className="font-mono text-[10px]">
                              {partner.phone}
                            </span>
                          </div>
                        ) : (
                          <span className="text-xs text-muted-foreground">
                            {partner.contactability}
                          </span>
                        )}
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
            {Math.min((page + 1) * pageSize, filteredPartners.length)} of{" "}
            {filteredPartners.length}
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
