# Balance constants

数値の正本は **`constants.yaml`** です。

## MkDocs（`docs/balance.md`）

本文は Markdown のまま書き、数値だけ `{dotted.key}` トークンにします。`mkdocs build` 時に `hooks/balance_tokens.py` が YAML から展開します。

例:

```markdown
| 等級 | {consumable.grade} |
| 重量 | {consumable.default_weight} |
| 重量・中行動 | {weapon.heavy.mid.pair} |
```

未知のトークンは **そのまま残り**、ビルド時に警告が出ます。

## シミュレータ

`sim/part7` などは [`balance/loader.py`](../balance/loader.py) 経由で `constants.yaml` を読みます。

## キー一覧（主要）

| プレフィックス | 内容 |
| :-- | :-- |
| `consumable.*` | 消耗品等級・重量 |
| `weapon.{light\|mid\|heavy}.{light\|mid\|heavy\|special}.*` | 待機・係数・`pair`（`3 / 4` 形式） |
| `armor.evasion.*` | 回避値 |
| `equipment.band.*` | マナ帯ごとの等級 |
| `phase1.*` | 錬金ペース仮定 |
| `part7_ref.n{N}.*` | Part7 典型値（再シム後に YAML を更新） |
