from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load .env from backend directory
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    temperature=0
)

SQL_PROMPT = """
You are an expert SQL analyst.

Database schema:
{schema}

User question:
{question}

Generate a READ-ONLY SQL query.

Rules:
- Only use tables and columns in the schema.
- Never modify data.
- Do not invent tables.
- Do not invent columns.
- Return only the SQL query.
"""
def generate_sql(question, schema):

    prompt = SQL_PROMPT.format(
        question=question,
        schema=schema
    )

    response = llm.invoke(prompt)

    return response.content