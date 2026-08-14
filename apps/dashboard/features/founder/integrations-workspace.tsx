"use client";

import { useQuery } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { StatusBadge } from "@/components/ui/status";
import { beaconApi } from "@/lib/api/beacon";
import { API_BASE_URL } from "@/lib/api/client";
import { gmailConnectUrl } from "@/lib/founder";

const PROVIDERS = [
  { id: "gmail", name: "Google", description: "Gmail outreach and reply sync", kind: "oauth" as const },
  { id: "microsoft", name: "Microsoft", description: "Outlook email and calendar", kind: "soon" as const },
  { id: "meta", name: "Meta", description: "WhatsApp Business messaging", kind: "soon" as const },
  { id: "calendly", name: "Calendly", description: "Meeting booking links", kind: "soon" as const },
  { id: "slack", name: "Slack", description: "Deal and reply notifications", kind: "soon" as const },
  { id: "openai", name: "OpenAI", description: "Draft generation quality", kind: "config" as const },
];

export function IntegrationsWorkspace() {
  const gmail = useQuery({
    queryKey: ["gmail-oauth-status"],
    queryFn: () => beaconApi.communicationOauthStatus("gmail"),
    refetchInterval: 30_000,
  });
  const readiness = useQuery({
    queryKey: ["execution-dashboard-card"],
    queryFn: () => beaconApi.executionDashboardCard(),
  });

  const gmailConnected = Boolean(gmail.data?.connected);
  const whatsappConnected = /connected|ready|active/i.test(String(readiness.data?.whatsapp || ""));

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <header className="space-y-2">
        <p className="text-sm text-muted-foreground">Connect once. Send every day.</p>
        <h1 className="font-display text-3xl font-semibold tracking-tight">Integrations</h1>
      </header>

      <div className="space-y-3">
        {PROVIDERS.map((provider) => {
          const connected =
            provider.id === "gmail"
              ? gmailConnected
              : provider.id === "meta"
                ? whatsappConnected
                : false;

          return (
            <Card key={provider.id}>
              <CardContent className="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
                <div>
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium">{provider.name}</p>
                    <StatusBadge tone={connected ? "ready" : provider.kind === "soon" ? "inactive" : "attention"}>
                      {connected ? "Connected" : provider.kind === "soon" ? "Coming soon" : "Not Connected"}
                    </StatusBadge>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">{provider.description}</p>
                  {provider.id === "gmail" && gmailConnected ? (
                    <p className="mt-1 text-xs text-status-ready">{gmail.data?.account_email || "Gmail linked"}</p>
                  ) : null}
                </div>
                <div className="flex gap-2">
                  {provider.id === "gmail" ? (
                    connected ? (
                      <Button variant="outline" size="sm" asChild>
                        <a href={`${API_BASE_URL}/communication/oauth/status?provider=gmail`}>Manage</a>
                      </Button>
                    ) : (
                      <Button size="sm" asChild>
                        <a href={gmailConnectUrl()}>Connect</a>
                      </Button>
                    )
                  ) : (
                    <Button size="sm" variant="outline" disabled>
                      {provider.kind === "soon" ? "Soon" : "Configure"}
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
