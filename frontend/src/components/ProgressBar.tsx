interface ProgressBarProps {
  current: number;
  total: number;
  label?: string;
}

export function ProgressBar({ current, total, label }: ProgressBarProps) {
  const pct = total > 0 ? Math.min(100, Math.round((current / total) * 100)) : 0;
  return (
    <div className="w-full space-y-1">
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>{label ?? "Processing"}</span>
        <span>
          {current} / {total} ({pct}%)
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          className="h-full bg-primary transition-all duration-150"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
