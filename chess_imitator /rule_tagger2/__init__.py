from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE_PATH = ROOT / "rule_tagger_lichessbot" / "rule_tagger2"
__path__ = [str(PACKAGE_PATH)]
