import { PageHeader } from '@/components/PageHeader';

export function ExportsPage() {
  return (
    <div>
      <PageHeader title="Exports" subtitle="Inventory and link report exports are generated from backend workflows." />
      <div className="rounded-lg border border-border bg-card p-5 text-sm text-muted-foreground">
        Use the Inventory Sync page to create Shopify inventory exports. Link report exports are also produced by the backend sample and audit flows.
      </div>
    </div>
  );
}
