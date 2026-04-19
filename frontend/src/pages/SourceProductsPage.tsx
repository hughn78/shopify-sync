import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { SimpleTable } from '../components/Table';

export function SourceProductsPage() {
  const [items, setItems] = useState<any[]>([]);
  useEffect(() => { api('/source-products').then(setItems); }, []);

  return (
    <div>
      <h2>Source Products</h2>
      <SimpleTable
        columns={['ID', 'Title', 'Handle', 'SKU', 'Barcode', 'APN', 'PDE', 'Status']}
        rows={items.map((item) => [item.id, item.title, item.handle || '', item.sku || '', item.barcode || '', item.apn || '', item.pde || '', item.status || ''])}
      />
    </div>
  );
}
