import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { SimpleTable } from '../components/Table';

export function CanonicalRegistryPage() {
  const [items, setItems] = useState<any[]>([]);
  useEffect(() => { api('/canonical-products').then(setItems); }, []);

  return (
    <div>
      <h2>Canonical Registry</h2>
      <SimpleTable
        columns={['ID', 'Canonical Name', 'Barcode', 'APN', 'PDE', 'Review Status']}
        rows={items.map((item) => [item.id, item.canonical_name, item.primary_barcode || '', item.primary_apn || '', item.primary_pde || '', item.review_status])}
      />
    </div>
  );
}
