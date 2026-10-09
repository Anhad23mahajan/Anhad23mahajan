import json
from typing import Literal
from pydantic import BaseModel, Field
from google import genai
from google.genai import types, errors

# 1. Current-idiom config objects (offline construction)
class Chart(BaseModel):
    type: Literal["bar","line","pie","number","table"]
    x: str | None = None
    y: str | None = None
class SqlPlan(BaseModel):
    sql: str = Field(description="One DuckDB SELECT on table data")
    chart: Chart

cfg_a = types.GenerateContentConfig(response_mime_type="application/json", response_schema=SqlPlan)           # pydantic class
cfg_b = types.GenerateContentConfig(response_mime_type="application/json", response_json_schema=SqlPlan.model_json_schema())  # JSON Schema
cfg_c = types.GenerateContentConfig(response_mime_type="application/json", response_json_schema=SqlPlan.model_json_schema(),
        thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW),
        max_output_tokens=1024, system_instruction="You write DuckDB SQL.",
        safety_settings=[types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH)])
cfg_d = types.GenerateContentConfig(temperature=0.0, thinking_config=types.ThinkingConfig(thinking_budget=0))
print("configs OK:", all(isinstance(c, types.GenerateContentConfig) for c in (cfg_a,cfg_b,cfg_c,cfg_d)))
print("dict-style config accepted by pydantic:", types.GenerateContentConfig.model_validate({"response_mime_type":"application/json","response_json_schema":{"type":"object"}}).response_json_schema)
print("JSON schema keys:", list(SqlPlan.model_json_schema()))

# 2. Client construction offline
c = genai.Client(api_key="x"*20)
print("client OK; has models.generate_content:", hasattr(c.models, "generate_content"), "| has interactions:", hasattr(c, "interactions"))

# 3. Blocked / empty response -> .text
r = types.GenerateContentResponse(candidates=[], prompt_feedback=types.GenerateContentResponsePromptFeedback(block_reason=types.BlockedReason.SAFETY))
print("empty candidates .text ->", repr(r.text))
r2 = types.GenerateContentResponse(candidates=[types.Candidate(finish_reason=types.FinishReason.SAFETY, content=None)])
print("SAFETY finish no content .text ->", repr(r2.text))
r3 = types.GenerateContentResponse(candidates=[types.Candidate(finish_reason=types.FinishReason.MAX_TOKENS, content=types.Content(role="model", parts=[types.Part(text='{"sql": "SELECT 1')]))])
print("MAX_TOKENS truncated .text ->", repr(r3.text), "finish:", r3.candidates[0].finish_reason)
print(".parsed on text response ->", r3.parsed)
try:
    r.text.strip()
except Exception as e:
    print("app pattern .text.strip() crash:", type(e).__name__, e)

# 4. error object construction + attributes
body = {"error":{"code":429,"message":"Quota exceeded for metric ... Please retry in 12s","status":"RESOURCE_EXHAUSTED",
        "details":[{"@type":"type.googleapis.com/google.rpc.RetryInfo","retryDelay":"12s"}]}}
e = errors.ClientError(429, body)
print("ClientError:", e.code, e.status, e.message[:30], "| str:", str(e)[:60], "| details type:", type(e.details).__name__)
e2 = errors.ServerError(503, {"error":{"code":503,"message":"The model is overloaded.","status":"UNAVAILABLE"}})
print("ServerError:", e2.code, e2.status, e2.message)
print("isinstance APIError:", isinstance(e, errors.APIError), isinstance(e2, errors.APIError))
