from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


APP_DIR = Path.home() / ".presenter_viewer"
LAYOUT_FILE = APP_DIR / "layout.json"

PANEL_KEYS = (
    "main_left",
    "right_top",
    "right_middle",
    "right_bottom",
)

VALID_PANEL_ROLES = (
    "slide_current",
    "slide_next",
    "notes_current",
    "notes_next",
)

DEFAULT_PANEL_ROLES = {
    "main_left": "slide_current",
    "right_top": "slide_next",
    "right_middle": "notes_current",
    "right_bottom": "notes_next",
}


@dataclass
class LayoutConfig:
    main_split_ratio: float = 0.68
    right_stack_ratios: list[float] = field(default_factory=lambda: [0.33, 0.34, 0.33])
    content_vs_pnote_ratio: float = 0.90    
    allow_duplicate_roles: bool = False
    panel_roles: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_PANEL_ROLES))


def _ensure_app_dir() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)


def _normalize_ratios(values: list[float], expected_len: int, fallback: list[float]) -> list[float]:
    if len(values) != expected_len:
        return fallback[:]

    safe_values = [max(float(v), 0.0) for v in values]
    total = sum(safe_values)
    if total <= 0:
        return fallback[:]

    return [v / total for v in safe_values]


def _clamp_ratio(value: float, fallback: float) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return fallback

    if v <= 0.0 or v >= 1.0:
        return fallback
    return v


def _sanitize_panel_roles(raw_roles: object, allow_duplicates: bool) -> dict[str, str]:
    if not isinstance(raw_roles, dict):
        return dict(DEFAULT_PANEL_ROLES)

    roles: dict[str, str] = {}

    for panel_key in PANEL_KEYS:
        role = raw_roles.get(panel_key)
        if isinstance(role, str) and role in VALID_PANEL_ROLES:
            roles[panel_key] = role
        else:
            roles[panel_key] = DEFAULT_PANEL_ROLES[panel_key]

    if allow_duplicates:
        return roles

    # Sin duplicados: reconstruir asegurando unicidad
    used: set[str] = set()
    result: dict[str, str] = {}

    for panel_key in PANEL_KEYS:
        role = roles[panel_key]
        if role not in used:
            result[panel_key] = role
            used.add(role)
        else:
            result[panel_key] = ""

    missing_roles = [role for role in VALID_PANEL_ROLES if role not in used]

    for panel_key in PANEL_KEYS:
        if result.get(panel_key, "") == "":
            result[panel_key] = missing_roles.pop(0)

    return result


def load_layout_config() -> LayoutConfig:
    _ensure_app_dir()

    if not LAYOUT_FILE.exists():
        config = LayoutConfig()
        save_layout_config(config)
        return config

    try:
        raw = json.loads(LAYOUT_FILE.read_text(encoding="utf-8"))
    except Exception:
        config = LayoutConfig()
        save_layout_config(config)
        return config

    if not isinstance(raw, dict):
        config = LayoutConfig()
        save_layout_config(config)
        return config

    main_split_ratio = _clamp_ratio(raw.get("main_split_ratio", 0.68), 0.68)
    content_vs_pnote_ratio = _clamp_ratio(raw.get("content_vs_pnote_ratio", 0.90), 0.90)

    right_stack_ratios = _normalize_ratios(
        raw.get("right_stack_ratios", [0.33, 0.34, 0.33]),
        expected_len=3,
        fallback=[0.33, 0.34, 0.33],
    )

    allow_duplicate_roles = bool(raw.get("allow_duplicate_roles", False))
    panel_roles = _sanitize_panel_roles(
        raw.get("panel_roles", DEFAULT_PANEL_ROLES),
        allow_duplicates=allow_duplicate_roles,
    )

    config = LayoutConfig(
        main_split_ratio=main_split_ratio,
        right_stack_ratios=right_stack_ratios,
        content_vs_pnote_ratio=content_vs_pnote_ratio,
        allow_duplicate_roles=allow_duplicate_roles,
        panel_roles=panel_roles,
    )

    # Reescribe normalizado
    save_layout_config(config)
    return config


def save_layout_config(config: LayoutConfig) -> None:
    _ensure_app_dir()

    normalized = LayoutConfig(
        main_split_ratio=_clamp_ratio(config.main_split_ratio, 0.68),
        right_stack_ratios=_normalize_ratios(
            config.right_stack_ratios,
            expected_len=3,
            fallback=[0.33, 0.34, 0.33],
        ),
        content_vs_pnote_ratio=_clamp_ratio(config.content_vs_pnote_ratio, 0.90),
        allow_duplicate_roles=bool(config.allow_duplicate_roles),
        panel_roles=_sanitize_panel_roles(
            config.panel_roles,
            allow_duplicates=bool(config.allow_duplicate_roles),
        ),
    )

    LAYOUT_FILE.write_text(
        json.dumps(asdict(normalized), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )