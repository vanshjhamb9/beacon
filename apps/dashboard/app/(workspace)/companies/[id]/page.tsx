"use client";

import { use } from "react";

import { CompanyWorkspace } from "@/features/companies/company-workspace";

export default function CompanyDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  return <CompanyWorkspace companyId={id} />;
}
