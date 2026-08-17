import { Suspense } from "react";
import { PartnerLeadsWorkspace } from "@/features/partner-leads/partner-leads-workspace";
import { Skeleton } from "@/components/ui/skeleton";

export default function PartnerLeadsPage() {
  return (
    <Suspense fallback={<Skeleton className="h-96 w-full" />}>
      <PartnerLeadsWorkspace />
    </Suspense>
  );
}
