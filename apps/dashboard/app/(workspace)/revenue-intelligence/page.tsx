import { Suspense } from "react";

import { RevenueIntelligenceWorkspace } from "@/features/revenue-intelligence/revenue-intelligence-workspace";
import { Skeleton } from "@/components/ui/skeleton";

export default function RevenueIntelligencePage() {
  return (
    <Suspense fallback={<Skeleton className="h-64 w-full" />}>
      <RevenueIntelligenceWorkspace />
    </Suspense>
  );
}
