"use client";

import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, SectionLabel } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { beaconApi } from "@/lib/api/beacon";
import { formatScore } from "@/lib/utils";

function Row({ label, value, verified }: { label: string; value?: unknown; verified?: boolean }) {
  const display = value == null || value === "" || value === "UNKNOWN" ? null : String(value);
  if (!display) return null;
  return (
    <div className="border-b border-border/50 py-3">
      <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">{label}</p>
      <div className="mt-1 flex flex-wrap items-center gap-2">
        <p className="text-base font-medium">{display}</p>
        {verified ? <Badge>Verified</Badge> : null}
      </div>
    </div>
  );
}

/** One-page OFC company view — hide anything unknown. */
export function OfcCompanyCard({ companyId }: { companyId: string }) {
  const cir = useQuery({
    queryKey: ["ofc-cir", companyId],
    queryFn: () => beaconApi.cirCompany(companyId),
    retry: false,
  });
  const erowd = useQuery({
    queryKey: ["ofc-erowd", companyId],
    queryFn: () => beaconApi.erowdCompany(companyId),
    retry: false,
  });
  const rev = useQuery({
    queryKey: ["ofc-rev-eval", companyId],
    queryFn: async () => {
      const card = await beaconApi.cirCompany(companyId);
      const founder = (card?.founder_card || {}) as Record<string, unknown>;
      return beaconApi.revEvaluate({
        company_id: companyId,
        company_name: founder.company,
        website: founder.website || erowd.data?.official_website,
        official_website: founder.website || erowd.data?.official_website,
        domain: erowd.data?.domain,
        industry: founder.industry,
        country: founder.country,
        description: founder.primary_product,
        business_email: founder.business_email,
        decision_maker: Array.isArray(founder.decision_makers) ? founder.decision_makers[0] : undefined,
        best_service: founder.best_service,
        why_now: Array.isArray(founder.buying_signals) ? (founder.buying_signals as string[]).join(", ") : founder.recommended_action,
        opportunity: founder.primary_opportunity,
        buying_signals: founder.buying_signals,
        confidence: founder.readiness_score,
        erowd_verified: erowd.data?.verified,
        cir_classification: founder.revenue_readiness,
        source: erowd.data?.collector || founder.website,
        evidence: founder.evidence,
        service_matches: founder.best_service ? [{ service: founder.best_service }] : [],
      });
    },
    enabled: !!cir.data,
    retry: false,
  });

  if (cir.isLoading || erowd.isLoading) return <Skeleton className="h-96 w-full" />;

  const card = (cir.data?.founder_card || {}) as Record<string, unknown>;
  const check = ((rev.data as { check?: Record<string, unknown> } | undefined)?.check || {}) as Record<string, unknown>;
  const ready = Boolean(check.is_revenue_ready || String(card.revenue_readiness || "").includes("Revenue Ready") || String(card.revenue_readiness || "").includes("Priority"));

  const email = String(card.business_email || check.email || "");
  const dm = String(
    (Array.isArray(card.decision_makers) && card.decision_makers[0]) || check.decision_maker_name || "",
  );
  const website = String(erowd.data?.official_website || card.website || "");
  const description = String(card.primary_product || check.description || "");
  const why = String(card.recommended_action || check.why_now || "");
  const service = String(card.best_service || check.best_service || "");

  // OFC rule: if critical unknowns → do not show as contactable card
  const complete = Boolean(website && description && email && email !== "UNKNOWN" && service && service !== "UNKNOWN");
  if (!complete && !ready) {
    return (
      <EmptyState
        title="Not ready for founder view"
        description="Missing website, description, business email, or service match. Hidden until evidence exists."
      />
    );
  }

  const vanshYes = ready && complete && Boolean(dm && dm !== "UNKNOWN");

  return (
    <Card className="border-border/70 shadow-soft">
      <CardHeader>
        <SectionLabel>Outbound brief</SectionLabel>
        <div className="flex flex-wrap items-center gap-2">
          <CardTitle className="text-3xl">{String(card.company || "Company")}</CardTitle>
          <Badge className={ready ? "bg-emerald-600 text-white" : "bg-muted text-muted-foreground"}>
            Revenue Ready {ready ? "YES" : "NO"}
          </Badge>
          <Badge variant={vanshYes ? "default" : "secondary"}>Would Vansh email today? {vanshYes ? "YES" : "NO"}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <Row label="Website" value={website} verified={Boolean(erowd.data?.verified)} />
        <Row label="Description" value={description} />
        <Row label="Employees" value={card.employees} />
        <Row label="Industry" value={card.industry || check.industry} />
        <Row label="Country" value={card.country || check.country} />
        <Row label="Decision Maker" value={dm} />
        <Row label="Business Email" value={email} verified={email.includes("@")} />
        <Row label="Phone" value={card.phone} verified={Boolean(card.phone && card.phone !== "UNKNOWN")} />
        <Row
          label="LinkedIn"
          value={erowd.data?.discovery_source === "linkedin_company_website" ? "Available" : undefined}
        />
        <Row
          label="Buying Intent"
          value={
            Array.isArray(card.buying_signals) && card.buying_signals.length
              ? `${formatScore(Number(card.readiness_score || check.confidence || 0), 0)} — ${(card.buying_signals as string[]).join(", ")}`
              : formatScore(Number(card.readiness_score || 0), 0)
          }
        />
        <Row label="Why Now" value={why} />
        <Row label="Recommended Service" value={service} />
        <Row
          label="Evidence"
          value={
            Array.isArray(card.evidence) && card.evidence.length
              ? (card.evidence as string[]).slice(0, 8).join(" · ")
              : String(erowd.data?.collector || "")
          }
        />
      </CardContent>
    </Card>
  );
}
