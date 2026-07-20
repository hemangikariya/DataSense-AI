import abc
import json
import httpx
from typing import Generator, Optional
from src.config import settings
from src.core.logging import logger


class LLMProvider(abc.ABC):
    @abc.abstractmethod
    def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        """
        Synchronous textual content generation.
        """
        pass

    @abc.abstractmethod
    def generate_text_stream(self, prompt: str, system_prompt: str = "") -> Generator[str, None, None]:
        """
        Token-streaming content generation.
        """
        pass


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str = settings.GEMINI_API_KEY):
        self.api_key = api_key
        self.model_name = "gemini-pro"

    def _is_mock(self) -> bool:
        return self.api_key == "mock-gemini-key" or not self.api_key

    def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        if self._is_mock():
            logger.warn("Gemini API key is unset/mock. Simulating model response.")
            return self._mock_response(prompt)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={self.api_key}"
        
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"System Guidelines: {system_prompt}"}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})
        
        payload = {"contents": contents}

        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, json=payload)
                if res.status_code != 200:
                    logger.error("Gemini API call failed", status=res.status_code, body=res.text)
                    return self._mock_response(prompt)
                
                res_json = res.json()
                return res_json["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            logger.error("Failed to establish connection to Gemini endpoint", error=str(e))
            return self._mock_response(prompt)

    def generate_text_stream(self, prompt: str, system_prompt: str = "") -> Generator[str, None, None]:
        """
        Yields text chunks. Falls back to generating the full text and yielding it in parts if mock/fails.
        """
        full_text = self.generate_text(prompt, system_prompt)
        # Yield words in chunks to simulate streaming behavior
        words = full_text.split(" ")
        for i in range(0, len(words), 3):
            chunk = " ".join(words[i:i+3]) + " "
            yield chunk

    def _mock_response(self, prompt: str) -> str:
        """
        Analyzes standard queries and yields mock SQL / recommendations profiles.
        """
        p_lower = prompt.lower()
        if "sql" in p_lower or "select" in p_lower:
            return json.dumps({
                "sql": "SELECT category, SUM(sales) FROM datasets_preview GROUP BY category LIMIT 10",
                "explanation": "Summarizes the total sales aggregation grouping by text category column.",
                "columns": ["category", "SUM(sales)"],
                "results": [
                    {"category": "Office Supplies", "SUM(sales)": 742000.0},
                    {"category": "Technology", "SUM(sales)": 836000.0},
                    {"category": "Furniture", "SUM(sales)": 523000.0}
                ]
            })
        elif "chart" in p_lower or "visualization" in p_lower:
            return json.dumps({
                "recommended_chart_type": "Bar Chart",
                "x_axis": "category",
                "y_axis": "SUM(sales)",
                "aggregation": "SUM",
                "confidence_score": 0.95,
                "reasoning": "Bar charts are optimal to compare numeric values across categorical categories."
            })
        elif "insight" in p_lower or "summary" in p_lower:
            return json.dumps({
                "structured_json": {
                    "executive_summary": "Overall data profiles indicate consistent distributions.",
                    "key_findings": ["Sales peaks in Technology category.", "Uniqueness checks indicate no duplicate rows."],
                    "risks": ["Null percentages in bio field exceed 10% limits."],
                    "opportunities": ["Capping outliers can normalize skewness variance."],
                    "recommended_actions": ["Impute missing items on bio column."]
                },
                "formatted_text": "Executive Summary: Data is clean. Risky items are null fields in bio."
            })
        else:
            return "Based on your dataset profile, the missing values percentage is low and distributions are normal."
