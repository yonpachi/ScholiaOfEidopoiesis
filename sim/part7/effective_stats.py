"""Part7: effective combat stats from Part6 quality + balance equipment tables."""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from balance.loader import ACTIONS_JA, get_constants  # noqa: E402

_bc = get_constants()

ACTIONS = ACTIONS_JA
WEAPON_TABLE = _bc.weapon_table
ARMOR_TABLE = _bc.weapon_table
OPTIMAL_ACTION_INDEX = _bc.optimal_action_index
BASE_ACTION_WAITS = _bc.base_action_waits
ITEM_WEIGHT_CORRECTION = _bc.item_weight_correction
REFERENCE_ATTEMPT = _bc.reference_attempt
QUALITY_PERCENTILES = ("p50", "p90")
CONSUMABLE_GRADE = _bc.consumable_grade
CONSUMABLE_DEFAULT_WEIGHT = _bc.consumable_default_weight
REFERENCE_ACTION_INDEX = 1  # 中行動 — summary / DPC chart reference


def grade_for_mana(n_extra: int) -> int:
    """Map mana count (n_extra) to equipment grade (higher = cruder design)."""
    return _bc.grade_for_mana(n_extra)


def base_effect(quality: int, grade: int) -> int:
    return quality // grade


def consumable_at_use(
    quality: int,
    action_index: int,
    item_weight: str,
    *,
    grade: int = CONSUMABLE_GRADE,
) -> tuple[int, int, int, int, float]:
    """Effect = B × wait (coef equals wait); DPC = B."""
    b = base_effect(quality, grade)
    wait = item_use_wait(action_index, item_weight)
    coef = wait
    effect = b * coef
    dpc = float(b)
    return b, wait, coef, effect, dpc


def consumable_reference(
    quality: int, *, grade: int = CONSUMABLE_GRADE
) -> tuple[int, int, int, int, float]:
    return consumable_at_use(quality, REFERENCE_ACTION_INDEX, CONSUMABLE_DEFAULT_WEIGHT, grade=grade)


def consumable_dpc(quality: int) -> float:
    return consumable_reference(quality)[4]


def item_use_wait(action_index: int, item_weight: str) -> int:
    return BASE_ACTION_WAITS[action_index] + ITEM_WEIGHT_CORRECTION[item_weight]


def consumable_dpc_at_use(action_index: int, item_weight: str, quality: int) -> tuple[int, float]:
    _, wait, _, _, dpc = consumable_at_use(quality, action_index, item_weight)
    return wait, dpc


def best_weapon_oneshot(
    quality: int, grade: int, weight: str
) -> tuple[str, int, int, int, int, float]:
    """Return best one-shot damage for a weapon weight (max over action tiers)."""
    best: tuple[str, int, int, int, int, float] | None = None
    for action, (wait, coef) in zip(ACTIONS, WEAPON_TABLE[weight], strict=True):
        b, dmg, dpc = weapon_damage(quality, grade, wait, coef)
        if best is None or dmg > best[4]:
            best = (action, wait, coef, b, dmg, dpc)
    assert best is not None
    return best


def best_armor_oneshot(
    quality: int, grade: int, weight: str
) -> tuple[str, int, int, int, int, int, float]:
    """Return best one-shot `<装甲>` for a weight (defense = B is action-invariant)."""
    best: tuple[str, int, int, int, int, int, float] | None = None
    for action, (wait, coef) in zip(ACTIONS, ARMOR_TABLE[weight], strict=True):
        b, defense, armor, dpc = armor_stats(quality, grade, wait, coef)
        if best is None or armor > best[5]:
            best = (action, wait, coef, b, defense, armor, dpc)
    assert best is not None
    return best


def weapon_damage(quality: int, grade: int, wait: int, atk_coef: int) -> tuple[int, int, float]:
    b = base_effect(quality, grade)
    dmg = b * atk_coef
    dpc = dmg / wait if wait > 0 else 0.0
    return b, dmg, dpc


def armor_stats(quality: int, grade: int, wait: int, def_coef: int) -> tuple[int, int, int, float]:
    b = base_effect(quality, grade)
    defense = b
    armor = b * def_coef
    dpc = armor / wait if wait > 0 else 0.0
    return b, defense, armor, dpc


@dataclass(frozen=True)
class QualityRow:
    n_extra: int
    attempt: int
    p50: int
    p90: int
    p99: int


def load_quality_progression(csv_path: Path) -> list[QualityRow]:
    rows: list[QualityRow] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(
                QualityRow(
                    n_extra=int(row["n_extra"]),
                    attempt=int(row["attempt"]),
                    p50=int(row["p50"]),
                    p90=int(row["p90"]),
                    p99=int(row["p99"]),
                )
            )
    return rows


def quality_at(row: QualityRow, percentile: str) -> int:
    return getattr(row, percentile)


def run_effective_stats(out_dir: Path) -> tuple[Path, Path, Path, Path]:
    csv_path = out_dir / "csv" / "quality_progression.csv"
    if not csv_path.is_file():
        raise FileNotFoundError(f"missing Part6 output: {csv_path}")

    quality_rows = load_quality_progression(csv_path)
    csv_sub = out_dir / "csv"
    csv_sub.mkdir(parents=True, exist_ok=True)

    detail_path = csv_sub / "effective_stats_detail.csv"
    summary_path = csv_sub / "effective_stats_summary.csv"
    oneshot_path = csv_sub / "effective_stats_oneshot.csv"
    optimal_path = csv_sub / "effective_stats_optimal_oneshot.csv"

    detail_fields = [
        "n_extra",
        "grade",
        "attempt",
        "percentile",
        "quality",
        "kind",
        "weight",
        "action",
        "wait",
        "coef",
        "B",
        "defense",
        "value",
        "dpc",
    ]
    summary_fields = [
        "n_extra",
        "equipment_grade",
        "attempt",
        "percentile",
        "quality",
        "consumable_grade",
        "consumable_weight",
        "consumable_action",
        "consumable_B",
        "consumable_wait",
        "consumable_effect",
        "consumable_dpc",
        "B",
        "weapon_weight",
        "weapon_action",
        "weapon_wait",
        "weapon_coef",
        "weapon_damage",
        "weapon_dpc",
        "armor_weight",
        "armor_action",
        "armor_wait",
        "armor_coef",
        "defense",
        "armor_strength",
        "armor_dpc",
        "weapon_dpc_per_consumable_dpc",
        "weapon_optimal_weight",
        "weapon_optimal_action",
        "weapon_optimal_damage",
        "weapon_optimal_dpc",
    ]
    oneshot_fields = [
        "n_extra",
        "equipment_grade",
        "attempt",
        "percentile",
        "quality",
        "kind",
        "weight",
        "action",
        "wait",
        "coef",
        "B",
        "defense",
        "oneshot_value",
        "dpc",
        "is_best_oneshot_for_weight",
    ]
    optimal_fields = [
        "n_extra",
        "equipment_grade",
        "attempt",
        "percentile",
        "quality",
        "consumable_effect",
        "consumable_dpc_ref",
        "equipment_B",
        "defense",
    ]
    for weight in WEAPON_TABLE:
        optimal_fields.extend(
            [
                f"weapon_{weight}_best_action",
                f"weapon_{weight}_best_wait",
                f"weapon_{weight}_best_coef",
                f"weapon_{weight}_best_damage",
                f"weapon_{weight}_best_dpc",
                f"armor_{weight}_best_action",
                f"armor_{weight}_best_wait",
                f"armor_{weight}_best_coef",
                f"armor_{weight}_best_armor",
                f"armor_{weight}_best_dpc",
            ]
        )

    detail_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    oneshot_rows: list[dict[str, object]] = []
    optimal_rows: list[dict[str, object]] = []

    by_n_attempt: dict[tuple[int, int], QualityRow] = {
        (r.n_extra, r.attempt): r for r in quality_rows
    }

    n_values = sorted({r.n_extra for r in quality_rows})

    for n_extra in n_values:
        equip_grade = grade_for_mana(n_extra)
        for attempt in sorted({r.attempt for r in quality_rows if r.n_extra == n_extra}):
            row = by_n_attempt.get((n_extra, attempt))
            if row is None:
                continue
            for percentile in QUALITY_PERCENTILES:
                q = quality_at(row, percentile)

                cons_b, cons_wait, cons_coef, cons_val, cons_dpc = consumable_reference(q)
                equip_b = base_effect(q, equip_grade)

                for item_weight in ITEM_WEIGHT_CORRECTION:
                    for ai, action in enumerate(ACTIONS):
                        b, wait, coef, effect, dpc = consumable_at_use(q, ai, item_weight)
                        row_common = {
                            "n_extra": n_extra,
                            "equipment_grade": equip_grade,
                            "attempt": attempt,
                            "percentile": percentile,
                            "quality": q,
                            "weight": item_weight,
                            "action": action,
                            "wait": wait,
                            "coef": coef,
                            "B": b,
                            "defense": "",
                            "dpc": round(dpc, 4),
                        }
                        oneshot_rows.append(
                            {
                                **row_common,
                                "kind": "consumable",
                                "oneshot_value": effect,
                                "is_best_oneshot_for_weight": "",
                            }
                        )
                        detail_rows.append(
                            {
                                **row_common,
                                "grade": CONSUMABLE_GRADE,
                                "kind": "consumable",
                                "value": effect,
                            }
                        )

                for weight, slots in WEAPON_TABLE.items():
                    weapon_entries: list[tuple[str, int, int, int, int, float]] = []
                    for action, (wait, coef) in zip(ACTIONS, slots, strict=True):
                        b, dmg, dpc = weapon_damage(q, equip_grade, wait, coef)
                        weapon_entries.append((action, wait, coef, b, dmg, dpc))
                    best_weapon_action = max(weapon_entries, key=lambda e: e[4])[0]
                    for action, wait, coef, b, dmg, dpc in weapon_entries:
                        detail_rows.append(
                            {
                                "n_extra": n_extra,
                                "grade": equip_grade,
                                "attempt": attempt,
                                "percentile": percentile,
                                "quality": q,
                                "kind": "weapon",
                                "weight": weight,
                                "action": action,
                                "wait": wait,
                                "coef": coef,
                                "B": b,
                                "defense": "",
                                "value": dmg,
                                "dpc": round(dpc, 4),
                            }
                        )
                        oneshot_rows.append(
                            {
                                "n_extra": n_extra,
                                "equipment_grade": equip_grade,
                                "attempt": attempt,
                                "percentile": percentile,
                                "quality": q,
                                "kind": "weapon",
                                "weight": weight,
                                "action": action,
                                "wait": wait,
                                "coef": coef,
                                "B": b,
                                "defense": "",
                                "oneshot_value": dmg,
                                "dpc": round(dpc, 4),
                                "is_best_oneshot_for_weight": action == best_weapon_action,
                            }
                        )

                for weight, slots in ARMOR_TABLE.items():
                    armor_entries: list[tuple[str, int, int, int, int, int, float]] = []
                    for action, (wait, coef) in zip(ACTIONS, slots, strict=True):
                        b, defense, armor, dpc = armor_stats(q, equip_grade, wait, coef)
                        armor_entries.append((action, wait, coef, b, defense, armor, dpc))
                    best_armor_action = max(armor_entries, key=lambda e: e[5])[0]
                    for action, wait, coef, b, defense, armor, dpc in armor_entries:
                        detail_rows.append(
                            {
                                "n_extra": n_extra,
                                "grade": equip_grade,
                                "attempt": attempt,
                                "percentile": percentile,
                                "quality": q,
                                "kind": "armor",
                                "weight": weight,
                                "action": action,
                                "wait": wait,
                                "coef": coef,
                                "B": b,
                                "defense": defense,
                                "value": armor,
                                "dpc": round(dpc, 4),
                            }
                        )
                        oneshot_rows.append(
                            {
                                "n_extra": n_extra,
                                "equipment_grade": equip_grade,
                                "attempt": attempt,
                                "percentile": percentile,
                                "quality": q,
                                "kind": "armor",
                                "weight": weight,
                                "action": action,
                                "wait": wait,
                                "coef": coef,
                                "B": b,
                                "defense": defense,
                                "oneshot_value": armor,
                                "dpc": round(dpc, 4),
                                "is_best_oneshot_for_weight": action == best_armor_action,
                            }
                        )

                b_mid, dmg_mid, dpc_mid = weapon_damage(
                    q, equip_grade, *WEAPON_TABLE["中量"][1]
                )
                _, defense_mid, armor_mid, armor_dpc_mid = armor_stats(
                    q, equip_grade, *ARMOR_TABLE["中量"][1]
                )

                opt_weight = "中量"
                opt_idx = OPTIMAL_ACTION_INDEX[opt_weight]
                opt_wait, opt_coef = WEAPON_TABLE[opt_weight][opt_idx]
                _, dmg_opt, dpc_opt = weapon_damage(q, equip_grade, opt_wait, opt_coef)

                opt_row: dict[str, object] = {
                    "n_extra": n_extra,
                    "equipment_grade": equip_grade,
                    "attempt": attempt,
                    "percentile": percentile,
                    "quality": q,
                    "consumable_effect": cons_val,
                    "consumable_dpc_ref": round(cons_dpc, 4),
                    "equipment_B": equip_b,
                    "defense": equip_b,
                }
                for weight in WEAPON_TABLE:
                    w_act, w_wait, w_coef, w_b, w_dmg, w_dpc = best_weapon_oneshot(
                        q, equip_grade, weight
                    )
                    a_act, a_wait, a_coef, a_b, a_def, a_armor, a_dpc = best_armor_oneshot(
                        q, equip_grade, weight
                    )
                    opt_row[f"weapon_{weight}_best_action"] = w_act
                    opt_row[f"weapon_{weight}_best_wait"] = w_wait
                    opt_row[f"weapon_{weight}_best_coef"] = w_coef
                    opt_row[f"weapon_{weight}_best_damage"] = w_dmg
                    opt_row[f"weapon_{weight}_best_dpc"] = round(w_dpc, 4)
                    opt_row[f"armor_{weight}_best_action"] = a_act
                    opt_row[f"armor_{weight}_best_wait"] = a_wait
                    opt_row[f"armor_{weight}_best_coef"] = a_coef
                    opt_row[f"armor_{weight}_best_armor"] = a_armor
                    opt_row[f"armor_{weight}_best_dpc"] = round(a_dpc, 4)
                optimal_rows.append(opt_row)

                summary_rows.append(
                    {
                        "n_extra": n_extra,
                        "equipment_grade": equip_grade,
                        "attempt": attempt,
                        "percentile": percentile,
                        "quality": q,
                        "consumable_grade": CONSUMABLE_GRADE,
                        "consumable_weight": CONSUMABLE_DEFAULT_WEIGHT,
                        "consumable_action": ACTIONS[REFERENCE_ACTION_INDEX],
                        "consumable_B": cons_b,
                        "consumable_wait": cons_wait,
                        "consumable_effect": cons_val,
                        "consumable_dpc": round(cons_dpc, 4),
                        "B": b_mid,
                        "weapon_weight": "中量",
                        "weapon_action": "中行動",
                        "weapon_wait": WEAPON_TABLE["中量"][1][0],
                        "weapon_coef": WEAPON_TABLE["中量"][1][1],
                        "weapon_damage": dmg_mid,
                        "weapon_dpc": round(dpc_mid, 4),
                        "armor_weight": "中量",
                        "armor_action": "中行動",
                        "armor_wait": ARMOR_TABLE["中量"][1][0],
                        "armor_coef": ARMOR_TABLE["中量"][1][1],
                        "defense": defense_mid,
                        "armor_strength": armor_mid,
                        "armor_dpc": round(armor_dpc_mid, 4),
                        "weapon_dpc_per_consumable_dpc": (
                            round(dpc_mid / cons_dpc, 4) if cons_dpc > 0 else ""
                        ),
                        "weapon_optimal_weight": opt_weight,
                        "weapon_optimal_action": ACTIONS[opt_idx],
                        "weapon_optimal_damage": dmg_opt,
                        "weapon_optimal_dpc": round(dpc_opt, 4),
                    }
                )

    _write_csv(detail_path, detail_fields, detail_rows)
    _write_csv(summary_path, summary_fields, summary_rows)
    _write_csv(oneshot_path, oneshot_fields, oneshot_rows)
    _write_csv(optimal_path, optimal_fields, optimal_rows)

    print(f"    CSV: {detail_path.name}")
    print(f"    CSV: {summary_path.name}")
    print(f"    CSV: {oneshot_path.name}")
    print(f"    CSV: {optimal_path.name}")
    return detail_path, summary_path, oneshot_path, optimal_path


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
