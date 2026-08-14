"use client";

import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { SectionLabel } from "@/components/ui/states";
import { beaconApi } from "@/lib/api/beacon";

type E2EResult = {
  scenario: string;
  passed: boolean;
  mode: string;
  steps: Array<{ name: string; passed: boolean; detail: string; duration_ms: number }>;
};

export function TestCenterWorkspace() {
  const [result, setResult] = useState<E2EResult | null>(null);
  const run = useMutation({
    mutationFn: beaconApi.qaE2ESandbox,
    onSuccess: (data) => setResult(data),
  });

  return (
    <div className="space-y-6">
      <div>
        <SectionLabel>Automated testing</SectionLabel>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Test Center</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Run the sandbox end-to-end pipeline from sales package through simulated reply and meeting booking.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Sandbox E2E</CardTitle>
          <CardDescription>
            Company → opportunity package → campaign → approval → sandbox send → reply → meeting → outcome
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button onClick={() => run.mutate()} disabled={run.isPending}>
            {run.isPending ? "Running…" : "Run sandbox pipeline"}
          </Button>
          {run.isError ? <p className="text-sm text-red-400">E2E run failed. Check API logs.</p> : null}
          {result ? (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Badge>{result.passed ? "PASSED" : "FAILED"}</Badge>
                <span className="text-sm text-muted-foreground">
                  {result.scenario} · {result.mode}
                </span>
              </div>
              {result.steps.map((step) => (
                <div key={step.name} className="rounded-lg border border-border/60 px-3 py-2">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium">{step.name}</p>
                    <Badge className="bg-muted text-muted-foreground ring-border">
                      {step.passed ? "pass" : "fail"}
                    </Badge>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">{step.detail}</p>
                  <p className="text-[11px] text-muted-foreground">{step.duration_ms.toFixed(1)} ms</p>
                </div>
              ))}
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
