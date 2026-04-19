import { useEffect, useState } from 'react';
import { Database, Layers, GitMerge, AlertTriangle, CheckCircle2, Upload, Download, RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';
import { PageHeader } from '@/components/PageHeader';
import { api } from '@/lib/api';
import type { DashboardSummary } from '@/lib/types';

export function DashboardPage() {
  const [stats, setStats] = useState<DashboardSummary | null>(null);

  useEffect(() => {
    api<DashboardSummary>('/dashboard').then(setStats).catch(console.error);
  }, []);

  return (
    <div>
      <PageHeader title="Dashboard" subtitle="Canonical product registry, review queue, and reconciliation readiness." />
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
        <KpiCard icon={Database} label="Canonical Products" value={stats?.canonical_products ?? 0} />
        <KpiCard icon={Layers} label="Linked to Shopify" value={stats?.linked_shopify_products ?? 0} />
        <KpiCard icon={Layers} label="Linked to FOS" value={stats?.linked_fos_products ?? 0} />
        <KpiCard icon={GitMerge} label="Needs Review" value={stats?.unresolved_links ?? 0} />
        <KpiCard icon={AlertTriangle} label="Conflicts" value={stats?.conflicts ?? 0} />
        <KpiCard icon={CheckCircle2} label="Ready to Sync" value={stats?.reconciliation_ready ?? 0} />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
        <QuickAction to="/imports" icon={Upload} label="Import Files" />
        <QuickAction to="/review" icon={GitMerge} label="Review Links" />
        <QuickAction to="/sync" icon={RefreshCw} label="Run Reconciliation" />
        <QuickAction to="/exports" icon={Download} label="Exports" />
      </div>
    </div>
  );
}

function KpiCard({ icon: Icon, label, value }: { icon: typeof Database; label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border bg-card p-5">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xs text-muted-foreground uppercase tracking-wide">{label}</div>
          <div className="mt-2 text-3xl font-bold tabular-nums text-foreground">{value.toLocaleString()}</div>
        </div>
        <div className="h-9 w-9 rounded-md border flex items-center justify-center border-primary/20 bg-primary/5 text-primary">
          <Icon className="h-4 w-4" />
        </div>
      </div>
    </div>
  );
}

function QuickAction({ to, icon: Icon, label }: { to: string; icon: typeof Upload; label: string }) {
  return (
    <Link to={to} className="flex items-center gap-3 rounded-lg border border-border bg-card p-4 hover:border-primary/40 hover:bg-primary/5 transition-colors">
      <div className="h-9 w-9 rounded-md bg-primary/10 text-primary flex items-center justify-center">
        <Icon className="h-4 w-4" />
      </div>
      <div className="text-sm font-medium text-foreground">{label}</div>
    </Link>
  );
}
