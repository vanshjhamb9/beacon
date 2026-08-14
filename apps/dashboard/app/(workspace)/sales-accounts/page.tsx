import { Suspense } from "react";

import { SalesAccountsWorkspace } from "@/features/sales-accounts/sales-accounts-workspace";
import { Skeleton } from "@/components/ui/skeleton";

export default function SalesAccountsPage() {
  return (
    <Suspense fallback={<Skeleton className="h-64 w-full" />}>
      <SalesAccountsWorkspace />
    </Suspense>
  );
}
