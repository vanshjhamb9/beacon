"""Clean the outreach pool — remove garbage, duplicates, and invalid leads."""
import json
import re
from pathlib import Path

POOL_PATH = Path(r"C:\Inowix intelligence system\New folder\exports\lead_engine_runs\_outreach_pool.json")

with open(POOL_PATH) as f:
    pool = json.load(f)

leads = pool.get("leads", [])
original_count = len(leads)

# Garbage detection patterns
GARBAGE_PATTERNS = [
    r"has anyone", r"soc 2", r"pentest", r"security audit", r"how to",
    r"what is", r"can you", r"help me", r"question", r"looking for",
    r"recommend", r"advice", r"suggestion", r"feedback", r"review",
]

def is_valid(lead: dict) -> tuple[bool, str]:
    """Check if a lead is valid. Returns (valid, reason)."""
    company = (lead.get("company") or "").strip()
    email = (lead.get("email") or "").strip().lower()
    
    # No company name
    if not company or len(company) < 2:
        return False, "no_company"
    
    # No email
    if not email or "@" not in email:
        return False, "no_email"
    
    # Garbage patterns in company name
    company_lower = company.lower()
    for pat in GARBAGE_PATTERNS:
        if re.search(pat, company_lower):
            return False, f"garbage_pattern:{pat}"
    
    # Garbage email domains
    if email.endswith(("@example.com", "@test.com", "@placeholder.com")):
        return False, "invalid_email_domain"
    
    # Company name looks like a question
    if company.strip().endswith("?") or company.strip().startswith("How"):
        return False, "question_not_company"
    
    # Too long company name (likely scraped wrong)
    if len(company) > 80:
        return False, "company_name_too_long"
    
    # Generic/test leads
    if company_lower in ("test", "unknown", "n/a", "none", "example"):
        return False, "generic_name"
    
    return True, "ok"


cleaned = []
removed = {}
for lead in leads:
    valid, reason = is_valid(lead)
    if valid:
        cleaned.append(lead)
    else:
        removed[reason] = removed.get(reason, 0) + 1

pool["leads"] = cleaned
pool["count"] = len(cleaned)

with open(POOL_PATH, "w") as f:
    json.dump(pool, f, indent=2, default=str)

print(f"Pool cleaned: {original_count} -> {len(cleaned)} ({original_count - len(cleaned)} removed)")
print("Removed reasons:")
for reason, count in sorted(removed.items(), key=lambda x: -x[1]):
    print(f"  {reason}: {count}")
