import { Suspense } from "react";

import { EcommerceLeadsWorkspace } from "@/features/ecommerce-leads/ecommerce-leads-workspace";
import { Skeleton } from "@/components/ui/skeleton";

export default function EcommerceLeadsPage() {
  return (
    <Suspense fallback={<Skeleton className="h-64 w-full" />}>
      <EcommerceLeadsWorkspace />
    </Suspense>
  );
}
