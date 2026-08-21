"""Create a parameter-gated review sketch in DXF format.

This module intentionally does not invent sprinkler geometry, elevations, spacing,
or code values. It produces an audit-oriented drawing that records supplied
parameters and the comparison result. A project template must be added only
after the governing source has been verified.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path


def _positive_number(value: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"不是有效数字: {value}") from exc
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("数值必须是大于 0 的有限数")
    return number


def _add_text(msp, text: str, x: float, y: float, height: float = 2.5) -> None:
    from ezdxf.enums import TextEntityAlignment

    msp.add_text(
        text,
        dxfattribs={"height": height},
    ).set_placement((x, y), align=TextEntityAlignment.LEFT)


def _add_box(msp, x1: float, y1: float, x2: float, y2: float) -> None:
    msp.add_lwpolyline(
        [(x1, y1), (x2, y1), (x2, y2), (x1, y2)],
        close=True,
    )


def build_review_dxf(
    obstruction_width_m: float,
    threshold_m: float,
    output_path: Path,
    source_ref: str | None,
) -> str:
    try:
        import ezdxf
    except ImportError as exc:
        raise RuntimeError(
            "缺少 ezdxf，请先在运行环境安装 requirements.txt。"
        ) from exc

    decision = obstruction_width_m > threshold_m
    decision_text = (
        "触发阈值比较：需依据已核实条文复核障碍物下方喷头"
        if decision
        else "未触发阈值比较：仍需依据完整条文和图纸复核"
    )

    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    _add_box(msp, 0, 0, 180, 90)
    _add_text(msp, "参数化节点图校核草图（非施工图）", 8, 80, 4.0)
    _add_text(msp, f"障碍物宽度 = {obstruction_width_m:g} m", 8, 68)
    _add_text(msp, f"阈值 B = {threshold_m:g} m（由使用者提供）", 8, 60)
    _add_text(msp, f"比较结果：{decision_text}", 8, 50, 3.0)
    _add_text(msp, "未绘制喷头定位、标高、间距或管径，避免程序猜测", 8, 38)
    _add_text(msp, "正式出图前必须补齐规范、图纸和几何参数", 8, 30)
    _add_text(msp, f"来源：{source_ref or '待核'}", 8, 20)
    _add_text(msp, "单位：m；本文件仅用于参数和来源核验", 8, 10)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(output_path)
    return decision_text


def main() -> int:
    parser = argparse.ArgumentParser(
        description="生成不猜测工程几何关系的 DXF 校核草图。"
    )
    parser.add_argument(
        "--obstruction-width-m",
        required=True,
        type=_positive_number,
        help="已从图纸/现场核实的障碍物宽度，单位 m",
    )
    parser.add_argument(
        "--threshold-m",
        required=True,
        type=_positive_number,
        help="已从规范条文核实的阈值，单位 m；不得使用默认值",
    )
    parser.add_argument(
        "--out",
        required=True,
        type=Path,
        help="输出 DXF 路径",
    )
    parser.add_argument(
        "--source-ref",
        default=None,
        help="规范、图纸或变更的可回查出处",
    )
    args = parser.parse_args()

    try:
        result = build_review_dxf(
            args.obstruction_width_m,
            args.threshold_m,
            args.out,
            args.source_ref,
        )
    except (RuntimeError, OSError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    print(result)
    print(f"已生成：{args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
