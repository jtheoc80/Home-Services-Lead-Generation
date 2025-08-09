from typing import Dict, Any

RESIDENTIAL_KEYWORDS = [
    "residential","single family","sfh","duplex","townhome","townhouse","apartment","multi-family",
    "remodel","addition","bathroom","kitchen","roof","siding","fence","pool","deck","garage",
    "foundation","window","hvac","plumbing","electrical"
]

def _get(d: dict, keys):
    for k in keys if isinstance(keys, list) else [keys]:
        if k in d and d[k] is not None:
            return d[k]
    return ""

def normalize_record(rec: Dict[str, Any], source: str) -> Dict[str, Any]:
    """
    Attempts to map common fields; supports Socrata address composition via '__address_composed' injected by adapter.
    """
    # direct keys + fallbacks
    permit_number = str(_get(rec, ["permit_number","permit","permit_","id","permitnum","permit_no"]))
    issued_date   = str(_get(rec, ["issue_date","issued_date","application_start_date","date_issued","issued"]))
    status        = str(_get(rec, ["status","current_status","permit_status"]))
    address       = str(_get(rec, ["__address_composed","address","full_address","street_address"]))
    city          = str(_get(rec, ["city","municipality"]))
    state         = str(_get(rec, ["state","state_abbr"]))
    zipcode       = str(_get(rec, ["zip","zipcode","postal_code"]))
    applicant     = str(_get(rec, ["applicant","applicant_name","owner_name","owner"]))
    contractor    = str(_get(rec, ["contractor","contractor_name","company_name"]))
    description   = str(_get(rec, ["description","work_description","summary"]))
    value         = _get(rec, ["estimated_cost","declared_valuation","value"])
    work_class    = str(_get(rec, ["work_class","permit_type","work_type","category"]))
    category      = str(_get(rec, ["category","occupancy_type","permit_type"]))
    lat           = _get(rec, ["latitude","lat"])
    lon           = _get(rec, ["longitude","lon","lng"])

    return {
        "source": source,
        "permit_number": permit_number,
        "issued_date": issued_date,
        "status": status,
        "address": address,
        "city": city,
        "state": state,
        "zipcode": zipcode,
        "applicant": applicant,
        "contractor": contractor,
        "description": description,
        "value": float(value) if str(value).replace(".","",1).isdigit() else None,
        "work_class": work_class,
        "category": category,
        "latitude": float(lat) if str(lat).replace(".","",1).replace("-","",1).isdigit() else None,
        "longitude": float(lon) if str(lon).replace(".","",1).replace("-","",1).isdigit() else None,
        "raw_json": rec,
    }
