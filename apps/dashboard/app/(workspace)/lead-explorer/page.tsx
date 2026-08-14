import { Suspense } from "react";

import { LeadExplorerWorkspace } from "@/features/lead-explorer/lead-explorer-workspace";
import { Skeleton } from "@/components/ui/skeleton";

export default function LeadExplorerPage() {
  return (
    <Suspense fallback={<Skeleton className="h-64 w-full" />}>
      <LeadExplorerWorkspace />
    </Suspense>
  );
}
