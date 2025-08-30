"""Entity resolution library for linking firms, permits, awards, and violations in Texas data."""

import logging
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """Base entity class."""

    id: str
    type: str  # firm, permit, award, violation, inspection
    attributes: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    confidence: float = 1.0


@dataclass
class Relationship:
    """Relationship between entities."""

    source_id: str
    target_id: str
    relationship_type: str  # issues, awarded, violates, inspects
    attributes: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Firm(Entity):
    """Business/contractor entity."""

    name: str = ""
    normalized_name: str = ""
    aliases: Set[str] = field(default_factory=set)
    addresses: Set[str] = field(default_factory=set)
    licenses: Set[str] = field(default_factory=set)
    phone_numbers: Set[str] = field(default_factory=set)

    def __post_init__(self):
        self.type = "firm"
        if self.name and not self.normalized_name:
            self.normalized_name = self._normalize_name(self.name)

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize business name for matching."""
        if not name:
            return ""

        # Convert to uppercase and remove extra spaces
        normalized = re.sub(r"\s+", " ", name.upper().strip())

        # Remove common business suffixes for matching
        suffixes = [
            r"\s+LLC$",
            r"\s+INC$",
            r"\s+CORP$",
            r"\s+LTD$",
            r"\s+LP$",
            r"\s+LLP$",
            r"\s+CO$",
            r"\s+COMPANY$",
            r"\s+CORPORATION$",
            r"\s+INCORPORATED$",
            r"\s+LIMITED$",
            r"\s+PARTNERSHIP$",
        ]

        for suffix in suffixes:
            normalized = re.sub(suffix, "", normalized)

        # Remove punctuation except spaces
        normalized = re.sub(r"[^\w\s]", "", normalized)

        return normalized.strip()


class EntityGraph:
    """Graph-based entity resolution system for Texas construction industry data."""

    def __init__(self, data_dir: str = "data/gold"):
        """Initialize the entity graph."""
        self.data_dir = Path(data_dir)
        self.entities: Dict[str, Entity] = {}
        self.relationships: List[Relationship] = []

        # Name normalization cache
        self._name_cache: Dict[str, str] = {}

        # Fuzzy matching thresholds
        self.name_similarity_threshold = 0.85
        self.address_similarity_threshold = 0.90

    def load_normalized_data(self) -> int:
        """Load normalized data and build entity graph."""
        total_loaded = 0

        # Load each category of normalized data
        for category in [
            "permits",
            "violations",
            "inspections",
            "bids",
            "awards",
            "contractors",
        ]:
            files = list(self.data_dir.glob(f"{category}_*.json"))

            for file_path in files:
                try:
                    with open(file_path, "r") as f:
                        records = json.load(f)

                    loaded = self._process_category_records(category, records)
                    total_loaded += loaded
                    logger.info(
                        f"Loaded {loaded} {category} records from {file_path.name}"
                    )

                except Exception as e:
                    logger.error(f"Error loading {file_path}: {e}")

        logger.info(f"Total entities loaded: {len(self.entities)}")
        logger.info(f"Total relationships: {len(self.relationships)}")

        return total_loaded

    def _process_category_records(
        self, category: str, records: List[Dict[str, Any]]
    ) -> int:
        """Process records from a specific category."""
        loaded = 0

        for record in records:
            try:
                if category == "permits":
                    self._process_permit(record)
                elif category == "violations":
                    self._process_violation(record)
                elif category == "inspections":
                    self._process_inspection(record)
                elif category in ["bids", "awards"]:
                    self._process_award(record)
                elif category == "contractors":
                    self._process_contractor(record)

                loaded += 1

            except Exception as e:
                logger.warning(
                    f"Error processing {category} record {record.get('id', 'unknown')}: {e}"
                )

        return loaded

    def _process_permit(self, record: Dict[str, Any]):
        """Process a permit record and create entities/relationships."""
        # Create permit entity
        permit_entity = Entity(
            id=record["id"],
            type="permit",
            attributes=record,
            confidence=record.get("quality_score", 1.0),
        )
        self.entities[permit_entity.id] = permit_entity

        # Create/link firm entity if applicant is present
        applicant = record.get("applicant")
        if applicant:
            firm_entity = self._get_or_create_firm(applicant, record)
            if firm_entity:
                self._add_relationship(
                    firm_entity.id,
                    permit_entity.id,
                    "issues",
                    {"permit_number": record.get("permit_number")},
                )

    def _process_violation(self, record: Dict[str, Any]):
        """Process a violation record."""
        # Create violation entity
        violation_entity = Entity(
            id=record["id"],
            type="violation",
            attributes=record,
            confidence=record.get("quality_score", 1.0),
        )
        self.entities[violation_entity.id] = violation_entity

        # Try to link to permits by address
        address = record.get("address")
        if address:
            related_permits = self._find_entities_by_address("permit", address)
            for permit_id in related_permits[:5]:  # Limit to avoid explosion
                self._add_relationship(
                    permit_id, violation_entity.id, "violates", {"address_match": True}
                )

    def _process_inspection(self, record: Dict[str, Any]):
        """Process an inspection record."""
        # Create inspection entity
        inspection_entity = Entity(
            id=record["id"],
            type="inspection",
            attributes=record,
            confidence=record.get("quality_score", 1.0),
        )
        self.entities[inspection_entity.id] = inspection_entity

        # Link to permit if permit_number is available
        permit_number = record.get("permit_number")
        if permit_number:
            related_permits = self._find_entities_by_attribute(
                "permit", "permit_number", permit_number
            )
            for permit_id in related_permits:
                self._add_relationship(
                    permit_id,
                    inspection_entity.id,
                    "inspects",
                    {"permit_number": permit_number},
                )

    def _process_award(self, record: Dict[str, Any]):
        """Process a bid/award record."""
        # Create award entity
        award_entity = Entity(
            id=record["id"],
            type="award",
            attributes=record,
            confidence=record.get("quality_score", 1.0),
        )
        self.entities[award_entity.id] = award_entity

        # Create/link firm entity if vendor is present
        vendor = record.get("vendor_name")
        if vendor:
            firm_entity = self._get_or_create_firm(vendor, record)
            if firm_entity:
                self._add_relationship(
                    firm_entity.id,
                    award_entity.id,
                    "awarded",
                    {
                        "contract_number": record.get("contract_number"),
                        "amount": record.get("amount"),
                    },
                )

    def _process_contractor(self, record: Dict[str, Any]):
        """Process a contractor license record."""
        # Create contractor license entity
        license_entity = Entity(
            id=record["id"],
            type="license",
            attributes=record,
            confidence=record.get("quality_score", 1.0),
        )
        self.entities[license_entity.id] = license_entity

        # Create/link firm entity
        business_name = record.get("business_name")
        if business_name:
            firm_entity = self._get_or_create_firm(business_name, record)
            if firm_entity:
                # Add license to firm
                firm_entity.licenses.add(record.get("license_number", ""))

                self._add_relationship(
                    firm_entity.id,
                    license_entity.id,
                    "licensed",
                    {
                        "license_number": record.get("license_number"),
                        "license_type": record.get("license_type"),
                    },
                )

    def _get_or_create_firm(
        self, name: str, context_record: Dict[str, Any]
    ) -> Optional[Firm]:
        """Get existing firm or create new one."""
        if not name or not name.strip():
            return None

        normalized_name = Firm._normalize_name(name)
        if not normalized_name:
            return None

        # Look for existing firm with similar name
        existing_firm = self._find_similar_firm(normalized_name)

        if existing_firm:
            # Update existing firm with new information
            existing_firm.aliases.add(name)

            # Add address if available
            address = context_record.get("address")
            if address:
                existing_firm.addresses.add(address)

            return existing_firm
        else:
            # Create new firm
            firm_id = self._generate_firm_id(normalized_name)

            firm = Firm(
                id=firm_id,
                name=name,
                normalized_name=normalized_name,
                aliases={name},
                attributes={"source_records": [context_record["id"]]},
            )

            # Add address if available
            address = context_record.get("address")
            if address:
                firm.addresses.add(address)

            self.entities[firm_id] = firm
            return firm

    def _find_similar_firm(self, normalized_name: str) -> Optional[Firm]:
        """Find existing firm with similar name."""
        for entity in self.entities.values():
            if isinstance(entity, Firm):
                # Exact match on normalized name
                if entity.normalized_name == normalized_name:
                    return entity

                # Check aliases
                for alias in entity.aliases:
                    if Firm._normalize_name(alias) == normalized_name:
                        return entity

                # Fuzzy matching for similar names
                similarity = self._calculate_name_similarity(
                    normalized_name, entity.normalized_name
                )
                if similarity >= self.name_similarity_threshold:
                    return entity

        return None

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names (simplified Jaccard similarity)."""
        if not name1 or not name2:
            return 0.0

        # Split into words
        words1 = set(name1.split())
        words2 = set(name2.split())

        if not words1 or not words2:
            return 0.0

        # Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0

    def _find_entities_by_address(self, entity_type: str, address: str) -> List[str]:
        """Find entities of given type with similar address."""
        if not address:
            return []

        normalized_address = self._normalize_address(address)
        matching_ids = []

        for entity_id, entity in self.entities.items():
            if entity.type != entity_type:
                continue

            entity_address = entity.attributes.get("address")
            if entity_address:
                entity_normalized = self._normalize_address(entity_address)
                similarity = self._calculate_address_similarity(
                    normalized_address, entity_normalized
                )

                if similarity >= self.address_similarity_threshold:
                    matching_ids.append(entity_id)

        return matching_ids

    def _find_entities_by_attribute(
        self, entity_type: str, attribute: str, value: str
    ) -> List[str]:
        """Find entities with matching attribute value."""
        if not value:
            return []

        matching_ids = []

        for entity_id, entity in self.entities.items():
            if entity.type != entity_type:
                continue

            entity_value = entity.attributes.get(attribute)
            if entity_value and str(entity_value).strip() == str(value).strip():
                matching_ids.append(entity_id)

        return matching_ids

    def _normalize_address(self, address: str) -> str:
        """Normalize address for comparison."""
        if not address:
            return ""

        # Basic normalization
        normalized = re.sub(r"\s+", " ", address.upper().strip())

        # Remove punctuation except spaces
        normalized = re.sub(r"[^\w\s]", "", normalized)

        return normalized

    def _calculate_address_similarity(self, addr1: str, addr2: str) -> float:
        """Calculate similarity between addresses."""
        if not addr1 or not addr2:
            return 0.0

        # Simple word-based similarity
        words1 = set(addr1.split())
        words2 = set(addr2.split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0

    def _generate_firm_id(self, normalized_name: str) -> str:
        """Generate unique ID for a firm."""
        return f"firm:{hashlib.md5(normalized_name.encode()).hexdigest()[:12]}"

    def _add_relationship(
        self, source_id: str, target_id: str, rel_type: str, attributes: Dict[str, Any]
    ):
        """Add a relationship between entities."""
        relationship = Relationship(
            source_id=source_id,
            target_id=target_id,
            relationship_type=rel_type,
            attributes=attributes,
        )
        self.relationships.append(relationship)

    def get_firm_profile(self, firm_id: str) -> Dict[str, Any]:
        """Get comprehensive profile for a firm."""
        if firm_id not in self.entities:
            return {}

        firm = self.entities[firm_id]
        if not isinstance(firm, Firm):
            return {}

        # Get all related entities
        permits = self._get_related_entities(firm_id, "issues", "permit")
        awards = self._get_related_entities(firm_id, "awarded", "award")
        licenses = self._get_related_entities(firm_id, "licensed", "license")
        violations = self._get_related_violations(firm_id)

        # Calculate metrics
        total_permit_value = sum(
            float(self.entities[pid].attributes.get("value", 0) or 0) for pid in permits
        )

        total_award_value = sum(
            float(self.entities[aid].attributes.get("amount", 0) or 0) for aid in awards
        )

        return {
            "firm_id": firm_id,
            "name": firm.name,
            "aliases": list(firm.aliases),
            "addresses": list(firm.addresses),
            "licenses": list(firm.licenses),
            "permits": {
                "count": len(permits),
                "total_value": total_permit_value,
                "recent": permits[:5],  # Most recent 5
            },
            "awards": {
                "count": len(awards),
                "total_value": total_award_value,
                "recent": awards[:5],
            },
            "violations": {"count": len(violations), "recent": violations[:5]},
            "licenses_held": {
                "count": len(licenses),
                "types": list(
                    set(
                        self.entities[lid].attributes.get("license_type", "")
                        for lid in licenses
                    )
                ),
            },
        }

    def _get_related_entities(
        self, firm_id: str, rel_type: str, entity_type: str
    ) -> List[str]:
        """Get entities related to a firm by relationship type."""
        related_ids = []

        for rel in self.relationships:
            if rel.source_id == firm_id and rel.relationship_type == rel_type:
                entity = self.entities.get(rel.target_id)
                if entity is not None and entity.type == entity_type:
                    related_ids.append(rel.target_id)

        return related_ids

    def _get_related_violations(self, firm_id: str) -> List[str]:
        """Get violations related to a firm (indirectly through permits)."""
        violation_ids = []

        # Get firm's permits
        permit_ids = self._get_related_entities(firm_id, "issues", "permit")

        # Find violations related to those permits
        for rel in self.relationships:
            if rel.source_id in permit_ids and rel.relationship_type == "violates":
                violation_ids.append(rel.target_id)

        return violation_ids

    def get_network_analysis(self) -> Dict[str, Any]:
        """Get network analysis of the entity graph."""
        firms = [e for e in self.entities.values() if isinstance(e, Firm)]

        # Calculate firm rankings
        firm_rankings = []
        for firm in firms:
            profile = self.get_firm_profile(firm.id)

            # Simple scoring based on activity
            score = (
                profile["permits"]["count"] * 10
                + profile["awards"]["count"] * 20
                + profile["licenses_held"]["count"] * 5
                - profile["violations"]["count"] * 15
            )

            firm_rankings.append(
                {
                    "firm_id": firm.id,
                    "name": firm.name,
                    "score": score,
                    "permits": profile["permits"]["count"],
                    "awards": profile["awards"]["count"],
                    "violations": profile["violations"]["count"],
                }
            )

        # Sort by score
        firm_rankings.sort(key=lambda x: x["score"], reverse=True)

        return {
            "total_firms": len(firms),
            "total_permits": len(
                [e for e in self.entities.values() if e.type == "permit"]
            ),
            "total_violations": len(
                [e for e in self.entities.values() if e.type == "violation"]
            ),
            "total_awards": len(
                [e for e in self.entities.values() if e.type == "award"]
            ),
            "total_relationships": len(self.relationships),
            "top_firms": firm_rankings[:20],
        }

    def save_graph(self, output_path: str):
        """Save the entity graph to a JSON file."""
        # Convert entities to serializable format
        entities_data = {}
        for entity_id, entity in self.entities.items():
            entity_data = {
                "id": entity.id,
                "type": entity.type,
                "attributes": entity.attributes,
                "created_at": entity.created_at.isoformat(),
                "confidence": entity.confidence,
            }

            # Add firm-specific fields
            if isinstance(entity, Firm):
                entity_data.update(
                    {
                        "name": entity.name,
                        "normalized_name": entity.normalized_name,
                        "aliases": list(entity.aliases),
                        "addresses": list(entity.addresses),
                        "licenses": list(entity.licenses),
                    }
                )

            entities_data[entity_id] = entity_data

        # Convert relationships to serializable format
        relationships_data = []
        for rel in self.relationships:
            relationships_data.append(
                {
                    "source_id": rel.source_id,
                    "target_id": rel.target_id,
                    "relationship_type": rel.relationship_type,
                    "attributes": rel.attributes,
                    "confidence": rel.confidence,
                    "created_at": rel.created_at.isoformat(),
                }
            )

        graph_data = {
            "entities": entities_data,
            "relationships": relationships_data,
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "total_entities": len(entities_data),
                "total_relationships": len(relationships_data),
            },
        }

        with open(output_path, "w") as f:
            json.dump(graph_data, f, indent=2)

        logger.info(f"Saved entity graph to {output_path}")


def main():
    """Example usage of the entity graph."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Initialize entity graph
    graph = EntityGraph()

    # Load normalized data
    total_loaded = graph.load_normalized_data()
    print(f"Loaded {total_loaded} records")

    # Get network analysis
    analysis = graph.get_network_analysis()
    print("\nNetwork Analysis:")
    print(f"  Total firms: {analysis['total_firms']}")
    print(f"  Total permits: {analysis['total_permits']}")
    print(f"  Total violations: {analysis['total_violations']}")
    print(f"  Total awards: {analysis['total_awards']}")
    print(f"  Total relationships: {analysis['total_relationships']}")

    # Show top firms
    print("\nTop 5 firms by activity:")
    for i, firm in enumerate(analysis["top_firms"][:5], 1):
        print(f"  {i}. {firm['name']} (Score: {firm['score']})")
        print(
            f"     Permits: {firm['permits']}, Awards: {firm['awards']}, Violations: {firm['violations']}"
        )

    # Save graph
    graph.save_graph("data/entity_graph.json")


if __name__ == "__main__":
    main()
