"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Shield, CheckCircle, AlertTriangle, TrendingUp,
  Target, DollarSign, Zap, Brain, Activity, BarChart3
} from "lucide-react";

export default function RICVPWorkspace() {
  const [activeTab, setActiveTab] = useState("overview");
  const [validationResult, setValidationResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [companyId, setCompanyId] = useState("");
  const [companyData, setCompanyData] = useState({
    company_name: "", primary_domain: "", industry: "", country: "",
    platform: "", monthly_traffic: 0, revenue_estimate: 0, account_score: 50,
  });

  const runValidation = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/ricvp/validate-company", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company_id: companyId || "test", company_data: companyData }),
      });
      const data = await res.json();
      setValidationResult(data);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">RICVP</h1>
          <p className="text-sm text-muted-foreground">Revenue Intelligence Calibration & Validation Platform</p>
        </div>
        <Badge variant="outline" className="gap-1"><Shield className="h-3 w-3" /> Validated</Badge>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="validate">Validate</TabsTrigger>
          <TabsTrigger value="evidence">Evidence</TabsTrigger>
          <TabsTrigger value="confidence">Confidence</TabsTrigger>
          <TabsTrigger value="calibration">Calibration</TabsTrigger>
          <TabsTrigger value="buying-window">Buying Window</TabsTrigger>
          <TabsTrigger value="revenue">Revenue</TabsTrigger>
          <TabsTrigger value="competition">Competition</TabsTrigger>
          <TabsTrigger value="learning">Learning</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Data Quality</CardTitle></CardHeader>
              <CardContent><div className="text-3xl font-bold text-green-600">0%</div></CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Confidence</CardTitle></CardHeader>
              <CardContent><div className="text-3xl font-bold">0%</div></CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Evidence Coverage</CardTitle></CardHeader>
              <CardContent><div className="text-3xl font-bold">0%</div></CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Calibration Accuracy</CardTitle></CardHeader>
              <CardContent><div className="text-3xl font-bold">0%</div></CardContent>
            </Card>
          </div>
          <Card>
            <CardHeader><CardTitle>Quality Rules</CardTitle></CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                {[
                  "Never invent phone numbers", "Never invent emails",
                  "Never invent decision makers", "Never invent revenue",
                  "Never invent traffic", "Never invent technologies",
                  "Every inference needs confidence", "Every inference needs evidence",
                ].map((rule, i) => (
                  <div key={i} className="flex items-center gap-2 p-2 border rounded">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span className="text-sm">{rule}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="validate" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Validate Company</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <Input placeholder="Company ID" value={companyId} onChange={e => setCompanyId(e.target.value)} />
              <div className="grid grid-cols-2 gap-4">
                <Input placeholder="Company Name" value={companyData.company_name} onChange={e => setCompanyData({...companyData, company_name: e.target.value})} />
                <Input placeholder="Domain" value={companyData.primary_domain} onChange={e => setCompanyData({...companyData, primary_domain: e.target.value})} />
                <Input placeholder="Industry" value={companyData.industry} onChange={e => setCompanyData({...companyData, industry: e.target.value})} />
                <Input placeholder="Platform" value={companyData.platform} onChange={e => setCompanyData({...companyData, platform: e.target.value})} />
              </div>
              <Button onClick={runValidation} disabled={loading}>{loading ? "Validating..." : "Run Full Validation"}</Button>
            </CardContent>
          </Card>
          {validationResult && (
            <div className="grid grid-cols-2 gap-4">
              <Card>
                <CardHeader><CardTitle className="text-sm">Confidence</CardTitle></CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{(validationResult.confidence?.overall_confidence * 100).toFixed(0)}%</div>
                  <Badge variant={validationResult.confidence?.confidence_grade === "A" ? "default" : "secondary"}>
                    Grade {validationResult.confidence?.confidence_grade}
                  </Badge>
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle className="text-sm">Buying Window</CardTitle></CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold capitalize">{validationResult.buying_window?.window_status?.replace("_", " ")}</div>
                  <p className="text-sm text-muted-foreground">{validationResult.buying_window?.reason}</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle className="text-sm">Revenue Opportunity</CardTitle></CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">${validationResult.revenue_estimation?.expected_arr?.toLocaleString()}</div>
                  <p className="text-sm text-muted-foreground">Expected ARR</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle className="text-sm">Recommendation</CardTitle></CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{validationResult.recommendation?.action}</div>
                  <p className="text-sm text-muted-foreground">{validationResult.recommendation?.reasoning}</p>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        <TabsContent value="evidence" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Evidence Trail</CardTitle></CardHeader>
            <CardContent>
              <p className="text-muted-foreground">Every data point includes: value, source, confidence, last verified, verification method, evidence URL, source reliability, cross-source agreement.</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="confidence" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Multi-Dimensional Confidence</CardTitle></CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                {["Discovery", "Technology", "Growth", "Intent", "Pain", "Decision Maker", "Revenue", "Contact", "Quality"].map(dim => (
                  <div key={dim} className="p-3 border rounded-lg text-center">
                    <div className="text-sm text-muted-foreground">{dim}</div>
                    <div className="text-xl font-bold">0%</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="calibration" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Score Calibration</CardTitle></CardHeader>
            <CardContent>
              <p className="text-muted-foreground">Every score is calibrated based on evidence quality, source reliability, and historical accuracy.</p>
              <div className="mt-4 p-4 border rounded-lg">
                <div className="text-sm text-muted-foreground">Calibration Rules</div>
                <ul className="mt-2 space-y-1 text-sm">
                  <li>High evidence (5+ sources): Factor 1.0</li>
                  <li>Moderate evidence (2-4 sources): Factor 0.85</li>
                  <li>Low evidence (1 source): Factor 0.6</li>
                  <li>No evidence: Factor 0.3</li>
                  <li>Conflicting data: Factor 0.5</li>
                  <li>Verified data: Factor 1.1</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="buying-window" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Buying Window Intelligence</CardTitle></CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                {["Immediate", "30 Days", "60 Days", "90 Days", "Future", "Dormant"].map(window => (
                  <div key={window} className="p-3 border rounded-lg text-center">
                    <div className="font-medium">{window}</div>
                    <div className="text-2xl font-bold">0</div>
                  </div>
                ))}
              </div>
              <div className="mt-4">
                <div className="text-sm font-medium">Signal Detection</div>
                <div className="mt-2 grid grid-cols-2 gap-2">
                  {["Hiring", "Funding", "Product Launch", "Tech Migration", "AI Adoption", "Traffic Growth", "Customer Complaints", "Competitor Changes"].map(signal => (
                    <div key={signal} className="flex items-center gap-2 text-sm">
                      <AlertTriangle className="h-3 w-3" />
                      {signal}
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="revenue" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Revenue Opportunity Estimation</CardTitle></CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 border rounded-lg">
                  <div className="text-sm text-muted-foreground">Monthly Orders</div>
                  <div className="text-2xl font-bold">0</div>
                </div>
                <div className="p-4 border rounded-lg">
                  <div className="text-sm text-muted-foreground">Monthly Visitors</div>
                  <div className="text-2xl font-bold">0</div>
                </div>
                <div className="p-4 border rounded-lg">
                  <div className="text-sm text-muted-foreground">Expected ARR</div>
                  <div className="text-2xl font-bold">$0</div>
                </div>
                <div className="p-4 border rounded-lg">
                  <div className="text-sm text-muted-foreground">Total Opportunity</div>
                  <div className="text-2xl font-bold">$0</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="competition" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Competitive Intelligence</CardTitle></CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 border rounded-lg">
                  <div className="text-sm text-muted-foreground">Technology Gaps</div>
                  <div className="text-2xl font-bold">0</div>
                </div>
                <div className="p-4 border rounded-lg">
                  <div className="text-sm text-muted-foreground">Replacement Opportunities</div>
                  <div className="text-2xl font-bold">0</div>
                </div>
                <div className="p-4 border rounded-lg">
                  <div className="text-sm text-muted-foreground">Migration Complexity</div>
                  <div className="text-2xl font-bold">-</div>
                </div>
                <div className="p-4 border rounded-lg">
                  <div className="text-sm text-muted-foreground">Switching Cost</div>
                  <div className="text-2xl font-bold">-</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="learning" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Continuous Learning</CardTitle></CardHeader>
            <CardContent>
              <p className="text-muted-foreground">Every sales outcome improves scoring. Nothing remains static.</p>
              <div className="mt-4 grid grid-cols-2 gap-4">
                <div className="p-4 border rounded-lg">
                  <div className="text-sm text-muted-foreground">Total Learnings</div>
                  <div className="text-2xl font-bold">0</div>
                </div>
                <div className="p-4 border rounded-lg">
                  <div className="text-sm text-muted-foreground">Win Rate</div>
                  <div className="text-2xl font-bold">0%</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
