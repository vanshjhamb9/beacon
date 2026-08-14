"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { Brain, TrendingUp, AlertTriangle, CheckCircle } from "lucide-react";

export function IntelligenceCard() {
  const analysis = useQuery({
    queryKey: ["intelligence-analysis"],
    queryFn: () => beaconApi.intelligenceAnalysis(),
    refetchInterval: 300_000, // Refresh every 5 minutes
  });

  const stats = useQuery({
    queryKey: ["lead-stats"],
    queryFn: () => beaconApi.leadStats(),
    refetchInterval: 30_000,
  });

  if (analysis.isLoading || stats.isLoading) {
    return <Skeleton className="h-48 w-full" />;
  }

  const data = analysis.data;
  const statsData = stats.data;
  const recommendations = data?.recommendations || [];

  return (
    <Card className="border-border/60 bg-card/60">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Brain className="h-4 w-4 text-purple-400" />
          Intelligence Engine
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Department Stats */}
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-lg border border-purple-500/20 bg-purple-500/5 p-3">
            <div className="text-xs text-purple-400">COMAI</div>
            <div className="text-2xl font-bold">{statsData?.comai || 0}</div>
            <div className="text-xs text-muted-foreground">leads</div>
          </div>
          <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 p-3">
            <div className="text-xs text-blue-400">Inowix</div>
            <div className="text-2xl font-bold">{statsData?.inowix || 0}</div>
            <div className="text-xs text-muted-foreground">leads</div>
          </div>
        </div>

        {/* Conversion Rates */}
        {data?.analysis?.comai && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Conversion Rate</span>
            <span className="font-medium">
              {((data.analysis.comai.conversion_rate || 0) * 100).toFixed(0)}% COMAI /{" "}
              {((data.analysis.inowix?.conversion_rate || 0) * 100).toFixed(0)}% Inowix
            </span>
          </div>
        )}

        {/* Recommendations */}
        {recommendations.length > 0 && (
          <div className="space-y-2">
            <div className="text-xs font-medium text-muted-foreground">
              {recommendations.length} Recommendations
            </div>
            {recommendations.slice(0, 3).map((rec: Record<string, unknown>, i: number) => (
              <div key={i} className="flex items-start gap-2 text-xs">
                {rec.priority === "high" ? (
                  <AlertTriangle className="mt-0.5 h-3 w-3 shrink-0 text-orange-400" />
                ) : (
                  <CheckCircle className="mt-0.5 h-3 w-3 shrink-0 text-green-400" />
                )}
                <span className="text-muted-foreground">{String(rec.action)}</span>
              </div>
            ))}
          </div>
        )}

        {/* Top Industries */}
        {data?.analysis?.top_industries?.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {data.analysis.top_industries.slice(0, 3).map((item: Record<string, unknown>, i: number) => (
              <Badge key={i} variant="secondary" className="text-[10px]">
                {String(item.industry)} ({((item.conversion_rate as number) * 100).toFixed(0)}%)
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
