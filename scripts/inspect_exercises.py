# inspect_exercises.py
import json
from collections import Counter

with open("../raw_data/exercises.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total Exercises: {len(data)}")

equipment_counts = Counter(ex.get("equipment") for ex in data)
mechanics_counts = Counter(ex.get("mechanic") for ex in data)

primary_muscles = set()
for ex in data:
    for m in ex.get("primaryMuscles", []):
        primary_muscles.add(m)

print("\n" + "=" * 50)
print("EQUIPMENT VALUES:")
for eq, count in equipment_counts.most_common():
    print(f"  - '{eq}': {count}")

print("\n" + "=" * 50)
print("MECHANICS VALUES:")
for mech, count in mechanics_counts.most_common():
    print(f"  - '{mech}': {count}")

print("\n" + "=" * 50)
print(f"PRIMARY MUSCLES ({len(primary_muscles)} unique):")
print(sorted(list(primary_muscles)))
print("=" * 50)