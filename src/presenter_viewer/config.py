from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LayoutConfig:
    main_split_ratio: float
    right_stack_ratios: list[float]
    content_vs_pnote_ratio: float


DEFAULT_LAYOUT = LayoutConfig(
    main_split_ratio=0.7,
    right_stack_ratios=[1 / 3, 1 / 3, 1 / 3],
    content_vs_pnote_ratio=0.93,
)


def _safe_ratio(value: object, fallback: float, min_value: float = 0.05, max_value: float = 0.95) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return fallback

    if value <= min_value or value >= max_value:
        return fallback

    return value


def _normalize_stack(values: object, fallback: list[float]) -> list[float]:
    if not isinstance(values, list) or len(values) != 3:
        return fallback

    cleaned: list[float] = []
    for v in values:
        try:
            f = float(v)
        except (TypeError, ValueError):
            return fallback
        if f <= 0:
            return fallback
        cleaned.append(f)

    total = sum(cleaned)
    if total <= 0:
        return fallback

    return [v / total for v in cleaned]


def load_layout_config(layout_path: Path | None = None) -> LayoutConfig:
    if layout_path is None:
        layout_path = Path("layout.json")

    if not layout_path.exists():
        return DEFAULT_LAYOUT

    try:
        data = json.loads(layout_path.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT_LAYOUT

    return LayoutConfig(
        main_split_ratio=_safe_ratio(
            data.get("main_split_ratio"),
            DEFAULT_LAYOUT.main_split_ratio,
            0.10,
            0.90,
        ),
        right_stack_ratios=_normalize_stack(
            data.get("right_stack_ratios"),
            DEFAULT_LAYOUT.right_stack_ratios,
        ),
        content_vs_pnote_ratio=_safe_ratio(
            data.get("content_vs_pnote_ratio"),
            DEFAULT_LAYOUT.content_vs_pnote_ratio,
            0.70,
            0.98,
        ),
    )


def save_layout_config(config: LayoutConfig, layout_path: Path | None = None) -> None:
    if layout_path is None:
        layout_path = Path("layout.json")

    payload = {
        "main_split_ratio": config.main_split_ratio,
        "right_stack_ratios": config.right_stack_ratios,
        "content_vs_pnote_ratio": config.content_vs_pnote_ratio,
    }

    layout_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )