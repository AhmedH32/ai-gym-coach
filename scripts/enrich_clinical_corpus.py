# scripts/enrich_clinical_corpus.py
import os
import re
import time
from pathlib import Path
from google import genai
from google.genai import types
from google.genai.errors import APIError

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is missing. Set it before running.")

client = genai.Client(
    api_key=API_KEY,
    http_options=types.HttpOptions(timeout=20000)
)

CORPUS_DIR = Path("rag_corpus/injuries")
if not CORPUS_DIR.exists():
    CORPUS_DIR = Path("../rag_corpus/injuries")

# Target 3.5 Flash Lite: 15 RPM limit, 500 Requests Per Day limit (498 available)
MODEL_NAME = "gemini-3.5-flash-lite"
REQUEST_DELAY_SEC = 4.5  # 60s / 15 RPM = 4.0s + 0.5s safety margin

ENRICHMENT_PROMPT = """You are an elite sports physical therapist and biomechanist.
I will give you an orthopedic sports medicine clinical protocol markdown card.
Your job is to generate a concise, high-density colloquial symptom and gym-trigger section for semantic search indexing.

Generate EXACTLY this markdown block (under 120 words total):
## Colloquial Symptom Presentation & Provocative Triggers
* **Anatomical Pain Sites:** [List 3-4 exact pain sites using colloquial terms and clinical names, e.g., 'inferior pole of kneecap, front of knee, tendon below knee']
* **Sensation Character:** [List 3-4 descriptive pain sensations, e.g., 'sharp barking ache, burning under load, stiff morning turnaround']
* **Provocative Gym Lifts & Angles:** [List 4-5 specific gym exercises and joint angles that provoke pain, e.g., 'deep back squats past 90 degrees, hack squats, forward knee shear lunges']
* **Gym-Floor Slang Cues:** [List 3 realistic athlete quotes, e.g., '"my kneecap is barking out of the hole", "pinching below the knee when squatting deep"']

Rules:
1. Output ONLY the markdown section above. Do not include introductory text, backticks, or concluding remarks.
2. Focus strictly on realistic colloquial phrasing used by lifters on the gym floor.
"""

def generate_enrichment(content: str, card_name: str, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        try:
            # Clean config without thinking_config to prevent 400 errors on Lite models
            cfg = types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=600,
            )
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=ENRICHMENT_PROMPT),
                            types.Part.from_text(text=f"Clinical Card:\n\n{content}")
                        ]
                    )
                ],
                config=cfg
            )
            text = response.text.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:markdown)?\s*|\s*```$", "", text, flags=re.IGNORECASE).strip()
            return text

        except APIError as e:
            if e.code == 429:
                wait_time = 20.0
                print(f"[429 Rate Limit] Sleeping {wait_time}s... ", end="", flush=True)
                time.sleep(wait_time)
            elif e.code == 503:
                wait_time = 10.0
                print(f"[503 Busy] Retrying in {wait_time}s... ", end="", flush=True)
                time.sleep(wait_time)
            else:
                raise e
        except Exception as ex:
            print(f"[Err: {type(ex).__name__}] Retrying in 4s... ", end="", flush=True)
            time.sleep(4.0)

    raise RuntimeError(f"Failed to generate enrichment for {card_name} after {max_retries} attempts.")

def main():
    md_files = sorted(list(CORPUS_DIR.glob("*.md")))
    print(f"Found {len(md_files)} clinical injury cards in {CORPUS_DIR}.")

    pending = [
        f for f in md_files
        if "## Colloquial Symptom Presentation & Provocative Triggers" not in f.read_text(encoding="utf-8")
    ]
    if not pending:
        print("✓ All 40 clinical cards already contain colloquial trigger sections. Nothing to do.")
        return

    print(f"Cards pending enrichment: {len(pending)}/{len(md_files)}")
    print(f"Pacing: 1 card every {REQUEST_DELAY_SEC}s (~{round(len(pending) * REQUEST_DELAY_SEC / 60, 1)} min total)")
    print(f"Target Model: {MODEL_NAME} (RPD Quota Available: 498)")
    print("-" * 75)

    for idx, md_file in enumerate(pending, 1):
        content = md_file.read_text(encoding="utf-8")
        print(f"[{idx}/{len(pending)}] Enriching: {md_file.name} ... ", end="", flush=True)

        t0 = time.perf_counter()
        enriched_block = generate_enrichment(content, md_file.name)
        elapsed = round(time.perf_counter() - t0, 2)

        target_marker = "## Absolute Contraindications"
        if target_marker in content:
            updated_content = content.replace(target_marker, f"{enriched_block}\n\n{target_marker}")
        else:
            updated_content = f"{content}\n\n{enriched_block}\n"

        md_file.write_text(updated_content, encoding="utf-8")
        print(f"✓ Saved in {elapsed}s")

        if idx < len(pending):
            time.sleep(REQUEST_DELAY_SEC)

    print("\n" + "=" * 75)
    print("✅ All clinical injury protocol cards successfully enriched.")

if __name__ == "__main__":
    main()