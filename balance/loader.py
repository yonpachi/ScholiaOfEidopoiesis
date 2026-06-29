"""Load balance/constants.yaml for MkDocs hooks and simulators."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DEFAULT_PATH = Path(__file__).resolve().parent / "constants.yaml"

WEIGHT_KEYS = ("light", "mid", "heavy")
ACTION_KEYS = ("light", "mid", "heavy", "special")
WEIGHT_EN_TO_JA = {"light": "軽量", "mid": "中量", "heavy": "重量"}
ACTION_EN_TO_JA = {
    "light": "軽行動",
    "mid": "中行動",
    "heavy": "重行動",
    "special": "特行動",
}
ACTIONS_JA = tuple(ACTION_EN_TO_JA[k] for k in ACTION_KEYS)
WEIGHTS_JA = tuple(WEIGHT_EN_TO_JA[k] for k in WEIGHT_KEYS)


def _parse_weight_correction(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value).strip().replace("±", "").replace("+", "")
    return int(text) if text.lstrip("-").isdigit() else 0


def _flatten(prefix: str, value: Any, out: dict[str, str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            _flatten(path, child, out)
        return
    if isinstance(value, list):
        for i, child in enumerate(value):
            _flatten(f"{prefix}.{i}", child, out)
        return
    if isinstance(value, float):
        if value == int(value):
            out[prefix] = str(int(value))
        else:
            text = f"{value:.4f}".rstrip("0").rstrip(".")
            out[prefix] = text
        return
    out[prefix] = str(value)


def _format_wait_coef(wait: int, coef: int) -> str:
    return f"{wait} / {coef}"


def build_doc_tokens(data: dict[str, Any]) -> dict[str, str]:
    """Build {dotted.key} expansion map for MkDocs."""
    tokens: dict[str, str] = {}
    _flatten("", data, tokens)

    weapon = data.get("weapon", {})
    for weight in WEIGHT_KEYS:
        for action in ACTION_KEYS:
            slot = weapon.get(weight, {}).get(action, {})
            if not slot:
                continue
            base = f"weapon.{weight}.{action}"
            tokens[f"{base}.pair"] = _format_wait_coef(slot["wait"], slot["coef"])

    armor_evasion = data.get("armor", {}).get("evasion", {})
    for weight in WEIGHT_KEYS:
        tokens[f"armor.evasion.{weight}"] = str(armor_evasion[weight])

    bands = data.get("equipment", {}).get("grade_by_n_extra", [])
    for band in bands:
        name = band["band"]
        tokens[f"equipment.band.{name}.grade"] = str(band["grade"])
        tokens[f"equipment.band.{name}.mana_range"] = str(band["mana_range"])

    tokens["equipment.broken_grade"] = str(data.get("equipment", {}).get("broken_grade", 1))

    for weight in WEIGHT_KEYS:
        opt = data.get("dpc_optimal", {}).get(weight, {})
        tokens[f"dpc_optimal.{weight}.action"] = str(opt.get("action", ""))
        ratio = opt.get("ratio", 0)
        tokens[f"dpc_optimal.{weight}.ratio"] = (
            str(int(ratio)) if ratio == int(ratio) else f"{ratio:.2f}"
        )

    phase1 = data.get("phase1", {})
    tokens["phase1.tag_use_percent"] = str(int(phase1.get("tag_use_ratio", 0.6) * 100))
    tokens["phase1.tag_stock_percent"] = str(int(phase1.get("tag_stock_ratio", 0.4) * 100))

    for i, row in enumerate(data.get("part7_ref", {}).get("rows", [])):
        for key, val in row.items():
            tokens[f"part7_ref.rows.{i}.{key}"] = str(val)
        n = row.get("n_extra")
        if n is not None:
            for key, val in row.items():
                tokens[f"part7_ref.n{n}.{key}"] = str(val)

    return tokens


def load_raw(path: Path | None = None) -> dict[str, Any]:
    constants_path = path or DEFAULT_PATH
    if not constants_path.is_file():
        raise FileNotFoundError(f"balance constants not found: {constants_path}")
    with open(constants_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"invalid balance constants: {constants_path}")
    return data


@dataclass(frozen=True)
class BalanceConstants:
    raw: dict[str, Any]
    weapon_table: dict[str, list[tuple[int, int]]]
    base_action_waits: tuple[int, int, int, int]
    item_weight_correction: dict[str, int]
    consumable_grade: int
    consumable_default_weight: str
    reference_attempt: int
    optimal_action_index: dict[str, int]
    grade_bands: tuple[tuple[int, int], ...]

    def grade_for_mana(self, n_extra: int) -> int:
        for n_extra_max, grade in self.grade_bands:
            if n_extra <= n_extra_max:
                return grade
        return self.grade_bands[-1][1]


_cached: BalanceConstants | None = None


def _build_weapon_table(data: dict[str, Any]) -> dict[str, list[tuple[int, int]]]:
    weapon = data.get("weapon", {})
    table: dict[str, list[tuple[int, int]]] = {}
    for weight_en in WEIGHT_KEYS:
        weight_ja = WEIGHT_EN_TO_JA[weight_en]
        slots: list[tuple[int, int]] = []
        for action_en in ACTION_KEYS:
            slot = weapon[weight_en][action_en]
            slots.append((slot["wait"], slot["coef"]))
        table[weight_ja] = slots
    return table


def _build_optimal_action_index(data: dict[str, Any]) -> dict[str, int]:
    action_to_index = {name: i for i, name in enumerate(ACTIONS_JA)}
    optimal: dict[str, int] = {}
    for weight_en in WEIGHT_KEYS:
        weight_ja = WEIGHT_EN_TO_JA[weight_en]
        action_name = data["dpc_optimal"][weight_en]["action"]
        optimal[weight_ja] = action_to_index[action_name]
    return optimal


def load_constants(path: Path | None = None) -> BalanceConstants:
    data = load_raw(path)

    waits = data["base_action_wait"]
    base_action_waits = tuple(waits[k] for k in ACTION_KEYS)

    corrections = data["item_weight_correction"]
    item_weight_correction = {
        WEIGHT_EN_TO_JA[k]: _parse_weight_correction(corrections[k]) for k in WEIGHT_KEYS
    }

    grade_bands = tuple(
        (band["n_extra_max"], band["grade"])
        for band in data["equipment"]["grade_by_n_extra"]
    )

    return BalanceConstants(
        raw=data,
        weapon_table=_build_weapon_table(data),
        base_action_waits=base_action_waits,
        item_weight_correction=item_weight_correction,
        consumable_grade=int(data["consumable"]["grade"]),
        consumable_default_weight=str(data["consumable"]["default_weight"]),
        reference_attempt=int(data["phase1"]["part7_reference_attempt"]),
        optimal_action_index=_build_optimal_action_index(data),
        grade_bands=grade_bands,
    )


def get_constants(path: Path | None = None, *, reload: bool = False) -> BalanceConstants:
    global _cached
    if _cached is None or reload or path is not None:
        _cached = load_constants(path)
    return _cached
