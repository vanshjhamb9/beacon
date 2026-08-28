"""Buying-event and reject regex for the cybersecurity lane.

Keywords discover candidates. They never independently qualify a lead.
"""

from __future__ import annotations

import re

# Explicit commercial buying events grouped by directive categories.
BUYING_PATTERNS: dict[str, list[str]] = {
    "vulnerability_security_issue": [
        r"(?:we\s+found|found|discovered|detected)\s+(?:a\s+)?(?:security\s+)?(?:vulnerability|security\s+(?:issue|bug|flaw|hole))",
        r"(?:our|the)\s+(?:website|app|application|platform|api|product)\s+(?:has|has\s+a)\s+(?:a\s+)?(?:security\s+(?:issue|problem|vulnerability|bug))",
        r"(?:need|looking\s+for|want)\s+(?:help\s+)?(?:fixing|remediat(?:e|ion)|patching)\s+(?:a\s+)?(?:vulnerability|security\s+(?:issue|bug))",
        r"(?:security\s+bug|security\s+issue)\s+(?:discovered|found|reported)",
        r"(?:need|looking\s+for)\s+someone\s+to\s+investigate\s+(?:a\s+)?(?:security|vuln)",
        r"(?:platform|website|app|system)\s+(?:was\s+)?(?:compromised|breached|hacked)",
        r"(?:security\s+incident|data\s+breach|account\s+takeover)\b.{0,80}(?:need|looking|help|investigate|respond|hired?|vendor|external)",
        r"(?:discovered|found)\s+(?:major\s+)?(?:security\s+flaws?|vulnerabilit(?:y|ies))\s+in\s+(?:my|our)\s+(?:web\s+store|website|app|application|platform|saas)",
        r"(?:need|looking\s+for|seeking|want)\s+(?:a\s+)?(?:penetration\s+test(?:ing)?|pentest(?:ing)?|pen\s*test)",
        r"(?:need|looking\s+for|seeking|want)\s+(?:a\s+)?(?:vulnerability\s+assessment|security\s+audit|security\s+assessment)",
        r"(?:need|looking\s+for|seeking|want)\s+(?:application\s+security\s+testing|web\s+application\s+penetration\s+test|api\s+security\s+testing|mobile\s+(?:app\s+)?security\s+testing)",
        r"(?:recommend|any(?:one|body)\s+(?:know|recommend|suggest))\s+(?:a\s+)?(?:good\s+)?(?:pentest|penetration\s+test(?:ing)?|vapt|security\s+audit)\s*(?:company|firm|vendor|provider|agency)?",
        r"(?:who\s+(?:do\s+you\s+)?(?:use|recommend)\s+for)\s+(?:pentest|penetration\s+test|vapt|security\s+audit)",
        r"(?:looking\s+to\s+(?:hire|get|find))\s+(?:a\s+)?(?:pentester|penetration\s+tester|pentest(?:ing)?|vapt|security\s+firm)",
        r"(?:quotes?\s+(?:for|on)\s+(?:a\s+)?)(?:pentest|penetration\s+test|vapt|security\s+audit)",
        r"(?:budget\s+for)\s+(?:a\s+)?(?:pentest|penetration\s+test|vapt)",
    ],
    "external_security_team": [
        r"(?:looking\s+for|need|seeking|want)\s+(?:a\s+)?(?:cybersecurity|cyber\s+security|information\s+security)\s+(?:company|firm|agency|vendor|provider)",
        r"(?:looking\s+for|need|seeking)\s+(?:a\s+)?(?:penetration\s+testing|pentest(?:ing)?|vapt)\s+(?:company|firm|agency|vendor|provider|partner)",
        r"(?:need|looking\s+for|seeking)\s+(?:a\s+)?(?:security\s+consultant|external\s+security\s+team|security\s+auditor)",
        r"(?:need|looking\s+for|seeking)\s+(?:an?\s+)?(?:ethical\s+hacker|application\s+security\s+expert)",
        r"(?:need|looking\s+for)\s+someone\s+to\s+(?:test|pentest|audit|assess)\s+(?:our|the)\s+(?:platform|app|website|api|product)",
        r"(?:hire|hiring|engaged?)\s+(?:an?\s+)?(?:external|outside|third[\s-]?party)\s+(?:security|pentest|vapt)",
        r"(?:need|looking\s+for|seeking|want)\s+(?:an?\s+)?(?:independent|third[\s-]?party)\s+(?:pentest|security\s+audit|security\s+assessment)",
    ],
    "compliance_vapt": [
        r"\b(?:need|looking\s+for|seeking|require[ds]?)\s+(?:a\s+)?(?:vapt|va\s*/\s*pt|va/pt)\b",
        r"(?:need|looking\s+for|require[ds]?)\s+(?:a\s+)?(?:penetration\s+testing|pentest|vapt|security)\s+report",
        r"(?:need|looking\s+for|require[ds]?)\s+(?:security\s+certification|security\s+assessment\s+for\s+compliance)",
        r"(?:need|looking\s+for|require[ds]?)\s+(?:soc\s*2|iso\s*27001|pci[\s-]?dss|hipaa|gdpr)\s+(?:security\s+)?(?:testing|assessment|audit|pentest|vapt)",
        r"(?:customer|enterprise|client|prospect)\s+(?:requires?|asked\s+for|needs?)\s+(?:a\s+)?(?:penetration\s+test|pentest|vapt|security\s+audit)",
        r"(?:need|looking\s+for)\s+security\s+testing\s+before\s+(?:enterprise\s+launch|go[\s-]?live|production)",
        r"soc\s*2.{0,160}(?:pentest|penetration\s+test|vapt)",
        r"(?:pentest|penetration\s+test|vapt).{0,160}soc\s*2",
        r"looking\s+for\s+an?\s+(?:alternative|more\s+affordable).{0,200}(?:pentest|vapt|penetration\s+test)",
        r"(?:pentest|vapt|penetration\s+test).{0,200}looking\s+for\s+an?\s+(?:alternative|more\s+affordable)",
        r"(?:affordable|cheaper|budget).{0,40}(?:pentest|penetration\s+test|vapt)\s+(?:option|vendor|company|provider)",
        r"alternative.{0,40}(?:to|for).{0,40}(?:cobalt|hackerone|bugcrowd).{0,80}(?:pentest|vapt)",
    ],
    "prelaunch_enterprise": [
        r"(?:launching|going\s+live|before\s+(?:launch|production|go[\s-]?live)).{0,60}(?:need|looking\s+for|require).{0,40}(?:security\s+test|pentest|vapt|security\s+audit|security\s+review)",
        r"(?:enterprise\s+customer|enterprise\s+deal)\s+(?:requires?|needs?|asked).{0,40}(?:security\s+audit|pentest|vapt)",
        r"(?:need|looking\s+for)\s+(?:a\s+)?(?:pentest|penetration\s+test|security\s+review|security\s+assessment)\s+before\s+(?:production|launch|go[\s-]?live)",
        r"(?:need|looking\s+for)\s+(?:external\s+security\s+validation|pre[\s-]?launch\s+security)",
    ],
    "security_contractor": [
        r"(?:hiring|looking\s+for|need)\s+(?:a\s+)?(?:freelance|contract(?:or)?|external)\s+(?:penetration\s+tester|pentester|security\s+consultant|security\s+researcher|application\s+security\s+engineer)",
        r"(?:looking\s+for|need)\s+(?:a\s+)?(?:cybersecurity\s+agency|appsec\s+engineer|security\s+contractor)",
        r"(?:contract|freelance|part[\s-]?time).{0,40}(?:pentest|vapt|application\s+security|appsec)",
    ],
    "compliance_driven": [
        r"(?:soc\s*2|iso\s*27001|pci[\s-]?dss|hipaa|gdpr).{0,80}(?:need|require|looking|before|audit|certification)",
        r"(?:audit|certification|compliance).{0,80}(?:need|require|looking).{0,40}(?:pentest|security|test|assessment)",
        r"(?:customer|client|investor|partner).{0,40}(?:requires?|asks?|needs?).{0,40}(?:security|pentest|audit|test)",
        r"(?:before|prior\s+to).{0,40}(?:launch|go[\s-]?live|production|enterprise|series|funding).{0,60}(?:security|pentest|audit|test|assessment)",
        r"(?:regulatory|compliance).{0,40}(?:requirement|obligation|deadline).{0,40}(?:security|pentest|audit)",
    ],
    "general_security_buying": [
        r"(?:we|our|my|the)\s+(?:startup|company|saas|app|platform|product|website|api).{0,60}(?:need|require|looking).{0,40}(?:security|pentest|audit|assessment|testing|vapt)",
        r"(?:need|require|looking|seeking).{0,40}(?:help|someone|team|company|firm|vendor|agency).{0,40}(?:with|for).{0,40}(?:security|pentest|audit|assessment|testing|vapt|vulnerability)",
        r"(?:security|pentest|audit|assessment|vapt).{0,80}(?:recommend|suggest|anyone|who|advice|thoughts?)",
        r"(?:budget|cost|price|affordable|cheap).{0,40}(?:pentest|security|audit|assessment|vapt|penetration)",
        r"(?:small|early[\s-]?stage|seed[\s-]?stage).{0,40}(?:startup|company).{0,60}(?:security|pentest|audit|assessment)",
        r"(?:anyone|has\s+anyone).{0,40}(?:used|tried|hired).{0,40}(?:pentester|pentest|vapt|security\s+(?:firm|company|consultant))",
        r"(?:we|our).{0,40}(?:need|want|looking).{0,40}(?:someone|anyone).{0,40}(?:to|for).{0,40}(?:pentest|security|audit|vapt)",
        r"(?:how|where)\s+(?:do|can)\s+(?:we|i|you)\s+(?:find|get|hire).{0,40}(?:pentest|security|audit|vapt)",
        r"(?:thinking|planning).{0,40}(?:about|of).{0,40}(?:getting|doing|hiring).{0,40}(?:pentest|security|audit|vapt)",
        r"(?:time|ready).{0,40}(?:for|to).{0,40}(?:get|do|have).{0,40}(?:pentest|security|audit|vapt|penetration)",
    ],
    "modern_security_buying": [
        r"(?:need|looking|seeking).{0,40}(?:AI|LLM|ML|machine\s+learning).{0,40}(?:security|red\s+team|pentest|audit|testing)",
        r"(?:AI|LLM|ML).{0,40}(?:security|red\s+team|pentest|audit).{0,40}(?:need|looking|vendor|company)",
        r"(?:need|looking|seeking).{0,40}(?:SBOM|software\s+bill).{0,40}(?:review|audit|assessment)",
        r"(?:supply\s+chain|third[\s-]?party).{0,40}(?:security|assessment|audit|review).{0,40}(?:need|looking|vendor)",
        r"(?:need|looking|seeking).{0,40}(?:shift[\s-]?left|DevSecOps|CI/?CD).{0,40}(?:security|testing|pentest)",
        r"(?:need|looking|seeking).{0,40}(?:Kubernetes|k8s|AWS|Azure|cloud).{0,40}(?:security|pentest|audit|assessment)",
        r"(?:need|looking|seeking).{0,40}(?:security\s+due\s+diligence|M&A\s+security|acquisition\s+security).{0,40}(?:review|assessment|audit)",
        r"(?:penetration\s+test|security\s+audit|vapt).{0,40}(?:Kubernetes|k8s|container|Docker|cloud)",
        r"(?:container|kubernetes|k8s).{0,40}(?:security|pentest|vulnerability).{0,40}(?:need|assessment|audit)",
        r"(?:cloud\s+security|AWS\s+security|Azure\s+security).{0,40}(?:assessment|audit|pentest).{0,40}(?:need|looking)",
    ],
}

PARTNER_PATTERNS: list[str] = [
    r"(?:need|looking\s+for|seeking)\s+(?:a\s+)?(?:cybersecurity|vapt|pentest(?:ing)?|security\s+testing)\s+partner(?:\s+for\s+clients)?",
    r"(?:need|looking\s+for)\s+(?:a\s+)?(?:white[\s-]?label)\s+(?:cybersecurity|vapt|pentest|security)",
    r"(?:need|looking\s+for)\s+(?:security\s+testing\s+subcontractor|pentesting\s+subcontractor)",
    r"(?:we\s+are\s+(?:a|an)\s+(?:web\s+development|saas\s+development|software|digital|it)\s+(?:agency|consultancy|msp)).{0,80}(?:need|looking).{0,40}(?:security|vapt|pentest)",
    r"(?:our\s+clients?\s+need)\s+(?:vapt|pentest|security\s+(?:testing|audit|assessment))",
]

# Matched first. If a reject pattern fires, the candidate is not a buying event.
REJECT_PATTERNS: dict[str, list[str]] = {
    "cybersecurity_news": [
        r"(?:breaking|reported|according\s+to|as\s+reported).{0,40}(?:breach|hack|ransomware|cve)",
        r"\bcve-\d{4}-\d+\b",
        r"(?:vulnerability\s+news|security\s+advisory|threat\s+intel(?:ligence)?)\b",
        r"(?:researchers?\s+(?:found|discovered|disclosed))\s+(?:a\s+)?(?:vulnerability|cve)",
    ],
    "third_party_vuln_news": [
        r"(?:company|firm|giant|bank)\s+(?:was\s+)?(?:hacked|breached|compromised)\b.{0,20}(?:report|article|news)",
        r"(?:in\s+the\s+news|techcrunch|krebsonsecurity|bleepingcomputer|thehackernews)",
    ],
    "security_blog": [
        r"(?:blog\s+post|write[\s-]?up|how[\s-]?to\s+guide|tutorial)\s+(?:on|about)\s+(?:security|pentest|cyber)",
        r"(?:what\s+is|guide\s+to|introduction\s+to)\s+(?:penetration\s+testing|vapt|soc\s*2|iso\s*27001)",
        r"(?:top\s+\d+|best\s+\d+|list\s+of)\s+(?:pentest|cybersecurity|vapt)\s+(?:tools|companies|firms)",
    ],
    "generic_discussion": [
        r"(?:cybersecurity\s+is\s+important|why\s+you\s+need\s+security|security\s+best\s+practices)\b",
        r"(?:thoughts\s+on|what\s+do\s+you\s+think\s+about)\s+(?:pentest|vapt|soc\s*2)",
        r"(?:career\s+advice|how\s+to\s+(?:learn|get\s+into)\s+(?:cyber|pentest))",
    ],
    "vendor_selling": [
        r"(?:we\s+(?:offer|provide|sell|deliver)\s+(?:pentest|vapt|cybersecurity|penetration\s+testing))",
        r"(?:our\s+(?:pentest|vapt|cybersecurity)\s+(?:service|offering|solution))",
        r"(?:hire\s+us|book\s+a\s+(?:demo|call)|request\s+a\s+quote).{0,40}(?:pentest|vapt|cyber)",
        r"(?:leading|award[\s-]?winning|trusted)\s+(?:pentest|vapt|cybersecurity)\s+(?:company|firm|provider)",
        r"(?:starting\s+at|packages?\s+from|pricing\s+for)\s+(?:pentest|vapt|security\s+audit)",
    ],
    "researcher_advertising": [
        r"(?:i\s+am\s+(?:a|an)\s+(?:security\s+researcher|pentester|ethical\s+hacker)).{0,60}(?:available|hire\s+me|open\s+for)",
        r"(?:offering\s+(?:pentest|vapt|bug\s+bounty)\s+services|dm\s+me\s+for\s+(?:pentest|vapt))",
    ],
    "job_seeker": [
        r"(?:looking|seeking|hunting)\s+for\s+(?:a\s+)?(?:job|role|position|internship)\s+(?:in\s+)?(?:cyber|security|pentest)",
        r"(?:hire\s+me|my\s+resume|open\s+to\s+work).{0,40}(?:security|pentest|appsec)",
        r"(?:i\s+want\s+to\s+(?:break\s+into|get\s+a\s+job\s+in)\s+cyber)",
    ],
    "offering_services": [
        r"(?:who\s+wants?\s+to\s+be\s+hired|who\s+is\s+hiring).{0,200}(?:security|pentest|ciso|cso|appsec)",
        r"(?:freelance|fractional|contract).{0,30}(?:ciso|cso|security\s+(?:consultant|advisor|officer))",
        r"(?:available\s+for\s+(?:hire|contract|freelance)).{0,40}(?:security|pentest|ciso)",
        r"(?:i\s+(?:am|'m)\s+(?:a\s+)?(?:freelance|fractional|independent)\s+(?:ciso|cso|security))",
        r"(?:my\s+(?:consulting|advisory)\s+(?:services|practice)).{0,40}(?:security|pentest)",
        r"(?:check\s+out\s+my|see\s+my|view\s+my).{0,30}(?:portfolio|services| offerings).{0,30}(?:security|pentest)",
    ],
    "student": [
        r"(?:student|coursework|assignment|college|university).{0,40}(?:pentest|vapt|cybersecurity)",
        r"(?:learning\s+(?:cyber|pentest)|bootcamp|tryhackme|hackthebox)\b",
        r"(?:pentest\+|pentest\s+tutor|comptia)",
    ],
    "directory_listing": [
        r"(?:best\s+cybersecurity\s+companies|company\s+directory|clutch\.co|goodfirms)",
        r"(?:top\s+vapt\s+vendors|list\s+of\s+pentest(?:ing)?\s+companies)",
    ],
    "funding_only": [
        r"(?:raised|closes|secures)\s+(?:a\s+)?(?:\$|€|£)?[\d.]+[mbk]?\s+(?:seed|series|round)",
    ],
    "tool_usage_only": [
        r"(?:we\s+use|using)\s+(?:cloudflare|okta|auth0|aws\s+waf|snyk|dependabot)\b",
        r"(?:security\s+page|trust\s+center|security\.md)\b",
    ],
    "generic_compliance_page": [
        r"(?:we\s+are\s+soc\s*2|iso\s*27001\s+certified|pci[\s-]?dss\s+compliant)\b",
        r"(?:privacy\s+policy|cookie\s+policy).{0,20}(?:gdpr|hipaa)",
    ],
    "bug_bounty_no_buyer": [
        r"(?:responsible\s+disclosure|bug\s+bounty|i\s+found\s+a\s+vuln\s+in\s+your)",
        r"(?:here\s+is\s+(?:a|the)\s+(?:poc|proof[\s-]?of[\s-]?concept)|writeup\s+of\s+(?:a\s+)?cve)",
    ],
}

SERVICE_PATTERNS: list[tuple[str, list[str]]] = [
    ("Web Application VAPT", [r"web\s+app(?:lication)?\s+(?:vapt|pentest|penetration\s+test)", r"website\s+(?:pentest|security\s+test|vapt)", r"owasp"]),
    ("API Security Testing", [r"api\s+security", r"api\s+(?:pentest|vapt|testing)"]),
    ("Mobile Application Security Testing", [r"mobile\s+(?:app\s+)?(?:security|pentest|vapt)", r"(?:ios|android)\s+(?:app\s+)?(?:security|pentest)"]),
    ("Infrastructure Security Assessment", [r"infrastructure\s+(?:security|assessment|pentest)", r"network\s+(?:pentest|security\s+assessment)", r"internal\s+network"]),
    ("Vulnerability Assessment", [r"vulnerability\s+assessment", r"\bva/pt\b", r"\bva\s*/\s*pt\b"]),
    ("Penetration Testing", [r"penetration\s+test(?:ing)?", r"\bpentest(?:ing)?\b", r"\bpen\s*test\b"]),
    ("Security Audit", [r"security\s+audit", r"security\s+review"]),
    ("Security Hardening", [r"security\s+harden(?:ing)?", r"lock\s+down\s+(?:our|the)\s+(?:app|platform|infra)"]),
    ("Vulnerability Remediation", [r"fix(?:ing)?\s+(?:a\s+)?(?:vulnerability|security\s+(?:issue|bug))", r"remediat(?:e|ion)"]),
    ("Secure Code Review", [r"secure\s+code\s+review", r"code\s+review.{0,20}security", r"sast"]),
    ("Cloud Security Assessment", [r"cloud\s+security", r"(?:aws|azure|gcp)\s+(?:security|pentest|assessment)"]),
    ("Compliance Security Testing", [r"soc\s*2", r"iso\s*27001", r"pci[\s-]?dss", r"hipaa", r"gdpr.{0,20}security"]),
    ("Pre-launch Security Assessment", [r"before\s+(?:launch|go[\s-]?live|production)", r"pre[\s-]?launch\s+security"]),
    ("Continuous Security Testing", [r"continuous\s+(?:security|pentest)", r"ongoing\s+security\s+testing", r"retainer.{0,20}(?:pentest|vapt)"]),
]

COUNTRY_HINTS: dict[str, str] = {
    "usa": "USA",
    "united states": "USA",
    "u.s.": "USA",
    "us-based": "USA",
    "canada": "Canada",
    "uk": "UK",
    "united kingdom": "UK",
    "britain": "UK",
    "london": "UK",
    "australia": "Australia",
    "germany": "Germany",
    "netherlands": "Netherlands",
    "switzerland": "Switzerland",
    "singapore": "Singapore",
    "uae": "UAE",
    "dubai": "UAE",
    "saudi": "Saudi Arabia",
    "ireland": "Ireland",
    "france": "France",
    "sweden": "Sweden",
    "norway": "Norway",
    "denmark": "Denmark",
    "finland": "Finland",
    "new zealand": "New Zealand",
    "belgium": "Belgium",
}

INDUSTRY_HINTS: dict[str, str] = {
    "fintech": "FinTech",
    "healthtech": "HealthTech",
    "edtech": "EdTech",
    "insurtech": "InsurTech",
    "proptech": "PropTech",
    "legaltech": "LegalTech",
    "hrtech": "HRTech",
    "saas": "SaaS",
    "marketplace": "Marketplace",
    "ecommerce": "E-commerce",
    "e-commerce": "E-commerce",
    "mobile app": "Mobile apps",
    "api": "APIs/platform",
    "logistics": "LogisticsTech",
    "ai startup": "AI startups",
    "b2b": "B2B software",
}


def compiled(patterns: list[str]) -> list[re.Pattern[str]]:
    return [re.compile(p, re.IGNORECASE | re.DOTALL) for p in patterns]


COMPILED_BUYING = {k: compiled(v) for k, v in BUYING_PATTERNS.items()}
COMPILED_PARTNER = compiled(PARTNER_PATTERNS)
COMPILED_REJECT = {k: compiled(v) for k, v in REJECT_PATTERNS.items()}
COMPILED_SERVICES = [(name, compiled(pats)) for name, pats in SERVICE_PATTERNS]
