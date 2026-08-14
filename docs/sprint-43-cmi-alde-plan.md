# Sprint 43 — CMI-ALDE Implementation Plan

## COMAI Market Intelligence & Autonomous Lead Discovery Engine

**Date:** 2026-07-31
**Sprint Goal:** Transform Beacon from a Shopify lead scraper into an AI Revenue Intelligence Platform that discovers companies with the highest probability of purchasing COMAI.

---

## 1. Architecture Overview

### 1.1 Current State
- 70 packages, 100+ DB tables, 70+ API routes
- Existing `ecommerce_leads` package with basic scraping, enrichment, and scoring
- Existing `discovery_quality_engine`, `lead_enrichment`, `decision_discovery` packages
- Current ICP is generic (SaaS/B2B focus, 10-50K employees, global)
- Existing seed list of ~200 hardcoded Indian companies

### 1.2 Target State
- **Product Intelligence Profile** — COMAI-specific knowledge embedded in every engine
- **ICP V2** — Indian D2C ecommerce, ₹5-150 Cr revenue, 15-250 employees
- **Multi-Source Discovery** — 15+ independent evidence sources
- **Evidence-Based Qualification** — Every field carries value/confidence/source/URL/freshness
- **Pain Intelligence** — Support overload, manual sales, poor personalization detection
- **Buying Intent Engine** — Hiring, expansion, funding, traffic signals
- **Decision Maker Discovery** — Founder-first, no generic emails
- **Revenue Opportunity Scoring** — Close probability, estimated ARR
- **Sales-Ready Output** — 400+ qualified leads with recommended outreach

---

## 2. New Package: `comai_intelligence`

### 2.1 Purpose
Embed COMAI product knowledge into every engine. This is the "brain" that tells the system what COMAI does, who buys it, and why.

### 2.2 File Structure
```
packages/comai_intelligence/
├── __init__.py
├── product_profile.py          # COMAI product catalog + capabilities
├── icp_engine.py               # Ideal Customer Profile matching
├── pain_mapper.py              # Maps company attributes to COMAI pain points
├── roi_calculator.py           # Estimates COMAI ROI for a prospect
└── close_probability.py        # Estimates likelihood of closing
```

### 2.3 Product Profile (`product_profile.py`)

```python
@dataclass
class COMAIProduct:
    name: str
    category: str
    description: str
    target_pains: list[str]
    target_industries: list[str]
    target_platforms: list[str]
    min_revenue: int        # ₹
    max_revenue: int        # ₹
    min_employees: int
    max_employees: int
    avg_deal_size: int      # ₹
    sales_cycle_days: int

COMAI_CATALOG = [
    COMAIProduct(
        name="AI Shopping Assistant",
        category="sales_automation",
        description="Conversational AI that guides shoppers to purchase",
        target_pains=["high_cart_abandonment", "poor_product_discovery", "low_conversion"],
        target_industries=["beauty", "fashion", "jewellery", "electronics"],
        target_platforms=["shopify", "shopify_plus", "woocommerce", "magento"],
        min_revenue=5_00_00_000,  # ₹5 Cr
        max_revenue=150_00_00_000,  # ₹150 Cr
        min_employees=15,
        max_employees=250,
        avg_deal_size=3_60_000,  # ₹3.6L ARR
        sales_cycle_days=45,
    ),
    # ... 9 more products
]
```

### 2.4 ICP Engine (`icp_engine.py`)

```python
class ICPEngine:
    """Deterministic ICP matching. No GPT dependency."""

    GEOGRAPHY = {"primary": ["India"], "future": ["UAE", "SA", "SG", "MY"]}
    
    REVENUE_RANGE = (5_00_00_000, 150_00_00_000)  # ₹5 Cr - ₹150 Cr
    
    EMPLOYEE_RANGE = (15, 250)
    
    PLATFORMS = {"shopify", "shopify_plus", "woocommerce", "magento", "headless_shopify"}
    
    TARGET_INDUSTRIES = {
        "beauty", "cosmetics", "skincare", "fashion", "apparel",
        "jewellery", "home_decor", "furniture", "baby_products",
        "pet_products", "organic_food", "luxury_d2c", "electronics_accessories",
        "health_wellness", "supplements",
    }
    
    REJECT = {
        "government", "hospitals", "banks", "universities", "agencies",
        "saas", "manufacturing_only", "marketplace", "amazon_only",
        "enterprise_retail", "conglomerates", "listed_retail_chains",
    }

    def score(self, company: dict) -> ICPScore:
        """Returns fit_score (0-100), confidence, and rejection_reason."""
        ...
```

### 2.5 Pain Mapper (`pain_mapper.py`)

Maps observable company attributes to COMAI pain points:

| Observable Signal | Pain Point | COMAI Product |
|---|---|---|
| No chatbot detected | No automated support | AI Customer Support |
| WhatsApp widget present | Heavy WhatsApp dependence | WhatsApp AI Automation |
| Large catalogue (500+ products) | Poor product discovery | Product Recommendation Engine |
| No personalization | Generic shopping experience | Customer Personalization |
| High traffic + low conversion | Cart abandonment | Cart Recovery |
| No email automation | Manual broadcast | Broadcast Automation |
| No tracking page | Manual order tracking | Order Tracking |
| Growing fast + no AI | Support overload | Sales Automation |

### 2.6 ROI Calculator (`roi_calculator.py`)

```python
class ROICalculator:
    """Estimates COMAI ROI based on observable company metrics."""
    
    def calculate(self, company: dict) -> ROIEstimate:
        # Based on: revenue, product_count, traffic, current_support_cost
        # Returns: estimated_savings, estimated_revenue_lift, payback_period, arr
        ...
```

---

## 3. ICP Configuration Update

### 3.1 New Config File: `config/comai_icp.yaml`

```yaml
# COMAI Ideal Customer Profile — Sprint 43

geography:
  primary:
    - India
  future:
    - UAE
    - Saudi Arabia
    - Singapore
    - Malaysia

company_stage: growing  # Not enterprise

revenue:
  min_annual: 50000000    # ₹5 Cr
  max_annual: 1500000000  # ₹150 Cr
  currency: INR
  confidence: estimated  # Estimates acceptable with confidence score

employees:
  min: 15
  max: 250

platforms:
  - shopify
  - shopify_plus
  - woocommerce
  - magento
  - headless_shopify
  - modern_ecommerce_stack

target_industries:
  - beauty
  - cosmetics
  - skincare
  - fashion
  - apparel
  - jewellery
  - home_decor
  - furniture
  - baby_products
  - pet_products
  - organic_food
  - luxury_d2c
  - electronics_accessories
  - health_wellness
  - supplements

reject:
  - government
  - hospitals
  - banks
  - universities
  - agencies
  - saas
  - manufacturing_only
  - marketplace
  - amazon_only
  - enterprise_retail
  - conglomerates
  - listed_retail_chains

decision_makers:
  priority:
    - founder
    - ceo
    - co-founder
    - head_of_ecommerce
    - head_of_growth
    - marketing_head
    - cx_head
    - customer_success_head
    - operations_head
  reject_generic:
    - support@
    - info@
    - hello@
    - sales@
  allow_generic_only_if: no_better_contact_exists
```

### 3.2 Update `config/ideal_customer_profile.yaml`

Replace the generic SaaS-focused ICP with the COMAI-specific one above.

---

## 4. Discovery Collectors — 15+ Sources

### 4.1 New Collectors to Build

| # | Source | Method | Purpose |
|---|---|---|---|
| 1 | **Shopify Store Directory** | API/Scrape | Indian Shopify stores via Shopify Exchange, Storeleads |
| 2 | **Google Search** | DuckDuckGo/Google | "shopify store india", "d2c brand india beauty" |
| 3 | **Google Business Profile** | Maps API | Indian ecommerce businesses |
| 4 | **Instagram** | Hashtag scrape | #indiand2c #shopindian #beautyindia |
| 5 | **Facebook** | Page scrape | Indian D2C brand pages |
| 6 | **LinkedIn** | Company search | Indian ecommerce companies |
| 7 | **YouTube** | Channel search | Indian brand channels |
| 8 | **Job Portals** | Naukri/LinkedIn Jobs | Companies hiring for ecommerce roles |
| 9 | **Press Releases** | PR websites | New product launches, funding |
| 10 | **Product Hunt** | API | Indian ecommerce products |
| 11 | **Review Platforms** | MouthShut, Trustpilot | Indian ecommerce reviews |
| 12 | **Technology Fingerprinting** | BuiltWith/Wappalyzer | Detect Shopify/WooCommerce stores |
| 13 | **DNS/SSL** | crt.sh, DNS lookup | Verify active stores |
| 14 | **Public Sitemap** | /sitemap.xml | Product count, collection count |
| 15 | **Startup Databases** | Tracxn, YourStory | Indian D2C startups |
| 16 | **Brand Directories** | Economic Times, Forbes India | Featured D2C brands |

### 4.2 File Structure for New Collectors

```
packages/comai_intelligence/discovery/
├── __init__.py
├── google_search_collector.py
├── instagram_collector.py
├── facebook_collector.py
├── linkedin_collector.py
├── youtube_collector.py
├── job_portal_collector.py
├── press_release_collector.py
├── review_platform_collector.py
├── startup_database_collector.py
├── brand_directory_collector.py
├── technology_fingerprint_collector.py
├── dns_ssl_collector.py
├── sitemap_collector.py
└── google_business_collector.py
```

### 4.3 Existing Collectors to Enhance

- **`ecommerce_leads/collectors/shopify_collector.py`** — Add Storeleads API, Shopify Exchange
- **`ecommerce_leads/collectors/social_collector.py`** — Add Instagram hashtag search, Facebook page detection
- **`ecommerce_leads/collectors/web_collector.py`** — Add DuckDuckGo search for Indian D2C brands
- **`ecommerce_leads/collectors/ecommerce_detector.py`** — Add Klaviyo, Judge.me, Razorpay, Shiprocket detection

---

## 5. Evidence-Based Data Model

### 5.1 New Table: `comai_leads_v2`

Replace the flat `ecommerce_leads` table with an evidence-based model:

```python
class ComaiLeadRow(BaseModel):
    """Evidence-based COMAI lead with confidence scoring."""
    __tablename__ = "comai_leads_v2"
    
    # Company Identity
    company_name: str          # Value
    company_name_confidence: float  # 0-1
    company_name_source: str   # "website", "linkedin", "google_business"
    company_name_evidence_url: str
    company_name_last_seen: datetime
    
    domain: str                # Primary domain
    website: str               # Full URL
    
    # Geography
    country: str               # "India"
    country_confidence: float
    country_source: str
    country_evidence_url: str
    
    city: str
    city_confidence: float
    city_source: str
    
    state: str
    
    # Industry
    industry: str              # "beauty", "fashion", etc.
    industry_confidence: float
    industry_source: str
    industry_evidence_url: str
    
    # Size Estimation
    estimated_revenue: int     # ₹ INR
    revenue_confidence: float  # 0-1
    revenue_source: str
    revenue_evidence_url: str
    revenue_range_min: int
    revenue_range_max: int
    
    estimated_employees: int
    employees_confidence: float
    employees_source: str
    employees_evidence_url: str
    
    # Platform Detection
    platform: str              # "shopify", "woocommerce", "magento"
    platform_confidence: float
    platform_source: str       # "html_fingerprint", "technology_detection"
    platform_evidence_url: str
    
    # Technology Stack
    technologies: list[dict]   # [{name, confidence, source, evidence_url}]
    
    # Pain Signals
    pain_signals: list[dict]   # [{pain_type, confidence, source, evidence_url, description}]
    
    # Buying Intent
    buying_signals: list[dict] # [{signal_type, confidence, source, evidence_url, detected_at}]
    
    # Contact Quality
    contacts: list[dict]       # [{email, phone, linkedin, role, confidence, verification_status, evidence_url}]
    decision_makers: list[dict] # [{name, role, email, linkedin, confidence, source}]
    
    # Scoring
    comai_score: float         # 0-100
    close_probability: float   # 0-1
    estimated_arr: int         # ₹ annual
    revenue_opportunity: str   # "high", "medium", "low"
    
    # Qualification Gates
    icp_pass: bool
    size_pass: bool
    growth_pass: bool
    platform_pass: bool
    pain_pass: bool
    intent_pass: bool
    reachability_pass: bool
    budget_pass: bool
    revenue_pass: bool
    close_pass: bool
    sales_ready: bool
    
    # Evidence
    evidence_links: list[str]  # All evidence URLs
    evidence_count: int
    last_verified: datetime
    freshness_score: float     # 0-1, decays over time
    
    # Sales Readiness
    lead_priority: str         # "SALES_READY", "WARM", "COLD", "REJECT"
    recommended_outreach: str  # "email", "linkedin", "whatsapp", "phone"
    outreach_angle: str        # Why COMAI fits this company
    
    # Source Attribution
    discovery_sources: list[str]  # Which collectors found this company
    discovery_date: datetime
```

### 5.2 Supporting Tables

```python
class ComaiLeadEvidence(BaseModel):
    """Individual evidence record for a lead field."""
    __tablename__ = "comai_lead_evidence"
    
    lead_id: UUID              # FK to comai_leads_v2
    field_name: str            # "industry", "platform", "email", etc.
    field_value: str
    confidence: float          # 0-1
    source: str                # "website_scrape", "google_search", "linkedin"
    source_url: str
    detected_at: datetime
    last_seen: datetime
    freshness_days: int        # How many days since last verified
    verification_method: str   # "http_200", "html_fingerprint", "manual"
    
class ComaiLeadTimeline(BaseModel):
    """Timeline of events for a lead."""
    __tablename__ = "comai_lead_timeline"
    
    lead_id: UUID
    event_type: str            # "discovered", "enriched", "qualified", "contacted"
    event_data: dict
    source: str
    detected_at: datetime

class ComaiLeadDecay(BaseModel):
    """Decay tracking for buying signals."""
    __tablename__ = "comai_lead_decay"
    
    lead_id: UUID
    signal_type: str
    signal_strength: float     # 0-1, decays over time
    decay_rate: float          # Per day
    last_updated: datetime
    expired: bool
```

---

## 6. Enhanced Technology Detection

### 6.1 Expand `EcommerceDetector`

Add detection for:

| Category | Technologies | Detection Method |
|---|---|---|
| **Ecommerce Platform** | Shopify, Shopify Plus, WooCommerce, Magento, BigCommerce | HTML fingerprint, API endpoints |
| **Email Marketing** | Klaviyo, Mailchimp, SendGrid, Drip | Script tags, form actions |
| **Reviews** | Judge.me, Yotpo, Stamped, Trustpilot | Widget scripts, API calls |
| **Support** | Zendesk, Freshdesk, Intercom, Gorgias, Tidio | Widget scripts, API endpoints |
| **Payments** | Razorpay, Cashfree, PayU, Stripe | Script tags, checkout URLs |
| **Shipping** | Shiprocket, Delhivery, BlueDart | Tracking page URLs |
| **Analytics** | Google Analytics, Meta Pixel, Hotjar | Script tags |
| **WhatsApp** | WhatsApp Business API, Wati, AiSensy | Button/link detection |
| **AI Chatbot** | Current AI chatbots (competitors) | Script tags, widget detection |
| **Automation** | Zapier, Make, Pabbly | Integration scripts |

### 6.2 New File: `packages/comai_intelligence/tech_detection.py`

```python
class COMAITechDetector:
    """Enhanced technology detection for ecommerce stacks."""
    
    ECOMMERCE_PLATFORMS = { ... }  # 10+ platforms
    EMAIL_MARKETING = { ... }      # 6+ tools
    REVIEW_PLATFORMS = { ... }     # 5+ tools
    SUPPORT_TOOLS = { ... }        # 6+ tools
    PAYMENT_GATEWAYS = { ... }     # 5+ gateways
    SHIPPING_PROVIDERS = { ... }   # 4+ providers
    ANALYTICS_TOOLS = { ... }      # 5+ tools
    WHATSAPP_TOOLS = { ... }       # 4+ tools
    AI_CHATBOTS = { ... }          # Competitor detection
    AUTOMATION_TOOLS = { ... }     # 4+ tools
    
    def detect_all(self, html: str, url: str) -> TechStack:
        """Detect entire technology stack from website HTML."""
        ...
```

---

## 7. Pain Intelligence Engine

### 7.1 New File: `packages/comai_intelligence/pain_engine.py`

```python
class PainIntelligenceEngine:
    """Detects and scores pain points that COMAI can solve."""
    
    PAIN_SIGNALS = {
        "support_overload": {
            "indicators": [
                "no_chatbot_detected",
                "high_traffic_low_support",
                "many_product_pages",
                "complex_product_catalog",
            ],
            "comai_products": ["ai_customer_support", "whatsapp_automation"],
            "weight": 0.9,
        },
        "manual_sales": {
            "indicators": [
                "no_ai_assistant",
                "high_cart_abandonment",
                "no_personalization",
            ],
            "comai_products": ["ai_shopping_assistant", "sales_automation"],
            "weight": 0.85,
        },
        "poor_personalization": {
            "indicators": [
                "no_recommendation_engine",
                "generic_product_pages",
                "no_customer_segmentation",
            ],
            "comai_products": ["product_recommendation", "customer_personalization"],
            "weight": 0.8,
        },
        "cart_abandonment": {
            "indicators": [
                "no_cart_recovery",
                "high_traffic_low_conversion",
                "no_checkout_optimization",
            ],
            "comai_products": ["cart_recovery"],
            "weight": 0.9,
        },
        "heavy_whatsapp": {
            "indicators": [
                "whatsapp_button_present",
                "no_ai_whatsapp",
                "manual_response_indicators",
            ],
            "comai_products": ["whatsapp_ai_automation", "broadcast_automation"],
            "weight": 0.85,
        },
        "weak_faq": {
            "indicators": [
                "no_faq_page",
                "no_knowledge_base",
                "no_self_service",
            ],
            "comai_products": ["ai_customer_support"],
            "weight": 0.7,
        },
        "fast_growth": {
            "indicators": [
                "hiring_signals",
                "new_collections",
                "traffic_growth",
                "expansion_signals",
            ],
            "comai_products": ["sales_automation", "order_tracking"],
            "weight": 0.75,
        },
    }
    
    def analyze(self, company: dict, tech_stack: dict) -> list[PainSignal]:
        """Analyze company for pain points COMAI can solve."""
        ...
    
    def score_pain_intensity(self, pains: list[PainSignal]) -> float:
        """Score overall pain intensity 0-100."""
        ...
```

---

## 8. Buying Intent Engine

### 8.1 New File: `packages/comai_intelligence/intent_engine.py`

```python
class BuyingIntentEngine:
    """Detects buying signals that decay over time."""
    
    INTENT_SIGNALS = {
        "hiring": {
            "keywords": [
                "ecommerce manager", "shopify developer", "digital marketing",
                "customer support", "operations manager", "growth manager",
            ],
            "sources": ["naukri", "linkedin_jobs", "instahyre"],
            "decay_rate": 0.05,  # 5% per day
            "weight": 0.9,
        },
        "expansion": {
            "indicators": [
                "new_product_collections",
                "new_country_launch",
                "new_store_location",
                "international_shipping",
            ],
            "decay_rate": 0.03,
            "weight": 0.8,
        },
        "funding": {
            "sources": ["tracxn", "yourstory", "press_releases"],
            "decay_rate": 0.02,
            "weight": 0.95,
        },
        "traffic_growth": {
            "sources": ["similarweb_estimate", "alexa_rank"],
            "decay_rate": 0.04,
            "weight": 0.7,
        },
        "website_redesign": {
            "indicators": [
                "recent_theme_change",
                "new_design",
                "updated_meta_tags",
            ],
            "decay_rate": 0.06,
            "weight": 0.6,
        },
        "marketing_expansion": {
            "indicators": [
                "new_ad_campaigns",
                "increased_social_activity",
                "new_influencer_partnerships",
            ],
            "decay_rate": 0.04,
            "weight": 0.65,
        },
        "crm_migration": {
            "indicators": [
                "new_chatbot_detected",
                "crm_change",
                "new_support_tool",
            ],
            "decay_rate": 0.03,
            "weight": 0.85,
        },
        "technology_migration": {
            "indicators": [
                "platform_change",
                "new_analytics",
                "new_payment_gateway",
            ],
            "decay_rate": 0.04,
            "weight": 0.7,
        },
    }
    
    def detect_signals(self, company: dict) -> list[IntentSignal]:
        """Detect all buying intent signals."""
        ...
    
    def calculate_intent_score(self, signals: list[IntentSignal]) -> float:
        """Score overall buying intent 0-100 with decay."""
        ...
```

---

## 9. Decision Maker Discovery — Enhanced

### 9.1 Enhanced Strategy

| Priority | Method | Source |
|---|---|---|
| 1 | About/Team page scrape | Website |
| 2 | LinkedIn company page | LinkedIn |
| 3 | Google Search "{company} founder" | Google |
| 4 | Crunchbase profile | Crunchbase |
| 5 | YourStory/Tracxn profile | Startup databases |
| 6 | Instagram bio | Instagram |
| 7 | Press mentions | News articles |

### 9.2 Contact Quality Rules

```python
CONTACT_QUALITY_RULES = {
    "never_return": ["support@", "info@", "hello@", "sales@"],
    "reject_generic_unless": {
        "condition": "no_better_contact_exists",
        "mark_as": "low_confidence",
    },
    "never_fabricate": ["phone_numbers", "email_addresses"],
    "if_unverifiable": "mark_as_UNKNOWN",
    "deduplicate": True,  # No duplicate phones across unrelated companies
}
```

### 9.3 New File: `packages/comai_intelligence/decision_maker_engine.py`

```python
class DecisionMakerEngine:
    """Discovers decision makers with evidence-based confidence."""
    
    PRIORITY_ROLES = [
        "founder", "ceo", "co-founder",
        "head_of_ecommerce", "head_of_growth",
        "marketing_head", "cx_head",
        "customer_success_head", "operations_head",
    ]
    
    REJECT_PREFIXES = ["support", "info", "hello", "sales", "help", "feedback"]
    
    async def discover(self, company: dict) -> list[DecisionMaker]:
        """Discover decision makers from multiple sources."""
        # 1. Website scrape (about, team, contact pages)
        # 2. LinkedIn search
        # 3. Google search
        # 4. Crunchbase lookup
        # 5. Startup database lookup
        # Merge, deduplicate, score confidence
        ...
    
    def _score_contact_quality(self, contact: dict) -> float:
        """Score contact quality 0-1 based on role, email type, verification."""
        ...
```

---

## 10. Lead Qualification Pipeline

### 10.1 10-Gate Qualification

```
Gate 1: ICP Match (industry, geography, platform)
    ↓
Gate 2: Company Size (revenue ₹5-150 Cr, employees 15-250)
    ↓
Gate 3: Growth Signals (hiring, expansion, funding)
    ↓
Gate 4: Technology Fit (Shopify/WooCommerce/Magento)
    ↓
Gate 5: Pain Signals (support overload, manual sales, etc.)
    ↓
Gate 6: Buying Intent (active signals with decay)
    ↓
Gate 7: Reachability (email/phone/LinkedIn found)
    ↓
Gate 8: Budget Indicators (revenue > ₹5 Cr)
    ↓
Gate 9: Revenue Opportunity (COMAI ROI > deal cost)
    ↓
Gate 10: Close Probability (> 20%)
    ↓
    SALES_READY
```

### 10.2 New File: `packages/comai_intelligence/qualification_pipeline.py`

```python
class QualificationPipeline:
    """10-gate qualification pipeline. Deterministic, no GPT."""
    
    def __init__(self):
        self.icp_engine = ICPEngine()
        self.pain_engine = PainIntelligenceEngine()
        self.intent_engine = BuyingIntentEngine()
        self.decision_engine = DecisionMakerEngine()
        self.roi_calculator = ROICalculator()
        self.close_calculator = CloseProbabilityCalculator()
    
    async def qualify(self, lead: dict) -> QualificationResult:
        """Run lead through all 10 gates."""
        gates = []
        
        # Gate 1: ICP Match
        icp_score = self.icp_engine.score(lead)
        gates.append(GateResult("icp", icp_score.passed, icp_score.confidence, icp_score.reason))
        
        # Gate 2: Company Size
        size_pass = self._check_size(lead)
        gates.append(GateResult("size", size_pass.passed, size_pass.confidence, size_pass.reason))
        
        # ... Gates 3-10
        
        sales_ready = all(g.passed for g in gates)
        
        return QualificationResult(
            lead=lead,
            gates=gates,
            sales_ready=sales_ready,
            overall_confidence=self._calculate_overall_confidence(gates),
        )
```

---

## 11. Revenue Opportunity Scoring

### 11.1 New File: `packages/comai_intelligence/revenue_scorer.py`

```python
class RevenueOpportunityScorer:
    """Estimates ARR and close probability."""
    
    def score(self, lead: dict, pains: list, intent: list, icp: ICPScore) -> RevenueScore:
        # 1. Estimate ARR based on:
        #    - Company revenue × COMAI penetration rate
        #    - Number of COMAI products applicable
        #    - Platform complexity
        
        # 2. Calculate close probability based on:
        #    - ICP fit score
        #    - Pain intensity
        #    - Buying intent strength
        #    - Contact quality
        #    - Budget indicators
        #    - Competition level
        
        # 3. Generate recommended outreach strategy
        
        ...
    
    def _estimate_arr(self, lead: dict, applicable_products: list) -> int:
        """Estimate annual recurring revenue in ₹."""
        ...
    
    def _calculate_close_probability(self, factors: dict) -> float:
        """Calculate probability of closing 0-1."""
        ...
```

### 11.2 Close Probability Factors

| Factor | Weight | Source |
|---|---|---|
| ICP Fit Score | 0.25 | ICPEngine |
| Pain Intensity | 0.20 | PainEngine |
| Buying Intent | 0.20 | IntentEngine |
| Contact Quality | 0.15 | DecisionMakerEngine |
| Budget Fit | 0.10 | RevenueEstimate |
| Competition Level | 0.10 | MarketAnalysis |

---

## 12. Sales-Ready Output Format

### 12.1 Output Schema

```python
class SalesReadyLead(BaseModel):
    """Complete sales-ready lead output."""
    
    # Company
    company_name: str
    website: str
    industry: str
    platform: str
    
    # Size
    estimated_revenue: str        # "₹8-12 Cr"
    estimated_revenue_confidence: float
    estimated_employees: str      # "30-50"
    estimated_employees_confidence: float
    traffic_estimate: str         # "50K-100K monthly visits"
    
    # Technology
    technology_stack: list[str]
    current_chatbot: str | None
    current_crm: str | None
    
    # Pain & Intent
    pain_summary: str             # "No AI support, heavy WhatsApp, growing fast"
    growth_summary: str           # "Hiring ecommerce manager, new collections launched"
    buying_signals: list[str]
    
    # Decision Makers
    decision_makers: list[DecisionMakerInfo]
    
    # Contact
    verified_email: str
    verified_phone: str
    linkedin_url: str
    
    # COMAI Fit
    reason_comai_fits: str        # "No chatbot, 500+ products, ₹10Cr revenue"
    expected_roi: str             # "₹2.4L annual savings + 15% conversion lift"
    estimated_arr: str            # "₹3.6L"
    close_probability: float      # 0.65
    
    # Scoring
    comai_score: float            # 87
    confidence_score: float       # 0.82
    lead_priority: str            # "SALES_READY"
    
    # Evidence
    evidence_links: list[str]     # 10+ URLs proving every claim
    
    # Outreach
    recommended_outreach: str     # "LinkedIn + Email"
    outreach_angle: str           # "COMAI can automate your WhatsApp support"
    best_time_to_reach: str       # "Tuesday-Thursday, 10am-12pm IST"
```

---

## 13. Implementation Phases

### Phase 1: Foundation (Days 1-3)
1. Create `packages/comai_intelligence/` package structure
2. Build `product_profile.py` with full COMAI catalog
3. Build `icp_engine.py` with COMAI-specific ICP
4. Create `config/comai_icp.yaml`
5. Update `config/ideal_customer_profile.yaml`
6. Create Alembic migration for `comai_leads_v2` table

### Phase 2: Discovery (Days 4-7)
7. Build `tech_detection.py` with enhanced ecommerce detection
8. Build Google Search collector
9. Build Instagram collector
10. Build job portal collector
11. Build startup database collector
12. Enhance existing Shopify collector
13. Build multi-source discovery orchestrator

### Phase 3: Intelligence (Days 8-11)
14. Build `pain_engine.py`
15. Build `intent_engine.py`
16. Build `decision_maker_engine.py`
17. Build `roi_calculator.py`
18. Build `close_probability.py`

### Phase 4: Qualification (Days 12-14)
19. Build `qualification_pipeline.py` with 10 gates
20. Build `revenue_scorer.py`
21. Build evidence tracking system

### Phase 5: Output & API (Days 15-17)
22. Build sales-ready output formatter
23. Create API routes for COMAI leads
24. Create Celery tasks for discovery pipeline
25. Build Excel/PDF export

### Phase 6: Execution (Days 18-21)
26. Run first discovery batch
27. Enrich and qualify leads
28. Validate data quality
29. Generate pipeline report
30. Iterate until 400+ qualified leads

---

## 14. Files to Create

| # | File Path | Purpose |
|---|---|---|
| 1 | `packages/comai_intelligence/__init__.py` | Package init |
| 2 | `packages/comai_intelligence/product_profile.py` | COMAI product catalog |
| 3 | `packages/comai_intelligence/icp_engine.py` | ICP matching engine |
| 4 | `packages/comai_intelligence/pain_mapper.py` | Pain point mapping |
| 5 | `packages/comai_intelligence/pain_engine.py` | Pain intelligence engine |
| 6 | `packages/comai_intelligence/intent_engine.py` | Buying intent detection |
| 7 | `packages/comai_intelligence/decision_maker_engine.py` | Decision maker discovery |
| 8 | `packages/comai_intelligence/tech_detection.py` | Enhanced tech detection |
| 9 | `packages/comai_intelligence/roi_calculator.py` | ROI estimation |
| 10 | `packages/comai_intelligence/close_probability.py` | Close probability scoring |
| 11 | `packages/comai_intelligence/revenue_scorer.py` | Revenue opportunity scoring |
| 12 | `packages/comai_intelligence/qualification_pipeline.py` | 10-gate qualification |
| 13 | `packages/comai_intelligence/evidence_tracker.py` | Evidence collection & tracking |
| 14 | `packages/comai_intelligence/output_formatter.py` | Sales-ready output formatting |
| 15 | `packages/comai_intelligence/decay_engine.py` | Signal decay over time |
| 16 | `packages/comai_intelligence/discovery/__init__.py` | Discovery package init |
| 17 | `packages/comai_intelligence/discovery/google_search_collector.py` | Google search discovery |
| 18 | `packages/comai_intelligence/discovery/instagram_collector.py` | Instagram discovery |
| 19 | `packages/comai_intelligence/discovery/job_portal_collector.py` | Job portal signals |
| 20 | `packages/comai_intelligence/discovery/startup_db_collector.py` | Startup database discovery |
| 21 | `packages/comai_intelligence/discovery/brand_directory_collector.py` | Brand directory discovery |
| 22 | `packages/comai_intelligence/discovery/technology_collector.py` | Tech fingerprint discovery |
| 23 | `packages/comai_intelligence/discovery/sitemap_collector.py` | Sitemap-based discovery |
| 24 | `packages/comai_intelligence/services/pipeline.py` | Main orchestration pipeline |
| 25 | `config/comai_icp.yaml` | COMAI ICP configuration |
| 26 | `apps/api/app/models/comai_leads_v2.py` | New lead model |
| 27 | `apps/api/app/schemas/comai_leads_v2.py` | New lead schemas |
| 28 | `apps/api/app/repositories/comai_leads_v2.py` | New lead repository |
| 29 | `apps/api/app/api/routes/comai_leads.py` | New API routes |
| 30 | `apps/worker/worker/comai_tasks.py` | Celery tasks |

---

## 15. Files to Modify

| # | File Path | Changes |
|---|---|---|
| 1 | `config/ideal_customer_profile.yaml` | Replace with COMAI-specific ICP |
| 2 | `packages/ecommerce_leads/collectors/ecommerce_detector.py` | Add Klaviyo, Judge.me, Razorpay, Shiprocket detection |
| 3 | `packages/ecommerce_leads/collectors/shopify_collector.py` | Add Storeleads API integration |
| 4 | `packages/ecommerce_leads/scoring/ecommerce_score.py` | Align scoring with COMAI products |
| 5 | `packages/ecommerce_leads/services/lead_pipeline.py` | Integrate with new qualification pipeline |
| 6 | `apps/api/app/api/routes/__init__.py` | Register new routes |
| 7 | `apps/api/app/models/__init__.py` | Import new model |
| 8 | `apps/worker/worker/celery_app.py` | Register new tasks |

---

## 16. Success Criteria

| Metric | Target |
|---|---|
| Total qualified leads | 400+ |
| Sales-ready leads (SALES_READY) | 200+ |
| Evidence-backed fields | 100% |
| Decision makers per lead | 1-3 |
| Verified emails | 80%+ of SALES_READY |
| Close probability > 40% | 150+ leads |
| Estimated ARR per lead | ₹2-5L average |
| Total pipeline ARR | ₹8-20 Cr |
| Discovery sources per lead | 3+ independent sources |
| Data freshness | < 7 days |

---

## 17. Key Architectural Decisions

1. **Deterministic Processing** — No GPT/LLM in qualification path. All scoring is rule-based.
2. **Evidence-Based** — Every field carries confidence, source, URL, freshness. No fabricated data.
3. **Append-Only** — New evidence creates new records. Never overwrite history.
4. **Decay** — Buying signals decay over time. Fresh signals weigh more.
5. **Multi-Source** — Never trust one source. Require 3+ independent evidence sources.
6. **Founder-First** — Decision maker priority: Founder > CEO > Co-founder > Head of...
7. **No Generic Emails** — Never return support@, info@, hello@, sales@ unless no alternative exists.
8. **Revenue-Focused** — Optimize for qualified revenue opportunities, not lead quantity.

---

## 18. Risk Mitigation

| Risk | Mitigation |
|---|---|
| Insufficient leads below 400 | Expand discovery sources, lower threshold incrementally |
| Fake/unverifiable contacts | Mark as UNKNOWN, never fabricate |
| Rate limiting on external sources | Implement exponential backoff, respect robots.txt |
| Stale data | Decay signals, re-verify weekly |
| ICP too narrow | Monitor rejection rate, adjust thresholds |
| Platform detection false positives | Require 2+ detection signals for confirmation |

---

**End of Sprint 43 Plan**
