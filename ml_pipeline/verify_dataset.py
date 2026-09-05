# ml_pipeline/verify_dataset.py
import json
from collections import Counter
from pathlib import Path

FINAL_PATH = Path("ml_pipeline/synthetic_data/train_data_final.jsonl")

def main():
    counts = Counter()
    total = 0
    max_tokens_approx = 0

    with open(FINAL_PATH, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            total += 1
            data = json.loads(line)
            msgs = data["messages"]
            assert len(msgs) == 3, f"Line {i+1} has invalid message length!"
            assert msgs[0]["role"] == "system"
            assert msgs[1]["role"] == "user"
            assert msgs[2]["role"] == "assistant"

            asst_text = msgs[2]["content"]
            approx_tokens = len(msgs[0]["content"] + msgs[1]["content"] + asst_text) // 4
            max_tokens_approx = max(max_tokens_approx, approx_tokens)

            try:
                parsed = json.loads(asst_text)
                if "tool_call" in parsed:
                    counts[parsed["tool_call"]["name"]] += 1
                else:
                    counts["JSON_NO_TOOL"] += 1
            except Exception:
                counts["DIRECT_TEXT_COACHING_OR_REFUSAL"] += 1

    print("=" * 60)
    print(f"FINAL DATASET INTEGRITY CHECK: {FINAL_PATH}")
    print(f"Total verified samples: {total}")
    print(f"Approx max sample tokens: {max_tokens_approx}")
    print("=" * 60)
    for k, v in counts.items():
        print(f"  {k:<35}: {v:>4} ({v/total*100:>5.1f}%)")
    print("=" * 60)

if __name__ == "__main__":
    main()