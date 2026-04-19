import { useEffect, useMemo, useState } from 'react';
import { PageHeader } from '@/components/PageHeader';
import { SimpleTable } from '@/components/Table';
import { api } from '@/lib/api';
import type { SourceProduct } from '@/lib/types';

const SOURCE_FILTERS = ['ALL', 'SHOPIFY_PRODUCTS', 'SHOPIFY_INVENTORY', 'FOS', 'PRICEBOOK', 'MASTERCATALOG', 'SCRAPED_CATALOG'] as const;

export function SourceProductsPage() {
  const [items, setItems] = useState<SourceProduct[]>([]);
  const [filter, setFilter] = useState<(typeof SOURCE_FILTERS)[number]>('ALL');
  const [selected, setSelected] = useState<SourceProduct | null>(null);

  useEffect(() => {
    const suffix = filter === 'ALL' ? '' : `?source=${encodeURIComponent(filter)}`;
    api<SourceProduct[]>(`/source-products${suffix}`).then(setItems).catch(console.error);
  }, [filter]);

  const counts = useMemo(() => {
    const result = Object.fromEntries(SOURCE_FILTERS.map((value) => [value, 0])) as Record<(typeof SOURCE_FILTERS)[number], number>;
    result.ALL = items.length;
    for (const item of items) {
      const key = (item.source_code || 'ALL') as (typeof SOURCE_FILTERS)[number];
      if (key in result) result[key] += 1;
    }
    return result;
  }, [items]);

  return (
    <div>
      <PageHeader title="Source Products" subtitle="Raw source-system rows currently loaded into the backend, including pricebooks and scraped catalogs." />
      <div className="flex gap-2 mb-4 flex-wrap">
        {SOURCE_FILTERS.map((value) => (
          <button key={value} onClick={() => setFilter(value)}>
            {value} ({value === 'ALL' ? items.length : items.filter((item) => item.source_code === value).length})
          </button>
        ))}
      </div>

      <SimpleTable
        columns={['ID', 'Type', 'Title', 'Vendor', 'Category', 'SKU', 'Barcode', 'APN', 'PDE', 'Status']}
        rows={items.map((item) => [
          item.id,
          <Badge value={item.source_code || 'UNKNOWN'} />,
          <button onClick={() => setSelected(item)}>{item.title}</button>,
          item.vendor || '',
          item.product_type || '',
          item.sku || '',
          item.barcode || '',
          item.apn || '',
          item.pde || '',
          item.status || '',
        ])}
      />

      {selected ? (
        <div className="rounded-lg border border-border bg-card p-5 mt-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="text-xs text-muted-foreground uppercase">Selected source row</div>
              <div className="text-2xl font-bold mt-1">{selected.title}</div>
              <div className="mt-2"><Badge value={selected.source_code || 'UNKNOWN'} /></div>
            </div>
            <button onClick={() => setSelected(null)}>Close</button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            <Info label="Vendor" value={selected.vendor} />
            <Info label="Category" value={selected.product_type} />
            <Info label="Handle / URL" value={selected.handle} />
            <Info label="SKU" value={selected.sku} />
            <Info label="Barcode" value={selected.barcode} />
            <Info label="APN" value={selected.apn} />
            <Info label="PDE" value={selected.pde} />
            <Info label="Status" value={selected.status} />
          </div>
          <div className="mt-4">
            <div className="text-xs text-muted-foreground uppercase mb-2">Raw payload preview</div>
            <pre className="rounded border border-border p-4 text-xs" style={{ overflowX: 'auto', background: '#f8f9fc' }}>
              {JSON.stringify(selected.raw_payload_json || {}, null, 2)}
            </pre>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function Badge({ value }: { value: string }) {
  return <span className="rounded border px-2 py-1 text-xs">{value}</span>;
}

function Info({ label, value }: { label: string; value?: string }) {
  return (
    <div className="rounded border border-border p-3">
      <div className="text-xs text-muted-foreground uppercase">{label}</div>
      <div className="mt-2 text-sm">{value || 'n/a'}</div>
    </div>
  );
}
