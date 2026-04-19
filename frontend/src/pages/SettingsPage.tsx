import { useEffect, useState } from 'react';
import { PageHeader } from '@/components/PageHeader';
import { api } from '@/lib/api';

export function SettingsPage() {
  const [settings, setSettings] = useState<Record<string, unknown>>({});

  useEffect(() => {
    api<Record<string, unknown>>('/settings').then(setSettings).catch(console.error);
  }, []);

  return (
    <div>
      <PageHeader title="Settings" subtitle="Current backend settings snapshot." />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(settings).map(([key, value]) => (
          <div key={key} className="rounded-lg border border-border bg-card p-4">
            <div className="text-xs uppercase tracking-wide text-muted-foreground">{key}</div>
            <div className="mt-2 text-sm font-medium text-foreground">{String(value)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
