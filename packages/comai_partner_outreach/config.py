"""Load COMAI partner outreach config from YAML + env overrides."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = ROOT / "config" / "comai_partner_outreach.yaml"

_ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")


def _resolve_env(value: Any) -> Any:
    if isinstance(value, str):

        def repl(match: re.Match[str]) -> str:
            return os.getenv(match.group(1), "")

        return _ENV_PATTERN.sub(repl, value)
    if isinstance(value, dict):
        return {k: _resolve_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env(v) for v in value]
    return value


def _load_yaml(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text) or {}
        if not isinstance(data, dict):
            raise ValueError("config root must be a mapping")
        return data
    except ImportError:
        # Minimal YAML subset parser for this config shape (no nested lists of maps beyond known keys).
        return _minimal_yaml(text)


def _minimal_yaml(text: str) -> dict[str, Any]:
    """Fallback parser when PyYAML is unavailable — enough for our config file."""
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any] | list[Any]]] = [(-1, root)]
    pending_key: str | None = None

    def current_container() -> dict[str, Any] | list[Any]:
        return stack[-1][1]

    for raw in text.splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        container = current_container()

        if line.startswith("- "):
            item = line[2:].strip().strip('"').strip("'")
            if isinstance(container, list):
                if ":" in item and not item.startswith("http"):
                    k, _, v = item.partition(":")
                    container.append({k.strip(): _scalar(v.strip())})
                else:
                    container.append(_scalar(item))
            elif isinstance(container, dict) and pending_key:
                lst: list[Any] = []
                container[pending_key] = lst
                stack.append((indent, lst))
                pending_key = None
                if ":" in item and not item.startswith("http"):
                    k, _, v = item.partition(":")
                    lst.append({k.strip(): _scalar(v.strip())})
                else:
                    lst.append(_scalar(item))
            continue

        if ":" in line:
            key, _, rest = line.partition(":")
            key = key.strip()
            rest = rest.strip()
            if not isinstance(container, dict):
                continue
            if rest == "":
                pending_key = key
                # peek: next non-empty will decide map vs list; create map by default
                child: dict[str, Any] = {}
                container[key] = child
                stack.append((indent, child))
            else:
                container[key] = _scalar(rest.strip('"').strip("'"))
                pending_key = None
    return root


def _scalar(value: str) -> Any:
    if value.lower() in ("true", "yes"):
        return True
    if value.lower() in ("false", "no"):
        return False
    if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
        return int(value)
    try:
        if "." in value:
            return float(value)
    except ValueError:
        pass
    return value


@dataclass
class PartnerOutreachConfig:
    video_url: str = "https://comai.in"
    thumbnail_url: str = ""
    logo_url: str = ""
    cta_label: str = "Watch COM sell on WhatsApp (2 min)"
    commission_pct: int = 15
    trial_days: int = 10
    referral_bonus_inr: int = 200
    referral_bonus_threshold: int = 2
    partner_page_url: str = "https://comai.in"
    calendly_url: str = ""
    from_name: str = "Vansh"
    from_email: str = "vansh@inowix.in"
    signoff_title: str = "COMAI"
    utm: dict[str, str] = field(default_factory=dict)
    max_per_hour: int = 20
    max_per_day: int = 80
    min_seconds_between_sends: int = 45
    business_start_hour: int = 9
    business_end_hour: int = 19
    weekdays_only: bool = True
    max_send_retries: int = 3
    sequence_steps: list[dict[str, Any]] = field(default_factory=list)
    stop_on: list[str] = field(default_factory=list)
    nurture_reentry_days: int = 60
    partner_type_angles: dict[str, str] = field(default_factory=dict)
    competitor_domains: set[str] = field(default_factory=set)
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def enabled(self) -> bool:
        return os.getenv("COMAI_PARTNER_OUTREACH_ENABLED", "false").lower() in (
            "1",
            "true",
            "yes",
            "on",
        )

    @property
    def dry_run(self) -> bool:
        # Default dry-run ON until explicitly disabled — safer for domain reputation.
        if not self.enabled:
            return True
        return os.getenv("COMAI_PARTNER_OUTREACH_DRY_RUN", "true").lower() in (
            "1",
            "true",
            "yes",
            "on",
        )

    def with_overrides(self, **kwargs: Any) -> PartnerOutreachConfig:
        data = {**self.__dict__, **kwargs}
        data.pop("raw", None)
        cfg = PartnerOutreachConfig(**{k: v for k, v in data.items() if k in PartnerOutreachConfig.__dataclass_fields__})
        cfg.raw = self.raw
        return cfg

    def partner_page_with_utm(self) -> str:
        base = self.partner_page_url or "https://comai.in"
        if not self.utm:
            return base
        from urllib.parse import urlencode, urlparse, urlunparse, parse_qs

        parsed = urlparse(base)
        q = parse_qs(parsed.query)
        for k, v in self.utm.items():
            q[k] = [str(v)]
        query = urlencode({k: v[0] for k, v in q.items()})
        return urlunparse(parsed._replace(query=query))

    def angle_for(self, agency_type: str) -> str:
        key = (agency_type or "").strip().lower().replace(" ", "_").replace("-", "_")
        if key in self.partner_type_angles:
            return self.partner_type_angles[key]
        # fuzzy contains
        for k, v in self.partner_type_angles.items():
            if k != "default" and k in key:
                return v
        aliases = {
            "marketing": "performance_marketing_agency",
            "video": "video_production_agency",
            "web": "website_development_agency",
            "website": "website_development_agency",
            "shopify": "shopify_development_agency",
            "freelance": "freelance_marketer",
            "consultant": "business_consultant",
            "creative": "creative_studio",
        }
        for needle, mapped in aliases.items():
            if needle in key and mapped in self.partner_type_angles:
                return self.partner_type_angles[mapped]
        return self.partner_type_angles.get(
            "default",
            "agencies and consultants like yours can offer clients WhatsApp lead management without building the tech",
        )


def load_config(path: Path | None = None) -> PartnerOutreachConfig:
    cfg_path = path or DEFAULT_CONFIG_PATH
    raw: dict[str, Any] = {}
    if cfg_path.exists():
        raw = _resolve_env(_load_yaml(cfg_path))

    video = raw.get("video") or {}
    brand = raw.get("brand") or {}
    economics = raw.get("economics") or {}
    links = raw.get("links") or {}
    safety = raw.get("send_safety") or {}
    hours = safety.get("business_hours_ist") or {}
    sequence = raw.get("sequence") or {}
    angles = raw.get("partner_type_angles") or {}
    competitors = raw.get("competitor_domains") or []

    video_url = (
        (video.get("url") or "").strip()
        or os.getenv("COMAI_PARTNER_VIDEO_URL", "")
        or "https://comai.in"
    )
    thumb = (
        (video.get("thumbnail_url") or "").strip()
        or os.getenv("COMAI_PARTNER_VIDEO_THUMB", "")
        or str(brand.get("default_thumbnail_url") or "")
    )
    logo = (
        (brand.get("logo_url") or "").strip()
        or os.getenv("COMAI_PARTNER_LOGO_URL", "")
        or str(brand.get("default_logo_url") or "")
    )

    return PartnerOutreachConfig(
        video_url=video_url,
        thumbnail_url=thumb,
        logo_url=logo,
        cta_label=str(video.get("cta_label") or "Watch COM sell on WhatsApp (2 min)"),
        commission_pct=int(economics.get("commission_pct") or 15),
        trial_days=int(economics.get("trial_days") or 10),
        referral_bonus_inr=int(economics.get("referral_bonus_inr") or 200),
        referral_bonus_threshold=int(economics.get("referral_bonus_threshold") or 2),
        partner_page_url=str(links.get("partner_page_url") or "https://comai.in"),
        calendly_url=str(links.get("calendly_url") or ""),
        from_name=str(links.get("from_name") or "Vansh"),
        from_email=str(links.get("from_email") or "vansh@inowix.in"),
        signoff_title=str(links.get("signoff_title") or "COMAI"),
        utm={str(k): str(v) for k, v in (links.get("utm") or {}).items()},
        max_per_hour=int(safety.get("max_per_hour") if safety.get("max_per_hour") is not None else 20),
        max_per_day=int(safety.get("max_per_day") if safety.get("max_per_day") is not None else 80),
        min_seconds_between_sends=int(
            safety.get("min_seconds_between_sends")
            if safety.get("min_seconds_between_sends") is not None
            else 45
        ),
        business_start_hour=int(hours["start_hour"]) if "start_hour" in hours else 9,
        business_end_hour=int(hours["end_hour"]) if "end_hour" in hours else 19,
        weekdays_only=bool(hours["weekdays_only"]) if "weekdays_only" in hours else True,
        max_send_retries=int(safety.get("max_send_retries") or 3),
        sequence_steps=list(sequence.get("steps") or [
            {"step": "intro", "day_offset": 0},
            {"step": "fu1", "day_offset": 3},
            {"step": "fu2", "day_offset": 7},
            {"step": "final", "day_offset": 14},
        ]),
        stop_on=list(sequence.get("stop_on") or [
            "replied", "bounce", "unsubscribed", "meeting", "partner_onboarded", "lost", "killed"
        ]),
        nurture_reentry_days=int(sequence.get("nurture_reentry_days") or 60),
        partner_type_angles={str(k): str(v) for k, v in angles.items()},
        competitor_domains={str(d).lower().strip() for d in competitors},
        raw=raw,
    )
