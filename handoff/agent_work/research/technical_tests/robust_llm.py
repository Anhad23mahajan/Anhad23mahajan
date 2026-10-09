"""Proposed replacement for llm._json (tested here with stub clients only; no live API key in the sandbox)."""
import json, re, time
from typing import Literal
from pydantic import BaseModel, Field, ValidationError
from google import genai
from google.genai import types, errors


class Chart(BaseModel):
    type: Literal["bar", "line", "pie", "number", "table"]
    x: str | None = None
    y: str | None = None


class SqlPlan(BaseModel):
    sql: str = Field(description="One DuckDB SELECT on table data")
    chart: Chart


def make_config(schema_model, level=types.ThinkingLevel.LOW):
    # NOTE: no temperature/top_p/top_k (ignored by Gemini 3.5-Flash-Lite / 3.8-Flash; future models return HTTP 400)
    return types.GenerateContentConfig(
        response_mime_type="application/json",
        response_json_schema=schema_model.model_json_schema(),
        thinking_config=types.ThinkingConfig(thinking_level=level),   # 3.8 Flash rejects MINIMAL; thinking_budget is gone on Gemini 3
        max_output_tokens=2048,                                       # thinking tokens count toward this: do not set it too low
    )


class Retryable(Exception): ...        # try the same model again after a pause
class NextModel(Exception): ...         # this model is exhausted / gone: try the next one
class Fatal(Exception): ...             # bad key, bad request: stop


def retry_delay(e: errors.APIError) -> float | None:
    """Parse google.rpc.RetryInfo ('12s') from the structured error body, if present."""
    try:
        for d in (e.details or {}).get("error", {}).get("details", []):
            if d.get("@type", "").endswith("RetryInfo"):
                return float(str(d["retryDelay"]).rstrip("s"))
    except Exception:
        pass
    return None


def is_daily_quota(e: errors.APIError) -> bool:
    try:
        for d in (e.details or {}).get("error", {}).get("details", []):
            if d.get("@type", "").endswith("QuotaFailure"):
                return any("PerDay" in v.get("quotaId", "") or "PerDay" in v.get("quotaMetric", "") for v in d.get("violations", []))
    except Exception:
        pass
    return False


def classify(e: Exception) -> Exception:
    if isinstance(e, errors.APIError):
        c = e.code
        if c == 429:                                   # per-model quota buckets: another model may still have budget
            return NextModel("rate-limited") if is_daily_quota(e) else Retryable(retry_delay(e) or 2.0)
        if c in (500, 502, 503, 504):
            return Retryable(1.5)
        if c == 404:
            return NextModel("model not found / retired")
        return Fatal(f"{c} {e.status}: {e.message}")   # 400 incl. 'API key not valid', 401, 403
    return e


def call_json(client, models, prompt, cfg, schema_model, sleep=time.sleep):
    last = None
    for model in models:
        for attempt in range(2):
            try:
                resp = client.models.generate_content(model=model, contents=prompt, config=cfg)
                text = resp.text                                   # None when blocked / no candidates / only thought parts
                if not text:
                    reason = getattr(getattr(resp, "prompt_feedback", None), "block_reason", None)
                    fin = resp.candidates[0].finish_reason if resp.candidates else None
                    raise NextModel(f"empty response (block_reason={reason}, finish_reason={fin})")
                fin = resp.candidates[0].finish_reason if resp.candidates else None
                if fin is not None and str(fin).endswith("MAX_TOKENS"):
                    raise Retryable(0)                             # truncated JSON: retry (or raise max_output_tokens)
                return schema_model.model_validate_json(text)      # schema-checks the values too, not just the JSON syntax
            except (ValidationError, json.JSONDecodeError) as e:
                last = e
                continue                                           # one more try on the same model
            except Exception as raw:
                e = classify(raw) if isinstance(raw, errors.APIError) else raw
                last = e
                if isinstance(e, Fatal): raise
                if isinstance(e, Retryable) and attempt == 0:
                    sleep(float(e.args[0]) if e.args else 1.0); continue
                break                                              # NextModel / second Retryable -> next model
    raise last


if __name__ == "__main__":
    # ---- stub tests
    class Resp:
        def __init__(self, text, fin="STOP", block=None):
            self.text = text
            self.candidates = [types.Candidate(finish_reason=getattr(types.FinishReason, fin))] if fin else []
            self.prompt_feedback = types.GenerateContentResponsePromptFeedback(block_reason=block) if block else None
    class Stub:
        def __init__(self, script): self.script = script; self.log = []; self.models = self
        def generate_content(self, model, contents, config):
            self.log.append(model); step = self.script[model].pop(0) if isinstance(self.script[model], list) else self.script[model]
            if isinstance(step, Exception): raise step
            return step
    ok = Resp('{"sql": "SELECT 1", "chart": {"type": "number"}}')
    q429_min = errors.ClientError(429, {"error": {"code": 429, "message": "quota", "status": "RESOURCE_EXHAUSTED", "details": [{"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "3s"}]}})
    q429_day = errors.ClientError(429, {"error": {"code": 429, "message": "quota", "status": "RESOURCE_EXHAUSTED", "details": [{"@type": "type.googleapis.com/google.rpc.QuotaFailure", "violations": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier"}]}]}})
    e503 = errors.ServerError(503, {"error": {"code": 503, "message": "overloaded", "status": "UNAVAILABLE"}})
    e404 = errors.ClientError(404, {"error": {"code": 404, "message": "models/x is not found", "status": "NOT_FOUND"}})
    e400 = errors.ClientError(400, {"error": {"code": 400, "message": "API key not valid. Please pass a valid API key.", "status": "INVALID_ARGUMENT"}})
    cfg = make_config(SqlPlan); slept = []
    def run(name, script):
        st = Stub(script); slept.clear()
        try: out = call_json(st, list(script), "p", cfg, SqlPlan, sleep=slept.append); res = f"OK sql={out.sql!r}"
        except Exception as e: res = f"RAISED {type(e).__name__}: {str(e)[:60]}"
        print(f"{name:40s} -> {res} | calls={st.log} sleeps={slept}")
    run("blocked then fallback model OK", {"A": [Resp(None, fin=None, block=types.BlockedReason.SAFETY)], "B": [ok]})
    run("429 per-minute: sleep 3s, retry same", {"A": [q429_min, ok]})
    run("429 per-day: jump to next model", {"A": [q429_day], "B": [ok]})
    run("503 twice then next model", {"A": [e503, e503], "B": [ok]})
    run("404 -> next model", {"A": [e404], "B": [ok]})
    run("400 bad key -> fatal, no retry", {"A": [e400], "B": [ok]})
    run("truncated (MAX_TOKENS) -> retry", {"A": [Resp('{"sql": "SELECT 1', fin="MAX_TOKENS"), ok]})
    run("invalid enum value -> retry/validate", {"A": [Resp('{"sql":"SELECT 1","chart":{"type":"donut"}}'), ok]})
    run("all models fail", {"A": [e503, e503], "B": [e404]})
