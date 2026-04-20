export interface DashboardSummary {
  canonical_products: number;
  linked_shopify_products: number;
  linked_fos_products: number;
  unresolved_links: number;
  conflicts: number;
  reconciliation_ready: number;
  import_batches: number;
  export_runs: number;
  legacy_duplicate_groups: number;
  legacy_duplicate_records: number;
}

export interface CanonicalProduct {
  id: number;
  canonical_name: string;
  normalized_name?: string;
  primary_barcode?: string;
  primary_apn?: string;
  primary_pde?: string;
  review_status: string;
  confidence_summary?: string;
}

export interface SourceProduct {
  id: number;
  title: string;
  external_variant_id?: string;
  external_inventory_item_id?: string;
  external_location_id?: string;
  source_location_name?: string;
  handle?: string;
  sku?: string;
  barcode?: string;
  apn?: string;
  pde?: string;
  status?: string;
  vendor?: string;
  product_type?: string;
  source_code?: string;
  raw_payload_json?: Record<string, unknown>;
}

export interface ImportBatch {
  id: number;
  import_type: string;
  filename: string;
  row_count: number;
  status: string;
  created_at: string;
}

export interface CandidateSummary {
  id: number;
  candidate_canonical_product_id?: number;
  candidate_rank: number;
  match_method: string;
  fuzzy_score?: number;
  ai_score?: number;
  ai_reason?: string;
  proposed_action?: string;
  canonical_product?: CanonicalProduct;
}

export interface LinkReviewItem {
  id: number;
  link_status: string;
  link_method: string;
  confidence_score?: number;
  fuzzy_score?: number;
  ai_score?: number;
  ai_reason?: string;
  locked: boolean;
  excluded: boolean;
  review_notes?: string;
  source_product: SourceProduct;
  canonical_product: CanonicalProduct;
  candidates?: CandidateSummary[];
}

export interface ImportPreviewResponse {
  detected_type: string;
  columns: string[];
  preview_rows: { row_number: number; data: Record<string, unknown> }[];
  missing_columns: string[];
  extra_columns: string[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface ReconciliationRow {
  id: number;
  shopify_handle?: string;
  shopify_title?: string;
  shopify_variant_id?: string;
  shopify_inventory_item_id?: string;
  shopify_location_id?: string;
  shopify_location_name?: string;
  fos_stock_name?: string;
  shopify_current_on_hand?: number;
  fos_soh?: number;
  proposed_shopify_on_hand?: number;
  delta?: number;
  sync_status: string;
  warning_flags_json?: { warnings?: string[] };
}
