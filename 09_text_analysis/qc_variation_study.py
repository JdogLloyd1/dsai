# qc_variation_study.py
# Run AI QC repeatedly on the same report to measure run-to-run variation.
# Execute from repo root: python 09_text_analysis/qc_variation_study.py

import importlib.util
import os
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
MOD_PATH = REPO_ROOT / "09_text_analysis" / "02_ai_quality_control modified.py"
N_RUNS = 10

LIKERT_COLS = [
    "accuracy",
    "formality",
    "faithfulness",
    "clarity",
    "succinctness",
    "relevance",
    "neutral_tone",
]


def _load_qc_module():
    spec = importlib.util.spec_from_file_location("ai_qc_modified", MOD_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    os.chdir(REPO_ROOT)
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    qc = _load_qc_module()
    reports, source_data = qc.load_sample_data()
    report = reports[0]
    prompt = qc.create_quality_control_prompt(report, source_data)

    rows = []
    errors = []
    for run in range(1, N_RUNS + 1):
        print(f"Run {run}/{N_RUNS} ...", flush=True)
        try:
            raw = qc.query_ai_quality_control(prompt, provider=qc.AI_PROVIDER)
            res = qc.parse_quality_control_results(raw)
            likert = res[LIKERT_COLS].iloc[0]
            overall = float(likert.mean())
            accurate = bool(res["accurate"].iloc[0])
            rows.append(
                {
                    "run": run,
                    **{c: int(likert[c]) for c in LIKERT_COLS},
                    "overall_score": round(overall, 4),
                    "accurate_pass": accurate,
                }
            )
        except Exception as e:
            errors.append((run, str(e)))
            print(f"  Error: {e}", flush=True)

    if not rows:
        print("No successful runs; cannot summarize.")
        return

    df = pd.DataFrame(rows)
    print()
    print("=" * 72)
    print("Per-run results (same prompt, same report)")
    print("=" * 72)
    print(df.to_string(index=False))
    print()

    print("=" * 72)
    print("Variation summary")
    print("=" * 72)
    print(
        f"Provider: {qc.AI_PROVIDER} | Model: {getattr(qc, 'OLLAMA_MODEL', 'n/a')} "
        f"| Ollama temperature: {getattr(qc, 'OLLAMA_TEMPERATURE', 'n/a')} "
        f"| seed: {getattr(qc, 'OLLAMA_SEED', 'n/a')}"
    )
    print(
        f"Accuracy check (accurate=True): {df['accurate_pass'].sum()}/{len(df)} PASS, "
        f"{(~df['accurate_pass']).sum()} FAIL"
    )
    if df["accurate_pass"].nunique() == 2:
        print("  Note: PASS/FAIL flipped across runs — boolean gate is unstable.")
    print()

    for col in LIKERT_COLS + ["overall_score"]:
        s = df[col]
        print(
            f"{col:14}  min={s.min():.4g}  max={s.max():.4g}  mean={s.mean():.4f}  "
            f"std={s.std(ddof=0):.4f}  range={s.max() - s.min():.4g}"
        )

    print()
    print(
        "Prompt-tightening ideas: set Ollama options.temperature≈0.1–0.3; use a larger model; "
        "add a deterministic rubric with worked example scores; require integer JSON only."
    )
    if errors:
        print()
        print("Failed runs:", errors)


if __name__ == "__main__":
    main()
