import os

from openai import OpenAI


class WebSearchAssistant:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.web_model = os.getenv("OPENAI_WEB_MODEL", "gpt-4o-mini")

    def answer_market_question(self, question):
        prompt = f"""
You are DataPrep AI, a live market knowledge assistant for data engineering interview prep.

Answer the user's question using current web information when needed.

Focus on:
- data engineering skills
- cloud platforms
- SQL
- Kafka
- Spark
- Airflow
- BigQuery
- Snowflake
- Databricks
- modern ETL and ELT tools
- interview preparation

Keep the answer practical and useful for someone preparing for data engineering interviews.
If the topic is current or changing, mention that trends can change over time.

User question:
{question}
"""

        try:
            response = self.client.responses.create(
                model=self.web_model,
                tools=[{"type": "web_search"}],
                input=prompt
            )

            return response.output_text

        except Exception:
            response = self.client.responses.create(
                model=self.web_model,
                tools=[{"type": "web_search_preview"}],
                input=prompt
            )

            return response.output_text