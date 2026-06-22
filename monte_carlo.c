/*
 * monte_carlo.c  ―  六属性ダイスTRPG モンテカルロ期待値計算
 *
 * ビルド例 (gcc):
 *   gcc -O2 -o monte_carlo monte_carlo.c
 *   .\monte_carlo.exe
 *
 * ビルド例 (MSVC):
 *   cl /O2 monte_carlo.c
 *   .\monte_carlo.exe
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* ================================================================
 * 定数・型定義
 * ================================================================ */

/* 1試行で取りうるダイスの最大個数（d4連鎖で増えるため余裕を持つ） */
#define MAX_DICE  256

/* キュー容量（連鎖が深い場合に備える） */
#define MAX_QUEUE 512

/* 風(d8)のトリガーモード */
typedef enum { WIND_INVERT, WIND_HALFTURN } WindMode;

/* ダイス1個の状態 */
typedef struct {
    int sides;  /* 面数: 4, 6, 8, 10, 12, 20 */
    int face;   /* 現在の出目 (1..sides) */
} Die;

/* ================================================================
 * ユーティリティ
 * ================================================================ */

/* 1..n の一様乱数 */
static inline int roll_die(int n)
{
    /* rand() は精度が低いが速度優先。高精度が必要なら mt19937 等へ差し替え可 */
    return (int)(rand() % n) + 1;
}

/* 出目 → 判定値 */
static inline int die_value(int sides, int face)
{
    if (face == 1) return -1;
    if (sides == 20 && face <= 3) return -1;  /* d20のみ出目1-3を-1扱い */
    if (sides == 20) return face / 2;  /* floor(出目/2) */
    return face;
}

/* -1ルール適用なし版（機械人用）
 * d20: floor(出目/2) のみ適用（1→0, 2→1, 3→1, ...)
 * その他: 出目そのまま（1→1）
 */
static inline int die_value_no_penalty(int sides, int face)
{
    if (sides == 20) return face / 2;
    return face;
}

/* 循環 ±1 調整: 1..N が環状に繋がっている */
static inline int cyclic_adjust(int sides, int face, int delta)
{
    int idx = face - 1;           /* 0..N-1 */
    idx = ((idx + delta) % sides + sides) % sides;
    return idx + 1;
}

/* 反転: N+1-face */
static inline int invert_face(int sides, int face)
{
    return sides + 1 - face;
}

/* 半回転: +N/2 循環 (偶数面のみ) */
static inline int half_turn_face(int sides, int face)
{
    return cyclic_adjust(sides, face, sides / 2);
}

/* ================================================================
 * FIFOキュー（固定長リングバッファ）
 * ================================================================ */

typedef struct {
    int buf[MAX_QUEUE];
    int head, tail, size;
} Queue;

static inline void queue_clear(Queue *q) { q->head = q->tail = q->size = 0; }
static inline int  queue_empty(const Queue *q) { return q->size == 0; }

static inline void queue_push(Queue *q, int v)
{
    q->buf[q->tail] = v;
    q->tail = (q->tail + 1) % MAX_QUEUE;
    q->size++;
}

static inline int queue_pop(Queue *q)
{
    int v = q->buf[q->head];
    q->head = (q->head + 1) % MAX_QUEUE;
    q->size--;
    return v;
}

/* ダイスのトリガー条件を判定する（queue_push の条件と一致させる） */
static inline int triggers(int sides, int face)
{
    if (sides == 4  && face >= 3) return 1;
    if (sides == 6  && face == 6) return 1;
    if (sides == 8  && face == 8) return 1;
    if (sides == 10 && face ==10) return 1;
    if (sides == 12 && face ==12) return 1;
    if (sides == 20 && face ==20) return 1;
    return 0;
}

/* ================================================================
 * エフェクト実装
 * ================================================================ */

/* 火(d4): 出目>=3 → ①自身を4（最大値）に固定 ＋ ②d4を1個追加（連鎖あり）
 * 自己強化: トリガーした瞬間に自身が確定で4になる（「点火したら燃え続ける」）。
 * 自身はすでにトリガー条件(>=3)を満たして処理中なので再キューは不要。
 * 追加d4は新たにトリガー判定を受ける（連鎖可）。                          */
static void effect_d4(Die *dice, int *n_dice, Queue *q, int idx)
{
    if (dice[idx].face < 3) return;
    /* ① 自身を最大値に固定 */
    dice[idx].face = 4;
    /* ② d4を1個追加ロール */
    int new_face = roll_die(4);
    dice[*n_dice].sides = 4;
    dice[*n_dice].face  = new_face;
    queue_push(q, *n_dice);
    (*n_dice)++;
}

/* 地(d6): 出目==6 → 自身以外・未発動の1個を ±1/±2 循環調整（利得が最大の方向を選ぶ）
 * 自身以外の未発動ダイスから最大利得の対象を1個選んで調整。
 * 調整後に最大値になったダイスはキューに積む。                              */
static void effect_d6_plusminus1(Die *dice, int n_dice, Queue *q, int idx,
                                  const int *used)
{
    if (dice[idx].face != 6) return;

    static const int deltas[] = {-2, -1, +1, +2};  /* 試す全方向 */

    int best_gain = 0;          /* 0より大きい利得のときのみ発動（任意発動） */
    int best_target = -1;
    int best_new_face = 0;

    for (int j = 0; j < n_dice; j++) {
        if (j == idx) continue;   /* 自身は対象外 */
        if (used[j]) continue;    /* 発動済みは対象外 */
        int n = dice[j].sides;
        int old_f = dice[j].face;
        for (int di = 0; di < 4; di++) {
            int new_f = cyclic_adjust(n, old_f, deltas[di]);
            int gain  = die_value(n, new_f) - die_value(n, old_f);
            if (gain > best_gain) {
                best_gain     = gain;
                best_target   = j;
                best_new_face = new_f;
            }
        }
    }

    if (best_target < 0) return;
    dice[best_target].face = best_new_face;
    if (triggers(dice[best_target].sides, best_new_face))
        queue_push(q, best_target);
}

/* 風(d8) 反転モード: 出目==8 → 自身以外・未発動の1個を反転（最大利得を選ぶ） */
static void effect_d8_invert(Die *dice, int n_dice, Queue *q, int idx,
                              const int *used)
{
    if (dice[idx].face != 8) return;

    int best_gain = 0;          /* 0より大きい利得のときのみ発動（任意発動） */
    int best_target = -1;
    int best_new_face = 0;

    for (int j = 0; j < n_dice; j++) {
        if (j == idx) continue;   /* 自身は対象外 */
        if (used[j]) continue;    /* 発動済みは対象外 */
        int n = dice[j].sides;
        int old_f = dice[j].face;
        int new_f = invert_face(n, old_f);
        int gain  = die_value(n, new_f) - die_value(n, old_f);
        if (gain > best_gain) {
            best_gain     = gain;
            best_target   = j;
            best_new_face = new_f;
        }
    }

    if (best_target < 0) return;
    dice[best_target].face = best_new_face;
    if (triggers(dice[best_target].sides, best_new_face))
        queue_push(q, best_target);
}

/* 風(d8) 半回転モード: 出目==8 → 自身以外・未発動の偶数面ダイスを半回転（最大利得を選ぶ） */
static void effect_d8_halfturn(Die *dice, int n_dice, Queue *q, int idx,
                                const int *used)
{
    if (dice[idx].face != 8) return;

    int best_gain = 0;          /* 0より大きい利得のときのみ発動（任意発動） */
    int best_target = -1;
    int best_new_face = 0;

    for (int j = 0; j < n_dice; j++) {
        if (j == idx) continue;   /* 自身は対象外 */
        if (used[j]) continue;    /* 発動済みは対象外 */
        int n = dice[j].sides;
        if (n % 2 != 0) continue;
        int old_f = dice[j].face;
        int new_f = half_turn_face(n, old_f);
        int gain  = die_value(n, new_f) - die_value(n, old_f);
        if (gain > best_gain) {
            best_gain     = gain;
            best_target   = j;
            best_new_face = new_f;
        }
    }

    if (best_target < 0) return;
    dice[best_target].face = best_new_face;
    if (triggers(dice[best_target].sides, best_new_face))
        queue_push(q, best_target);
}

/* 闇(d10): 出目==10 → 自身以外・未発動の1個を反転（N+1-face）して最大利得を選ぶ。
 * 反転後に最大値になったダイスはキューに積む（連鎖可）。                    */
static void effect_d10_invert(Die *dice, int n_dice, Queue *q, int idx,
                               const int *used)
{
    if (dice[idx].face != 10) return;

    int best_gain     = 0;      /* 0より大きい利得のときのみ発動（任意発動） */
    int best_target   = -1;
    int best_new_face = 0;

    for (int j = 0; j < n_dice; j++) {
        if (j == idx) continue;   /* 自身は対象外 */
        if (used[j]) continue;    /* 発動済みは対象外 */
        int n     = dice[j].sides;
        int old_f = dice[j].face;
        int new_f = invert_face(n, old_f);
        int gain  = die_value(n, new_f) - die_value(n, old_f);
        if (gain > best_gain) {
            best_gain     = gain;
            best_target   = j;
            best_new_face = new_f;
        }
    }

    if (best_target < 0) return;
    dice[best_target].face = best_new_face;
    if (triggers(dice[best_target].sides, best_new_face))
        queue_push(q, best_target);
}

/* 光(d12): 出目==12 → 自身以外・未発動の1個を最大値にセット（最大利得を選ぶ）
 * 最大値にセット後にトリガー条件を満たす場合はキューに積む（連鎖可）。      */
static void effect_d12_perfect(Die *dice, int n_dice, Queue *q, int idx,
                                const int *used)
{
    if (dice[idx].face != 12) return;

    int best_gain = 0;          /* 0より大きい利得のときのみ発動（任意発動） */
    int best_target = -1;

    for (int j = 0; j < n_dice; j++) {
        if (j == idx) continue;   /* 自身は対象外 */
        if (used[j]) continue;    /* 発動済みは対象外 */
        int n = dice[j].sides;
        int old_f = dice[j].face;
        int new_f = n;  /* 最大値 */
        int gain  = die_value(n, new_f) - die_value(n, old_f);
        if (gain > best_gain) {
            best_gain   = gain;
            best_target = j;
        }
    }

    if (best_target < 0) return;
    dice[best_target].face = dice[best_target].sides;
    /* 最大値にセットされたダイスがトリガー条件を満たすならキューに積む */
    if (triggers(dice[best_target].sides, dice[best_target].sides))
        queue_push(q, best_target);
}

/* 水(d20): 出目==20 → 自身以外・未発動の1個を振り直し（期待利得が最大の対象を選ぶ）
 * 振り直し後の結果は必ず受け入れる（上下問わず確定）。
 * 期待利得 > 0 の対象がなければ発動しない（任意発動）。
 * 振り直し後にトリガー条件を満たせば連鎖可。                               */
static void effect_d20_reroll(Die *dice, int n_dice, Queue *q, int idx,
                               const int *used)
{
    if (dice[idx].face != 20) return;

    int best_target = -1;
    double best_expected_gain = 0.0;  /* 0より大きい期待利得のときのみ発動 */

    for (int j = 0; j < n_dice; j++) {
        if (j == idx) continue;   /* 自身は対象外 */
        if (used[j]) continue;    /* 発動済みは対象外 */
        int n = dice[j].sides;
        int old_val = die_value(n, dice[j].face);
        /* 振り直し後の期待value = ダイスの期待値（出目1=-1, 他=出目 or /2） */
        double expected_new = 0.0;
        for (int f = 1; f <= n; f++) expected_new += die_value(n, f);
        expected_new /= n;
        double expected_gain = expected_new - old_val;
        if (expected_gain > best_expected_gain) {
            best_expected_gain = expected_gain;
            best_target = j;
        }
    }

    if (best_target < 0) return;
    /* 実際に振り直す */
    int n = dice[best_target].sides;
    int new_face = roll_die(n);
    dice[best_target].face = new_face;
    if (triggers(n, new_face))
        queue_push(q, best_target);
}

/* ================================================================
 * シミュレーションコア
 * ================================================================ */

static int cmp_int(const void *a, const void *b)
{
    return (*(int *)a) - (*(int *)b);
}

/*
 * simulate_pool:
 *   pool_sides : ダイス面数の配列
 *   n_pool     : 配列長
 *   trials     : 試行回数
 *   wind_mode  : WIND_INVERT or WIND_HALFTURN
 *   out_avg    : 平均値 (出力)
 *   out_p50    : 中央値 (出力)
 *   out_p90    : 90パーセンタイル (出力)
 *   out_p99    : 99パーセンタイル (出力)
 */
void simulate_pool(
    const int *pool_sides, int n_pool,
    int trials, WindMode wind_mode,
    double *out_avg, int *out_p50, int *out_p90, int *out_p99)
{
    int *totals = (int *)malloc(sizeof(int) * trials);
    if (!totals) { perror("malloc"); exit(1); }

    Die dice[MAX_DICE];
    int used[MAX_DICE];  /* 発動済みフラグ: 1=発動済み（対象に取れない） */
    Queue q;

    for (int t = 0; t < trials; t++) {
        /* 初期ロール */
        int n_dice = n_pool;
        for (int i = 0; i < n_pool; i++) {
            dice[i].sides = pool_sides[i];
            dice[i].face  = roll_die(pool_sides[i]);
            used[i] = 0;
        }

        /* 初期トリガーをキューに積む */
        queue_clear(&q);
        for (int i = 0; i < n_dice; i++) {
            int s = dice[i].sides, f = dice[i].face;
            if      (s == 4  && f >= 3) queue_push(&q, i);
            else if (s == 6  && f == 6) queue_push(&q, i);
            else if (s == 8  && f == 8) queue_push(&q, i);
            else if (s == 10 && f ==10) queue_push(&q, i);
            else if (s == 12 && f ==12) queue_push(&q, i);
            else if (s == 20 && f ==20) queue_push(&q, i);
        }

        /* エフェクト処理ループ */
        while (!queue_empty(&q)) {
            int idx = queue_pop(&q);
            if (used[idx]) continue;  /* 既に発動済みならスキップ */

            /* ★バグ修正: 今この瞬間のトリガー条件を再チェック
             * キューに積まれた後に他の効果で出目が変わり、
             * トリガー条件を失っている場合は used を立てずにスキップ */
            if (!triggers(dice[idx].sides, dice[idx].face)) continue;

            used[idx] = 1;            /* 発動済みにマーク */
            int s = dice[idx].sides;

            /* d4の連鎖で追加されたダイスはused=0で初期化 */
            int prev_n = n_dice;
            switch (s) {
                case 4:  effect_d4(dice, &n_dice, &q, idx);  break;
                case 6:  effect_d6_plusminus1(dice, n_dice, &q, idx, used); break;
                case 8:
                    if (wind_mode == WIND_INVERT)
                        effect_d8_invert(dice, n_dice, &q, idx, used);
                    else
                        effect_d8_halfturn(dice, n_dice, &q, idx, used);
                    break;
                case 10: effect_d10_invert(dice, n_dice, &q, idx, used); break;
                case 12: effect_d12_perfect(dice, n_dice, &q, idx, used); break;
                case 20: effect_d20_reroll(dice, n_dice, &q, idx, used); break;
            }
            /* d4連鎖で追加された新規ダイスのusedを0で初期化 */
            for (int i = prev_n; i < n_dice; i++) used[i] = 0;
        }

        /* 合計値を記録 */
        int total = 0;
        for (int i = 0; i < n_dice; i++)
            total += die_value(dice[i].sides, dice[i].face);
        totals[t] = total;
    }

    /* ソートしてパーセンタイル計算 */
    qsort(totals, trials, sizeof(int), cmp_int);

    double sum = 0.0;
    for (int i = 0; i < trials; i++) sum += totals[i];
    *out_avg = sum / trials;
    *out_p50 = totals[(int)(0.50 * (trials - 1))];
    *out_p90 = totals[(int)(0.90 * (trials - 1))];
    *out_p99 = totals[(int)(0.99 * (trials - 1))];

    free(totals);
}

/* ================================================================
 * 全列挙による限界貢献度分析
 *
 * 評価ダイス: d4(0), d6(1), d8(2), d10(3), d20(4)  各0~15個、合計0~15個
 * d12       : 0 or 1個（別枠, index=5）
 *
 * 限界貢献度の定義:
 *   構成 S のavgを avg(S) とする。
 *   ダイス d の限界貢献度 = avg(S∪{d}) - avg(S)
 *   これを「S の合計が0~14個（追加後1~15個）」の全構成で平均する。
 *
 * グラフ用データ:
 *   横軸 = S内の他ダイス合計個数 (0~14)
 *   縦軸 = その他ダイス個数での限界貢献度の平均
 *   → marginal_sum_by_n[dice][n_others], marginal_cnt_by_n[dice][n_others]
 *
 * キャッシュ戦略:
 *   counts[5] × has_d12 を線形インデックスに変換して double 配列に保存。
 *   サイズ = 16^5 × 2 = 2,097,152エントリ ≒ 16MB。
 *   未計算エントリは NaN で管理。
 * ================================================================ */

#include <math.h>  /* NAN, isnan */

#define MAX_N      10   /* ダイスプール上限 */
#define BASE       11   /* インデックス基数 (0~10 → 11進) */
#define N_DICE_TYPES 5
static const int  DICE_SIDES[N_DICE_TYPES] = {4, 6, 8, 10, 20};

/* counts[5] + has_d12 → フラットインデックス */
static inline int cache_idx(const int c[5], int d12)
{
    return ((((c[0]*BASE + c[1])*BASE + c[2])*BASE + c[3])*BASE + c[4])
           + d12 * (BASE*BASE*BASE*BASE*BASE);
}

static void run_full_enumeration(int trials_enum, WindMode wind_mode,
                                 const char *out_dir)
{
    const int CACHE_SIZE = BASE*BASE*BASE*BASE*BASE * 2;  /* 11^5×2 = 322,102 ≒ 2.5MB */
    double *cache = (double *)malloc(sizeof(double) * CACHE_SIZE);
    if (!cache) { perror("malloc"); exit(1); }
    for (int i = 0; i < CACHE_SIZE; i++) cache[i] = NAN;

    /* --- パス1: 全有効構成のavgをキャッシュに格納 ---
     * 前提: d10は常に1個固定。counts[3] >= 1。
     * 追加ダイス(d4/d6/d8/d10/d20)の合計は 1~MAX_N (d10の1個を含む)。
     * d12は 0 or 1個（別枠）。                                           */
    int counts[5];
    int pool[MAX_DICE];
    long n_computed = 0;

    /* 総構成数を事前計算（進捗表示用）: counts[3](d10) >= 1 */
    long n_total = 0;
    for (int a=0; a<=MAX_N; a++)
    for (int b=0; b<=MAX_N-a; b++)
    for (int c=0; c<=MAX_N-a-b; c++)
    for (int d=1; d<=MAX_N-a-b-c; d++)       /* d10 >= 1 */
    for (int e=0; e<=MAX_N-a-b-c-d; e++) {
        n_total += 2;  /* d12あり/なし（合計が1以上なのでd12なし=1通りも必ず有効） */
    }
    printf("  総構成数: %ld\n", n_total);
    fflush(stdout);

    for (counts[0]=0; counts[0]<=MAX_N; counts[0]++)
    for (counts[1]=0; counts[1]<=MAX_N-(counts[0]); counts[1]++)
    for (counts[2]=0; counts[2]<=MAX_N-(counts[0]+counts[1]); counts[2]++)
    for (counts[3]=1; counts[3]<=MAX_N-(counts[0]+counts[1]+counts[2]); counts[3]++)  /* d10 >= 1 */
    for (counts[4]=0; counts[4]<=MAX_N-(counts[0]+counts[1]+counts[2]+counts[3]); counts[4]++) {
        for (int d12 = 0; d12 <= 1; d12++) {
            int idx = cache_idx(counts, d12);
            /* プール構築 */
            int np = 0;
            for (int t = 0; t < N_DICE_TYPES; t++)
                for (int k = 0; k < counts[t]; k++)
                    pool[np++] = DICE_SIDES[t];
            if (d12) pool[np++] = 12;

            double avg; int p50,p90,p99;
            simulate_pool(pool, np, trials_enum, wind_mode,
                          &avg, &p50, &p90, &p99);
            cache[idx] = avg;
            n_computed++;

            /* 進捗表示: PROGRESS: プレフィックス付きで出力（100構成ごと） */
            if (n_computed % 100 == 0 || n_computed == n_total) {
                printf("PROGRESS1: %ld / %ld  (%.1f%%)\n",
                       n_computed, n_total,
                       100.0 * n_computed / n_total);
                fflush(stdout);
            }
        }
    }
    printf("\n  キャッシュ完了: %ld 構成\n", n_computed);
    fflush(stdout);

    /* --- パス2: 限界貢献度の集計 ---
     * [6][MAX_N] の2次元配列で「他ダイス合計個数別」に集計する。
     * 横軸 n_others = S内の総ダイス数 (0 ~ MAX_N-1) */
    double marginal_sum[6][MAX_N];
    long   marginal_cnt[6][MAX_N];
    double marginal_sum_all[6];
    long   marginal_cnt_all[6];
    for (int t = 0; t < 6; t++) {
        marginal_sum_all[t] = 0.0;
        marginal_cnt_all[t] = 0;
        for (int n = 0; n < MAX_N; n++) {
            marginal_sum[t][n] = 0.0;
            marginal_cnt[t][n] = 0;
        }
    }

    /* パス2の総ステップ数を事前計算（進捗表示用）
     * d10固定1個前提: counts[3] >= 1、追加後の合計が MAX_N 以下 */
    long p2_total = 0;
    for (int a=0; a<=MAX_N-1; a++)
    for (int b=0; b<=MAX_N-1-a; b++)
    for (int c=0; c<=MAX_N-1-a-b; c++)
    for (int d=1; d<=MAX_N-1-a-b-c; d++)     /* d10 >= 1 */
    for (int e=0; e<=MAX_N-1-a-b-c-d; e++) {
        for (int d12 = 0; d12 <= 1; d12++) {
            int total = a+b+c+d+e+d12;
            if (total <= MAX_N - 1) p2_total++;
        }
    }
    long p2_done = 0;

    for (counts[0]=0; counts[0]<=MAX_N-1; counts[0]++)
    for (counts[1]=0; counts[1]<=MAX_N-1-(counts[0]); counts[1]++)
    for (counts[2]=0; counts[2]<=MAX_N-1-(counts[0]+counts[1]); counts[2]++)
    for (counts[3]=1; counts[3]<=MAX_N-1-(counts[0]+counts[1]+counts[2]); counts[3]++)  /* d10 >= 1 */
    for (counts[4]=0; counts[4]<=MAX_N-1-(counts[0]+counts[1]+counts[2]+counts[3]); counts[4]++) {
        int sub = counts[0]+counts[1]+counts[2]+counts[3]+counts[4];

        for (int d12 = 0; d12 <= 1; d12++) {
            int total = sub + d12;
            /* 追加後が MAX_N 以下になる構成のみ */
            if (total > MAX_N - 1) continue;

            double avg_base = cache[cache_idx(counts, d12)];
            int n_others = total;  /* 追加前の総数(d10含む) = 横軸の値 */

            /* d4/d6/d8/d10/d20 を1個追加
             * d10は「少なくとも1個」が前提なので、2個目以降の追加も集計する */
            for (int t = 0; t < N_DICE_TYPES; t++) {
                counts[t]++;
                double avg_plus = cache[cache_idx(counts, d12)];
                counts[t]--;
                if (isnan(avg_plus)) continue;  /* キャッシュ未計算ならスキップ */
                double diff = avg_plus - avg_base;
                marginal_sum[t][n_others]     += diff;
                marginal_cnt[t][n_others]     += 1;
                marginal_sum_all[t]           += diff;
                marginal_cnt_all[t]           += 1;
            }

            /* d12を1個追加（has_d12==0 のときのみ） */
            if (d12 == 0) {
                double avg_plus = cache[cache_idx(counts, 1)];
                if (!isnan(avg_plus)) {
                    double diff = avg_plus - avg_base;
                    marginal_sum[5][n_others]     += diff;
                    marginal_cnt[5][n_others]     += 1;
                    marginal_sum_all[5]           += diff;
                    marginal_cnt_all[5]           += 1;
                }
            }

            /* 進捗表示: PROGRESS2: プレフィックス付きで出力（100ステップごと） */
            p2_done++;
            if (p2_done % 100 == 0 || p2_done == p2_total) {
                printf("PROGRESS2: %ld / %ld  (%.1f%%)\n",
                       p2_done, p2_total,
                       100.0 * p2_done / p2_total);
                fflush(stdout);
            }
        }
    }
    printf("\n  集計完了\n");
    fflush(stdout);

    /* --- 結果出力: 総合 --- */
    printf("\n");
    printf("============================================================\n");
    printf("  全構成列挙による 限界貢献度 (Marginal Contribution)\n");
    printf("  ※ d10は少なくとも1個固定。全構成で counts[d10] >= 1。\n");
    printf("  trials/composition = %d,  wind_mode = %s,  max_pool = %d\n",
           trials_enum, wind_mode == WIND_INVERT ? "invert" : "halfturn", MAX_N);
    printf("============================================================\n");
    printf("%-6s  avg_marginal  sample_count\n", "dice");
    printf("------  ------------  ------------\n");

    const char *names6[6] = {"d4","d6","d8","d10","d20","d12"};
    for (int t = 0; t < 6; t++) {
        double mc = marginal_cnt_all[t] > 0
                    ? marginal_sum_all[t] / (double)marginal_cnt_all[t]
                    : 0.0;
        printf("%-6s  %12.4f  %12ld\n", names6[t], mc, marginal_cnt_all[t]);
    }
    printf("----\n");
    printf("※ 値 = ダイス1個追加による期待値の平均増分\n");

    /* --- CSVファイル出力 (グラフ用) --- */
    char csv_path[512];
    snprintf(csv_path, sizeof(csv_path), "%smarginal_by_n.csv", out_dir);
    FILE *fp = fopen(csv_path, "w");
    if (!fp) { perror("fopen"); free(cache); return; }

    /* ヘッダー行 */
    fprintf(fp, "n_others");
    for (int t = 0; t < 6; t++) fprintf(fp, ",%s", names6[t]);
    fprintf(fp, "\n");

    /* データ行: n_others = 0 ~ MAX_N-1 */
    for (int n = 0; n < MAX_N; n++) {
        fprintf(fp, "%d", n);
        for (int t = 0; t < 6; t++) {
            if (marginal_cnt[t][n] > 0)
                fprintf(fp, ",%.4f", marginal_sum[t][n] / (double)marginal_cnt[t][n]);
            else
                fprintf(fp, ",");  /* データなし */
        }
        fprintf(fp, "\n");
    }
    fclose(fp);
    printf("\nCSV出力: %s\n", csv_path);

    free(cache);
}

/* ================================================================
 * Part 3: 難易度設計テーブル
 *
 * 「1d10 + 属性ダイス1個」のプールで、各目標値における成功率を計算する。
 * 組み合わせ:
 *   - d10のみ (基準)
 *   - d10 + d4 (火)
 *   - d10 + d6 (地)
 *   - d10 + d8 (風)
 *   - d10 + d20 (水)
 * 目標値: 1 ~ 25 を総当たりで出力する。
 * ================================================================ */

/*
 * simulate_success_rate:
 *   pool_sides, n_pool : ダイス構成
 *   trials             : 試行回数
 *   wind_mode          : 風モード
 *   target             : 成功に必要な達成値（以上で成功）
 *   戻り値             : 成功率 (0.0~1.0)
 */
static double simulate_success_rate(
    const int *pool_sides, int n_pool,
    int trials, WindMode wind_mode, int target)
{
    Die dice[MAX_DICE];
    int used[MAX_DICE];
    Queue q;
    int success = 0;

    for (int t = 0; t < trials; t++) {
        int n_dice = n_pool;
        for (int i = 0; i < n_pool; i++) {
            dice[i].sides = pool_sides[i];
            dice[i].face  = roll_die(pool_sides[i]);
            used[i] = 0;
        }

        queue_clear(&q);
        for (int i = 0; i < n_dice; i++) {
            if (triggers(dice[i].sides, dice[i].face))
                queue_push(&q, i);
        }

        while (!queue_empty(&q)) {
            int idx = queue_pop(&q);
            if (used[idx]) continue;
            if (!triggers(dice[idx].sides, dice[idx].face)) continue;
            used[idx] = 1;
            int s = dice[idx].sides;
            int prev_n = n_dice;
            switch (s) {
                case 4:  effect_d4(dice, &n_dice, &q, idx);  break;
                case 6:  effect_d6_plusminus1(dice, n_dice, &q, idx, used); break;
                case 8:
                    if (wind_mode == WIND_INVERT)
                        effect_d8_invert(dice, n_dice, &q, idx, used);
                    else
                        effect_d8_halfturn(dice, n_dice, &q, idx, used);
                    break;
                case 10: effect_d10_invert(dice, n_dice, &q, idx, used); break;
                case 12: effect_d12_perfect(dice, n_dice, &q, idx, used); break;
                case 20: effect_d20_reroll(dice, n_dice, &q, idx, used); break;
            }
            for (int i = prev_n; i < n_dice; i++) used[i] = 0;
        }

        int total = 0;
        for (int i = 0; i < n_dice; i++)
            total += die_value(dice[i].sides, dice[i].face);
        if (total >= target) success++;
    }

    return (double)success / trials;
}

static void run_difficulty_table(int trials, WindMode wind_mode,
                                 const char *out_dir)
{
    /* 評価するプール構成 */
    typedef struct { const char *name; int pool[2]; int n; } Combo;
    static const Combo combos[] = {
        { "d10only",       {10},     1 },
        { "d10+d4(Fire)",  {10, 4},  2 },
        { "d10+d6(Earth)", {10, 6},  2 },
        { "d10+d8(Wind)",  {10, 8},  2 },
        { "d10+d20(Water)",{10, 20}, 2 },
    };
    const int N_COMBOS = 5;
    const int TARGET_MIN = 1;
    const int TARGET_MAX = 25;

    printf("\n");
    printf("============================================================\n");
    printf("  Part3: 難易度設計テーブル (trials=%d)\n", trials);
    printf("  「1d10 + 属性ダイス1個」の組み合わせ別 成功率\n");
    printf("  ※ 目標値以上の達成値で成功\n");
    printf("============================================================\n");

    /* ヘッダー行 */
    printf("目標値  ");
    for (int c = 0; c < N_COMBOS; c++)
        printf("  %-12s", combos[c].name);
    printf("\n");
    printf("------  ");
    for (int c = 0; c < N_COMBOS; c++) printf("  ------------");
    printf("\n");

    /* 目標値ごとに成功率を出力 */
    for (int tgt = TARGET_MIN; tgt <= TARGET_MAX; tgt++) {
        printf("%6d  ", tgt);
        for (int c = 0; c < N_COMBOS; c++) {
            double rate = simulate_success_rate(
                combos[c].pool, combos[c].n,
                trials, wind_mode, tgt);
            printf("  %11.1f%%", rate * 100.0);
        }
        printf("\n");
    }

    /* CSVファイル出力 */
    char csv_path[512];
    snprintf(csv_path, sizeof(csv_path), "%sdifficulty_table.csv", out_dir);
    FILE *fp = fopen(csv_path, "w");
    if (!fp) { perror("fopen"); return; }

    /* ヘッダー */
    fprintf(fp, "target");
    for (int c = 0; c < N_COMBOS; c++) fprintf(fp, ",%s", combos[c].name);
    fprintf(fp, "\n");

    /* データ */
    for (int tgt = TARGET_MIN; tgt <= TARGET_MAX; tgt++) {
        fprintf(fp, "%d", tgt);
        for (int c = 0; c < N_COMBOS; c++) {
            double rate = simulate_success_rate(
                combos[c].pool, combos[c].n,
                trials, wind_mode, tgt);
            fprintf(fp, ",%.4f", rate);
        }
        fprintf(fp, "\n");
    }
    fclose(fp);
    printf("\nCSV出力: %s\n", csv_path);
}

/* ================================================================
 * Part 4: 六種族 判定時効果 強さ比較
 *
 * 全有効ダイスプール構成（Part2と同一範囲）を列挙し、各構成について
 * 「種族効果なし」と「種族効果あり」との達成値差（期待値増分）を計算する。
 *
 * 種族効果一覧:
 *   0: 人間        … 全反応後、任意ダイス1つを裏返す
 *   1: 機械人      … 振る前にd10→d12置換（反応なし、出目1=1）
 *   2: 獣人        … 全反応後、任意ダイス1つをペナルティ付き振り直し
 *   3: ホムンクルス … 全反応後、三択から1つ選んで適用
 *   4: 付喪A       … 全反応後、未反応ダイス1つの出目を+1（循環）
 *   5: 付喪B       … 全反応後、任意ダイス2つの出目を入れ替え
 *
 * 集計方針:
 *   各構成 S について trials_per_pool 回シミュレートし E[delta(S)] を得る。
 *   それを全構成で平均した E_all[delta] を主指標とする。
 *   また「プール合計個数 n 別」の集計も行い CSV に出力する。
 * ================================================================ */

#define N_RACES 6

/* ----------------------------------------------------------------
 * ベースライン達成値計算
 * n_dice 個のダイス配列の達成値合計を返す
 * ---------------------------------------------------------------- */
static int score_baseline(const Die *dice, int n_dice)
{
    int total = 0;
    for (int i = 0; i < n_dice; i++)
        total += die_value(dice[i].sides, dice[i].face);
    return total;
}

/* ================================================================
 * 反応ループ共通処理
 *
 * dice/used/n_dice を in-place で更新する。
 * 呼び出し前に dice[]/used[] は初期化済みであること。
 * skip_trigger_sides: このサイズのダイスはトリガーキューに積まない
 *                     (0 = 制限なし)
 * ================================================================ */
static void run_react_loop(Die *dice, int *used, int *n_dice,
                           WindMode wind_mode, int skip_trigger_sides)
{
    Queue q;
    queue_clear(&q);
    for (int i = 0; i < *n_dice; i++) {
        if (dice[i].sides == skip_trigger_sides) continue;
        if (triggers(dice[i].sides, dice[i].face))
            queue_push(&q, i);
    }
    while (!queue_empty(&q)) {
        int idx = queue_pop(&q);
        if (used[idx]) continue;
        if (!triggers(dice[idx].sides, dice[idx].face)) continue;
        used[idx] = 1;
        int prev_n = *n_dice;
        switch (dice[idx].sides) {
            case 4:  effect_d4(dice, n_dice, &q, idx); break;
            case 6:  effect_d6_plusminus1(dice, *n_dice, &q, idx, used); break;
            case 8:
                if (wind_mode == WIND_INVERT)
                    effect_d8_invert(dice, *n_dice, &q, idx, used);
                else
                    effect_d8_halfturn(dice, *n_dice, &q, idx, used);
                break;
            case 10: effect_d10_invert(dice, *n_dice, &q, idx, used); break;
            case 12: effect_d12_perfect(dice, *n_dice, &q, idx, used); break;
            case 20: effect_d20_reroll(dice, *n_dice, &q, idx, used); break;
        }
        for (int i = prev_n; i < *n_dice; i++) used[i] = 0;
    }
}

/* ================================================================
 * 反応ループ: k ステップだけ処理して止まる版
 *
 * run_react_loop と同じ処理を max_steps ステップで打ち切る。
 * max_steps < 0 のときは制限なし（= run_react_loop と同等）。
 * 戻り値: 実際に処理したステップ数
 * ================================================================ */
static int run_react_loop_steps(Die *dice, int *used, int *n_dice,
                                WindMode wind_mode, int max_steps)
{
    Queue q;
    queue_clear(&q);
    for (int i = 0; i < *n_dice; i++) {
        if (triggers(dice[i].sides, dice[i].face))
            queue_push(&q, i);
    }
    int steps = 0;
    while (!queue_empty(&q)) {
        if (max_steps >= 0 && steps >= max_steps) break;
        int idx = queue_pop(&q);
        if (used[idx]) continue;
        if (!triggers(dice[idx].sides, dice[idx].face)) continue;
        used[idx] = 1;
        steps++;
        int prev_n = *n_dice;
        switch (dice[idx].sides) {
            case 4:  effect_d4(dice, n_dice, &q, idx); break;
            case 6:  effect_d6_plusminus1(dice, *n_dice, &q, idx, used); break;
            case 8:
                if (wind_mode == WIND_INVERT)
                    effect_d8_invert(dice, *n_dice, &q, idx, used);
                else
                    effect_d8_halfturn(dice, *n_dice, &q, idx, used);
                break;
            case 10: effect_d10_invert(dice, *n_dice, &q, idx, used); break;
            case 12: effect_d12_perfect(dice, *n_dice, &q, idx, used); break;
            case 20: effect_d20_reroll(dice, *n_dice, &q, idx, used); break;
        }
        for (int i = prev_n; i < *n_dice; i++) used[i] = 0;
    }
    return steps;
}

/* ----------------------------------------------------------------
 * 人間: 裏返し（コスト −3）
 *   raw 状態（ロール直後、used=全0）を受け取る。
 *   任意ダイス1つを反転し、そのダイスは反応済み（used=1）として扱う。
 *   その後 run_react_loop を走らせる（反転ダイス自身は連鎖しない）。
 *   コスト −3: 即時利得 >= 3 のときのみ使用。
 * ---------------------------------------------------------------- */
static int score_human(const Die *dice_raw, int n_dice_raw,
                       WindMode wind_mode, int *out_used)
{
    /* ベースライン（能力不使用）*/
    Die base[MAX_DICE]; int used_base[MAX_DICE]; int n_base = n_dice_raw;
    memcpy(base, dice_raw, sizeof(Die)*n_base);
    memset(used_base, 0, sizeof(int)*n_base);
    run_react_loop(base, used_base, &n_base, wind_mode, 0);
    int best = score_baseline(base, n_base);
    *out_used = 0;

    /* gain > 0 の全候補を試す: 反転+react_loop後 -n_dice_raw が best を超えるか */
    for (int i = 0; i < n_dice_raw; i++) {
        int new_f = invert_face(dice_raw[i].sides, dice_raw[i].face);
        int gain  = die_value(dice_raw[i].sides, new_f)
                  - die_value(dice_raw[i].sides, dice_raw[i].face);
        if (gain <= 0) continue;
        Die t[MAX_DICE]; int u[MAX_DICE]; int nn = n_dice_raw;
        memcpy(t, dice_raw, sizeof(Die)*nn); memset(u, 0, sizeof(int)*nn);
        t[i].face = new_f;
        u[i] = 1;  /* 反転したダイスは反応済みとして扱う */
        run_react_loop(t, u, &nn, wind_mode, 0);
        int s = score_baseline(t, nn) - n_dice_raw;  /* コスト = ダイス数 */
        if (s > best) { best = s; *out_used = 1; }
    }
    return best;
}

/* ----------------------------------------------------------------
 * 獣人: ペナルティ付き振り直し
 *   raw 状態を受け取る。任意ダイス1つを振り直し。
 *   新出目 < 旧出目 → 強制 face=1（= −1）。
 *   振り直し後のダイスは used=0（未反応）→ 連鎖発火の候補になる。
 * ---------------------------------------------------------------- */
static int score_beast(const Die *dice_raw, int n_dice_raw,
                       WindMode wind_mode, int *out_used)
{
    int best_target  = -1;
    double best_gain = 0.0;
    for (int i = 0; i < n_dice_raw; i++) {
        int n        = dice_raw[i].sides;
        int old_face = dice_raw[i].face;
        int old_val  = die_value(n, old_face);
        double exp_new = 0.0;
        for (int f = 1; f <= n; f++) {
            int val = (f < old_face) ? -1 : die_value(n, f);
            exp_new += val;
        }
        exp_new /= n;
        double g = exp_new - old_val;
        if (g > best_gain) { best_gain = g; best_target = i; }
    }
    Die  tmp[MAX_DICE]; int used[MAX_DICE]; int n = n_dice_raw;
    memcpy(tmp, dice_raw, sizeof(Die) * n); memset(used, 0, sizeof(int) * n);
    *out_used = (best_target >= 0) ? 1 : 0;
    if (best_target >= 0) {
        int old_face = tmp[best_target].face;
        int new_face = roll_die(tmp[best_target].sides);
        tmp[best_target].face = (new_face < old_face) ? 1 : new_face;
        /* used=0 のまま → 振り直し後に連鎖発火の候補になる */
    }
    run_react_loop(tmp, used, &n, wind_mode, 0);
    return score_baseline(tmp, n);
}

/* ----------------------------------------------------------------
 * ホムンクルス: 後出し三択
 *   択A: 反応ループ完了後の状態で −1 ダイスを 0 に換算（スコア加算）
 *   択B: raw 状態で未反応の非(−1)ダイス1つを +1 → react_loop（固定+1ボーナス）
 *   択C: raw 状態で未反応ダイス1つを循環−2 → react_loop（コスト −5）
 *   out_option: 0=A, 1=B, 2=C, -1=不使用
 * ---------------------------------------------------------------- */
static int score_homunculus(const Die *dice_raw, int n_dice_raw,
                             WindMode wind_mode, int *out_option)
{
    /* まず通常の react_loop を走らせて base と後処理状態を得る */
    Die  dice_reacted[MAX_DICE]; int used_r[MAX_DICE]; int n_r = n_dice_raw;
    memcpy(dice_reacted, dice_raw, sizeof(Die) * n_r);
    memset(used_r, 0, sizeof(int) * n_r);
    run_react_loop(dice_reacted, used_r, &n_r, wind_mode, 0);
    int base = score_baseline(dice_reacted, n_r);
    int best_score = base;
    *out_option = -1;  /* -1=不使用 */

    /* --- 択A: 反応後の全ダイスに die_value_no_penalty で集計（コストなし） --- */
    {
        int s = 0;
        for (int i = 0; i < n_r; i++)
            s += die_value_no_penalty(dice_reacted[i].sides, dice_reacted[i].face);
        if (s > best_score) { best_score = s; *out_option = 0; }
    }

    /* --- 択B: 連鎖報酬（反応済みダイス数 ÷2 を達成値に加算）--- */
    /* 反応ループ完了後の used_r[] で 1 になっている個数の半分（切り捨て）を加算    */
    /* 常に適用（発動条件なし）、コストなし                                          */
    {
        int reacted = 0;
        for (int i = 0; i < n_r; i++)
            reacted += used_r[i];
        int s = base + reacted / 2;
        if (s > best_score) { best_score = s; *out_option = 1; }
    }

    /* --- 択C: 変異（反応ループ中の任意タイミングに1回）
     * 「ちょうど k ステップ処理した直後に発動する」パターンを k=0,1,...全ステップ で全試し。
     * 各パターン: k ステップ分ループ → 最高 die_value ダイス除外 → 残り循環+1 → 続きのループ
     * コスト: 発動時点のダイス総数（除外前の nn）を達成値から差し引く */
    if (n_dice_raw >= 2) {
        /* まず k=0〜「全ステップ完了後」まで試す。
         * 上限把握のため一度フルシミュレートしてステップ数を測る */
        Die  tmp0[MAX_DICE]; int used0[MAX_DICE]; int nn0 = n_dice_raw;
        memcpy(tmp0, dice_raw, sizeof(Die)*nn0); memset(used0, 0, sizeof(int)*nn0);
        int total_steps = run_react_loop_steps(tmp0, used0, &nn0, wind_mode, -1);

        /* k=0（発動前にループなし）から k=total_steps（フルループ後）まで全試し */
        for (int k = 0; k <= total_steps; k++) {
            Die  tmp[MAX_DICE]; int used[MAX_DICE]; int nn = n_dice_raw;
            memcpy(tmp, dice_raw, sizeof(Die)*nn); memset(used, 0, sizeof(int)*nn);
            /* k ステップ処理 */
            run_react_loop_steps(tmp, used, &nn, wind_mode, k);
            int cost = nn;  /* 発動時点のダイス総数（除外前）がコスト */
            /* 現時点の最高 die_value ダイスを除外し残りを循環+1 */
            int drop = 0;
            int best_val = die_value(tmp[0].sides, tmp[0].face);
            for (int i = 1; i < nn; i++) {
                int v = die_value(tmp[i].sides, tmp[i].face);
                if (v > best_val) { best_val = v; drop = i; }
            }
            Die  t2[MAX_DICE]; int u2[MAX_DICE]; int nn2 = 0;
            for (int i = 0; i < nn; i++) {
                if (i == drop) continue;
                t2[nn2]       = tmp[i];
                t2[nn2].face  = cyclic_adjust(t2[nn2].sides, t2[nn2].face, +1);
                u2[nn2]       = used[i];  /* 既に発動済みのものは発動済みのまま */
                nn2++;
            }
            /* 除外した drop の used 状態に関係なく残りのループを再開 */
            run_react_loop(t2, u2, &nn2, wind_mode, 0);
            int s = score_baseline(t2, nn2) - cost;  /* コスト差し引き */
            if (s > best_score) { best_score = s; *out_option = 2; }
        }
    } else {
        /* n=1 のときは除外できないので循環+1のみ（コストあり） */
        Die tmp[MAX_DICE]; int used[MAX_DICE]; int nn = n_dice_raw;
        memcpy(tmp, dice_raw, sizeof(Die)*nn); memset(used, 0, sizeof(int)*nn);
        tmp[0].face = cyclic_adjust(tmp[0].sides, tmp[0].face, +1);
        run_react_loop(tmp, used, &nn, wind_mode, 0);
        int s = score_baseline(tmp, nn) - nn;  /* コスト差し引き */
        if (s > best_score) { best_score = s; *out_option = 2; }
    }

    return best_score;
}

/* ----------------------------------------------------------------
 * 付喪B: 下限保証振り直し（コスト 0）
 *   raw 状態を受け取る。任意ダイス1つを振り直す（下限保証）。
 *   振り直し後のダイスは used=1（反応済み）→ 連鎖しない（獣人との差別化）。
 *   ただし振り直し直後にトリガー条件を満たす場合は連鎖発火する
 *   （react_loop がキューに積む前に used=1 にするのでキューに積まれない）。
 *   ※ run_react_loop は呼び出し前の used=1 のダイスをスキップするため、
 *     振り直したダイスは他の連鎖の対象にはならない。
 * ---------------------------------------------------------------- */
static int score_tsukumogami_B(const Die *dice_raw, int n_dice_raw,
                                WindMode wind_mode, int *out_used)
{
    int best_target = -1;
    double best_exp_gain = 0.0;
    for (int i = 0; i < n_dice_raw; i++) {
        int n        = dice_raw[i].sides;
        int old_face = dice_raw[i].face;
        int old_val  = die_value(n, old_face);
        double exp_new = 0.0;
        for (int f = 1; f <= n; f++)
            exp_new += (f <= old_face) ? old_val : die_value(n, f);
        exp_new /= n;
        double g = exp_new - old_val;
        if (g > best_exp_gain) { best_exp_gain = g; best_target = i; }
    }
    Die  tmp[MAX_DICE]; int used[MAX_DICE]; int n = n_dice_raw;
    memcpy(tmp, dice_raw, sizeof(Die)*n); memset(used, 0, sizeof(int)*n);
    *out_used = (best_target >= 0) ? 1 : 0;
    if (best_target >= 0) {
        int old_face = tmp[best_target].face;
        int new_face = roll_die(tmp[best_target].sides);
        if (new_face <= old_face) new_face = old_face;  /* 下限保証 */
        tmp[best_target].face = new_face;
        used[best_target] = 1;  /* 振り直し後は反応済みにマーク */
    }
    run_react_loop(tmp, used, &n, wind_mode, 0);
    return score_baseline(tmp, n) + 1;
}

/* ----------------------------------------------------------------
 * 半霊: 越境（反応ループ完了後に1回）
 *   全ての反応終了後、used=1 のダイスを最大 1 個選び used=0 に戻す。
 *   その後再度 run_react_loop を走らせ、リセットしたダイスの連鎖を再起動させる。
 *   期待利得が最大の反応済みダイス 1 個を選択する。
 *   対象がない場合は能力を使わない。コストなし。
 * ---------------------------------------------------------------- */
static int score_hanrei(const Die *dice_raw, int n_dice_raw,
                        WindMode wind_mode, int *out_used)
{
    /* ベースライン（能力不使用・フルループ） */
    Die  tmp[MAX_DICE]; int used[MAX_DICE]; int n = n_dice_raw;
    memcpy(tmp, dice_raw, sizeof(Die)*n); memset(used, 0, sizeof(int)*n);
    run_react_loop(tmp, used, &n, wind_mode, 0);
    int base_score = score_baseline(tmp, n);
    *out_used = 0;

    /* used=1 のダイス中から期待利得最大の 1 個を選択 */
    int best_target = -1;
    double best_gain = 0.0;
    for (int i = 0; i < n; i++) {
        if (!used[i]) continue;
        if (!triggers(tmp[i].sides, tmp[i].face)) continue;
        Die  t2[MAX_DICE]; int u2[MAX_DICE]; int n2 = n;
        memcpy(t2, tmp, sizeof(Die)*n); memcpy(u2, used, sizeof(int)*n);
        u2[i] = 0;  /* リセット */
        run_react_loop(t2, u2, &n2, wind_mode, 0);
        double g = score_baseline(t2, n2) - base_score;
        if (g > best_gain) { best_gain = g; best_target = i; }
    }

    if (best_target < 0) return base_score;

    /* 選択したダイスを used=0 に戻して再ループ */
    used[best_target] = 0;
    run_react_loop(tmp, used, &n, wind_mode, 0);
    *out_used = 1;
    return score_baseline(tmp, n);
}

/* ----------------------------------------------------------------
 * 機械人: d10→d12 置換 + 通常反応ループ + -1ルールなしでスコア計算。
 *   d10 を 1 個 d12 に置換してロール。
 *   反応ループは通常通り実行（d12 含む全ダイスがトリガー対象）。
 *   スコア計算は -1 ルール適用なし（die_value_no_penalty）。
 *   補正なし（スコアそのまま返す）。
 * ---------------------------------------------------------------- */
static int score_machine_d12(const int *pool_sides, int n_pool,
                             WindMode wind_mode)
{
    /* d10 を 1 個 d12 に置換 */
    int replaced_pool[MAX_DICE];
    int replaced = 0;
    for (int i = 0; i < n_pool; i++) {
        if (pool_sides[i] == 10 && !replaced) {
            replaced_pool[i] = 12;
            replaced = 1;
        } else {
            replaced_pool[i] = pool_sides[i];
        }
    }
    /* ロール */
    Die dice[MAX_DICE]; int used[MAX_DICE]; int n = n_pool;
    for (int i = 0; i < n_pool; i++) {
        dice[i].sides = replaced_pool[i];
        dice[i].face  = roll_die(replaced_pool[i]);
        used[i] = 0;
    }
    /* 通常反応ループ（全ダイス対象、skip なし） */
    run_react_loop(dice, used, &n, wind_mode, 0);
    /* -1 ルール適用なしで合計 */
    int total = 0;
    for (int i = 0; i < n; i++)
        total += die_value_no_penalty(dice[i].sides, dice[i].face);
    return total;
}

/* ----------------------------------------------------------------
 * 全構成列挙・種族効果強さ比較
 * ---------------------------------------------------------------- */
static void run_race_ability_comparison(int trials_per_pool, WindMode wind_mode,
                                        const char *out_dir)
{
    /* 集計配列 */
    double delta_sum_all[N_RACES];
    long   delta_cnt_all[N_RACES];
    double delta_sum_by_n[N_RACES][MAX_N + 1];
    long   delta_cnt_by_n[N_RACES][MAX_N + 1];
    long   use_cnt_by_n[N_RACES][MAX_N + 1];       /* per-n 使用試行数 */
    double used_delta_sum_by_n[N_RACES][MAX_N + 1]; /* per-n 使用時delta合計 */
    long   homo_option_cnt[3];
    long   homo_option_cnt_by_n[3][MAX_N + 1];
    /* 使用率・発動時効果量用 */
    long   use_cnt_all[N_RACES];
    double used_delta_sum_all[N_RACES];  /* 使用した試行のみのdelta合計 */

    for (int r = 0; r < N_RACES; r++) {
        delta_sum_all[r] = 0.0;
        delta_cnt_all[r] = 0;
        use_cnt_all[r]   = 0;
        used_delta_sum_all[r] = 0.0;
        for (int n = 0; n <= MAX_N; n++) {
            delta_sum_by_n[r][n]      = 0.0;
            delta_cnt_by_n[r][n]      = 0;
            use_cnt_by_n[r][n]        = 0;
            used_delta_sum_by_n[r][n] = 0.0;
        }
    }
    homo_option_cnt[0] = homo_option_cnt[1] = homo_option_cnt[2] = 0;
    for (int o = 0; o < 3; o++)
        for (int n = 0; n <= MAX_N; n++)
            homo_option_cnt_by_n[o][n] = 0;

    /* 確定プール配列（最大 MAX_DICE 個） */
    int pool[MAX_DICE];
    int counts[5];

    /* --- 総構成数を事前計算（進捗表示用）: n_pool_total >= 2 のみ --- */
    long n_total = 0;
    for (int a=0; a<=MAX_N; a++)
    for (int b=0; b<=MAX_N-a; b++)
    for (int c=0; c<=MAX_N-a-b; c++)
    for (int d=1; d<=MAX_N-a-b-c; d++)
    for (int e=0; e<=MAX_N-a-b-c-d; e++) {
        int sub = a+b+c+d+e;
        if (sub + 0 >= 2) n_total++;  /* d12なし */
        if (sub + 1 >= 2) n_total++;  /* d12あり */
    }
    printf("  総構成数: %ld\n", n_total);
    fflush(stdout);

    long n_done = 0;

    for (counts[0]=0; counts[0]<=MAX_N; counts[0]++)
    for (counts[1]=0; counts[1]<=MAX_N-(counts[0]); counts[1]++)
    for (counts[2]=0; counts[2]<=MAX_N-(counts[0]+counts[1]); counts[2]++)
    for (counts[3]=1; counts[3]<=MAX_N-(counts[0]+counts[1]+counts[2]); counts[3]++)
    for (counts[4]=0; counts[4]<=MAX_N-(counts[0]+counts[1]+counts[2]+counts[3]); counts[4]++) {
        int sub = counts[0]+counts[1]+counts[2]+counts[3]+counts[4];

        for (int d12 = 0; d12 <= 1; d12++) {
            int np = 0;
            for (int t = 0; t < N_DICE_TYPES; t++)
                for (int k = 0; k < counts[t]; k++)
                    pool[np++] = DICE_SIDES[t];
            if (d12) pool[np++] = 12;
            int n_pool = np;
            int n_pool_total = sub + d12;  /* 横軸用 */

            /* MIN_POOL=2: d10のみ（n_pool_total==1）は集計しない */
            if (n_pool_total < 2) { n_done++; continue; }
            double sum_delta[N_RACES];
            for (int r = 0; r < N_RACES; r++) sum_delta[r] = 0.0;
            long   sum_homo[3] = {0, 0, 0};
            long   sum_used[N_RACES];
            double sum_used_delta[N_RACES];
            for (int r = 0; r < N_RACES; r++) { sum_used[r] = 0; sum_used_delta[r] = 0.0; }

            Die  dice_raw[MAX_DICE];   /* ロール直後の raw 状態 */
            Die  dice_base[MAX_DICE];  /* 通常反応後の状態 */
            int  used_base[MAX_DICE];
            int  n_raw, n_base;

            for (int tr = 0; tr < trials_per_pool; tr++) {
                /* Step1: ロールのみ（反応なし） */
                n_raw = n_pool;
                for (int i = 0; i < n_pool; i++) {
                    dice_raw[i].sides = pool[i];
                    dice_raw[i].face  = roll_die(pool[i]);
                }

                /* Step2: 通常反応ループ → base スコア */
                n_base = n_raw;
                memcpy(dice_base, dice_raw, sizeof(Die) * n_raw);
                memset(used_base, 0, sizeof(int) * n_raw);
                run_react_loop(dice_base, used_base, &n_base, wind_mode, 0);
                int base = score_baseline(dice_base, n_base);

                /* 0: 人間 （raw→反転→react） */
                {
                    int hu = 0;
                    int s = score_human(dice_raw, n_raw, wind_mode, &hu);
                    double d = s - base;
                    sum_delta[0] += d;
                    if (hu) { sum_used[0]++; sum_used_delta[0] += d; }
                }

                /* 1: 機械人 （d12プール・通常反応・-1ルールなし） */
                {
                    int m12 = score_machine_d12(pool, n_pool, wind_mode);
                    double d = m12 - base;
                    sum_delta[1] += d;
                    sum_used[1]++;
                    sum_used_delta[1] += d;
                }

                /* 2: 獣人 （raw→ペナルティ振り直し used=0 →react） */
                {
                    int bu = 0;
                    int s = score_beast(dice_raw, n_raw, wind_mode, &bu);
                    double d = s - base;
                    sum_delta[2] += d;
                    if (bu) { sum_used[2]++; sum_used_delta[2] += d; }
                }

                /* 3: ホムンクルス（A=react後スコア+α, B/C=raw→ability→react） */
                {
                    int opt = -1;
                    int s = score_homunculus(dice_raw, n_raw, wind_mode, &opt);
                    double d = s - base;
                    sum_delta[3] += d;
                    if (opt >= 0) { sum_homo[opt]++; sum_used[3]++; sum_used_delta[3] += d; }
                }

                /* 4: 付喪B （raw→振り直し used=1 →react） */
                {
                    int bu2 = 0;
                    int s = score_tsukumogami_B(dice_raw, n_raw, wind_mode, &bu2);
                    double d = s - base;
                    sum_delta[4] += d;
                    if (bu2) { sum_used[4]++; sum_used_delta[4] += d; }
                }

                /* 5: 半霊 （react後 used=1を1個 used=0にリセット→再react） */
                {
                    int hu = 0;
                    int s = score_hanrei(dice_raw, n_raw, wind_mode, &hu);
                    double d = s - base;
                    sum_delta[5] += d;
                    if (hu) { sum_used[5]++; sum_used_delta[5] += d; }
                }
            }

            /* 集計 */
            for (int r = 0; r < N_RACES; r++) {
                double avg_d = sum_delta[r] / trials_per_pool;
                delta_sum_all[r]                  += avg_d;
                delta_cnt_all[r]                  += 1;
                delta_sum_by_n[r][n_pool_total]      += avg_d;
                delta_cnt_by_n[r][n_pool_total]      += 1;
                use_cnt_by_n[r][n_pool_total]         += sum_used[r];
                used_delta_sum_by_n[r][n_pool_total]  += sum_used_delta[r];
                use_cnt_all[r]                        += sum_used[r];
                used_delta_sum_all[r]                 += sum_used_delta[r];
            }
            for (int o = 0; o < 3; o++) {
                homo_option_cnt[o] += sum_homo[o];
                homo_option_cnt_by_n[o][n_pool_total] += sum_homo[o];
            }

            n_done++;
            if (n_done % 100 == 0 || n_done == n_total) {
                printf("PROGRESS4: %ld / %ld  (%.1f%%)\n",
                       n_done, n_total, 100.0 * n_done / n_total);
                fflush(stdout);
            }
        }
    }

    /* --- コンソール出力 --- */
    printf("\n");
    printf("============================================================\n");
    printf("  Part4: 六種族 判定時効果 強さ比較（全構成列挙）\n");
    printf("  trials/pool=%d, wind_mode=%s, max_pool=%d\n",
           trials_per_pool,
           wind_mode == WIND_INVERT ? "invert" : "halfturn", MAX_N);
    printf("  ※ d10>=1固定、d12は0-1個、全有効構成の平均を表示\n");
    printf("============================================================\n");
    printf("%-14s  avg_delta  use_rate  delta|use   sample_count\n", "種族");
    printf("--------------  ---------  --------  ----------  ------------\n");

    static const char *race_names[N_RACES] = {
        "人間", "機械人", "獣人", "ホムンクルス", "付喪B(入替)", "半霊"
    };
    static const char *race_names_csv[N_RACES] = {
        "Hume", "Makina", "Bestia", "Homunculus", "Relicia", "Umbra"
    };
    for (int r = 0; r < N_RACES; r++) {
        double avg = delta_cnt_all[r] > 0
                   ? delta_sum_all[r] / (double)delta_cnt_all[r]
                   : 0.0;
        long ttotal = delta_cnt_all[r] * (long)trials_per_pool;
        double use_rate = ttotal > 0
                        ? (double)use_cnt_all[r] / ttotal
                        : 0.0;
        double delta_given_use = use_cnt_all[r] > 0
                               ? used_delta_sum_all[r] / (double)use_cnt_all[r]
                               : 0.0;
        printf("%-14s  %+9.4f  %7.1f%%  %+10.4f  %12ld\n",
               race_names[r], avg, use_rate * 100.0, delta_given_use,
               delta_cnt_all[r]);
    }
    printf("----\n");
    printf("※ avg_delta    = 種族効果による達成値の平均増分（不使用時は0）\n");
    printf("※ use_rate     = 能力を使用した試行の割合\n");
    printf("※ delta|use    = 能力を使用した試行のみの平均増分\n");

    /* ホムンクルス三択の選択率 */
    long homo_total = homo_option_cnt[0] + homo_option_cnt[1] + homo_option_cnt[2];
    if (homo_total > 0) {
        printf("\nホムンクルス三択選択率:\n");
        static const char *homo_names[3] = {"A(全-1→0)", "B(最大値固定-3)", "C(全循環+1-n)"};
        for (int o = 0; o < 3; o++) {
            printf("  %-14s : %6ld  (%.1f%%)\n",
                   homo_names[o], homo_option_cnt[o],
                   100.0 * homo_option_cnt[o] / homo_total);
        }
    }

    /* --- CSV出力: race_ability_by_n.csv --- */
    char csv_path[512];
    snprintf(csv_path, sizeof(csv_path), "%srace_ability_by_n.csv", out_dir);
    FILE *fp = fopen(csv_path, "w");
    if (fp) {
        fprintf(fp, "n_pool");
        for (int r = 0; r < N_RACES; r++) fprintf(fp, ",%s", race_names_csv[r]);
        fprintf(fp, "\n");
        for (int n = 1; n <= MAX_N; n++) {
            fprintf(fp, "%d", n);
            for (int r = 0; r < N_RACES; r++) {
                if (delta_cnt_by_n[r][n] > 0)
                    fprintf(fp, ",%.4f",
                            delta_sum_by_n[r][n] / (double)delta_cnt_by_n[r][n]);
                else
                    fprintf(fp, ",");
            }
            fprintf(fp, "\n");
        }
        fclose(fp);
        printf("\nCSV出力: %s\n", csv_path);
    } else {
        perror("fopen race_ability_by_n.csv");
    }

    /* --- CSV出力: race_use_rate_by_n.csv --- */
    snprintf(csv_path, sizeof(csv_path), "%srace_use_rate_by_n.csv", out_dir);
    fp = fopen(csv_path, "w");
    if (fp) {
        fprintf(fp, "n_pool");
        for (int r = 0; r < N_RACES; r++) fprintf(fp, ",%s", race_names_csv[r]);
        fprintf(fp, "\n");
        for (int n = 1; n <= MAX_N; n++) {
            fprintf(fp, "%d", n);
            for (int r = 0; r < N_RACES; r++) {
                long total = (long)delta_cnt_by_n[r][n] * trials_per_pool;
                if (total > 0)
                    fprintf(fp, ",%.4f",
                            (double)use_cnt_by_n[r][n] / (double)total);
                else
                    fprintf(fp, ",");
            }
            fprintf(fp, "\n");
        }
        fclose(fp);
        printf("CSV出力: %s\n", csv_path);
    } else {
        perror("fopen race_use_rate_by_n.csv");
    }

    /* --- CSV出力: race_delta_use_by_n.csv --- */
    snprintf(csv_path, sizeof(csv_path), "%srace_delta_use_by_n.csv", out_dir);
    fp = fopen(csv_path, "w");
    if (fp) {
        fprintf(fp, "n_pool");
        for (int r = 0; r < N_RACES; r++) fprintf(fp, ",%s", race_names_csv[r]);
        fprintf(fp, "\n");
        for (int n = 1; n <= MAX_N; n++) {
            fprintf(fp, "%d", n);
            for (int r = 0; r < N_RACES; r++) {
                if (use_cnt_by_n[r][n] > 0)
                    fprintf(fp, ",%.4f",
                            used_delta_sum_by_n[r][n] / (double)use_cnt_by_n[r][n]);
                else
                    fprintf(fp, ",");
            }
            fprintf(fp, "\n");
        }
        fclose(fp);
        printf("CSV出力: %s\n", csv_path);
    } else {
        perror("fopen race_delta_use_by_n.csv");
    }

    /* --- CSV出力: homunculus_option_distribution.csv --- */
    snprintf(csv_path, sizeof(csv_path), "%shomunculus_option_distribution.csv", out_dir);
    fp = fopen(csv_path, "w");
    if (fp) {
        fprintf(fp, "option,count,rate\n");
        static const char *homo_csv_names[3] = {
            "A(all_neg_to_0)", "B(max_fix-3)", "C(all_cyc+1-n)"
        };
        for (int o = 0; o < 3; o++) {
            double rate = homo_total > 0
                        ? (double)homo_option_cnt[o] / homo_total
                        : 0.0;
            fprintf(fp, "%s,%ld,%.4f\n",
                    homo_csv_names[o], homo_option_cnt[o], rate);
        }
        fclose(fp);
        printf("CSV出力: %s\n", csv_path);
    } else {
        perror("fopen homunculus_option_distribution.csv");
    }

    /* --- CSV出力: homunculus_option_by_n.csv --- */
    snprintf(csv_path, sizeof(csv_path), "%shomunculus_option_by_n.csv", out_dir);
    fp = fopen(csv_path, "w");
    if (fp) {
        fprintf(fp, "n_pool,A_rate,B_rate,C_rate\n");
        for (int n = 1; n <= MAX_N; n++) {
            long total_n = homo_option_cnt_by_n[0][n]
                         + homo_option_cnt_by_n[1][n]
                         + homo_option_cnt_by_n[2][n];
            fprintf(fp, "%d", n);
            for (int o = 0; o < 3; o++) {
                double rate = total_n > 0
                            ? (double)homo_option_cnt_by_n[o][n] / total_n
                            : 0.0;
                fprintf(fp, ",%.4f", rate);
            }
            fprintf(fp, "\n");
        }
        fclose(fp);
        printf("CSV出力: %s\n", csv_path);
    } else {
        perror("fopen homunculus_option_by_n.csv");
    }
}

/* ================================================================
 * Part 5: 1d10(固定) + N個のランダム属性ダイス 合計達成値の平均
 *
 * テストプレイ基準値算出用。
 * デフォルトで振る1d10は固定。追加ダイスは
 * {d4(火), d6(地), d8(風), d20(水)} の4種から一様ランダムに選ぶ。
 * （d10(闇)は固定枠、d12(光)は特殊枠なので除外）
 *
 * 各試行ごとに種族（6種）もランダムに選択し、
 * 反応ルール＋種族能力を最大利得で適用した達成値を記録する。
 *
 * 出力CSV: basic4_pool_avg.csv
 *   n_extra, avg, p50, p90, p99
 * ================================================================ */

static void run_basic4_pool_avg(int trials, WindMode wind_mode, const char *out_dir)
{
    /* 基本4ダイス: d4/d6/d8/d20 */
    static const int BASIC4[4] = {4, 6, 8, 20};
    const int MAX_EXTRA = 9;  /* 追加ダイスの最大個数 */
    const int N_RACE    = 6;  /* 種族数 */

    printf("\n");
    printf("============================================================\n");
    printf("  Part5: 1d10(固定) + N×ランダム基本4ダイス 合計達成値\n");
    printf("  基本4ダイス = {d4(火), d6(地), d8(風), d20(水)}\n");
    printf("  各試行: ダイス構成・種族ともにランダム選択\n");
    printf("  反応ルール＋種族能力(最大利得)を適用\n");
    printf("  trials=%d,  N=0~%d\n", trials, MAX_EXTRA);
    printf("============================================================\n");
    printf("%-10s  %10s  %8s  %8s  %8s\n", "n_extra", "avg", "p50", "p90", "p99");
    printf("----------  ----------  --------  --------  --------\n");

    char csv_path[512];
    snprintf(csv_path, sizeof(csv_path), "%sbasic4_pool_avg.csv", out_dir);
    FILE *fp = fopen(csv_path, "w");
    if (!fp) { perror("fopen basic4_pool_avg.csv"); return; }
    fprintf(fp, "n_extra,avg,p50,p90,p99\n");

    Die  dice_raw[MAX_DICE];

    for (int n = 0; n <= MAX_EXTRA; n++) {
        int *totals = (int *)malloc(sizeof(int) * trials);
        if (!totals) { perror("malloc"); exit(1); }

        for (int t = 0; t < trials; t++) {
            /* ---- プール構築: d10固定 + n個ランダム基本4ダイス ---- */
            int pool[MAX_DICE];
            pool[0] = 10;
            for (int i = 0; i < n; i++)
                pool[1 + i] = BASIC4[rand() % 4];
            int n_pool = 1 + n;

            /* ---- ロール (dice_raw) ---- */
            for (int i = 0; i < n_pool; i++) {
                dice_raw[i].sides = pool[i];
                dice_raw[i].face  = roll_die(pool[i]);
            }

            /* ---- 種族をランダム選択し、最大利得で処理 ---- */
            int race  = rand() % N_RACE;
            int dummy = 0;
            int score;

            switch (race) {
                case 0: /* 人間: 反転（コスト -n_pool） */
                    score = score_human(dice_raw, n_pool, wind_mode, &dummy);
                    break;
                case 1: /* 機械人: d10→d12置換・-1ルールなし（内部で再ロール） */
                    score = score_machine_d12(pool, n_pool, wind_mode);
                    break;
                case 2: /* 獣人: ペナルティ付き振り直し */
                    score = score_beast(dice_raw, n_pool, wind_mode, &dummy);
                    break;
                case 3: { /* ホムンクルス: 後出し三択 */
                    int opt = -1;
                    score = score_homunculus(dice_raw, n_pool, wind_mode, &opt);
                    break;
                }
                case 4: /* 付喪B: 下限保証振り直し */
                    score = score_tsukumogami_B(dice_raw, n_pool, wind_mode, &dummy);
                    break;
                case 5: /* 半霊: 反応済みリセット */
                    score = score_hanrei(dice_raw, n_pool, wind_mode, &dummy);
                    break;
                default:
                    score = 0;
                    break;
            }
            totals[t] = score;
        }

        /* ---- ソートしてパーセンタイル計算 ---- */
        qsort(totals, trials, sizeof(int), cmp_int);
        double sum = 0.0;
        for (int i = 0; i < trials; i++) sum += totals[i];
        double avg = sum / trials;
        int p50 = totals[(int)(0.50 * (trials - 1))];
        int p90 = totals[(int)(0.90 * (trials - 1))];
        int p99 = totals[(int)(0.99 * (trials - 1))];

        printf("%10d  %10.3f  %8d  %8d  %8d\n", n, avg, p50, p90, p99);
        fprintf(fp, "%d,%.4f,%d,%d,%d\n", n, avg, p50, p90, p99);
        free(totals);
    }

    fclose(fp);
    printf("\nCSV出力: %s\n", csv_path);
}

/* ================================================================
 * main
 *   引数: [出力ディレクトリパス]
 *   省略時はカレントディレクトリに出力
 * ================================================================ */
int main(int argc, char *argv[])
{
    if (argc >= 3)
        srand((unsigned int)atoi(argv[2]));
    else
        srand((unsigned int)time(NULL));

    /* 出力先ディレクトリ（末尾にパス区切りを付ける） */
    char out_dir[512] = "";
    if (argc >= 2) {
        snprintf(out_dir, sizeof(out_dir), "%s\\", argv[1]);
    }

    const WindMode WIND = WIND_HALFTURN;  /* WIND_INVERTに変更可 */

    /* ---- Part 1: 単一ダイス×5 参照表 ---- */
    printf("=== Part1: 単一ダイス x5 参照表 (trials=20000) ===\n");
    printf("%-6s  avg/die  p50/die  p90/die  p99/die\n", "pool");
    printf("------  -------  -------  -------  -------\n");

    static const int   ref_sides[] = {4, 6, 8, 10, 12, 20};
    static const char *ref_names[] = {"d4","d6","d8","d10","d12","d20"};
    for (int t = 0; t < 6; t++) {
        int pool[5];
        for (int i = 0; i < 5; i++) pool[i] = ref_sides[t];
        double avg; int p50, p90, p99;
        simulate_pool(pool, 5, 20000, WIND, &avg, &p50, &p90, &p99);
        printf("%-6s  %7.3f  %7.1f  %7.1f  %7.1f\n",
               ref_names[t], avg/5.0,
               (double)p50/5.0, (double)p90/5.0, (double)p99/5.0);
    }

    /* ---- Part 2: 全列挙・限界貢献度分析 ---- */
    printf("\n=== Part2: 全列挙 限界貢献度分析 (trials/comp=1000, max=%d) ===\n", MAX_N);
    printf("計算中（数分かかる場合があります）...\n");
    fflush(stdout);
    run_full_enumeration(10000, WIND, out_dir);

    /* ---- Part 3: 難易度設計テーブル ---- */
    printf("\n=== Part3: 難易度設計テーブル (trials=100000) ===\n");
    fflush(stdout);
    run_difficulty_table(100000, WIND, out_dir);

    /* ---- Part 4: 六種族 判定時効果 強さ比較 ---- */
    printf("\n=== Part4: 六種族 判定時効果 強さ比較 (trials/pool=200, max=%d) ===\n", MAX_N);
    printf("計算中（数分かかる場合があります）...\n");
    fflush(stdout);
    run_race_ability_comparison(10000, WIND, out_dir);

    /* ---- Part 5: 1d10 + N×ランダム基本4ダイス 合計達成値の平均 ---- */
    printf("\n=== Part5: 1d10(固定) + N×ランダム基本4ダイス 合計達成値 (trials=50000) ===\n");
    fflush(stdout);
    run_basic4_pool_avg(50000, WIND, out_dir);

    return 0;
}
