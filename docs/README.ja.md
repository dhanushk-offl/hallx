# hallx（日本語）

[![Tests](https://github.com/dhanushk-offl/hallx/actions/workflows/test.yml/badge.svg)](https://github.com/dhanushk-offl/hallx/actions/workflows/test.yml)
[![Release](https://github.com/dhanushk-offl/hallx/actions/workflows/release.yml/badge.svg)](https://github.com/dhanushk-offl/hallx/actions/workflows/release.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/dhanushk-offl/hallx/badge)](https://scorecard.dev/viewer/?uri=github.com/dhanushk-offl/hallx)
[![PyPI](https://img.shields.io/pypi/v/hallx.svg)](https://pypi.org/project/hallx/)

`hallx` は、LLM 出力向けの軽量なリスクスコアリング・ガードレールライブラリです。  
本番環境で回答を採用する前に、次の実務的な問いに答えます。

`この出力はどれくらいリスクが高いか？`

## なぜ Hallx か

本番での LLM 失敗は見えにくいことが多いです。

- 流暢だが根拠のない回答
- 見た目は正しいが厳密な JSON コンシューマで失敗
- 同一プロンプトでも生成の揺れが大きい

Hallx は意思決定レイヤとして機能します。

- スコア化
- 問題点の可視化
- `proceed` / `retry` の判断
- フィードバックを使った閾値調整

## Hallx が提供するもの

| 機能 | 出力 |
|---|---|
| リスクスコア | `confidence`（`0.0`〜`1.0`） |
| リスク分類 | `risk_level`（`high` / `medium` / `low`） |
| 診断情報 | `issues` |
| 実行時ヒント | `recommendation` |
| 運用ループ | フィードバック保存 + キャリブレーション |

## 想定ユーザー

- RAG / チャット機能を提供するチーム
- 機械処理 JSON を返すバックエンド
- LLM 出力が後続処理を起動する業務フロー
- リトライ/ブロック方針を管理する Ops/QA チーム

注: 医療・法務・金融など高リスク領域では、Hallx 単体ではなくドメイン検証と人的レビューを併用してください。

## スコアリングモデル

Hallx は 3 つのヒューリスティック信号を使います。

- `schema`: 構造的妥当性
- `consistency`: 複数生成時の安定性
- `grounding`: 主張とコンテキストの整合性

```text
confidence = clamp(
  schema_score * w_schema +
  consistency_score * w_consistency +
  grounding_score * w_grounding,
  0.0, 1.0
)
```

既定（`balanced`）重み:
- `w_schema = 0.34`
- `w_consistency = 0.33`
- `w_grounding = 0.33`

リスクマッピング:
- `< 0.40` -> `high`
- `< 0.75` -> `medium`
- `>= 0.75` -> `low`

チェックがスキップされた場合は、過信を防ぐために既定でペナルティが適用されます。

## エンドツーエンドの流れ

![Hallx workflow](images/hallx-working-flow.svg)

1. プロンプトと任意のコンテキスト/スキーマを受け取る
2. Adapter/Callable で応答を生成
3. `schema` / `consistency` / `grounding` を実行
4. `confidence` と `risk_level` を計算
5. `recommendation` に基づき `proceed` / `retry` を適用
6. レビュー済み結果を保存し、閾値を継続調整

## Quick Start

```python
from hallx import Hallx

checker = Hallx(profile="balanced")
result = checker.check(
    prompt="Summarize refund policy",
    response={"summary": "Refunds are allowed within 30 days."},
    context=["Refunds are allowed within 30 days of purchase."],
)

print(result.confidence, result.risk_level)
print(result.issues)
print(result.recommendation)
```

## Safety Profiles

| Profile | 目的 | 既定 `consistency_runs` | Skip penalty |
|---|---|---:|---:|
| `fast` | 低レイテンシ | 2 | 0.15 |
| `balanced` | 汎用 | 3 | 0.25 |
| `strict` | 厳格運用 | 4 | 0.40 |

## 関連ドキュメント

- English: [README.en.md](README.en.md)
- தமிழ்: [README.ta.md](README.ta.md)
- മലയാളം: [README.ml.md](README.ml.md)
- Usage: [USAGE.md](USAGE.md)
- Production: [PRODUCTION.md](PRODUCTION.md)
