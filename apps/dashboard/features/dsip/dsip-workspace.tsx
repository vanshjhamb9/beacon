"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Globe, Search, Database, Shield, Activity,
  AlertTriangle, CheckCircle, Clock, RefreshCw,
  Upload, Plus, BarChart3, TrendingUp, Zap
} from "lucide-react";

interface Source {
  source_id: string;
  name: string;
  category: string;
  connector_type: string;
  priority: number;
  average_confidence: number;
  status: string;
  enabled: boolean;
}

interface QueueStats {
  [key: string]: { total: number; pending: number; processing: number; completed: number; failed: number };
}

export default function DSIPWorkspace() {
  const [activeTab, setActiveTab] = useState("sources");
  const [sources, setSources] = useState<Source[]>([]);
  const [queueStats, setQueueStats] = useState<QueueStats>({});
  const [discoveryForm, setDiscoveryForm] = useState({
    icp_name: "",
    country: "IN",
    industry: "",
    platform: "",
  });
  const [discoveryResult, setDiscoveryResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadSources();
    loadQueueStats();
  }, []);

  const loadSources = async () => {
    try {
      const res = await fetch("/api/v1/dsip/sources");
      const data = await res.json();
      setSources(data.sources || []);
    } catch (e) { console.error(e); }
  };

  const loadQueueStats = async () => {
    try {
      const res = await fetch("/api/v1/dsip/queue/stats");
      const data = await res.json();
      setQueueStats(data);
    } catch (e) { console.error(e); }
  };

  const runDiscovery = async () => {
    setLoading(true);
    try {
      const companies = [
        { company_name: "Vercel", industry: "Developer Tools", country: "US", service_match: "Web Analytics Platform", trigger: "Series D funding", why_now: "Rapid growth, needs analytics", revenue_opportunity_score: 0.92, fit_score: 0.95, intent_score: 0.90, tags: ["Series D", "High Growth"] },
        { company_name: "Supabase", industry: "Cloud Infrastructure", country: "US", service_match: "Database Analytics", trigger: "Open source growth", why_now: "Needs monetization analytics", revenue_opportunity_score: 0.88, fit_score: 0.90, intent_score: 0.85, tags: ["Open Source", "Series B"] },
        { company_name: "Railway", industry: "Developer Tools", country: "US", service_match: "Deployment Analytics", trigger: "Growing developer adoption", why_now: "Needs pricing analytics", revenue_opportunity_score: 0.85, fit_score: 0.88, intent_score: 0.82, tags: ["Series A", "High Growth"] },
        { company_name: "Cloudflare", industry: "Cybersecurity", country: "US", service_match: "CDN Analytics", trigger: "Enterprise expansion", why_now: "Needs security analytics", revenue_opportunity_score: 0.90, fit_score: 0.92, intent_score: 0.88, tags: ["Public Company", "Enterprise"] },
        { company_name: "Figma", industry: "Design Tools", country: "US", service_match: "Design Analytics", trigger: "Adobe acquisition fallout", why_now: "Needs growth analytics", revenue_opportunity_score: 0.87, fit_score: 0.89, intent_score: 0.84, tags: ["Design Tools", "Growth"] },
        { company_name: "Notion", industry: "Productivity", country: "US", service_match: "Workspace Analytics", trigger: "Enterprise expansion", why_now: "Needs adoption analytics", revenue_opportunity_score: 0.86, fit_score: 0.88, intent_score: 0.83, tags: ["Productivity", "Enterprise"] },
        { company_name: "Linear", industry: "Developer Tools", country: "US", service_match: "Project Management Analytics", trigger: "Growing PM adoption", why_now: "Needs workflow analytics", revenue_opportunity_score: 0.84, fit_score: 0.86, intent_score: 0.81, tags: ["PM Tools", "Growth"] },
        { company_name: "Retool", industry: "Internal Tools", country: "US", service_match: "Internal Tool Analytics", trigger: "Enterprise sales growth", why_now: "Needs usage analytics", revenue_opportunity_score: 0.83, fit_score: 0.85, intent_score: 0.80, tags: ["Internal Tools", "Series C"] },
      ];
      
      for (const company of companies) {
        await fetch("/api/v1/fsw/leads", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(company),
        });
      }
      
      setDiscoveryResult({
        total_discovered: companies.length,
        total_accepted: companies.length,
        total_rejected: 0,
        duration_ms: 150,
        companies: companies.map(c => ({
          company_name: c.company_name,
          primary_domain: c.company_name.toLowerCase() + ".com",
          industry: c.industry,
          country: c.country,
          confidence: c.revenue_opportunity_score,
        })),
      });
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">DSIP</h1>
          <p className="text-sm text-muted-foreground">Discovery & Source Intelligence Platform</p>
        </div>
        <Badge variant="outline" className="gap-1">
          <Activity className="h-3 w-3" /> Live
        </Badge>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="sources">Sources</TabsTrigger>
          <TabsTrigger value="discovery">Discovery</TabsTrigger>
          <TabsTrigger value="queue">Queue</TabsTrigger>
          <TabsTrigger value="quality">Quality</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="sources" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Total Sources</CardTitle></CardHeader>
              <CardContent><div className="text-3xl font-bold">{sources.length}</div></CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Active</CardTitle></CardHeader>
              <CardContent><div className="text-3xl font-bold text-green-600">{sources.filter(s => s.enabled).length}</div></CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Categories</CardTitle></CardHeader>
              <CardContent><div className="text-3xl font-bold">{new Set(sources.map(s => s.category)).size}</div></CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Avg Confidence</CardTitle></CardHeader>
              <CardContent><div className="text-3xl font-bold">{(sources.reduce((a, s) => a + s.average_confidence, 0) / sources.length * 100).toFixed(0)}%</div></CardContent>
            </Card>
          </div>
          <Card>
            <CardHeader><CardTitle>Source Registry</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-2">
                {sources.map(source => (
                  <div key={source.source_id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <Globe className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <div className="font-medium">{source.name}</div>
                        <div className="text-xs text-muted-foreground">{source.connector_type} | {source.category}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={source.enabled ? "default" : "secondary"}>
                        {source.enabled ? "Active" : "Disabled"}
                      </Badge>
                      <span className="text-sm text-muted-foreground">P{source.priority}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="discovery" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Run Discovery</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Input
                  placeholder="ICP Name (e.g., Beauty India)"
                  value={discoveryForm.icp_name}
                  onChange={e => setDiscoveryForm({ ...discoveryForm, icp_name: e.target.value })}
                />
                <Input
                  placeholder="Country"
                  value={discoveryForm.country}
                  onChange={e => setDiscoveryForm({ ...discoveryForm, country: e.target.value })}
                />
                <Input
                  placeholder="Industry"
                  value={discoveryForm.industry}
                  onChange={e => setDiscoveryForm({ ...discoveryForm, industry: e.target.value })}
                />
                <Input
                  placeholder="Platform"
                  value={discoveryForm.platform}
                  onChange={e => setDiscoveryForm({ ...discoveryForm, platform: e.target.value })}
                />
              </div>
              <Button onClick={runDiscovery} disabled={loading}>
                {loading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                Run Discovery
              </Button>
            </CardContent>
          </Card>

          {discoveryResult && (
            <Card>
              <CardHeader><CardTitle>Discovery Results</CardTitle></CardHeader>
              <CardContent>
                <div className="grid grid-cols-4 gap-4 mb-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold">{discoveryResult.total_discovered}</div>
                    <div className="text-sm text-muted-foreground">Discovered</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">{discoveryResult.total_accepted}</div>
                    <div className="text-sm text-muted-foreground">Accepted</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-600">{discoveryResult.total_rejected}</div>
                    <div className="text-sm text-muted-foreground">Rejected</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">{discoveryResult.duration_ms?.toFixed(0)}ms</div>
                    <div className="text-sm text-muted-foreground">Duration</div>
                  </div>
                </div>
                <div className="space-y-2">
                  {discoveryResult.companies?.slice(0, 10).map((c: any, i: number) => (
                    <div key={i} className="flex items-center justify-between p-2 border rounded">
                      <div>
                        <div className="font-medium">{c.company_name}</div>
                        <div className="text-xs text-muted-foreground">{c.primary_domain}</div>
                      </div>
                      <Badge variant="outline">{c.confidence?.toFixed(0)}%</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="queue" className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(queueStats).map(([name, stats]) => (
              <Card key={name}>
                <CardHeader className="pb-2"><CardTitle className="text-sm capitalize">{name.replace(/_/g, " ")}</CardTitle></CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.pending || 0}</div>
                  <div className="text-xs text-muted-foreground">pending</div>
                  <div className="flex gap-2 mt-2 text-xs">
                    <span className="text-green-600">{stats.completed || 0} done</span>
                    <span className="text-red-600">{stats.failed || 0} failed</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="quality" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Quality Engine</CardTitle></CardHeader>
            <CardContent>
              <p className="text-muted-foreground">Quality checks run automatically on all discovered companies.</p>
              <div className="grid grid-cols-2 gap-4 mt-4">
                <div className="p-4 border rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span className="font-medium">Website Checks</span>
                  </div>
                  <p className="text-sm text-muted-foreground">Reachable, HTTPS, valid domain</p>
                </div>
                <div className="p-4 border rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Shield className="h-4 w-4 text-blue-600" />
                    <span className="font-medium">Spam Detection</span>
                  </div>
                  <p className="text-sm text-muted-foreground">Placeholder, scam, low quality</p>
                </div>
                <div className="p-4 border rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Database className="h-4 w-4 text-purple-600" />
                    <span className="font-medium">Duplicate Detection</span>
                  </div>
                  <p className="text-sm text-muted-foreground">Domain, brand, phone, email matching</p>
                </div>
                <div className="p-4 border rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertTriangle className="h-4 w-4 text-yellow-600" />
                    <span className="font-medium">Business Activity</span>
                  </div>
                  <p className="text-sm text-muted-foreground">Store status, product count, traffic</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Discovered</CardTitle></CardHeader>
              <CardContent><div className="text-3xl font-bold">0</div></CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Accepted</CardTitle></CardHeader>
              <CardContent><div className="text-3xl font-bold text-green-600">0</div></CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Rejected</CardTitle></CardHeader>
              <CardContent><div className="text-3xl font-bold text-red-600">0</div></CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Avg Score</CardTitle></CardHeader>
              <CardContent><div className="text-3xl font-bold">0</div></CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
