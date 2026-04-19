import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/PageHeader';
import { SimpleTable } from '@/components/Table';
import { api } from '@/lib/api';
import type { CanonicalProduct } from '@/lib/types';

export function CanonicalRegistryPage() {
  const [items, setItems] = useState<CanonicalProduct[]>([]);

  useEffect(() => {
    api<CanonicalProduct[]>('/canonical-products').then(setItems).catch(console.error);
  }, []);

  return (
    <div>
      <PageHeader title="Canonical Registry" subtitle="Master product identity layer across Shopify and FOS." />
      <SimpleTable
        columns={['ID', 'Canonical Name', 'Barcode', 'APN', 'PDE', 'Review Status']}
        rows={items.map((item) => [item.id, item.canonical_name, item.primary_barcode || '', item.primary_apn || '', item.primary_pde || '', item.review_status])}
      />
    </div>
  );
}
