"""
Pydantic model for building permit records with normalization helpers.
"""
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
import json


class PermitRecord(BaseModel):
    """
    Normalized building permit record.
    
    Core fields that should be present in most permit systems.
    Additional fields can be stored in the `extra_data` dict.
    """
    
    # Core identification
    jurisdiction: str = Field(..., description="Source jurisdiction/city name")
    permit_id: str = Field(..., description="Permit number/ID from source system")
    
    # Address and location
    address: Optional[str] = Field(None, description="Full street address")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    
    # Permit details
    description: Optional[str] = Field(None, description="Work description/project details")
    work_class: Optional[str] = Field(None, description="Type/category of work")
    category: Optional[str] = Field(None, description="Permit category (residential/commercial/etc)")
    status: Optional[str] = Field(None, description="Permit status")
    
    # Dates
    issue_date: Optional[datetime] = Field(None, description="Date permit was issued")
    application_date: Optional[datetime] = Field(None, description="Date application was submitted")
    expiration_date: Optional[datetime] = Field(None, description="Permit expiration date")
    
    # People and value
    applicant: Optional[str] = Field(None, description="Applicant/contractor name")
    owner: Optional[str] = Field(None, description="Property owner name")
    value: Optional[float] = Field(None, description="Declared project value")
    
    # Metadata
    source_url: Optional[str] = Field(None, description="Source URL where record was found")
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="When this record was scraped")
    
    # Additional data that doesn't fit standard schema
    extra_data: Dict[str, Any] = Field(default_factory=dict, description="Additional source-specific fields")
    
    model_config = ConfigDict(
        extra="forbid",
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )
    
    @field_validator('category', mode='before')
    @classmethod
    def normalize_category(cls, v):
        """Normalize category to standard values."""
        if not v:
            return v
        v_lower = str(v).lower()
        if any(keyword in v_lower for keyword in ['residential', 'single', 'family', 'duplex']):
            return 'residential'
        elif any(keyword in v_lower for keyword in ['commercial', 'office', 'retail', 'industrial']):
            return 'commercial'
        return v
    
    @field_validator('address', mode='before')
    @classmethod
    def normalize_address(cls, v):
        """Basic address normalization."""
        if not v:
            return v
        # Basic cleanup - remove extra whitespace, proper case
        address = ' '.join(str(v).split())
        return address.title() if address else None
    
    def get_hash(self) -> str:
        """
        Generate a stable hash for deduplication.
        Uses jurisdiction + permit_id as primary key, falls back to content hash.
        """
        # Primary approach: use jurisdiction + permit_id
        if self.jurisdiction and self.permit_id:
            key_data = f"{self.jurisdiction}|{self.permit_id}"
            return hashlib.sha256(key_data.encode('utf-8')).hexdigest()[:16]
        
        # Fallback: content-based hash of key fields
        key_fields = {
            'jurisdiction': self.jurisdiction,
            'address': self.address,
            'description': self.description,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'applicant': self.applicant,
            'value': self.value
        }
        
        # Create deterministic string from sorted key fields
        key_str = json.dumps(key_fields, sort_keys=True, default=str)
        return hashlib.sha256(key_str.encode('utf-8')).hexdigest()[:16]
    
    def is_residential(self) -> bool:
        """
        Determine if this permit is likely for residential work.
        Uses category field and description keywords.
        """
        # Check category first
        if self.category and 'residential' in self.category.lower():
            return True
        
        # Check description for residential keywords
        if self.description:
            desc_lower = self.description.lower()
            residential_keywords = [
                'single family', 'duplex', 'residential', 'house', 'home',
                'addition', 'renovation', 'remodel', 'bathroom', 'kitchen',
                'garage', 'deck', 'porch', 'fence', 'pool', 'shed'
            ]
            return any(keyword in desc_lower for keyword in residential_keywords)
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/export."""
        data = self.dict()
        # Flatten extra_data into main dict for CSV export
        if self.extra_data:
            data.update(self.extra_data)
        return data
    
    @classmethod
    def from_raw_data(cls, raw_data: Dict[str, Any], jurisdiction: str, 
                      field_mappings: Optional[Dict[str, str]] = None) -> "PermitRecord":
        """
        Create PermitRecord from raw scraped data with field mappings.
        
        Args:
            raw_data: Raw data dict from scraper
            jurisdiction: Source jurisdiction name
            field_mappings: Optional mapping of source fields to PermitRecord fields
        """
        mappings = field_mappings or {}
        
        # Apply field mappings
        mapped_data = {}
        extra_data = {}
        
        for source_field, value in raw_data.items():
            if source_field in mappings:
                target_field = mappings[source_field]
                mapped_data[target_field] = value
            else:
                # Store unmapped fields in extra_data
                extra_data[source_field] = value
        
        # Ensure jurisdiction is set
        mapped_data['jurisdiction'] = jurisdiction
        mapped_data['extra_data'] = extra_data
        
        return cls(**mapped_data)