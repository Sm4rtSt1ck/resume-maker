"""Field specifications for the interactive data editor.

The editor is driven entirely by these specs: `build_specs` merges the keys
found in template.json (so fields missing from the data file still show up)
with the keys of the data file being edited, and infers a spec for each
value. Per-key customisation lives in `OVERRIDES` — adding a new field to
template.json is enough for it to appear in the editor.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from modules.consts import BASE_DIR

SKILL_LEVELS = ["low", "mid", "high"]
WORK_FORMATS = ["office", "hybrid", "remote"]
TITLE_FIELD_CANDIDATES = ("place", "name", "title", "specialty")


def pretty(key: str) -> str:
    return key.replace("_", " ").strip().capitalize()


@dataclass
class FieldSpec:
    key: str

    @property
    def label(self) -> str:
        return pretty(self.key)


@dataclass
class TextSpec(FieldSpec):
    """A single editable line of text."""


@dataclass
class MultiChoiceSpec(FieldSpec):
    """A fixed set of options, any subset of which can be checked."""

    options: list[str] = field(default_factory=list)


@dataclass
class StrListSpec(FieldSpec):
    """A growable list of plain strings (e.g. hobbies)."""


@dataclass
class ObjListSpec(FieldSpec):
    """A growable list of records (e.g. education, work_experience)."""

    item_fields: list[str] = field(default_factory=list)
    title_field: str = ""


@dataclass
class DictSpec(FieldSpec):
    """A fixed mapping of scalar values."""

    fields: list[str] = field(default_factory=list)


@dataclass
class LeveledDictSpec(FieldSpec):
    """A name -> level mapping (e.g. skills), one column per level."""

    levels: list[str] = field(default_factory=lambda: list(SKILL_LEVELS))


def _unique(*iterables) -> list:
    seen = []
    for iterable in iterables:
        for item in iterable or ():
            if item not in seen:
                seen.append(item)
    return seen


def _str_items(value) -> list[str]:
    return [item for item in (value or []) if isinstance(item, str)]


def _record_fields(*lists_of_dicts) -> list[str]:
    fields = []
    for items in lists_of_dicts:
        for item in items or ():
            if isinstance(item, dict):
                for key in item:
                    if key not in fields:
                        fields.append(key)
    return fields


OVERRIDES = {
    "work_formats": lambda key, value, ref: MultiChoiceSpec(
        key, options=_unique(_str_items(ref), WORK_FORMATS, _str_items(value))
    ),
    "skills": lambda key, value, ref: LeveledDictSpec(key),
}


def infer_spec(key: str, value, reference_value=None) -> FieldSpec:
    if key in OVERRIDES:
        return OVERRIDES[key](key, value, reference_value)

    sample = value if value not in (None, "", [], {}) else reference_value
    if isinstance(sample, list):
        has_records = any(isinstance(item, dict) for item in (value or [])) or \
            any(isinstance(item, dict) for item in (reference_value or []))
        if has_records:
            fields = _record_fields(reference_value, value) or ["value"]
            title = next((f for f in TITLE_FIELD_CANDIDATES if f in fields), fields[0])
            return ObjListSpec(key, item_fields=fields, title_field=title)
        return StrListSpec(key)
    if isinstance(sample, dict):
        ref_dict = reference_value if isinstance(reference_value, dict) else None
        val_dict = value if isinstance(value, dict) else None
        return DictSpec(key, fields=_unique(ref_dict, val_dict))
    return TextSpec(key)


def load_reference() -> dict:
    try:
        with open(BASE_DIR / "template.json", encoding="utf-8") as f:
            reference = json.load(f)
        return reference if isinstance(reference, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def build_specs(data: dict) -> list[FieldSpec]:
    reference = load_reference()
    keys = _unique(reference, data)
    return [infer_spec(key, data.get(key), reference.get(key)) for key in keys]
