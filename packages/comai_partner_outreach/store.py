"""JSON file store for partner outreach campaigns (workspace-style persistence)."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any

from comai_partner_outreach.types import (
    PartnerCampaign,
    PartnerEvent,
    PartnerLead,
    PartnerMessage,
    now_iso,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STORE_DIR = ROOT / "exports" / "comai_partner_outreach"

_lock = threading.RLock()
logger = logging.getLogger(__name__)


class PartnerOutreachStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or DEFAULT_STORE_DIR
        self.root.mkdir(parents=True, exist_ok=True)
        self._index_path = self.root / "index.json"
        self._rate_path = self.root / "rate_limit.json"
        self._sent_path = self.root / "sent_emails.json"

    def _read_json(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return default

    def _write_json(self, path: Path, data: Any) -> None:
        """Atomic-ish write with Windows-friendly retries (AV / indexer file locks)."""
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(data, indent=2, ensure_ascii=False)
        tmp = path.with_suffix(path.suffix + f".{os.getpid()}.{threading.get_ident()}.tmp")
        last_err: Exception | None = None
        for attempt in range(8):
            try:
                tmp.write_text(payload, encoding="utf-8")
                try:
                    os.replace(tmp, path)
                except PermissionError:
                    # Destination locked — remove then rename, or fall back to direct write
                    try:
                        if path.exists():
                            path.unlink()
                        os.replace(tmp, path)
                    except OSError:
                        path.write_text(payload, encoding="utf-8")
                        try:
                            tmp.unlink(missing_ok=True)
                        except OSError:
                            pass
                return
            except OSError as exc:
                last_err = exc
                time.sleep(0.05 * (attempt + 1))
                try:
                    tmp.unlink(missing_ok=True)
                except OSError:
                    pass
        logger.error("Failed writing %s after retries: %s", path, last_err)
        if last_err:
            raise last_err

    def _campaign_dir(self, campaign_id: str) -> Path:
        d = self.root / "campaigns" / campaign_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def list_campaign_ids(self) -> list[str]:
        with _lock:
            idx = self._read_json(self._index_path, {"campaigns": []})
            return list(idx.get("campaigns") or [])

    def save_campaign(self, campaign: PartnerCampaign) -> None:
        with _lock:
            path = self._campaign_dir(campaign.id) / "campaign.json"
            campaign.updated_at = now_iso()
            self._write_json(path, campaign.to_dict())
            idx = self._read_json(self._index_path, {"campaigns": []})
            ids = list(idx.get("campaigns") or [])
            if campaign.id not in ids:
                ids.insert(0, campaign.id)
                idx["campaigns"] = ids
                self._write_json(self._index_path, idx)

    def get_campaign(self, campaign_id: str) -> PartnerCampaign | None:
        with _lock:
            path = self._campaign_dir(campaign_id) / "campaign.json"
            data = self._read_json(path, None)
            if not data:
                return None
            return PartnerCampaign.from_dict(data)

    def save_leads(self, campaign_id: str, leads: list[PartnerLead]) -> None:
        with _lock:
            path = self._campaign_dir(campaign_id) / "leads.json"
            self._write_json(path, [l.to_dict() for l in leads])

    def get_leads(self, campaign_id: str) -> list[PartnerLead]:
        with _lock:
            path = self._campaign_dir(campaign_id) / "leads.json"
            data = self._read_json(path, [])
            return [PartnerLead.from_dict(x) for x in data]

    def upsert_lead(self, lead: PartnerLead) -> None:
        with _lock:
            leads = self.get_leads(lead.campaign_id)
            found = False
            for i, existing in enumerate(leads):
                if existing.id == lead.id:
                    lead.updated_at = now_iso()
                    leads[i] = lead
                    found = True
                    break
            if not found:
                leads.append(lead)
            self.save_leads(lead.campaign_id, leads)

    def append_message(self, message: PartnerMessage) -> None:
        with _lock:
            path = self._campaign_dir(message.campaign_id) / "messages.json"
            data = self._read_json(path, [])
            data.append(message.to_dict())
            self._write_json(path, data)

    def get_messages(self, campaign_id: str) -> list[PartnerMessage]:
        with _lock:
            path = self._campaign_dir(campaign_id) / "messages.json"
            data = self._read_json(path, [])
            return [PartnerMessage.from_dict(x) for x in data]

    def append_event(self, event: PartnerEvent) -> None:
        self.append_events([event])

    def append_events(self, events: list[PartnerEvent]) -> None:
        if not events:
            return
        with _lock:
            # Group by campaign for fewer writes
            by_campaign: dict[str, list[PartnerEvent]] = {}
            for event in events:
                by_campaign.setdefault(event.campaign_id, []).append(event)
            for campaign_id, batch in by_campaign.items():
                path = self._campaign_dir(campaign_id) / "events.json"
                data = self._read_json(path, [])
                data.extend(e.to_dict() for e in batch)
                self._write_json(path, data)

    def get_events(self, campaign_id: str) -> list[PartnerEvent]:
        with _lock:
            path = self._campaign_dir(campaign_id) / "events.json"
            data = self._read_json(path, [])
            return [PartnerEvent.from_dict(x) for x in data]

    def load_rate_state(self) -> dict[str, Any]:
        with _lock:
            return self._read_json(self._rate_path, {})

    def save_rate_state(self, data: dict[str, Any]) -> None:
        with _lock:
            self._write_json(self._rate_path, data)

    def load_sent_emails(self) -> set[str]:
        with _lock:
            data = self._read_json(self._sent_path, {"emails": []})
            return {str(e).lower() for e in data.get("emails") or []}

    def mark_sent_email(self, email: str) -> None:
        with _lock:
            data = self._read_json(self._sent_path, {"emails": []})
            emails = {str(e).lower() for e in data.get("emails") or []}
            emails.add(email.lower())
            self._write_json(self._sent_path, {"emails": sorted(emails)})

    def all_leads(self) -> list[PartnerLead]:
        leads: list[PartnerLead] = []
        for cid in self.list_campaign_ids():
            leads.extend(self.get_leads(cid))
        return leads

    def inbox(self, limit: int = 100) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for cid in self.list_campaign_ids():
            for msg in self.get_messages(cid):
                if msg.direction != "inbound":
                    continue
                items.append(msg.to_dict())
        items.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        return items[:limit]

    def clear_all_campaigns(self) -> dict[str, Any]:
        """Remove all campaign folders and reset index / rate / sent tracking."""
        import shutil

        with _lock:
            campaigns_root = self.root / "campaigns"
            removed = 0
            if campaigns_root.exists():
                for child in list(campaigns_root.iterdir()):
                    if child.is_dir():
                        shutil.rmtree(child, ignore_errors=True)
                        removed += 1
                    elif child.is_file():
                        child.unlink(missing_ok=True)
            self._write_json(self._index_path, {"campaigns": []})
            self._write_json(self._rate_path, {})
            self._write_json(self._sent_path, {"emails": []})
            return {"cleared": True, "campaigns_removed": removed}
