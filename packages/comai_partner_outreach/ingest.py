"""Excel/CSV ingest for COMAI partner outreach campaigns."""

from __future__ import annotations

import csv
import io
import re
import zipfile
from dataclasses import dataclass, field
from email.utils import parseaddr
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from comai_partner_outreach.config import PartnerOutreachConfig
from comai_partner_outreach.types import PartnerLead, new_id, now_iso

COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "email": ("email", "work email", "work_email", "e-mail", "mail"),
    "first_name": ("first name", "first_name", "firstname", "founder first", "fname"),
    "last_name": ("last name", "last_name", "lastname", "surname", "lname"),
    "agency_name": (
        "agency name",
        "agency_name",
        "company",
        "company name",
        "business name",
        "agency",
        "organization",
        "organisation",
    ),
    "agency_type": ("agency type", "agency_type", "type", "category", "partner type", "vertical"),
    "website": ("website", "url", "agency url", "agency_url", "site", "web"),
    "domain": ("domain", "website domain"),
    "city": ("city", "location", "hq"),
    "phone": ("phone", "mobile", "whatsapp", "contact number", "phone number"),
    "services": ("services", "service", "offerings"),
    "notes": ("notes", "note", "why", "angle", "observation", "comments"),
    "linkedin_url": ("linkedin", "linkedin url", "linkedin_url"),
    "client_examples": ("client examples", "clients", "client_examples", "portfolio"),
    "founder_name": ("founder name", "founder_name", "contact name", "name", "full name"),
}

EMAIL_RE = re.compile(r"^[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}$", re.I)


@dataclass
class IngestResult:
    leads: list[PartnerLead] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    total_rows: int = 0
    valid_rows: int = 0
    skipped_rows: int = 0


def _norm_header(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower().replace("_", " "))


def _map_headers(headers: list[str]) -> dict[str, int]:
    mapped: dict[str, int] = {}
    normalized = [_norm_header(h) for h in headers]
    for canonical, aliases in COLUMN_ALIASES.items():
        for idx, header in enumerate(normalized):
            if header in aliases:
                mapped[canonical] = idx
                break
    return mapped


def _cell(row: list[str], mapping: dict[str, int], key: str) -> str:
    idx = mapping.get(key)
    if idx is None or idx >= len(row):
        return ""
    return str(row[idx] or "").strip()


def _split_founder_name(full: str) -> tuple[str, str]:
    parts = [p for p in (full or "").split() if p]
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def _domain_from_email_or_website(email: str, website: str, domain: str) -> str:
    if domain:
        return domain.lower().removeprefix("www.")
    if email and "@" in email:
        return email.split("@", 1)[1].lower().strip()
    if website:
        host = re.sub(r"^https?://", "", website.strip(), flags=re.I).split("/")[0]
        return host.lower().removeprefix("www.")
    return ""


def _valid_email(email: str) -> bool:
    _, addr = parseaddr(email)
    addr = (addr or email or "").strip().lower()
    return bool(EMAIL_RE.match(addr))


def _is_competitor(domain: str, email: str, config: PartnerOutreachConfig) -> bool:
    domains = config.competitor_domains
    d = (domain or "").lower()
    e = (email or "").lower()
    if d in domains:
        return True
    for c in domains:
        if c and (d.endswith(c) or e.endswith("@" + c)):
            return True
    return False


def rows_from_csv_text(text: str) -> tuple[list[str], list[list[str]]]:
    reader = csv.reader(io.StringIO(text))
    rows = [list(r) for r in reader]
    if not rows:
        return [], []
    return [str(h) for h in rows[0]], [[str(c) for c in r] for r in rows[1:]]


def rows_from_xlsx_bytes(data: bytes) -> tuple[list[str], list[list[str]]]:
    """Minimal XLSX reader (first sheet) without openpyxl."""
    try:
        import openpyxl  # type: ignore

        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        ws = wb.active
        rows_iter = list(ws.iter_rows(values_only=True))
        if not rows_iter:
            return [], []
        headers = [str(c or "") for c in rows_iter[0]]
        body = [["" if c is None else str(c) for c in r] for r in rows_iter[1:]]
        return headers, body
    except ImportError:
        pass

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
            for si in root.findall("m:si", ns):
                texts = [t.text or "" for t in si.findall(".//m:t", ns)]
                shared.append("".join(texts))

        sheet_name = "xl/worksheets/sheet1.xml"
        if sheet_name not in zf.namelist():
            sheets = [n for n in zf.namelist() if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")]
            if not sheets:
                raise ValueError("No worksheet found in XLSX")
            sheet_name = sorted(sheets)[0]

        root = ET.fromstring(zf.read(sheet_name))
        ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        rows_out: list[list[str]] = []
        for row in root.findall("m:sheetData/m:row", ns):
            cells: dict[int, str] = {}
            max_idx = 0
            for c in row.findall("m:c", ns):
                ref = c.attrib.get("r", "A1")
                col = 0
                for ch in ref:
                    if ch.isalpha():
                        col = col * 26 + (ord(ch.upper()) - ord("A") + 1)
                    else:
                        break
                col -= 1
                max_idx = max(max_idx, col)
                v = c.find("m:v", ns)
                raw = v.text if v is not None and v.text is not None else ""
                if c.attrib.get("t") == "s" and raw.isdigit():
                    idx = int(raw)
                    cells[col] = shared[idx] if idx < len(shared) else ""
                else:
                    cells[col] = raw
            rows_out.append([cells.get(i, "") for i in range(max_idx + 1)])
        if not rows_out:
            return [], []
        return rows_out[0], rows_out[1:]


def parse_tabular(
    headers: list[str],
    body: list[list[str]],
    *,
    campaign_id: str,
    config: PartnerOutreachConfig,
    already_sent: set[str] | None = None,
) -> IngestResult:
    mapping = _map_headers(headers)
    result = IngestResult(total_rows=len(body))
    seen_in_batch: set[str] = set()
    sent = {e.lower() for e in (already_sent or set())}

    if "email" not in mapping:
        result.errors.append({"row": 0, "error": "Missing required column: email"})
        result.skipped_rows = len(body)
        return result

    for i, row in enumerate(body, start=2):
        if not any(str(c).strip() for c in row):
            continue
        email = _cell(row, mapping, "email").lower().strip()
        first = _cell(row, mapping, "first_name")
        last = _cell(row, mapping, "last_name")
        if not first and "founder_name" in mapping:
            first, last = _split_founder_name(_cell(row, mapping, "founder_name"))
        agency = _cell(row, mapping, "agency_name")
        agency_type = _cell(row, mapping, "agency_type")
        website = _cell(row, mapping, "website")
        domain = _domain_from_email_or_website(email, website, _cell(row, mapping, "domain"))

        if not email or not _valid_email(email):
            result.errors.append({"row": i, "email": email, "error": "invalid_or_missing_email"})
            result.skipped_rows += 1
            continue
        if email in seen_in_batch:
            result.errors.append({"row": i, "email": email, "error": "duplicate_in_file"})
            result.skipped_rows += 1
            continue
        if email in sent:
            result.errors.append({"row": i, "email": email, "error": "already_sent"})
            result.skipped_rows += 1
            continue
        if _is_competitor(domain, email, config):
            result.errors.append({"row": i, "email": email, "error": "competitor_excluded", "domain": domain})
            result.skipped_rows += 1
            continue

        seen_in_batch.add(email)
        lead = PartnerLead(
            id=new_id(),
            campaign_id=campaign_id,
            email=email,
            first_name=first,
            last_name=last,
            agency_name=agency or domain or email.split("@")[0],
            agency_type=agency_type,
            website=website,
            domain=domain,
            city=_cell(row, mapping, "city"),
            phone=_cell(row, mapping, "phone"),
            services=_cell(row, mapping, "services"),
            notes=_cell(row, mapping, "notes"),
            linkedin_url=_cell(row, mapping, "linkedin_url"),
            client_examples=_cell(row, mapping, "client_examples"),
            stage="uploaded",
            row_index=i,
            created_at=now_iso(),
            updated_at=now_iso(),
        )
        result.leads.append(lead)
        result.valid_rows += 1

    return result


def parse_upload(
    *,
    filename: str,
    content: bytes,
    campaign_id: str,
    config: PartnerOutreachConfig,
    already_sent: set[str] | None = None,
) -> IngestResult:
    name = (filename or "").lower()
    if name.endswith(".csv") or name.endswith(".txt"):
        text = content.decode("utf-8-sig", errors="replace")
        headers, body = rows_from_csv_text(text)
    elif name.endswith(".xlsx"):
        headers, body = rows_from_xlsx_bytes(content)
    elif name.endswith(".xls"):
        raise ValueError("Legacy .xls is not supported — export as .xlsx or .csv")
    else:
        # Try CSV first, then xlsx
        try:
            text = content.decode("utf-8-sig")
            if "," in text.splitlines()[0] if text.splitlines() else "":
                headers, body = rows_from_csv_text(text)
            else:
                headers, body = rows_from_xlsx_bytes(content)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"Unsupported file type for {filename}: {exc}") from exc

    return parse_tabular(
        headers,
        body,
        campaign_id=campaign_id,
        config=config,
        already_sent=already_sent,
    )


def parse_file_path(
    path: Path,
    *,
    campaign_id: str,
    config: PartnerOutreachConfig,
    already_sent: set[str] | None = None,
) -> IngestResult:
    return parse_upload(
        filename=path.name,
        content=path.read_bytes(),
        campaign_id=campaign_id,
        config=config,
        already_sent=already_sent,
    )
