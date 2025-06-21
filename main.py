import os
import csv
from enum import Enum
from typing import List, Dict, Any
from pydantic import BaseModel
from openai import OpenAI, AzureOpenAI
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

# システムプロンプトの設定
SYSTEM_PROMPT = """あなたは与えられたデータを適切なカテゴリに分類する専門家です。
データの内容を分析し、最も適切なカテゴリタグを選択してください。
分類の際は以下の点を考慮してください：
- データの主要なテーマや内容
- キーワードの関連性
- 文脈や意図
信頼度は0.0から1.0の範囲で、分類の確実性を表してください。
理由は分類の根拠を簡潔に説明してください。"""

class CategoryTag(str, Enum):
    TECHNOLOGY = "technology"
    BUSINESS = "business"
    FINANCE = "finance"
    HEALTH = "health"
    EDUCATION = "education"
    ENTERTAINMENT = "entertainment"
    SPORTS = "sports"
    POLITICS = "politics"
    SCIENCE = "science"
    OTHER = "other"

class TaggedRow(BaseModel):
    category: CategoryTag
    confidence: float
    reason: str

class CSVClassifier:
    def __init__(self, api_key: str = None, system_prompt: str = None):
        self.system_prompt = system_prompt or SYSTEM_PROMPT
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
    
    def classify_row(self, row_data: Dict[str, Any]) -> TaggedRow:
        row_text = " ".join([f"{k}: {v}" for k, v in row_data.items()])
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"以下のデータを分類してください：\n{row_text}"}
        ]
        
        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=messages,
            response_format=TaggedRow,
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
    classifier = CSVClassifier()
    
    csv_file = input("CSVファイルのパスを入力してください: ")
    output_file = input("出力ファイルのパス（省略可）: ") or None
    
    try:
        result = classifier.process_csv(csv_file, output_file)
        print("\n分類結果:")
        print(result[['category', 'confidence', 'reason']].head())
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
