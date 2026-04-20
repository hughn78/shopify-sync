export const API = {
  health: '/health',
  dashboard: '/dashboard',
  settings: '/settings',
  auditSummary: '/audit-summary',

  imports: '/imports',
  importsPreview: '/imports/preview',
  importBatches: '/import-batches',

  canonicalProducts: '/canonical-products',
  reviewOptions: '/review-options',
  sourceProducts: '/source-products',

  linkReview: '/link-review',
  linkReviewBulk: '/link-review/bulk',
  linkReviewById: (id: number) => `/link-review/${id}`,

  reconciliationRuns: '/reconciliation-runs',
  reconciliationRows: (runId: number) => `/reconciliation-rows/${runId}`,

  exportInventory: (runId: number) => `/exports/inventory/${runId}`,
} as const;
