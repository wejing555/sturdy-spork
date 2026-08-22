#!/usr/bin/env python3
"""Deterministic PDF drawing scanner for engineering document triage.

This script does NOT make design decisions and does NOT OCR by default.
It extracts the PDF text layer, hashes files, scores pages by engineering
keywords, and renders selected pages for later human/AI visual review.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Iterable

import fitz  # PyMuPDF


KEYWORD_GROUPS = {
    "design_notes": ["设计说明", "施工说明", "说明", "材料表", "图例"],
    "water_supply": ["给水", "生活给水", "冷水", "热水", "PP-R", "PPR", "钢塑复合"],
    "drainage": ["排水", "污水", "废水", "通气", "UPVC", "PVC-U", "螺旋消音"],
    "rainwater": ["雨水", "雨水斗", "屋面雨水", "溢流"],
    "heating": ["采暖", "供水温度", "回水温度", "地板辐射", "分集水器", "PE-RT", "PERT"],
    "pressure_drainage": ["压力排水", "排水泵", "集水坑", "污水泵", "潜污泵"],
    "insulation": ["保温", "防结露", "橡塑", "绝热"],
    "testing": ["试压", "水压试验", "灌水", "通球", "冲洗", "消毒"],
    "change": ["变更", "修改", "优化", "补充", "B01", "A01"],
    "system_diagram": ["系统图", "原理图", "轴测图"],
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_name(path: Path) -> str:
    stem = path.stem
    stem = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff._-]+", "_", stem)
    return stem[:120] or "pdf"


def find_pdfs(root: Path) -> Iterable[Path]:
    return sorted(p for p in root.rglob("*.pdf") if p.is_file())


def score_text(text: str) -> tuple[int, list[str], dict[str, int]]:
    normalized = re.sub(r"\s+", "", text or "")
    matched_groups: list[str] = []
    counts: dict[str, int] = {}
    score = 0
    for group, words in KEYWORD_GROUPS.items():
        c = sum(normalized.count(w) for w in words)
        if c:
            matched_groups.append(group)
            counts[group] = c
            score += c
    return score, matched_groups, counts


def render_page(page: fitz.Page, out_path: Path, dpi: int) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pix = page.get_pixmap(dpi=dpi, alpha=False)
    pix.save(out_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path, help="Directory containing PDFs")
    parser.add_argument("--out", type=Path, default=Path("scan_output"))
    parser.add_argument("--dpi", type=int, default=220)
    parser.add_argument(
        "--render",
        choices=["none", "candidates", "all"],
        default="candidates",
        help="Which pages to render as PNG",
    )
    parser.add_argument(
        "--candidate-threshold",
        type=int,
        default=1,
        help="Minimum keyword score for candidate rendering",
    )
    args = parser.parse_args()

    root = args.input_dir.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "text").mkdir(exist_ok=True)
    (out / "rendered").mkdir(exist_ok=True)

    pdfs = list(find_pdfs(root))
    manifest: list[dict] = []
    page_rows: list[list] = []
    candidate_rows: list[list] = []

    for pdf in pdfs:
        rel = pdf.relative_to(root)
        file_entry = {
            "relative_path": str(rel).replace("\\", "/"),
            "size_bytes": pdf.stat().st_size,
            "sha256": sha256(pdf),
            "status": "ok",
            "pages": None,
            "error": None,
        }
        try:
            doc = fitz.open(pdf)
            file_entry["pages"] = doc.page_count
            base = safe_name(pdf)
            text_dir = out / "text" / base
            render_dir = out / "rendered" / base
            text_dir.mkdir(parents=True, exist_ok=True)

            for idx in range(doc.page_count):
                page = doc.load_page(idx)
                text = page.get_text("text") or ""
                page_no = idx + 1
                text_path = text_dir / f"p{page_no:04d}.txt"
                text_path.write_text(text, encoding="utf-8", errors="ignore")

                score, groups, counts = score_text(text)
                row = [
                    file_entry["relative_path"],
                    page_no,
                    len(text),
                    score,
                    ";".join(groups),
                    json.dumps(counts, ensure_ascii=False),
                    str(text_path.relative_to(out)).replace("\\", "/"),
                ]
                page_rows.append(row)

                is_candidate = score >= args.candidate_threshold or page_no == 1
                if is_candidate:
                    candidate_rows.append(row)

                should_render = (
                    args.render == "all"
                    or (args.render == "candidates" and is_candidate)
                )
                if should_render:
                    render_page(page, render_dir / f"p{page_no:04d}.png", args.dpi)

            doc.close()
        except Exception as exc:  # keep scanning other files
            file_entry["status"] = "error"
            file_entry["error"] = repr(exc)
        manifest.append(file_entry)

    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    header = [
        "relative_path",
        "page_no",
        "text_chars",
        "keyword_score",
        "matched_groups",
        "group_counts_json",
        "text_file",
    ]
    for name, rows in [("pages.csv", page_rows), ("candidate_pages.csv", candidate_rows)]:
        with (out / name).open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)

    summary = {
        "input_dir": str(root),
        "pdf_count": len(pdfs),
        "ok_count": sum(1 for x in manifest if x["status"] == "ok"),
        "error_count": sum(1 for x in manifest if x["status"] == "error"),
        "page_count": len(page_rows),
        "candidate_page_count": len(candidate_rows),
        "dpi": args.dpi,
        "render_mode": args.render,
        "note": "No OCR and no design inference performed. Candidate pages require visual review.",
    }
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
