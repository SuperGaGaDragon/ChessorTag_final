#!/usr/bin/env python3
"""
Generate PDF versions of the Yuyaochen and Xuehaowen HTML reports.

The script wraps the bundled wkhtmltopdf binary (placed in pdf_exports/wkhtmltox)
so we don't rely on any system-wide installs. Run it from the repo root:

    python3 pdf_exports/export_reports.py

Output PDFs are written to pdf_exports/output/.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    assets_root = Path(__file__).resolve().parent
    wkhtmltopdf = assets_root / "wkhtmltox" / "bin" / "wkhtmltopdf"
    output_dir = assets_root / "output"
    css_bundle = assets_root / "report_styles.css"

    if not wkhtmltopdf.exists():
        print(f"wkhtmltopdf binary is missing at {wkhtmltopdf}", file=sys.stderr)
        return 1

    if not css_bundle.exists():
        print(f"CSS bundle is missing at {css_bundle}", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    reports = {
        "yuyaochen": repo_root / "website" / "reports" / "yuyaochen.html",
        "xuehaowen": repo_root / "website" / "reports" / "xuehaowen.html",
    }

    for name, html_path in reports.items():
        if not html_path.exists():
            print(f"Report not found: {html_path}", file=sys.stderr)
            return 1

        output_pdf = output_dir / f"{name}.pdf"
        cmd = [
            str(wkhtmltopdf),
            "--enable-local-file-access",
            "--user-style-sheet",
            str(css_bundle),
            str(html_path),
            str(output_pdf),
        ]

        print(f"Rendering {html_path} -> {output_pdf}")
        subprocess.run(cmd, check=True)

    print("All reports rendered successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
