from __future__ import annotations

from enum import Enum


class LinkStatus(str, Enum):
    AUTO_ACCEPTED = 'AUTO_ACCEPTED'
    NEEDS_REVIEW = 'NEEDS_REVIEW'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    EXCLUDED = 'EXCLUDED'
    CONFLICT = 'CONFLICT'


class LinkMethod(str, Enum):
    EXACT_BARCODE = 'EXACT_BARCODE'
    EXACT_APN = 'EXACT_APN'
    EXACT_PDE = 'EXACT_PDE'
    EXACT_SKU = 'EXACT_SKU'
    NORMALIZED_NAME = 'NORMALIZED_NAME'
    FUZZY_PLUS_AI = 'FUZZY_PLUS_AI'
    CREATED_NEW_CANONICAL = 'CREATED_NEW_CANONICAL'


class ImportType(str, Enum):
    SHOPIFY_PRODUCTS = 'SHOPIFY_PRODUCTS'
    SHOPIFY_INVENTORY = 'SHOPIFY_INVENTORY'
    FOS = 'FOS'
    PRICEBOOK = 'PRICEBOOK'
    MASTERCATALOG = 'MASTERCATALOG'
    SCRAPED_CATALOG = 'SCRAPED_CATALOG'


class ReviewAction(str, Enum):
    APPROVE = 'approve'
    REJECT = 'reject'
    EXCLUDE = 'exclude'
    REASSIGN = 'reassign'
    CREATE_CANONICAL = 'create_canonical'


class SyncStatus(str, Enum):
    READY = 'READY'
    REVIEW = 'REVIEW'


class ProductReviewStatus(str, Enum):
    NEEDS_REVIEW = 'NEEDS_REVIEW'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'


class BatchStatus(str, Enum):
    IMPORTED = 'IMPORTED'
    FAILED = 'FAILED'


class CandidateAction(str, Enum):
    AUTO_ACCEPT = 'AUTO_ACCEPT'
    REVIEW = 'REVIEW'
