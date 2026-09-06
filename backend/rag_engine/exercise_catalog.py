import json
import re
from pathlib import Path
from typing import Any


class ExerciseCatalog:
    """
    In-memory exercise catalog optimized for microsecond constraint filtering
    and token-efficient LLM projection.
    """

    MUSCLE_MAP: dict[str, list[str]] = {
        "quad": ["quadriceps"],
        "quads": ["quadriceps"],
        "lat": ["lats"],
        "glute": ["glutes"],
        "hamstring": ["hamstrings"],
        "delt": ["shoulders"],
        "delts": ["shoulders"],
        "shoulder": ["shoulders"],
        "abs": ["abdominals"],
        "calf": ["calves"],
        # Functional pulling targets: strictly isolates lumbar/spinal erectors
        "back": ["lats", "middle back"],
        "upper back": ["middle back", "traps"],
        "lower back": ["lower back"],
        "arms": ["biceps", "triceps"],
        "legs": ["quadriceps", "hamstrings", "glutes", "calves"],
    }

    def __init__(self, catalog_path: str = "raw_data/exercises.json") -> None:
        p = Path(catalog_path)
        # If relative and doesn't exist from CWD, resolve relative to project root
        if not p.is_absolute() and not p.exists():
            project_root = Path(__file__).resolve().parent.parent.parent
            p = project_root / catalog_path

        self.catalog_path = p
        self.exercises: list[dict[str, Any]] = []
        self.valid_ids: set[str] = set()
        self._load_and_prune()

    @staticmethod
    def _stem(word: str) -> str:
        """Strips plural 's', 'es', or 'ies' suffixes for robust categorical equality."""
        w = word.lower().strip()
        if w.endswith("ies"):
            return w[:-3] + "y"
        if w.endswith("es") and len(w) > 4:
            return w[:-2]
        if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
            return w[:-1]
        return w

    def _load_and_prune(self) -> None:
        if not self.catalog_path.exists():
            raise FileNotFoundError(f"Exercise catalog missing at {self.catalog_path}")

        with open(self.catalog_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        for item in raw_data:
            eid = str(item["id"]).strip()
            raw_muscles = item.get("primaryMuscles", item.get("primary_muscles", []))
            raw_equip = item.get("equipment") or "other"
            raw_mech = item.get("mechanic") or item.get("mechanics") or "unspecified"

            pruned = {
                "id": eid,
                "name": str(item["name"]).strip(),
                "primary_muscles": [m.lower().strip() for m in raw_muscles],
                "equipment": str(raw_equip).lower().strip(),
                "equipment_stemmed": self._stem(str(raw_equip)),
                "mechanic": str(raw_mech).lower().strip(),
                "mechanic_stemmed": self._stem(str(raw_mech)),
            }
            self.exercises.append(pruned)
            self.valid_ids.add(eid)

    def search(
        self,
        muscle: str | None = None,
        equipment: str | None = None,
        exclude_mechanics: str | None = None,
        limit: int = 5
    ) -> list[dict[str, Any]]:
        target_muscles: set[str] = set()
        if muscle:
            m_clean = muscle.lower().strip()
            if m_clean in self.MUSCLE_MAP:
                target_muscles.update(self.MUSCLE_MAP[m_clean])
            else:
                target_muscles.add(self._stem(m_clean))
                target_muscles.add(m_clean)

        allowed_equipment: set[str] = set()
        if equipment:
            tokens = re.split(r"[,/]|(?:\band\b)", equipment.lower())
            for t in tokens:
                clean_t = t.strip()
                if clean_t:
                    allowed_equipment.add(self._stem(clean_t))
                    allowed_equipment.add(clean_t)

        negative_tags: set[str] = set()
        if exclude_mechanics:
            neg_tokens = re.split(r"[,/]|(?:\band\b)", exclude_mechanics.lower())
            for nt in neg_tokens:
                clean_nt = nt.strip()
                if clean_nt:
                    negative_tags.add(self._stem(clean_nt))
                    negative_tags.add(clean_nt)

        candidates: list[dict[str, Any]] = []

        for ex in self.exercises:
            if negative_tags:
                ex_props = {
                    ex["mechanic"], ex["mechanic_stemmed"],
                    ex["equipment"], ex["equipment_stemmed"],
                    ex["name"].lower()
                }
                if any(neg in prop for neg in negative_tags for prop in ex_props):
                    continue

            if target_muscles:
                if not target_muscles.intersection(set(ex["primary_muscles"])):
                    continue

            if allowed_equipment:
                ex_eqs = {ex["equipment"], ex["equipment_stemmed"]}
                match = any(
                    req in eq or eq in req
                    for req in allowed_equipment
                    for eq in ex_eqs
                )
                if not match:
                    continue

            candidates.append(ex)
            if len(candidates) >= limit:
                break

        return candidates

    def format_for_prompt(self, candidates: list[dict[str, Any]]) -> str:
        if not candidates:
            return "No matching exercises found in catalog."

        lines = []
        for ex in candidates:
            muscles_str = ", ".join(ex["primary_muscles"])
            lines.append(
                f"- [{ex['id']}] {ex['name']} | "
                f"Equipment: {ex['equipment']} | "
                f"Mechanic: {ex['mechanic']} | "
                f"Target: {muscles_str}"
            )
        return "\n".join(lines)