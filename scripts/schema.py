"""Dataset schema (JSON-Schema-style) for one artifact record."""

ARTIFACT_SCHEMA = {
    "type": "object",
    "required": ["id", "names", "description", "images", "sources"],
    "properties": {
        "id": {"type": "string"},
        "names": {
            "type": "object",
            "properties": {
                "ar": {"type": "string"},
                "en": {"type": "string"},
                "alt_ar": {"type": "array", "items": {"type": "string"}},
                "alt_en": {"type": "array", "items": {"type": "string"}},
            },
        },
        "category": {"type": "string"},
        "period": {
            "type": "object",
            "properties": {
                "ar": {"type": "string"},
                "en": {"type": "string"},
                "year_min": {"type": ["integer", "null"]},
                "year_max": {"type": ["integer", "null"]},
            },
        },
        "dynasty": {
            "type": "object",
            "properties": {
                "ar": {"type": "string"},
                "en": {"type": "string"},
            },
        },
        "material": {"type": "array", "items": {"type": "string"}},
        "dimensions": {"type": "object"},
        "provenance": {
            "type": "object",
            "properties": {
                "site_ar": {"type": "string"},
                "site_en": {"type": "string"},
            },
        },
        "discovery": {
            "type": "object",
            "properties": {
                "year": {"type": ["integer", "null"]},
                "by_ar": {"type": "string"},
                "by_en": {"type": "string"},
            },
        },
        "current_location": {
            "type": "object",
            "properties": {
                "museum_id": {"type": "string"},
                "museum_ar": {"type": "string"},
                "museum_en": {"type": "string"},
                "city_ar": {"type": "string"},
                "city_en": {"type": "string"},
                "country": {"type": "string"},
                "hall_id": {"type": "string"},
                "hall_ar": {"type": "string"},
                "hall_en": {"type": "string"},
            },
        },
        "description": {
            "type": "object",
            "properties": {
                "ar": {"type": "string"},
                "en": {"type": "string"},
                "ar_intro": {"type": "string"},
                "en_intro": {"type": "string"},
            },
        },
        "images": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["filename", "source", "license"],
                "properties": {
                    "filename": {"type": "string"},
                    "source_url": {"type": "string"},
                    "credit": {"type": "string"},
                    "license": {"type": "string"},
                    "width": {"type": "integer"},
                    "height": {"type": "integer"},
                    "is_primary": {"type": "boolean"},
                    "source": {"type": "string"},
                    "caption_ar": {"type": "string"},
                    "caption_en": {"type": "string"},
                },
            },
        },
        "sources": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "url": {"type": "string"},
                    "title": {"type": "string"},
                    "license": {"type": "string"},
                },
            },
        },
        "tags": {"type": "array", "items": {"type": "string"}},
        "related_ids": {"type": "array", "items": {"type": "string"}},
        "qa_pairs_ar": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "q": {"type": "string"},
                    "a": {"type": "string"},
                    "evidence": {"type": "string"},
                },
            },
        },
    },
}


def empty_record(artifact_id: str) -> dict:
    return {
        "id": artifact_id,
        "names": {"ar": "", "en": "", "alt_ar": [], "alt_en": []},
        "category": "",
        "period": {"ar": "", "en": "", "year_min": None, "year_max": None},
        "dynasty": {"ar": "", "en": ""},
        "material": [],
        "dimensions": {},
        "provenance": {"site_ar": "", "site_en": ""},
        "discovery": {"year": None, "by_ar": "", "by_en": ""},
        "current_location": {
            "museum_id": "",
            "museum_ar": "",
            "museum_en": "",
            "city_ar": "",
            "city_en": "",
            "country": "",
            "hall_id": "",
            "hall_ar": "",
            "hall_en": "",
        },
        "description": {"ar": "", "en": "", "ar_intro": "", "en_intro": ""},
        "images": [],
        "sources": [],
        "tags": [],
        "related_ids": [],
        "qa_pairs_ar": [],
    }
