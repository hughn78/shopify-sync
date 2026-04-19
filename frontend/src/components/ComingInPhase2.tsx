import type { LucideIcon } from "lucide-react";

interface ComingInPhase2Props {
  icon: LucideIcon;
  title: string;
  description: string;
}

export function ComingInPhase2({ icon: Icon, title, description }: ComingInPhase2Props) {
  return (
    <div className="rounded-lg border border-dashed border-border bg-card p-12 text-center">
      <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
        <Icon className="h-6 w-6" />
      </div>
      <h2 className="text-lg font-semibold text-foreground">{title}</h2>
      <p className="mt-2 text-sm text-muted-foreground max-w-md mx-auto">{description}</p>
      <div className="mt-6 inline-flex items-center gap-2 rounded-full bg-warning/15 text-warning-foreground border border-warning/30 px-3 py-1 text-xs font-medium">
        <span className="h-1.5 w-1.5 rounded-full bg-warning" />
        Coming in Phase 2
      </div>
    </div>
  );
}
