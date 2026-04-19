import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/PageHeader';
import { SimpleTable } from '@/components/Table';
import { api } from '@/lib/api';
import type { SourceProduct } from '@/lib/types';

export function SourceProductsPage() {
  const [items, setItems] = useState<SourceProduct[]>([]);

  useEffect(() => {
    api<SourceProduct[]>('/source-products').then(setItems).catch(console.error);
  }, []);

  return (
    <div>
      <PageHeader title="Source Products" subtitle="Raw source-system rows currently loaded into the backend." />
      <SimpleTable
        columns={['ID', 'Title', 'Handle', 'SKU', 'Barcode', 'APN', 'PDE', 'Status']}
        rows={items.map((item) => [item.id, item.title, item.handle || '', item.sku || '', item.barcode || '', item.apn || '', item.pde || '', item.status || ''])}
      />
    </div>
  );
}
