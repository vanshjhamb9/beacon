"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

// Types
interface ICPProfile {
  id: string;
  name: string;
  industries: string[];
  countries: string[];
  platforms: string[];
  min_score: number;
}

interface CompanyAnalysis {
  domain: string;
  company_name: string;
  final_classification: string;
  overall_score: number;
  confidence: number;
  icp_match: any;
  growth_analysis: any;
  intent_analysis: any;
  revenue_score: any;
}

interface DashboardSummary {
  total_companies: number;
  hot_leads: number;
  warm_leads: number;
  cold_leads: number;
  rejected: number;
  avg_score: number;
  qualification_rate: number;
}

export default function ARIEWorkspace() {
  const [icpProfiles, setIcpProfiles] = useState<ICPProfile[]>([]);
  const [selectedICP, setSelectedICP] = useState<string>("");
  const [analysisResults, setAnalysisResults] = useState<CompanyAnalysis[]>([]);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [nlInput, setNlInput] = useState("");
  const [generatedICP, setGeneratedICP] = useState<any>(null);

  // Load ICP templates
  useEffect(() => {
    loadICPTemplates();
    loadDashboardSummary();
  }, []);

  const loadICPTemplates = async () => {
    try {
      const res = await fetch("/api/v1/arie/icp/templates");
      const data = await res.json();
      setIcpProfiles(data.templates || []);
    } catch (error) {
      console.error("Failed to load ICP templates:", error);
    }
  };

  const loadDashboardSummary = async () => {
    try {
      const res = await fetch("/api/v1/arie/dashboard/summary");
      const data = await res.json();
      setSummary(data);
    } catch (error) {
      console.error("Failed to load dashboard summary:", error);
    }
  };

  const generateICPFromNL = async () => {
    if (!nlInput.trim()) return;
    
    setLoading(true);
    try {
      const res = await fetch("/api/v1/arie/icp/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description: nlInput }),
      });
      const data = await res.json();
      setGeneratedICP(data);
    } catch (error) {
      console.error("Failed to generate ICP:", error);
    } finally {
      setLoading(false);
    }
  };

  const analyzeCompany = async (domain: string) => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/arie/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ domain }),
      });
      const data = await res.json();
      setAnalysisResults((prev) => [...prev, data]);
    } catch (error) {
      console.error("Failed to analyze company:", error);
    } finally {
      setLoading(false);
    }
  };

  const getClassificationColor = (classification: string) => {
    switch (classification) {
      case "HOT":
        return "bg-red-500";
      case "WARM":
        return "bg-orange-500";
      case "COLD":
        return "bg-blue-500";
      case "REJECTED":
        return "bg-gray-500";
      default:
        return "bg-yellow-500";
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">ARIE - AI Revenue Intelligence Engine</h1>
        <Badge variant="outline" className="text-sm">
          v3.0
        </Badge>
      </div>

      {/* Dashboard Summary */}
      {summary && (
        <div className="grid grid-cols-6 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold">{summary.total_companies}</div>
              <div className="text-sm text-muted-foreground">Total Companies</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-red-500">{summary.hot_leads}</div>
              <div className="text-sm text-muted-foreground">Hot Leads</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-orange-500">{summary.warm_leads}</div>
              <div className="text-sm text-muted-foreground">Warm Leads</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-blue-500">{summary.cold_leads}</div>
              <div className="text-sm text-muted-foreground">Cold Leads</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold">{summary.avg_score.toFixed(1)}</div>
              <div className="text-sm text-muted-foreground">Avg Score</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold">{summary.qualification_rate.toFixed(1)}%</div>
              <div className="text-sm text-muted-foreground">Qualification Rate</div>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue="icp" className="w-full">
        <TabsList>
          <TabsTrigger value="icp">ICP Management</TabsTrigger>
          <TabsTrigger value="analyze">Company Analysis</TabsTrigger>
          <TabsTrigger value="results">Analysis Results</TabsTrigger>
          <TabsTrigger value="pipeline">Pipeline</TabsTrigger>
        </TabsList>

        {/* ICP Management Tab */}
        <TabsContent value="icp" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Generate ICP from Natural Language</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4">
                <Input
                  placeholder="Describe your ideal customer... (e.g., 'I sell AI WhatsApp automation for beauty brands in India')"
                  value={nlInput}
                  onChange={(e) => setNlInput(e.target.value)}
                  className="flex-1"
                />
                <Button onClick={generateICPFromNL} disabled={loading}>
                  {loading ? "Generating..." : "Generate ICP"}
                </Button>
              </div>

              {generatedICP && (
                <div className="mt-4 p-4 bg-muted rounded-lg">
                  <h3 className="font-semibold mb-2">Generated ICP: {generatedICP.name}</h3>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="font-medium">Industries:</span>{" "}
                      {generatedICP.industries?.join(", ")}
                    </div>
                    <div>
                      <span className="font-medium">Countries:</span>{" "}
                      {generatedICP.countries?.join(", ")}
                    </div>
                    <div>
                      <span className="font-medium">Platforms:</span>{" "}
                      {generatedICP.platforms?.join(", ")}
                    </div>
                    <div>
                      <span className="font-medium">Pain Categories:</span>{" "}
                      {generatedICP.pain_categories?.join(", ")}
                    </div>
                    <div>
                      <span className="font-medium">Intent Signals:</span>{" "}
                      {generatedICP.intent_signals?.join(", ")}
                    </div>
                    <div>
                      <span className="font-medium">Min Traffic:</span>{" "}
                      {generatedICP.min_monthly_traffic?.toLocaleString()}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>ICP Templates</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                {icpProfiles.map((icp) => (
                  <div
                    key={icp.id}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedICP === icp.id
                        ? "border-primary bg-primary/5"
                        : "hover:border-primary/50"
                    }`}
                    onClick={() => setSelectedICP(icp.id)}
                  >
                    <h3 className="font-semibold">{icp.name}</h3>
                    <div className="text-sm text-muted-foreground mt-1">
                      {icp.industries?.join(", ")}
                    </div>
                    <div className="flex gap-2 mt-2">
                      {icp.countries?.map((c) => (
                        <Badge key={c} variant="secondary" className="text-xs">
                          {c}
                        </Badge>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Company Analysis Tab */}
        <TabsContent value="analyze" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Analyze Company</CardTitle>
            </CardHeader>
            <CardContent>
              <CompanyAnalysisForm onSubmit={analyzeCompany} loading={loading} />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analysis Results Tab */}
        <TabsContent value="results" className="space-y-4">
          {analysisResults.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center text-muted-foreground">
                No analysis results yet. Analyze a company to see results here.
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {analysisResults.map((result, idx) => (
                <AnalysisResultCard key={idx} result={result} />
              ))}
            </div>
          )}
        </TabsContent>

        {/* Pipeline Tab */}
        <TabsContent value="pipeline" className="space-y-4">
          <PipelineView results={analysisResults} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

// Company Analysis Form Component
function CompanyAnalysisForm({
  onSubmit,
  loading,
}: {
  onSubmit: (domain: string) => void;
  loading: boolean;
}) {
  const [domain, setDomain] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (domain.trim()) {
      onSubmit(domain.trim());
      setDomain("");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-4">
      <Input
        placeholder="Enter company domain (e.g., mamaearth.in)"
        value={domain}
        onChange={(e) => setDomain(e.target.value)}
        className="flex-1"
      />
      <Button type="submit" disabled={loading || !domain.trim()}>
        {loading ? "Analyzing..." : "Analyze"}
      </Button>
    </form>
  );
}

// Analysis Result Card Component
function AnalysisResultCard({ result }: { result: CompanyAnalysis }) {
  const getClassificationColor = (classification: string) => {
    switch (classification) {
      case "HOT":
        return "bg-red-500 text-white";
      case "WARM":
        return "bg-orange-500 text-white";
      case "COLD":
        return "bg-blue-500 text-white";
      case "REJECTED":
        return "bg-gray-500 text-white";
      default:
        return "bg-yellow-500 text-white";
    }
  };

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-xl font-semibold">{result.company_name || result.domain}</h3>
            <p className="text-muted-foreground">{result.domain}</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge className={getClassificationColor(result.final_classification)}>
              {result.final_classification}
            </Badge>
            <div className="text-right">
              <div className="text-2xl font-bold">{result.overall_score.toFixed(1)}</div>
              <div className="text-xs text-muted-foreground">Score</div>
            </div>
          </div>
        </div>

        {/* Score Breakdown */}
        {result.revenue_score && (
          <div className="mt-4 grid grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-lg font-semibold">
                {result.revenue_score.icp_score?.score?.toFixed(0) || "N/A"}
              </div>
              <div className="text-xs text-muted-foreground">ICP</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold">
                {result.revenue_score.technology_fit?.score?.toFixed(0) || "N/A"}
              </div>
              <div className="text-xs text-muted-foreground">Technology</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold">
                {result.revenue_score.growth_score?.score?.toFixed(0) || "N/A"}
              </div>
              <div className="text-xs text-muted-foreground">Growth</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold">
                {result.revenue_score.intent_score?.score?.toFixed(0) || "N/A"}
              </div>
              <div className="text-xs text-muted-foreground">Intent</div>
            </div>
          </div>
        )}

        {/* Sales Package Preview */}
        {result.sales_package && (
          <div className="mt-4 p-4 bg-muted rounded-lg">
            <h4 className="font-semibold mb-2">Sales Package</h4>
            <p className="text-sm">{result.sales_package.why_this_company}</p>
            <div className="mt-2 text-sm">
              <span className="font-medium">ROI:</span>{" "}
              {result.sales_package.roi_estimate?.roi || "N/A"}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Pipeline View Component
function PipelineView({ results }: { results: CompanyAnalysis[] }) {
  const pipeline = {
    hot: results.filter((r) => r.final_classification === "HOT"),
    warm: results.filter((r) => r.final_classification === "WARM"),
    cold: results.filter((r) => r.final_classification === "COLD"),
    rejected: results.filter((r) => r.final_classification === "REJECTED"),
  };

  return (
    <div className="grid grid-cols-4 gap-4">
      <Card>
        <CardHeader className="bg-red-500/10">
          <CardTitle className="text-red-500">Hot ({pipeline.hot.length})</CardTitle>
        </CardHeader>
        <CardContent className="p-2">
          {pipeline.hot.map((r, idx) => (
            <div key={idx} className="p-2 border-b last:border-0">
              <div className="font-medium">{r.company_name || r.domain}</div>
              <div className="text-sm text-muted-foreground">Score: {r.overall_score.toFixed(1)}</div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="bg-orange-500/10">
          <CardTitle className="text-orange-500">Warm ({pipeline.warm.length})</CardTitle>
        </CardHeader>
        <CardContent className="p-2">
          {pipeline.warm.map((r, idx) => (
            <div key={idx} className="p-2 border-b last:border-0">
              <div className="font-medium">{r.company_name || r.domain}</div>
              <div className="text-sm text-muted-foreground">Score: {r.overall_score.toFixed(1)}</div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="bg-blue-500/10">
          <CardTitle className="text-blue-500">Cold ({pipeline.cold.length})</CardTitle>
        </CardHeader>
        <CardContent className="p-2">
          {pipeline.cold.map((r, idx) => (
            <div key={idx} className="p-2 border-b last:border-0">
              <div className="font-medium">{r.company_name || r.domain}</div>
              <div className="text-sm text-muted-foreground">Score: {r.overall_score.toFixed(1)}</div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="bg-gray-500/10">
          <CardTitle className="text-gray-500">Rejected ({pipeline.rejected.length})</CardTitle>
        </CardHeader>
        <CardContent className="p-2">
          {pipeline.rejected.map((r, idx) => (
            <div key={idx} className="p-2 border-b last:border-0">
              <div className="font-medium">{r.company_name || r.domain}</div>
              <div className="text-sm text-muted-foreground">{r.icp_match?.negative_reason}</div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
