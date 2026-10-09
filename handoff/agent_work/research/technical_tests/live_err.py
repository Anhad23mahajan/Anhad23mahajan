from google import genai
from google.genai import types, errors
c = genai.Client(api_key="AIzaSy" + "A"*33)   # deliberately invalid key
for model in ["gemini-3.8-flash", "no-such-model-xyz"]:
    try:
        c.models.generate_content(model=model, contents="hi", config=types.GenerateContentConfig(response_mime_type="application/json"))
    except errors.APIError as e:
        print(model, "->", type(e).__name__, "code=", e.code, "status=", e.status, "| msg:", e.message[:90])
        print("   str(e)[:150]:", str(e)[:150])
    except Exception as e:
        print(model, "-> NON-APIError", type(e).__name__, str(e)[:200])
