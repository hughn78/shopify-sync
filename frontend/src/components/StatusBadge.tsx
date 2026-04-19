import { cn } from "@/lib/utils";

type LinkStatusType = "AUTO_ACCEPTED" | "APPROVED" | "NEEDS_REVIEW" | "CONFLICT" | "REJECTED" | "EXCLUDED";
type ReviewStatusType = "auto_accepted" | "needs_review" | "approved" | "conflict";
type SyncStatusType = "pending" | "approved" | "excluded" | "conflict" | "no_fos" | "no_shopify";
type ImportStatusType = "pending" | "complete" | "error";

type AnyStatus = LinkStatusType | ReviewStatusType | SyncStatusType | ImportStatusType | string;

interface StatusBadgeProps {
  status: AnyStatus;
  className?: string;
}

const STYLES: Record<string, string> = {
  // Link statuses
  AUTO_ACCEPTED: "bg-success/15 text-success border-success/30",
  APPROVED: "bg-success/15 text-success border-success/30",
  NEEDS_REVIEW: "bg-warning/15 text-warning-foreground border-warning/40",
  CONFLICT: "bg-destructive/15 text-destructive border-destructive/30",
  REJECTED: "bg-muted text-muted-foreground border-border",
  EXCLUDED: "bg-muted text-muted-foreground border-border",
  // Review statuses (lowercase)
  auto_accepted: "bg-success/15 text-success border-success/30",
  approved: "bg-success/15 text-success border-success/30",
  needs_review: "bg-warning/15 text-warning-foreground border-warning/40",
  conflict: "bg-destructive/15 text-destructive border-destructive/30",
  // Sync statuses
  pending: "bg-info/15 text-info border-info/30",
  excluded: "bg-muted text-muted-foreground border-border",
  no_fos: "bg-warning/15 text-warning-foreground border-warning/40",
  no_shopify: "bg-warning/15 text-warning-foreground border-warning/40",
  // Import statuses
  complete: "bg-success/15 text-success border-success/30",
  error: "bg-destructive/15 text-destructive border-destructive/30",
};

function pretty(s: string): string {
  return s.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const style = STYLES[status] ?? "bg-secondary text-secondary-foreground border-border";
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium whitespace-nowrap",
        style,
        className
      )}
    >
      {pretty(status)}
    </span>
  );
}
