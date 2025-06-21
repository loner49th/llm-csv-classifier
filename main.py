import os
import csv
import argparse
from enum import Enum
from typing import List, Dict, Any
from pydantic import BaseModel
from openai import OpenAI, AzureOpenAI
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

# 分類対象のカテゴリ定義
DEFAULT_CATEGORIES = {
    "TECHNOLOGY": "技術、IT、プログラミング、AI関連",
    "BUSINESS": "ビジネス、経営、マーケティング関連", 
    "FINANCE": "金融、投資、経済関連",
    "HEALTH": "健康、医療、フィットネス関連",
    "EDUCATION": "教育、学習、研修関連",
    "ENTERTAINMENT": "エンターテイメント、映画、音楽関連",
    "SPORTS": "スポーツ、運動、競技関連",
    "POLITICS": "政治、政策、社会問題関連",
    "SCIENCE": "科学、研究、学術関連",
    "OTHER": "その他のカテゴリ"
}

def create_category_enum(categories: dict):
    """動的にCategoryTagを生成"""
    return Enum('CategoryTag', {key: key.lower() for key in categories.keys()}, type=str)

def generate_system_prompt(categories: dict) -> str:
    """カテゴリ情報を含むシステムプロンプトを生成"""
    category_list = "\n".join([f"- {key}: {desc}" for key, desc in categories.items()])
    
    return f"""あなたは与えられたデータを適切なカテゴリに分類する専門家です。
データの内容を分析し、以下のカテゴリから最も適切なものを選択してください。

利用可能なカテゴリ:
{category_list}

分類の際は以下の点を考慮してください：
- データの主要なテーマや内容
- キーワードの関連性
- 文脈や意図
信頼度は0.0から1.0の範囲で、分類の確実性を表してください。
理由は分類の根拠を簡潔に説明してください。"""

# デフォルトのカテゴリとプロンプト
CategoryTag = create_category_enum(DEFAULT_CATEGORIES)
SYSTEM_PROMPT = generate_system_prompt(DEFAULT_CATEGORIES)

class TaggedRow(BaseModel):
    category: CategoryTag
    confidence: float
    reason: str

class CSVClassifier:
    def __init__(self, api_key: str = None, system_prompt: str = None, categories: dict = None):
        # カスタムカテゴリが指定された場合はプロンプトとEnumを再生成
        if categories is not None:
            self.categories = categories
            self.system_prompt = generate_system_prompt(categories)
            self.category_enum = create_category_enum(categories)
        else:
            self.categories = DEFAULT_CATEGORIES
            self.system_prompt = system_prompt or SYSTEM_PROMPT
            self.category_enum = CategoryTag
        
        self.model = os.getenv("MODEL_NAME", "gpt-4o-2024-08-06")
        
        # Azure OpenAI Serviceの設定確認
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        api_version = os.getenv("AZURE_API_VERSION", "2024-10-21")
        
        if azure_endpoint and azure_api_key:
            # Azure OpenAI Service使用
            self.client = AzureOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=azure_api_key,
                api_version=api_version
            )
        else:
            # OpenAI使用
            self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
    
    def read_csv(self, file_path: str) -> pd.DataFrame:
        return pd.read_csv(file_path)
    
    def classify_row(self, row_data: Dict[str, Any]):
        row_text = " ".join([f"{k}: {v}" for k, v in row_data.items()])
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"以下のデータを分類してください：\n{row_text}"}
        ]
        
        # 動的にTaggedRowクラスを生成
        from pydantic import create_model
        TaggedRowDynamic = create_model(
            'TaggedRow',
            category=(self.category_enum, ...),
            confidence=(float, ...),
            reason=(str, ...)
        )
        
        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=messages,
            response_format=TaggedRowDynamic,
        )
        
        return completion.choices[0].message.parsed
    
    def process_csv(self, file_path: str, output_path: str = None):
        df = self.read_csv(file_path)
        results = []
        
        for index, row in df.iterrows():
            row_dict = row.to_dict()
            tagged_result = self.classify_row(row_dict)
            
            result_row = {
                **row_dict,
                'category': tagged_result.category.value,
                'confidence': tagged_result.confidence,
                'reason': tagged_result.reason
            }
            results.append(result_row)
            
            print(f"Row {index + 1}: {tagged_result.category.value} (confidence: {tagged_result.confidence:.2f})")
        
        output_df = pd.DataFrame(results)
        
        if output_path:
            output_df.to_csv(output_path, index=False)
            print(f"結果を {output_path} に保存しました")
        
        return output_df

def main():
    parser = argparse.ArgumentParser(description='CSV分類ツール')
    parser.add_argument('input_file', nargs='?', help='入力CSVファイルのパス')
    parser.add_argument('-o', '--output', help='出力CSVファイルのパス')
    parser.add_argument('--interactive', action='store_true', help='インタラクティブモードで実行')
    
    args = parser.parse_args()
    
    classifier = CSVClassifier()
    
    if args.interactive or not args.input_file:
        # インタラクティブモード
        csv_file = input("CSVファイルのパスを入力してください: ")
        output_file = input("出力ファイルのパス（省略可）: ") or None
    else:
        # コマンドライン引数モード
        csv_file = args.input_file
        output_file = args.output
    
    try:
        result = classifier.process_csv(csv_file, output_file)
        print("\n分類結果:")
        print(result[['category', 'confidence', 'reason']].head())
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
