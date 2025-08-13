"""
Field aliases for permit data normalization.

This module contains mappings from various source field names to standardized
field names in the gold.permits schema. The normalizer uses these aliases to
pick the first available field from each list.
"""

# Primary permit field aliases - ordered by preference
PERMIT_ALIASES = {
    # Core identification
    "permit_id": [
        "permit_number", "permit_no", "record_id", "application_number", 
        "permitnum", "permitid", "appl_no", "permit_id", "id", "objectid"
    ],
    
    # Date fields
    "issued_at": [
        "issued_date", "issue_date", "issued", "issue_dt", "date_issued",
        "issueddate", "permit_issued_date", "issued_on"
    ],
    "applied_at": [
        "applied_date", "application_date", "file_date", "submitted_date",
        "applied", "app_date", "date_applied", "application_submitted"
    ],
    "finaled_at": [
        "final_date", "completed_date", "finaled_date", "completion_date",
        "final", "finalized_date", "final_inspection_date"
    ],
    
    # Status and classification
    "status": [
        "status", "permit_status", "current_status", "state", "permit_state"
    ],
    "permit_type": [
        "permit_type", "work_type", "project_type", "permit_class", 
        "type", "permit_category", "category"
    ],
    "subtype": [
        "subtype", "subcategory", "sub_type", "permit_subtype", 
        "work_subtype", "secondary_type"
    ],
    "work_class": [
        "workclass", "work_class", "work_class_group", "construction_type",
        "project_class", "building_type"
    ],
    
    # Description
    "description": [
        "description", "work_description", "scope_of_work", "desc",
        "project_description", "work_desc", "details", "project_name"
    ],
    
    # Location
    "address_full": [
        "address", "project_address", "location", "site_address", 
        "full_address", "property_address", "street_address"
    ],
    "postal_code": [
        "zip", "zipcode", "postal_code", "zip_code", "postcode"
    ],
    "parcel_id": [
        "parcel", "parcel_id", "apn", "property_id", "parcel_number",
        "tax_id", "account_number"
    ],
    
    # Project details
    "valuation": [
        "estimated_cost", "job_value", "valuation", "declared_value",
        "project_cost", "construction_cost", "value", "cost"
    ],
    
    # Parties
    "contractor_name": [
        "contractor", "contractor_name", "business_name", "company_name",
        "contractor_company", "builder_name", "applicant_company"
    ],
    "contractor_license": [
        "license", "license_no", "license_number", "contractor_license",
        "business_license", "trade_license"
    ],
    
    # Geography
    "latitude": [
        "latitude", "lat", "y", "location_latitude", "coord_y", "point_y"
    ],
    "longitude": [
        "longitude", "lon", "long", "x", "location_longitude", "coord_x", "point_x"
    ],
    
    # Additional fields
    "url": [
        "url", "record_url", "link", "permit_url", "details_url"
    ],
    
    # Property details
    "property_owner": [
        "owner", "property_owner", "owner_name", "property_owner_name"
    ],
    "square_footage": [
        "square_footage", "sq_ft", "area", "floor_area", "building_area"
    ],
    "units": [
        "units", "dwelling_units", "number_of_units", "unit_count"
    ],
    "stories": [
        "stories", "floors", "number_of_stories", "building_stories"
    ]
}

# Alternative field names for different jurisdictions
JURISDICTION_SPECIFIC_ALIASES = {
    "dallas": {
        # Dallas-specific field mappings
        "permit_id": ["permit_number", "record_id"],
        "issued_at": ["issued_date", "issue_date"],
        "status": ["permit_status", "status"],
        "description": ["work_description", "description"]
    },
    "austin": {
        # Austin-specific field mappings  
        "permit_id": ["permit_num", "permit_number"],
        "issued_at": ["issued_date", "issue_date"],
        "status": ["status_current", "status"],
        "description": ["description", "work_description"]
    },
    "arlington": {
        # Arlington ArcGIS-specific field mappings
        "permit_id": ["OBJECTID", "PERMIT_NUM", "PERMITNUM"],
        "issued_at": ["ISSUE_DATE", "ISSUEDDATE"],
        "status": ["STATUS", "PERMIT_STATUS"],
        "description": ["DESCRIPTION", "PROJECT_DESC"]
    }
}

# Field type mappings for validation and conversion
FIELD_TYPES = {
    # Date fields
    "issued_at": "datetime",
    "applied_at": "datetime", 
    "finaled_at": "datetime",
    
    # Numeric fields
    "valuation": "numeric",
    "latitude": "float",
    "longitude": "float",
    "square_footage": "numeric",
    "units": "integer",
    "stories": "integer",
    
    # Text fields
    "permit_id": "string",
    "status": "string",
    "permit_type": "string",
    "subtype": "string",
    "work_class": "string",
    "description": "text",
    "address_full": "string",
    "postal_code": "string",
    "parcel_id": "string",
    "contractor_name": "string",
    "contractor_license": "string",
    "url": "string",
    "property_owner": "string"
}

# Status normalization mappings
STATUS_MAPPINGS = {
    # Active statuses
    "issued": "ACTIVE",
    "active": "ACTIVE", 
    "approved": "ACTIVE",
    "valid": "ACTIVE",
    "current": "ACTIVE",
    
    # Closed statuses
    "completed": "CLOSED",
    "finalized": "CLOSED",
    "closed": "CLOSED",
    "expired": "CLOSED",
    "final": "CLOSED",
    
    # Pending statuses
    "pending": "PENDING",
    "in_review": "PENDING",
    "under_review": "PENDING",
    "submitted": "PENDING",
    "applied": "PENDING",
    
    # Cancelled statuses
    "cancelled": "CANCELLED",
    "canceled": "CANCELLED",
    "void": "CANCELLED",
    "voided": "CANCELLED",
    "rejected": "CANCELLED"
}

# Permit type standardization
PERMIT_TYPE_MAPPINGS = {
    # Building permits
    "building": "BUILDING",
    "new_construction": "NEW_CONSTRUCTION",
    "addition": "ADDITION",
    "alteration": "ALTERATION",
    "renovation": "RENOVATION",
    "remodel": "RENOVATION",
    
    # Trade-specific permits
    "electrical": "ELECTRICAL",
    "plumbing": "PLUMBING",
    "mechanical": "MECHANICAL",
    "hvac": "MECHANICAL",
    "roofing": "ROOFING",
    
    # Specialized permits
    "demolition": "DEMOLITION",
    "pool": "POOL",
    "fence": "FENCE",
    "sign": "SIGN",
    "fire": "FIRE_PROTECTION"
}