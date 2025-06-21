# LLM CSV Classifier

OpenAI APIのStructured Outputsを使用してCSVファイルの各行を自動分類するツールです。

## 機能

- CSVファイルの各行を自動分類（デフォルト：10種類のカテゴリ）
- OpenAI API または Azure OpenAI ServiceのStructured Outputsによる高精度な分類
- 動的カテゴリ定義対応（カテゴリの追加・変更が簡単）
- 分類理由と信頼度スコア付き
- 結果をCSVファイルに出力可能

## 前提条件

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (Python パッケージマネージャー)

## セットアップ

1. 依存関係のインストール:
```bash
uv sync
```

2. 環境変数の設定:
```bash
cp .env.example .env
```

`.env`ファイルに以下を設定してください：

### OpenAI API使用の場合:
```bash
OPENAI_API_KEY=your-openai-api-key-here
MODEL_NAME=gpt-4o-2024-08-06
```

### Azure OpenAI Service使用の場合:
```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-openai-api-key-here
AZURE_API_VERSION=2024-10-21
MODEL_NAME=your-deployment-name
```

## 使用方法

### コマンドライン引数で実行（推奨）
```bash
uv run python main.py input.csv -o output.csv
```

### ヘルプの表示
```bash
uv run python main.py --help
```

### インタラクティブモード
```bash
uv run python main.py --interactive
```

プログラムが以下を求めます:
- 入力CSVファイルのパス
- 出力ファイルのパス（省略可）

## 分類カテゴリ

デフォルトで以下のカテゴリが用意されています：

- Technology（技術）
- Business（ビジネス）
- Finance（金融）
- Health（健康）
- Education（教育）
- Entertainment（エンターテイメント）
- Sports（スポーツ）
- Politics（政治）
- Science（科学）
- Other（その他）

### カテゴリのカスタマイズ

#### 方法1: プログラム実行時に指定（推奨）

```python
from main import CSVClassifier

custom_categories = {
    "URGENT": "緊急性の高いタスク",
    "NORMAL": "通常のタスク", 
    "LOW": "優先度の低いタスク"
}

classifier = CSVClassifier(categories=custom_categories)
result = classifier.process_csv("input.csv", "output.csv")
```

#### 方法2: DEFAULT_CATEGORIESを編集

`main.py`の`DEFAULT_CATEGORIES`辞書を直接編集：

```python
DEFAULT_CATEGORIES = {
    "CATEGORY1": "カテゴリ1の説明",
    "CATEGORY2": "カテゴリ2の説明",
    "CATEGORY3": "カテゴリ3の説明"
}
```

**注意**: カテゴリを変更した場合、EnumとPydanticモデルは自動的に動的生成されるため、手動でEnumクラスを編集する必要はありません。

### システムプロンプトのカスタマイズ

```python
classifier = CSVClassifier(system_prompt="カスタムプロンプト")
```

## 出力形式

元のCSVデータに以下の列が追加されます:
- `category`: 分類されたカテゴリ
- `confidence`: 信頼度スコア (0.0-1.0)
- `reason`: 分類理由

## 技術仕様

- Python 3.10+
- uv (パッケージマネージャー)
- OpenAI API または Azure OpenAI Service
- 対応モデル: GPT-4o-2024-08-06
- Pydantic v2でのStructured Outputs
- Pandasによる高速CSV処理

## サポートするサービス

### OpenAI API
- モデル: `gpt-4o-2024-08-06`
- 直接OpenAI APIを使用

### Azure OpenAI Service
- API Version: `2024-10-21` (GA) または `2024-08-01-preview`
- モデル: GPT-4o-2024-08-06のデプロイ
- **対応リージョン（2025年現在）**: 
  - Australia East, Brazil South, Canada East
  - East US, East US 2, France Central
  - Germany West Central, Italy North, Japan East
  - Korea Central, North Central US, Norway East
  - South Africa North, South Central US, South India
  - Spain Central, Sweden Central, Switzerland North
  - UAE North, UK South, West Europe
  - West US, West US 3
- Global Standard デプロイメントで利用可能