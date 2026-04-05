import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Neo DevOps Agent API",
    description="API для классификации SRE/DevOps инцидентов",
    version="1.0.0"
)

API_KEY = os.getenv("OPENAI_API_KEY", "lm-studio")
BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5-nano")

client = AsyncOpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)


class IncidentRequest(BaseModel):
    description: str = Field(
        ...,
        json_schema_extra={
            "example": "Упала БД из-за нехватки памяти в поде."
        }
    )


class IncidentClassification(BaseModel):
    incident_type: str
    severity: str
    infrastructure: str
    summary: str


@app.post("/analyze-incident", response_model=IncidentClassification)
async def analyze_incident(request: IncidentRequest):
    system_prompt = """
Ты — DevOps AI ассистент. Твоя задача: проанализировать описание инцидента и вернуть структурированный JSON.

Обязательные поля в JSON:
- "incident_type" (строка, краткий тип инцидента, например OOM, NetworkTimeout, DB_Crash)
- "severity" (строка, выбери из: Low, Medium, High, Critical)
- "infrastructure" (строка, затронутый компонент: Kubernetes, Database, Network, Frontend и т.д.)
- "summary" (строка, выжимка проблемы в одно предложение)

Верни ТОЛЬКО валидный JSON, без markdown-разметки и лишнего текста.
""".strip()

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.description}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        raw_content = response.choices[0].message.content

        if not raw_content:
            raise HTTPException(status_code=500, detail="LLM вернула пустой ответ.")

        parsed_json = json.loads(raw_content)

        # Провалидируем ответ через Pydantic
        validated = IncidentClassification(**parsed_json)
        return validated

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="LLM вернула невалидный JSON.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при вызове LLM: {str(e)}")


@app.get("/health")
async def health_check():
    return {"status": "ok", "model": MODEL_NAME}