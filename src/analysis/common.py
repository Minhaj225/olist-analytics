from pathlib import Path

import pandas as pd

from src.config import ROOT


FIGURES = ROOT / "reports/figures"


def read_sql(query):
    from src.db import engine

    return pd.read_sql(query, engine())


def write_findings(heading, body):
    path = ROOT / "docs/findings.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    text = path.read_text() if path.exists() else "# Findings\n\nResults below are generated from the local Olist CSVs.\n"
    start = f"\n## {heading}\n"
    if start in text:
        before, rest = text.split(start, 1)
        next_heading = rest.find("\n## ")
        text = before + (rest[next_heading:] if next_heading >= 0 else "")
    path.write_text(text.rstrip() + "\n" + start + "\n" + body.strip() + "\n")


def save_figure(name):
    import matplotlib.pyplot as plt

    FIGURES.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(FIGURES / name, dpi=140)
    plt.close()
