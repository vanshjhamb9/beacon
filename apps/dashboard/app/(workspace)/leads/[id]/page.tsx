"use client";

import { use } from "react";
import { LeadDetailWorkspace } from "@/features/leads/lead-detail-workspace";

export default function LeadDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <LeadDetailWorkspace leadId={id} />;
}
