"""initial canonical registry schema

Revision ID: 0001_initial_canonical_registry
Revises: None
Create Date: 2026-04-19 15:35:00
"""

from alembic import op
import sqlalchemy as sa


revision = '0001_initial_canonical_registry'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'canonical_products',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('canonical_name', sa.String(length=512), nullable=False),
        sa.Column('normalized_name', sa.String(length=512)),
        sa.Column('preferred_brand', sa.String(length=255)),
        sa.Column('preferred_form', sa.String(length=255)),
        sa.Column('preferred_strength', sa.String(length=255)),
        sa.Column('preferred_pack_size', sa.String(length=255)),
        sa.Column('primary_barcode', sa.String(length=64)),
        sa.Column('primary_apn', sa.String(length=64)),
        sa.Column('primary_pde', sa.String(length=64)),
        sa.Column('status', sa.String(length=64), nullable=False, server_default='ACTIVE'),
        sa.Column('review_status', sa.String(length=64), nullable=False, server_default='NEEDS_REVIEW'),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_from_source', sa.String(length=64)),
        sa.Column('confidence_summary', sa.Text()),
    )
    op.create_index('ix_canonical_products_normalized_name', 'canonical_products', ['normalized_name'])
    op.create_index('ix_canonical_products_primary_apn', 'canonical_products', ['primary_apn'])
    op.create_index('ix_canonical_products_primary_barcode', 'canonical_products', ['primary_barcode'])

    op.create_table(
        'source_systems',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('code', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
    )
    op.create_index('ix_source_systems_code', 'source_systems', ['code'], unique=True)

    op.create_table(
        'import_batches',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('import_type', sa.String(length=64), nullable=False),
        sa.Column('filename', sa.String(length=512), nullable=False),
        sa.Column('file_hash', sa.String(length=128)),
        sa.Column('row_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('notes', sa.Text()),
        sa.Column('status', sa.String(length=64), nullable=False, server_default='IMPORTED'),
    )
    op.create_index('ix_import_batches_import_type', 'import_batches', ['import_type'])

    op.create_table(
        'source_products',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('source_system_id', sa.Integer(), sa.ForeignKey('source_systems.id'), nullable=False),
        sa.Column('source_record_key', sa.String(length=255), nullable=False),
        sa.Column('external_product_id', sa.String(length=255)),
        sa.Column('external_variant_id', sa.String(length=255)),
        sa.Column('external_inventory_item_id', sa.String(length=255)),
        sa.Column('external_location_id', sa.String(length=255)),
        sa.Column('source_location_name', sa.String(length=255)),
        sa.Column('handle', sa.String(length=255)),
        sa.Column('title', sa.String(length=512), nullable=False),
        sa.Column('normalized_title', sa.String(length=512)),
        sa.Column('sku', sa.String(length=128)),
        sa.Column('barcode', sa.String(length=128)),
        sa.Column('apn', sa.String(length=128)),
        sa.Column('pde', sa.String(length=128)),
        sa.Column('vendor', sa.String(length=255)),
        sa.Column('product_type', sa.String(length=255)),
        sa.Column('status', sa.String(length=64)),
        sa.Column('raw_payload_json', sa.JSON()),
        sa.Column('last_import_batch_id', sa.Integer(), sa.ForeignKey('import_batches.id')),
        sa.Column('first_seen_at', sa.DateTime(), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint('source_system_id', 'source_record_key', name='uq_source_record'),
    )
    for name in ['source_system_id', 'external_variant_id', 'external_inventory_item_id', 'external_location_id', 'handle', 'title', 'normalized_title', 'sku', 'barcode', 'apn', 'pde']:
        op.create_index(f'ix_source_products_{name}', 'source_products', [name])

    op.create_table(
        'product_identifiers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('canonical_product_id', sa.Integer(), sa.ForeignKey('canonical_products.id'), nullable=False),
        sa.Column('identifier_type', sa.String(length=64), nullable=False),
        sa.Column('identifier_value', sa.String(length=128), nullable=False),
        sa.Column('normalized_identifier_value', sa.String(length=128), nullable=False),
        sa.Column('source', sa.String(length=64)),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('first_seen_at', sa.DateTime(), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(), nullable=False),
    )
    for name in ['canonical_product_id', 'identifier_type', 'identifier_value', 'normalized_identifier_value']:
        op.create_index(f'ix_product_identifiers_{name}', 'product_identifiers', [name])

    op.create_table(
        'source_product_links',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('canonical_product_id', sa.Integer(), sa.ForeignKey('canonical_products.id'), nullable=False),
        sa.Column('source_product_id', sa.Integer(), sa.ForeignKey('source_products.id'), nullable=False),
        sa.Column('link_status', sa.String(length=64), nullable=False),
        sa.Column('link_method', sa.String(length=64), nullable=False),
        sa.Column('confidence_score', sa.Float()),
        sa.Column('fuzzy_score', sa.Float()),
        sa.Column('ai_score', sa.Float()),
        sa.Column('ai_reason', sa.Text()),
        sa.Column('locked', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('excluded', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('approved_by', sa.String(length=255)),
        sa.Column('approved_at', sa.DateTime()),
        sa.Column('review_notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('source_product_id', name='uq_source_product_link'),
    )
    for name in ['canonical_product_id', 'source_product_id', 'link_status', 'link_method']:
        op.create_index(f'ix_source_product_links_{name}', 'source_product_links', [name])

    op.create_table(
        'candidate_links',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('run_id', sa.String(length=128), nullable=False),
        sa.Column('source_product_id', sa.Integer(), sa.ForeignKey('source_products.id'), nullable=False),
        sa.Column('candidate_canonical_product_id', sa.Integer(), sa.ForeignKey('canonical_products.id')),
        sa.Column('candidate_source_product_id', sa.Integer(), sa.ForeignKey('source_products.id')),
        sa.Column('candidate_rank', sa.Integer(), nullable=False),
        sa.Column('match_method', sa.String(length=64), nullable=False),
        sa.Column('fuzzy_score', sa.Float()),
        sa.Column('ai_score', sa.Float()),
        sa.Column('ai_reason', sa.Text()),
        sa.Column('proposed_action', sa.String(length=64)),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    for name in ['run_id', 'source_product_id', 'candidate_canonical_product_id']:
        op.create_index(f'ix_candidate_links_{name}', 'candidate_links', [name])

    op.create_table(
        'inventory_snapshots',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('canonical_product_id', sa.Integer(), sa.ForeignKey('canonical_products.id')),
        sa.Column('source_product_id', sa.Integer(), sa.ForeignKey('source_products.id')),
        sa.Column('source_system_id', sa.Integer(), sa.ForeignKey('source_systems.id'), nullable=False),
        sa.Column('source_location', sa.String(length=255)),
        sa.Column('on_hand', sa.Integer()),
        sa.Column('available', sa.Integer()),
        sa.Column('committed', sa.Integer()),
        sa.Column('unavailable', sa.Integer()),
        sa.Column('captured_at', sa.DateTime(), nullable=False),
        sa.Column('import_batch_id', sa.Integer(), sa.ForeignKey('import_batches.id')),
    )
    for name in ['canonical_product_id', 'source_product_id', 'source_system_id']:
        op.create_index(f'ix_inventory_snapshots_{name}', 'inventory_snapshots', [name])

    op.create_table(
        'inventory_reconciliation_runs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('notes', sa.Text()),
        sa.Column('settings_snapshot_json', sa.JSON()),
    )

    op.create_table(
        'inventory_reconciliation_rows',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('run_id', sa.Integer(), sa.ForeignKey('inventory_reconciliation_runs.id'), nullable=False),
        sa.Column('canonical_product_id', sa.Integer(), sa.ForeignKey('canonical_products.id')),
        sa.Column('shopify_source_product_id', sa.Integer(), sa.ForeignKey('source_products.id')),
        sa.Column('fos_source_product_id', sa.Integer(), sa.ForeignKey('source_products.id')),
        sa.Column('shopify_handle', sa.String(length=255)),
        sa.Column('shopify_title', sa.String(length=512)),
        sa.Column('shopify_variant_id', sa.String(length=255)),
        sa.Column('shopify_inventory_item_id', sa.String(length=255)),
        sa.Column('shopify_location_id', sa.String(length=255)),
        sa.Column('shopify_location_name', sa.String(length=255)),
        sa.Column('shopify_sku', sa.String(length=128)),
        sa.Column('shopify_barcode', sa.String(length=128)),
        sa.Column('fos_stock_name', sa.String(length=512)),
        sa.Column('fos_apn', sa.String(length=128)),
        sa.Column('shopify_current_on_hand', sa.Integer()),
        sa.Column('fos_soh', sa.Integer()),
        sa.Column('proposed_shopify_on_hand', sa.Integer()),
        sa.Column('delta', sa.Integer()),
        sa.Column('sync_status', sa.String(length=64), nullable=False, server_default='REVIEW'),
        sa.Column('warning_flags_json', sa.JSON()),
        sa.Column('reviewed_by', sa.String(length=255)),
        sa.Column('reviewed_at', sa.DateTime()),
        sa.Column('review_notes', sa.Text()),
    )
    op.create_index('ix_inventory_reconciliation_rows_run_id', 'inventory_reconciliation_rows', ['run_id'])
    op.create_index('ix_inventory_reconciliation_rows_canonical_product_id', 'inventory_reconciliation_rows', ['canonical_product_id'])

    op.create_table(
        'manual_review_actions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('entity_type', sa.String(length=64), nullable=False),
        sa.Column('entity_id', sa.String(length=128), nullable=False),
        sa.Column('action_type', sa.String(length=64), nullable=False),
        sa.Column('old_value_json', sa.JSON()),
        sa.Column('new_value_json', sa.JSON()),
        sa.Column('user_note', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_manual_review_actions_entity_type', 'manual_review_actions', ['entity_type'])
    op.create_index('ix_manual_review_actions_entity_id', 'manual_review_actions', ['entity_id'])

    op.create_table(
        'export_runs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('export_type', sa.String(length=64), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('row_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('manifest_json', sa.JSON()),
        sa.Column('notes', sa.Text()),
    )
    op.create_index('ix_export_runs_export_type', 'export_runs', ['export_type'])

    op.create_table(
        'app_settings',
        sa.Column('key', sa.String(length=128), primary_key=True),
        sa.Column('value', sa.Text(), nullable=False),
    )


def downgrade() -> None:
    for table in [
        'app_settings', 'export_runs', 'manual_review_actions', 'inventory_reconciliation_rows',
        'inventory_reconciliation_runs', 'inventory_snapshots', 'candidate_links', 'source_product_links',
        'product_identifiers', 'source_products', 'import_batches', 'source_systems', 'canonical_products'
    ]:
        op.drop_table(table)
