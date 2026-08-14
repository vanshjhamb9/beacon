"use client";

import { use } from "react";

import { OpportunityWorkspace } from "@/features/opportunities/opportunity-workspace";

export default function OpportunityDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  return <OpportunityWorkspace opportunityId={id} />;
}
