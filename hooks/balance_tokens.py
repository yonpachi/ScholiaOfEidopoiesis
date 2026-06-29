"""MkDocs hook: expand {dotted.key} tokens in Markdown from balance/constants.yaml."""

from __future__ import annotations

import re
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from balance.loader import build_doc_tokens, load_raw  # noqa: E402

_TOKEN_PATTERN = re.compile(r"\{([a-z][a-z0-9_.]*)\}")
_BALANCE_KEY = re.compile(
    r"^(?:consumable|weapon|armor|equipment|phase1|part7_ref|timeline|base_action_wait|"
    r"item_weight_correction|dpc_optimal|deck|meta)\."
)
_TOKENS: dict[str, str] | None = None


def _load_tokens(config) -> dict[str, str]:
    global _TOKENS
    if _TOKENS is not None:
        return _TOKENS

    root = Path(config.config_file_path).parent
    constants_path = root / "balance" / "constants.yaml"
    if not constants_path.is_file():
        raise FileNotFoundError(f"balance constants not found: {constants_path}")

    _TOKENS = build_doc_tokens(load_raw(constants_path))
    return _TOKENS


def on_config(config, **kwargs) -> None:
    _load_tokens(config)


def on_page_markdown(markdown: str, *, page, config, **kwargs) -> str:
    tokens = _load_tokens(config)
    unknown: set[str] = set()

    def replacer(match: re.Match[str]) -> str:
        key = match.group(1)
        if key in tokens:
            return tokens[key]
        if _BALANCE_KEY.match(key):
            unknown.add(key)
        return match.group(0)

    result = _TOKEN_PATTERN.sub(replacer, markdown)
    if unknown:
        warnings.warn(
            f"balance_tokens [{page.file.src_path}]: unknown token(s): "
            + ", ".join(sorted(f"{{{u}}}" for u in unknown)),
            stacklevel=1,
        )
    return result
