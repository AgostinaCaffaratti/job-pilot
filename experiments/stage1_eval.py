"""Stage 1: score saved matcher runs against the human labels. Pure code, no API calls.

Usage: uv run --no-sync python experiments/stage1_eval.py logs/run_profile.json [more runs...]

Semantics (see NOTES.md, "eval semantics v1"):
  si / quizas  + compatible|requiere_verificacion -> hit
  si / quizas  + descartada                       -> MISS (critical, target: zero)
  no           + descartada                       -> hit
  no           + requiere_verificacion            -> tolerated (adds review load)
  no           + compatible                       -> FALSE POSITIVE
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
VALID_LABELS = {"si", "no", "quizas"}
VALID_CLASSES = {"compatible", "requiere_verificacion", "descartada"}


def read_label(path: Path) -> str:
    """Read `interesa: <value>` from the human label block. Fail loudly on anything unknown."""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip().lower().startswith("interesa:"):
            value = line.split(":", 1)[1].strip().lower()
            if value not in VALID_LABELS:
                raise ValueError(f"{path.name}: invalid label {value!r}, expected one of {sorted(VALID_LABELS)}")
            return value
    raise ValueError(f"{path.name}: no 'interesa:' line found")


def verdict(label: str, model: str) -> str:
    if model not in VALID_CLASSES:
        return "INVALID"
    if label in ("si", "quizas"):
        return "MISS" if model == "descartada" else "hit"
    if model == "descartada":
        return "hit"
    return "tolerated" if model == "requiere_verificacion" else "FALSE+"


def evaluate(run_path: Path) -> None:
    run = json.loads(run_path.read_text(encoding="utf-8"))
    rows = []
    for name, result in sorted(run.items()):
        label = read_label(ROOT / "data/private/jobs" / name)
        model = result.get("clasificacion", "?")
        rows.append((name, label, model, result.get("score"), verdict(label, model)))

    print(f"\n=== {run_path.name} ===")
    print(f"{'oferta':8}{'tu etiqueta':13}{'modelo':24}{'score':7}resultado")
    for name, label, model, score, v in rows:
        print(f"{name:8}{label:13}{model:24}{str(score):7}{v}")

    good = [r for r in rows if r[1] in ("si", "quizas")]
    missed = [r for r in good if r[4] == "MISS"]
    review = [r for r in rows if r[2] == "requiere_verificacion"]
    false_pos = [r for r in rows if r[4] == "FALSE+"]
    print(f"\nBuenas ofertas descartadas: {len(missed)} de {len(good)}   (meta: 0)")
    print(f"Carga de revision:          {len(review)} de {len(rows)} en requiere_verificacion")
    print(f"Falsos positivos:           {len(false_pos)}")


if len(sys.argv) < 2:
    sys.exit("usage: stage1_eval.py <run.json> [<run.json> ...]")
for arg in sys.argv[1:]:
    evaluate(ROOT / arg)
