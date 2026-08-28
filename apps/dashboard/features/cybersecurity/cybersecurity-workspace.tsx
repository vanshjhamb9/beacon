"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiGet } from "@/lib/api/client";

interface Lead {
  opportunity_id: string;
  company_name: string;
  company_url: string;
  country: string;
  industry: string;
  priority: string;
  final_verdict: string;
  buying_event: string;
  services_needed: string[];
  decision_maker: string;
  email: string;
  email_status: string;
  contactability: string;
  evidence_count: number;
  evidence_confidence: string;
}

interface Summary {
  has_data: boolean;
  sales_ready_count: number;
  total_evidence_items: number;
}

const PRIORITY_COLORS: Record<string, string> = {
  ACTIVE_BUYING_EVENT: "bg-red-500/15 text-red-500",
  VERIFIED_SECURITY_PAIN: "bg-yellow-500/15 text-yellow-500",
  HIGH_POTENTIAL_OUTBOUND: "bg-blue-500/15 text-blue-500",
};

const VERDICT_COLORS: Record<string, string> = {
  SALES_READY: "bg-green-500/15 text-green-500",
  MARKETING_READY: "bg-yellow-500/15 text-yellow-500",
  NOT_READY: "bg-red-500/15 text-red-500",
};

export function CybersecurityWorkspace() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [leadsRes, summaryRes] = await Promise.allSettled([
        apiGet<Lead[]>("/cybersecurity/leads"),
        apiGet<Summary>("/cybersecurity/summary"),
      ]);
      if (leadsRes.status === "fulfilled") setLeads(leadsRes.value);
      if (summaryRes.status === "fulfilled") setSummary(summaryRes.value);
    } catch (e) {
      setError("Failed to fetch cybersecurity data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <header className="flex items-center justify-between">
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">Cybersecurity Buyer Discovery</p>
          <h1 className="font-display text-3xl font-semibold tracking-tight">
            Cybersecurity Leads
          </h1>
        </div>
        <Button onClick={fetchData} disabled={loading}>
          {loading ? "Loading..." : "Refresh"}
        </Button>
      </header>

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/5 p-4 text-sm text-red-500">
          {error}
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">SALES_READY</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{summary?.sales_ready_count ?? leads.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Evidence Items</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{summary?.total_evidence_items ?? 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{summary?.has_data ? "Active" : "No Data"}</div>
          </CardContent>
        </Card>
      </div>

      {/* Leads Table */}
      <Card>
        <CardHeader>
          <CardTitle>Discovered Leads</CardTitle>
          <CardDescription>Companies with active cybersecurity buying signals</CardDescription>
        </CardHeader>
        <CardContent>
          {leads.length === 0 ? (
            <div className="py-8 text-center text-muted-foreground">
              No leads found. Run discovery first via the API.
            </div>
          ) : (
            <div className="space-y-3">
              {leads.map((lead) => (
                <div
                  key={lead.opportunity_id}
                  className="flex items-center justify-between rounded-lg border border-border/60 p-4"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <p className="font-medium">{lead.company_name}</p>
                      <Badge variant="outline" className={PRIORITY_COLORS[lead.priority] ?? ""}>
                        {lead.priority.replace(/_/g, " ")}
                      </Badge>
                      <Badge variant="outline" className={VERDICT_COLORS[lead.final_verdict] ?? ""}>
                        {lead.final_verdict.replace(/_/g, " ")}
                      </Badge>
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground truncate">
                      {lead.buying_event}
                    </p>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {lead.services_needed.map((s) => (
                        <Badge key={s} variant="secondary" className="text-xs">
                          {s.replace(/_/g, " ")}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div className="ml-4 text-right text-sm">
                    <p className="font-medium">{lead.decision_maker}</p>
                    <p className="text-muted-foreground">{lead.email}</p>
                    <p className="text-xs text-muted-foreground">
                      {lead.evidence_count} evidence · {lead.evidence_confidence}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
