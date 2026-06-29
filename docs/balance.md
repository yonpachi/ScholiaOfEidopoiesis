ルール、データ作成時の基準として確定したものを順に記載していく

---

## 前提

このシステムでは **d4, d6, d8, d10, d12, d20** を使うことを前提とする

それぞれダイスに対して、以下のように設定する

| 属性 | ダイス | 反応条件 | 反応効果                                    |
| :--: | :----: | :------: | :------------------------------------------ |
|  火  |   d4   |  3以上   | **延焼** — 自身を4にし、d4を1個追加して振る |
|  土  |   d6   |    6     | **変動** — 他ダイス1個を循環±1または±2      |
|  風  |   d8   |    8     | **旋回** — 他ダイス1個を半回転              |
|  水  |  d20   |    20    | **流転** — 他ダイス1個を振り直す            |
|  闇  |  d10   |    10    | **覚醒** — 他ダイス1個を裏返す              |
|  光  |  d12   |    12    | **昇華** — 他ダイス1個を最大値にする        |

---

## 達成値算出

達成値算出は以下のように行う

### 1. ダイスロール

1d10を基本とし、マナに応じた **ダイス** を加えて振る

ダイス \(d\) について、**面数** を \(s\)、**出目** を \(f\) とし、\( d(s,f) \)とまとめて扱う

ダイスの集合を **プール** \(P\) とし、 **n** 個のダイスの集合を\(P_n = \bigl(d(s_1,f_1),\ldots,d(s_n,f_n)\bigr)\)とする

プール内の各ダイスは互いに区別する

### 2. 反応

反応はダイスの出目 \(f\) およびプール \(P\) のみを更新する

プール \(P\) の各ダイスは、**未反応** か **反応済み** のいずれかである

プール内の未反応ダイスの集合を \(Q\) 、反応済みダイスの集合を \(R\) とする
\( \bigl( \ Q \cap R = \varnothing, \ Q \cup R = P \ \bigr) \)

上記の表の通り、ダイスには面数 \(s\) ごとに閾値が存在する

これを **反応条件** \(\tau(d) := \tau(s(d), f(d))\)とする

\(
\tau(s,f) = \begin{cases}
1 & s = 4,\ f \geq 3 \\
1 & s = 6,\ f = 6 \\
1 & s = 8,\ f = 8 \\
1 & s = 10,\ f = 10 \\
1 & s = 12,\ f = 12 \\
1 & s = 20,\ f = 20 \\
0 & \text{上記以外}
\end{cases}
\)

#### 出目操作

\(
\begin{aligned}
循環\delta： & \mathrm{cyc}(s,f,\delta) = ((f-1+\delta) \bmod s) + 1 \\
反転： &\mathrm{inv}(s,f) = s + 1 - f \\
半回転： &\mathrm{half}(s,f) = \mathrm{cyc}(s,f,s/2) \\
振り足し： &\mathrm{roll}(s) \sim \mathrm{Unif}\{1,\ldots,s\}
\end{aligned}
\)

#### 各属性の反応

\(d' \in P \setminus \{d\}\) は効果ごとに選ぶ

\(\tau(s(d), f(d)) = 1\) のとき、\(s(d)\) により:

\(
\begin{aligned}
s(d)=4:\ & f(d) \leftarrow 4;\
  d' \leftarrow \mathrm{roll}(4);\
  P \leftarrow P \cup \{d'\},\ Q \leftarrow Q \cup \{d'\} \\
s(d)=6:\ & f(d') \leftarrow \mathrm{cyc}(s(d'), f(d'), \delta),
  \ \delta \in \{\pm 1, \pm 2\} \\
s(d)=8:\ & f(d') \leftarrow \mathrm{half}(s(d'), f(d')) \\
s(d)=20:\ & f(d') \leftarrow \mathrm{roll}(s(d')) \\
s(d)=10:\ & f(d') \leftarrow \mathrm{inv}(s(d'), f(d')) \\
s(d)=12:\ & f(d') \leftarrow s(d')
\end{aligned}
\)

#### 反応ループ

\(
(P, Q, R) \leftarrow (P_n,\, P_n,\, \varnothing)
\)

\(
\begin{aligned}
&\text{while} \exists d \in Q,\ \tau(d) = 1: \\
&\quad d \in Q \text{ を選ぶ（}\tau(d)=1\text{）} \\
&\quad \text{各属性の反応を } d \text{ に適用し、} f \text{ および } P,\, Q \text{ を更新} \\
&\quad Q \leftarrow Q \setminus \{d\},\quad R \leftarrow R \cup \{d\}
\end{aligned}
\)

\(\forall d \in Q,\ \tau(d) = 0\) になった時点で §3 へ進む。各反応の前後で \(Q \cap R = \varnothing\)、\(Q \cup R = P\) を保つ。

### 3. 出目と点数の変換

d4,d6,d8,d10,d12,d20を同時に扱えるルールにするために、出目の読み方を以下の通りに設定する

\( v(s,f) =
\begin{cases}
{} & -1 & s \neq 20, \ f=1 \\
{} & -1 & s=20,\ f \leq 3 \\
{} & \lfloor f/2 \rfloor & s=20,\ f > 3 \\
{} & f & 上記以外
\end{cases}
\)


現行の設定で、基本４ダイス間は大体強さが揃っていて、4ダイス＜闇＜光となっている

土が序盤弱め、後半強めとなっているが、特徴として許容

ここらへんはダイスシステムから自ずと決まった値なので、前提として据える

<img src="../data/part1.png" alt="part1" width="50%"><img src="../data/part2.png" alt="part1" width="50%">

---

## 種族の判定時効果(4)

上記のダイスシステムを前提に、各種族の判定時の特殊効果を作成

各種族につき１つの効果(ホムンクルスは３つ)をそれぞれ限界貢献度から算出し、ある程度の強さの整合性を取った

使用ダイス数が７個ぐらいで大体の強さが同じぐらいになるようになった

ホムンクルスと半霊が他と比べて、ダイス数が小さい時に弱く、多い時に強くなっているが、種族特徴として許容する

ホムンクルスについては、３つの能力の使用率が極端に分かれず、総合値も強くなりすぎないように調整

<img src="../data/part4-1.png" alt="part4-1" width="50%"><img src="../data/part4-2.png" alt="part4-2" width="50%">

---

## １マナ辺りの効果量(5)

ダイスシステム、判定時能力を元に、それぞれのダイス個数での期待値、上振れ値を算出した

基本的に判定は錬金でのみ行われる想定なので、ここでのダイスの期待値がそのまま品質、アイテムの効果値に相関する

現行のシステムだと大体１ダイス増えるごとに大体5.5上昇するので、それを前提としたゲームバランスにする必要がある

<div class="balance-side-by-side">

<div class="balance-side-by-side__chart">
<img src="../data/part5.png" alt="Part5">

上昇幅は avg(N) − avg(N−1)。N=1〜9の平均は+5.51。

</div>

<div class="balance-side-by-side__table">

<table>
<thead>
<tr><th>マナ数 N</th><th>期待値 (avg)</th><th>p90</th><th>p99</th><th>期待値の上昇幅</th></tr>
</thead>
<tbody>
<tr><td>0</td><td>6.60</td><td>10</td><td>12</td><td>—</td></tr>
<tr><td>1</td><td>11.80</td><td>18</td><td>28</td><td>+5.20</td></tr>
<tr><td>2</td><td>17.18</td><td>25</td><td>39</td><td>+5.38</td></tr>
<tr><td>3</td><td>22.71</td><td>33</td><td>49</td><td>+5.53</td></tr>
<tr><td>4</td><td>28.20</td><td>41</td><td>57</td><td>+5.49</td></tr>
<tr><td>5</td><td>33.69</td><td>48</td><td>66</td><td>+5.49</td></tr>
<tr><td>6</td><td>39.22</td><td>55</td><td>74</td><td>+5.53</td></tr>
<tr><td>7</td><td>44.73</td><td>63</td><td>81</td><td>+5.51</td></tr>
<tr><td>8</td><td>50.25</td><td>70</td><td>89</td><td>+5.52</td></tr>
<tr><td>9</td><td>55.82</td><td>76</td><td>97</td><td>+5.57</td></tr>
</tbody>
</table>

</div>

</div>

---

## アイテムの品質、効果量（[6](log.md#log-6)）

ランダムな種族、マナ種でそれぞれレシピを10回錬金した場合の品質の平均値を算出した

\( \text{アイテムの品質} = \text{熟練度} + \max(r_1, \ldots, r_k) \)

- 錬金値：レシピに指定されたマナ+1d10で判定を行った値
- 熟練度：現在のレシピで錬金を行った回数

難易度、失敗などの設定は一旦考えないものとする

<img src="../data/part6-1.png" alt="part6-1" width="33.33333%"><img src="../data/part6-2.png" alt="part6-2" width="33.33333%"><img src="../data/part6-3.png" alt="part6-3" width="33.33333%">

アイテムの品質については、錬金を行った回数(熟練度)＋今までの試行で採用した数値(錬金値)で確定

消耗品も装備品と同様に \(B = \lfloor \text{品質} / \text{等級} \rfloor\) を経由する。消耗品は **完成品に近い** 設計効率を想定し、テンプレートの等級を **低く**（数値を小さく）固定する（下記「消耗品の基準」）。

使用時の待機値は [戦闘](combat.md) と同様、**行動段階の基本待機値 ＋ アイテムの重量補正** とする。消耗品の **効果係数は常にその待機値と等しい**。

\[
\text{効果量} = B \times \text{待機値},\qquad
\text{消耗品 DPC} = \frac{B \times \text{待機値}}{\text{待機値}} = B
\]

行動帯によって **一撃の回復量** は増減するが、**カウントあたり効率（DPC）は常に \(B\)** である。装備品は **試作寄り** の設計効率を想定し、マナ帯に応じて等級を **高く**（数値を大きく）設定する（下記「マナ帯ごとの基準」）。装備品の DPC・典型火力は [PC実効値（Part7）](#pc実効値part7) を参照。

---

## 戦闘カウント

ダイス・品質に続く **第2層** の数値基準。タイムライン上の行動コストと装備の係数表を固定する。

数値の正本は [`balance/constants.yaml`](../balance/constants.yaml) です。本文中の `` `{dotted.key}` `` は MkDocs ビルド時に YAML から展開されます（[README](../balance/README.md)）。

行動の宣言・解決・ダメージ処理などの手順は [戦闘](combat.md) を、装備の重量・等級の一般説明は [錬金とアイテム](alchemy.md) を参照。

### タイムライン

戦闘は **0〜{timeline.count_max}** の **{timeline.counts}カウント** で構成するタイムライン上で進行する。

- 手番を終えたキャラクターは、行動の **待機値** ぶんコマを後方へ進める
- {timeline.count_max}を超えた分は次ラウンドの対応カウントへ繰り越す
- 探索中の戦闘は **簡易戦闘** とし、特記がなければ **{timeline.simple_combat_rounds}ラウンド** で終了する

### 行動段階

プレイしたカードの数字から **行動段階** を決める。行動段階は待機値と装備の係数を参照する。

| カードの数字 | A〜3 | 4〜7 | 8〜10 | J〜K |
| :----------: | :--: | :--: | :---: | :--: |
| 行動段階     | 軽行動 | 中行動 | 重行動 | 特行動 |

### 基本待機値

行動段階ごとに **基本待機値** を固定する。段階差は **1**、軽行動と特行動の比は **1:2** とする。

| 行動段階 | 軽行動 | 中行動 | 重行動 | 特行動 |
| :------: | :----: | :----: | :----: | :----: |
| 基本待機値 | {base_action_wait.light} | {base_action_wait.mid} | {base_action_wait.heavy} | {base_action_wait.special} |

アイテム・レシピの **使用**・ **想成** では、待機値を次式で求める。

\[
\text{待機値} = \text{基本待機値} + \text{重量補正}
\]

### 重量補正

| 重量 | 軽量 | 中量 | 重量 |
| :--: | :--: | :--: | :--: |
| 重量補正 | {item_weight_correction.light} | {item_weight_correction.mid} | {item_weight_correction.heavy} |

攻撃・防御・回避・離脱など装備品を参照する行動では、下記の装備テーブルに従い、行動段階と装備重量から待機値と係数を決める（テーブル左が待機値、右が係数）。

### 装備品の算出

装備品の基準効果量 \(B\) を

\[
B = \left\lfloor \frac{\text{品質}}{\text{等級}} \right\rfloor
\]

とする（端数切捨て）。

等級は **品質の数値を係数表に接続するための除数** である。固定した待機値・係数表（DPC 設計）を維持したまま、品質スケールの暴れを抑える。

### 等級

等級は **その設計・仕組みがどれだけ洗練されているか** を表す。数値が小さいほど設計効率が高く、同じ品質からより大きな \(B\) が得られる。

レア度や優劣そのものではなく、「試作に近いか／完成品に近いか」の目安として扱う。**消耗品は完成品側（等級低）**、**装備品は試作側（等級高）** をデフォルトとする。

#### 消耗品の基準

| 項目 | デフォルト |
| :-- | :--: |
| 等級 | {consumable.grade} |
| 重量 | {consumable.default_weight} |

効果係数は **使用時の待機値と常に等しい**（別表を持たない）。

#### 装備品：マナ帯ごとの基準

レシピのマナコスト帯を根底の目安とし、装備品テンプレートの等級を次のように固定する。

| マナ帯 | 目安 | 等級 |
| :----: | :--- | :--: |
| 序盤   | {equipment.band.early.mana_range} | {equipment.band.early.grade}    |
| 中盤   | {equipment.band.mid.mana_range} | {equipment.band.mid.grade}    |
| 終盤   | {equipment.band.late.mana_range} | {equipment.band.late.grade}    |
| 10+    | {equipment.band.tier10.mana_range}    | {equipment.band.tier10.grade}    |
| 壊れ   | —    | {equipment.broken_grade}    |

「壊れ」は帯の基準を超えて設計が極限まで洗練された装備向けの等級である。

#### 個別データでの調整

上記は **根底の目安** である。武器・防具に付与されている印記・条件付き効果・タグ由来の追加効果など、**数値以外の強み** がある場合は、等級を帯の基準より **1 段階良くする**（7→6 など、数値を小さくする）ことで、総合的な強さのバランスを取ってよい。

逆に、強力な効果文を持つ代わりに基礎火力を抑えたい場合は、等級を基準より **1 段階悪くする**（7→8 など、数値を大きくする）こともできる。

**武器**

\[
\text{ダメージ} = \left\lfloor B \times \text{攻撃係数} \right\rfloor
\]

| 重量／行動段階 | 軽行動 | 中行動 | 重行動 | 特行動 |
| :------------: | :----: | :----: | :----: | :----: |
| 軽量           | {weapon.light.light.pair}  | {weapon.light.mid.pair}  | {weapon.light.heavy.pair}  | {weapon.light.special.pair}  |
| 中量           | {weapon.mid.light.pair}  | {weapon.mid.mid.pair}  | {weapon.mid.heavy.pair}  | {weapon.mid.special.pair}  |
| 重量           | {weapon.heavy.light.pair}  | {weapon.heavy.mid.pair}  | {weapon.heavy.heavy.pair}  | {weapon.heavy.special.pair}  |

**防具**

\[
\text{防御値} = B,\qquad
\text{`<装甲>` の強度} = B \times \text{係数}
\]

`<装甲>` の待機値・係数は **武器と同じ表** を用いる。防御行動は `<装甲>` を得る行為であるため、係数表を揃えても攻撃より総合的な強さは抑えられる想定とする。

| 防具重量 | 軽量 | 中量 | 重量 |
| :------: | :--: | :--: | :--: |
| 回避値   | {armor.evasion.light}    | {armor.evasion.mid}    | {armor.evasion.heavy}    |

| 重量／行動段階 | 軽行動 | 中行動 | 重行動 | 特行動 |
| :------------: | :----: | :----: | :----: | :----: |
| 軽量           | {weapon.light.light.pair}  | {weapon.light.mid.pair}  | {weapon.light.heavy.pair}  | {weapon.light.special.pair}  |
| 中量           | {weapon.mid.light.pair}  | {weapon.mid.mid.pair}  | {weapon.mid.heavy.pair}  | {weapon.mid.special.pair}  |
| 重量           | {weapon.heavy.light.pair}  | {weapon.heavy.mid.pair}  | {weapon.heavy.heavy.pair}  | {weapon.heavy.special.pair}  |

### カウントあたり効率（DPC）

重量ごとに最適な行動段階が異なるよう、係数表を設計している。基準効果量 \(B\) が同じとき、

\[
\text{DPC} = \frac{B \times \text{係数}}{\text{待機値}} \approx \frac{\text{係数}}{\text{待機値}} \times B
\]

各重量の **最適行動段階** における DPC 目安:

| 重量 | 最適行動段階 | DPC 目安（\(B=1\) 換算） |
| :--: | :----------: | :----------------------: |
| 軽量 | {dpc_optimal.light.action}       | ≈ {dpc_optimal.light.ratio}                   |
| 中量 | {dpc_optimal.mid.action}       | ≈ {dpc_optimal.mid.ratio}                   |
| 重量 | {dpc_optimal.heavy.action}       | ≈ {dpc_optimal.heavy.ratio}                   |

軽量は低数字カード、重量は高数字カードと相性がよい。重量差は **待機値・係数・等級** の組み合わせで吸収し、**カウントあたりの効率を揃えつつ手札の使い分け** に差を出す。

---

## PC実効値（Part7）

品質（Part6）と戦闘カウント・等級（第2層）を掛け合わせ、**PC側の戦闘実数** に換算する。`sim/part7` による決定論シムの出力を、第3層（絶対スケール）の **PC側入力** として扱う。

敵 HP・危険度・戦闘値 \(V\)・素材経済は **本節では決めない**（Phase 1〜3 で接続）。

### 参照条件

| 項目 | 値 |
| :-- | :-- |
| 典型品質 | Part6 `quality_progression.csv` の **attempt=5, p50** |
| 装備等級 | マナ数 \(n_{\text{extra}}\) から [装備品：マナ帯ごとの基準](#装備品マナ帯ごとの基準) を適用 |
| 消耗品 | 等級 **{consumable.grade}**・{consumable.default_weight}・中行動を DPC 比較の参照（一撃効果は行動帯で変動） |
| 装備 DPC 参照 | 中量・中行動（`part7-1`）／重量ごとの最適行動帯（`part7-2`） |

錬金 attempt=5 は「同レシピを数回試したうえでの典型品質」の目安とする。

### 換算式

\[
B_{\text{装備}} = \left\lfloor \frac{Q}{\text{等級}_{\text{装備}}} \right\rfloor,\qquad
B_{\text{消耗}} = \left\lfloor \frac{Q}{{consumable.grade}} \right\rfloor
\]

\[
\text{武器ダメージ} = \lfloor B_{\text{装備}} \times \text{攻撃係数} \rfloor,\qquad
\text{装備 DPC} = \frac{\text{ダメージ}}{\text{待機}}
\]

\[
\text{消耗品効果} = B_{\text{消耗}} \times \text{待機値},\qquad
\text{消耗品 DPC} = B_{\text{消耗}}
\]

\[
\text{防御値} = B_{\text{装備}},\qquad
\text{`<装甲>`} = \lfloor B_{\text{装備}} \times \text{係数} \rfloor
\]

### カード52枚の加重平均 DPC（\(B=1\) 換算）

行動段階の出現確率（4スート × 各ランク）：軽 12/52、中 16/52、重 12/52、特 12/52。

同一 \(B\) を前提に、ランダムに1枚プレイしたときの期待 DPC：

\[
\overline{\text{DPC}} = \sum_i p_i \cdot \frac{\text{係数}_i}{\text{待機}_i}
\]

| 重量 | 期待 DPC（\(B=1\)） | 期待係数 \(\overline{\text{coef}}\) |
| :--: | :-----------------: | :-------------------------------: |
| 軽量 | ≈ 1.22 | 4.00 |
| 中量 | ≈ 1.24（正確には **161/130**） | **72/13** ≈ 5.54 |
| 重量 | ≈ 1.27 | 7.15 |
| 消耗品 | **1.00** | （係数＝待機のため） |

**同一 \(B\)** では装備のカード平均 DPC は消耗品より **約2〜3割高い**。テストプレイ帯で消耗品の DPC が上に見えるのは、**等級差**（消耗 3 vs 装備 7/6/5）による \(B\) の差が主因である。

### 典型値（attempt=5, p50）

Part6 典型品質 \(Q\) から換算した代表値。武器・防具は **中量・中行動**、消耗品は **中量・中行動** の一撃効果。

| \(n_{\text{extra}}\) | 装備等級 | \(Q\) | 消耗 DPC | 武器 DPC | 防御値 | 消耗一撃 | 武器一撃 |
| :------------------: | :------: | ----: | -------: | -------: | -----: | -------: | -------: |
| {part7_ref.n1.n_extra} | {part7_ref.n1.equip_grade} | {part7_ref.n1.quality} | {part7_ref.n1.consumable_dpc} | {part7_ref.n1.weapon_dpc} | {part7_ref.n1.defense} | {part7_ref.n1.consumable_oneshot} | {part7_ref.n1.weapon_oneshot} |
| {part7_ref.n3.n_extra} | {part7_ref.n3.equip_grade} | {part7_ref.n3.quality} | {part7_ref.n3.consumable_dpc} | {part7_ref.n3.weapon_dpc} | {part7_ref.n3.defense} | {part7_ref.n3.consumable_oneshot} | {part7_ref.n3.weapon_oneshot} |
| {part7_ref.n6.n_extra} | {part7_ref.n6.equip_grade} | {part7_ref.n6.quality} | {part7_ref.n6.consumable_dpc} | {part7_ref.n6.weapon_dpc} | {part7_ref.n6.defense} | {part7_ref.n6.consumable_oneshot} | {part7_ref.n6.weapon_oneshot} |
| {part7_ref.n9.n_extra} | {part7_ref.n9.equip_grade} | {part7_ref.n9.quality} | {part7_ref.n9.consumable_dpc} | {part7_ref.n9.weapon_dpc} | {part7_ref.n9.defense} | {part7_ref.n9.consumable_oneshot} | {part7_ref.n9.weapon_oneshot} |

（\(n_{\text{extra}}\)=2,4,5,7,8 も同 CSV に出力。`sim/part7` 再実行で更新可能。）

### Part7 から言えること

1. **消耗品は DPC 最強がデフォルト**  
   リソース（マナ・素材・アイテム在庫）を消費する対価として、カウント効率は装備より高く設計する。消耗品等級 **{consumable.grade}** はシム上の仮置きであり、**探索・錬金ペース（Phase 1）と経済が決まってから** 確定する。

2. **装備は「常時付与＋手番コスト付き」が本丸**  
   攻撃・防御行動で `<装甲>` やダメージを得る。係数表は重量×行動帯の使い分け用。

3. **防御値 \(= B_{\text{装備}}\) はおまけの常時軽減**  
   手番コストなしで常に付与されるため、強くしすぎない。中量の期待一撃 \(B \times 72/13\) に対し、防御値 1 点は **約18%** 相当（\(1/\overline{\text{coef}}\)）。  
   ポーション等で **常時防御の上乗せ** 余地はある。体感調整は **エミュレート・テストプレイ** で行う。

4. **重量武器**  
   最適帯は特行動（DPC ≈ 1.57×\(B\)）。重行動は特行動の次に一撃が大きい位置づけ。中行動係数 6 は「常用帯でも完全な罠にならない」調整。

5. **テストプレイ想定**  
   マナ \(n_{\text{extra}}\) **{phase1.test_play_n_extra_max} 前後（等級5帯）まで** を主な検証レンジとする。等級 4（10+ マナ）は現段階では想定外。

### Part7 が決めないこと

| 項目 | 理由 |
| :-- | :-- |
| 消耗品等級の確定 | 素材・使用回数・製作コスト未定 |
| 敵 HP・火力・戦闘値 \(V\) | 危険度・人数補正（Phase 2）と接続が必要 |
| 2R タイムライン上の TTK | `sim/part9`（任意）またはプレイテスト |
| 防御値の倍率変更 | 現行 \(=B\) を維持。上記テストで必要なら検討 |

### シム出力

`sim/part7/run.py`（Part6 CSV 入力・決定論・試行乱数なし）

| 出力 | 内容 |
| :-- | :-- |
| `effective_stats_summary.csv` | マナ帯×attempt×百分位の DPC・一撃・防御値 |
| `effective_stats_detail.csv` | 重量×行動帯×種別の全組み合わせ |
| `effective_stats_oneshot.csv` / `optimal_oneshot.csv` | 一撃最大・最適行動帯 |
| `part7-1` 〜 `part7-4` PNG | DPC 比較・一撃比較・ヒートマップ |

---

## ゲーム進行・錬金ペース（Phase 1）

探索経済・成長日数の前提。**数値の確定**（探索1回≒錬金何回分、カゴ上限など）は Part8 または手計算で後続接続する。

### 確定したプレイ目標

| 項目 | 方針 |
| :-- | :-- |
| 副依頼 | **{phase1.sub_quest_days_min}〜{phase1.sub_quest_days_max}日** で完結するペース |
| 主依頼 | **約1週間（{phase1.main_quest_days}セッション）** |
| 1セッション | **約{phase1.session_hours}時間**（1日＝1セッション） |
| 倉庫 | **ストック型**（日次で使い切らない。計画錬金・余剰タグのバッファ） |
| 装備 | **現段階では装備レシピ想定なし**。初期装備を決めたら固定。成長の主軸は **消耗品・想成** |
| 錬金頻度 | レシピ複数・素材ランダムのため **毎日2回は上限**。平均 **1日{phase1.alchemy_per_day_avg}回** で見積もる |

### 標準1日パターン（案β）

| フェイズ | 行動 |
| :-- | :-- |
| **昼** | 探索（素材回収） |
| **夕** | 街務（錬金・買い物・交流・研究から **{phase1.town_actions_per_phase}回まで**。錬金は **0〜2回**、平均{phase1.alchemy_per_day_avg}回） |

- 昼に集めた素材の **約{phase1.tag_use_percent}%** をその日の夕〜翌日以降の錬金で消費するイメージ（**{phase1.tag_stock_percent}% は倉庫に残る**）。
- 探索タグの **80〜90%を当日夕に使い切る** 日次完結型（案α）は採用しない。

### 成長アンカー（Part6・Part7 との接続）

| 期間 | 目安 |
| :-- | :-- |
| **1週間** | 主依頼1件分。同一レシピに集中した場合 **attempt ≈ {phase1.main_quest_days}**（{phase1.alchemy_per_day_avg}日1錬金×{phase1.main_quest_days}日） |
| **2〜3日** | 副依頼1件分。**attempt ≈ {phase1.sub_quest_days_min}〜{phase1.sub_quest_days_max}** |
| **5日** | 案βの「中盤成長」目安。Part7 典型 Q は **attempt={phase1.part7_reference_attempt}, p50** を参照 |

装備を作らないため、Part7 の **消耗品 DPC・一撃** を主依頼・戦闘難度の PC 側アンカーとする。武器・防具の典型値は **初期装備固定** の参照用。

### Phase 1 で次に決めること

1. **基準レシピ1つ**（序盤・タグ2〜3・マナ2〜4）— catalog または仮置き
2. **探索1回の期待タグ数** — 5イベント前後・スート比率から（Part8 または手計算）
3. **整合チェック** — \(\dfrac{\text{1日平均錬金で消費タグ}}{\text{探索1回の期待タグ}} \approx 0.6\) となるよう素材側を調整
4. **5日目・7日目** の典型 Q が Part7 表で「使える」消耗品帯に入るか確認

### 意図的に Phase 1 では決めない

| 項目 | 理由 |
| :-- | :-- |
| 素材カゴ上限の確定値 | 探索供給が決まってから導出 |
| 消耗品等級の確定 | 上記経済の後 |
| 装備レシピ・装備成長 | 現段階スコープ外 |

---
