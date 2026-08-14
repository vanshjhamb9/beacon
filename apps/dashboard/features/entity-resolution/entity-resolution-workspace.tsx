"use client";

import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";

type Row = {
  company?: string;
  official_website?: string;
  confidence?: number;
  verified?: boolean;
  source?: string;
  collector?: string;
  evidence_count?: number;
  status?: string;
  admitted?: boolean;
  rejected?: boolean;
};

export function EntityResolutionWorkspace() {
  const dashboard = useQuery({
    queryKey: ["erowd-dashboard"],
    queryFn: () => beaconApi.erowdDashboard(),
    refetchInterval: 60_000,
  });
  const report = useQuery({
    queryKey: ["erowd-report"],
    queryFn: () => beaconApi.erowdReport(),
    refetchInterval: 120_000,
  });

  if (dashboard.isError) {
    return <ErrorState title="Entity Resolution unavailable" description="API /entity-resolution/dashboard failed." />;
  }

  const items = ((dashboard.data?.items as Row[]) || []) as Row[];
  const admitted = Number(dashboard.data?.admitted || 0);
  const rejected = Number(dashboard.data?.rejected || 0);

  return (
    <div className="space-y-6">
      <div>
        <SectionLabel>Identity foundation</SectionLabel>
        <h1 className="text-2xl font-semibold tracking-tight">Entity Resolution</h1>
        <p className="text-sm text-muted-foreground">
          Official website first. A company without a verified official website stays a signal.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Admitted</CardDescription>
            <CardTitle>{dashboard.isLoading ? <Skeleton className="h-7 w-16" /> : admitted}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Rejected</CardDescription>
            <CardTitle>{dashboard.isLoading ? <Skeleton className="h-7 w-16" /> : rejected}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Discovery rate</CardDescription>
            <CardTitle>
              {report.isLoading ? <Skeleton className="h-7 w-16" /> : `${Number(report.data?.discovery_rate || 0)}%`}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Resolution queue</CardTitle>
          <CardDescription>Company · Official Website · Confidence · Verified · Source · Collector · Evidence · Status</CardDescription>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full min-w-[960px] text-left text-sm">
            <thead className="border-b text-muted-foreground">
              <tr>
                <th className="py-2 pr-3 font-medium">Company</th>
                <th className="py-2 pr-3 font-medium">Official Website</th>
                <th className="py-2 pr-3 font-medium">Confidence</th>
                <th className="py-2 pr-3 font-medium">Verified</th>
                <th className="py-2 pr-3 font-medium">Source</th>
                <th className="py-2 pr-3 font-medium">Collector</th>
                <th className="py-2 pr-3 font-medium">Evidence</th>
                <th className="py-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.isLoading &&
                Array.from({ length: 6 }).map((_, i) => (
                  <tr key={i} className="border-b">
                    <td className="py-3" colSpan={8}>
                      <Skeleton className="h-5 w-full" />
                    </td>
                  </tr>
                ))}
              {!dashboard.isLoading && items.length === 0 && (
                <tr>
                  <td className="py-6 text-muted-foreground" colSpan={8}>
                    No resolution runs yet. Run rebuild or wait for collectors + intelligence.
                  </td>
                </tr>
              )}
              {items.map((row, idx) => (
                <tr key={`${row.company}-${idx}`} className="border-b align-top">
                  <td className="py-3 pr-3 font-medium">{row.company || "—"}</td>
                  <td className="py-3 pr-3">
                    {row.official_website ? (
                      <a className="text-primary underline-offset-2 hover:underline" href={row.official_website} target="_blank" rel="noreferrer">
                        {row.official_website}
                      </a>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="py-3 pr-3">{Number(row.confidence || 0).toFixed(0)}</td>
                  <td className="py-3 pr-3">
                    <Badge variant={row.verified ? "default" : "secondary"}>{row.verified ? "Yes" : "No"}</Badge>
                  </td>
                  <td className="py-3 pr-3">{row.source || "—"}</td>
                  <td className="py-3 pr-3">{row.collector || "—"}</td>
                  <td className="py-3 pr-3">{row.evidence_count ?? 0}</td>
                  <td className="py-3">
                    <Badge variant={row.admitted ? "default" : "outline"}>{row.status || (row.admitted ? "ADMITTED" : "REJECTED")}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
