"""Tests for Part7 effective stats."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from effective_stats import (  # noqa: E402
    CONSUMABLE_DEFAULT_WEIGHT,
    CONSUMABLE_GRADE,
    REFERENCE_ACTION_INDEX,
    armor_stats,
    best_weapon_oneshot,
    consumable_at_use,
    consumable_dpc,
    consumable_dpc_at_use,
    consumable_reference,
    grade_for_mana,
    weapon_damage,
)
from balance.loader import get_constants  # noqa: E402

_BC = get_constants()


class TestGradeForMana(unittest.TestCase):
    def test_equipment_bands(self) -> None:
        bands = _BC.grade_bands
        self.assertEqual(grade_for_mana(1), bands[0][1])
        self.assertEqual(grade_for_mana(3), bands[0][1])
        self.assertEqual(grade_for_mana(4), bands[1][1])
        self.assertEqual(grade_for_mana(6), bands[1][1])
        self.assertEqual(grade_for_mana(7), bands[2][1])
        self.assertEqual(grade_for_mana(9), bands[2][1])
        self.assertEqual(grade_for_mana(10), bands[3][1])
        self.assertEqual(grade_for_mana(12), bands[3][1])


class TestCombatStats(unittest.TestCase):
    def test_weapon_mid_mid(self) -> None:
        b, dmg, dpc = weapon_damage(42, 7, 4, 6)
        self.assertEqual(b, 6)
        self.assertEqual(dmg, 36)
        self.assertAlmostEqual(dpc, 9.0)

    def test_armor_matches_weapon_coef(self) -> None:
        b, defense, armor, dpc = armor_stats(42, 7, 4, 6)
        self.assertEqual(b, 6)
        self.assertEqual(defense, 6)
        self.assertEqual(armor, 36)
        self.assertAlmostEqual(dpc, 9.0)

    def test_consumable_coef_equals_wait(self) -> None:
        self.assertEqual(CONSUMABLE_GRADE, _BC.consumable_grade)
        self.assertEqual(CONSUMABLE_DEFAULT_WEIGHT, _BC.consumable_default_weight)
        # Q=36 -> B=12; 中行動+中量 wait=4 -> effect=48, dpc=12
        b, wait, coef, effect, dpc = consumable_reference(36)
        self.assertEqual(b, 12)
        self.assertEqual(wait, 4)
        self.assertEqual(coef, wait)
        self.assertEqual(effect, 48)
        self.assertAlmostEqual(dpc, 12.0)
        self.assertAlmostEqual(consumable_dpc(36), 12.0)

    def test_consumable_dpc_flat_across_actions(self) -> None:
        for ai in range(4):
            _, dpc = consumable_dpc_at_use(ai, "中量", 36)
            self.assertAlmostEqual(dpc, 12.0)
        # One-shot scales with wait
        _, _, _, effect_light, _ = consumable_at_use(36, 0, "中量")
        _, _, _, effect_special, _ = consumable_at_use(36, 3, "中量")
        self.assertEqual(effect_light, 12 * 3)
        self.assertEqual(effect_special, 12 * 6)

    def test_best_weapon_oneshot(self) -> None:
        action, wait, coef, b, dmg, _ = best_weapon_oneshot(42, 7, "重量")
        self.assertEqual(action, "特行動")
        self.assertEqual(b, 6)
        self.assertEqual(dmg, 6 * 11)


if __name__ == "__main__":
    unittest.main()
