# LEAD QUALITY REPORT — Beacon AI

**Audit Date:** 2026-08-08
**Sample Size:** 203 leads (full database)

---

## Executive Summary

| Metric | Value | Status |
|--------|-------|--------|
| Total Leads | 203 | WARNING (low volume) |
| Valid Websites | 203 (100%) | PASS |
| HTTPS Websites | 203 (100%) | PASS |
| Working Emails | 93 (45.8%) | FAILED |
| Working Phones | 136 (67.0%) | WARNING |
| Decision Makers Found | 0 (0%) | FAILED |
| Platform Detection Working | 0 (0%) | FAILED |
| Technology Detection Working | 0 (0%) | FAILED |
| Social Links Found | 0 (0%) | FAILED |
| Duplicate Rate | 0% | PASS |
| Average COMAI Score | 70.32 | WARNING |
| Sales Ready Leads | 91 (44.8%) | WARNING |

---

## Field Completeness

| Field | Populated | Missing | Coverage | Status |
|-------|-----------|---------|----------|--------|
| company_name | 203 | 0 | 100% | PASS |
| website | 203 | 0 | 100% | PASS |
| domain | 203 | 0 | 100% | PASS |
| industry | 203 | 0 | 100% | PASS |
| country | 203 | 0 | 100% | PASS |
| description | 203 | 0 | 100% | PASS |
| comai_score | 203 | 0 | 100% | PASS |
| lead_priority | 203 | 0 | 100% | PASS |
| email | 93 | 110 | 45.8% | FAILED |
| phone | 136 | 67 | 67.0% | WARNING |
| owner_name | 0 | 203 | 0% | FAILED |
| founder_name | 0 | 203 | 0% | FAILED |
| sales_reason | 0 | 203 | 0% | FAILED |
| social_links | 0 | 203 | 0% | FAILED |
| instagram_url | 0 | 203 | 0% | FAILED |
| facebook_url | 0 | 203 | 0% | FAILED |
| linkedin_url | 0 | 203 | 0% | FAILED |
| product_count | 203 | 0 | 100% | WARNING (all = 1) |

---

## Platform Detection

| Platform | Count | Percentage | Status |
|----------|-------|------------|--------|
| unknown | 203 | 100% | FAILED |

**Root Cause:** `EcommerceDetector.detect()` silently swallows all exceptions. Cloudflare-protected sites block the basic HTTP request, and the incomplete User-Agent triggers bot detection.

---

## Technology Detection

| Technology | Detected | Percentage | Status |
|------------|----------|------------|--------|
| Shopify | 0 | 0% | FAILED |
| WooCommerce | 0 | 0% | FAILED |
| Magento | 0 | 0% | FAILED |
| Chatbot | 0 | 0% | FAILED |
| WhatsApp | 0 | 0% | FAILED |
| CRM | 0 | 0% | FAILED |

**Root Cause:** Same as platform detection — HTTP requests fail silently.

---

## Contact Discovery

### Email Coverage

| Metric | Value |
|--------|-------|
| Emails Found | 93 |
| Emails Missing | 110 |
| Coverage | 45.8% |

### Phone Coverage

| Metric | Value |
|--------|-------|
| Phones Found | 136 |
| Phones Missing | 67 |
| Coverage | 67.0% |

### Decision Maker Coverage

| Metric | Value |
|--------|-------|
| Owner Names Found | 0 |
| Founder Names Found | 0 |
| Decision Makers Found | 0 |
| Coverage | 0% |

**Root Cause:** Contact enrichment depends on successful website crawling. Since HTTP requests fail silently (Cloudflare), the contact scraper cannot extract emails, phones, or decision maker information from website pages.

---

## Industry Distribution

| Industry | Count | Percentage |
|----------|-------|------------|
| fashion | 42 | 20.7% |
| beauty | 23 | 11.3% |
| food | 20 | 9.9% |
| electronics | 17 | 8.4% |
| home | 14 | 6.9% |
| education | 14 | 6.9% |
| health | 13 | 6.4% |
| restaurant | 11 | 5.4% |
| fitness | 10 | 4.9% |
| fintech | 9 | 4.4% |
| quick_commerce | 7 | 3.4% |
| travel | 7 | 3.4% |
| spa | 6 | 3.0% |
| logistics | 5 | 2.5% |
| automotive | 5 | 2.5% |

---

## Country Distribution

| Country | Count | Percentage |
|---------|-------|------------|
| India | 203 | 100% |

---

## COMAI Score Distribution

| Score Range | Classification | Expected | Actual |
|-------------|----------------|----------|--------|
| >= 90 | HOT | Any | 0 |
| >= 70 | WARM | Any | Most (avg 70.32) |
| < 70 | LOW | Any | Some |

| Metric | Value |
|--------|-------|
| Average | 70.32 |
| Maximum | 85 |
| Minimum | 50 |

**Note:** No leads scored above 85 because technology detection returns 0 for all platforms (losing 25 Technology Fit points) and no chatbot/WhatsApp/CRM detection (affecting other scoring dimensions).

---

## Lead Priority Classification

| Priority | Count | Percentage |
|----------|-------|------------|
| SALES_READY | 91 | 44.8% |
| LOW | 65 | 32.0% |
| WARM_LEAD | 47 | 23.2% |

---

## Top 10 Leads (by COMAI Score)

| Company | Website | Platform | Email | Phone | Score |
|---------|---------|----------|-------|-------|-------|
| V-Guard | vguard.in | unknown | mail@vguard.in | +916022021165 | 85 |
| Havells | havells.com | unknown | marketing@havells.com | +918045775666 | 85 |
| Bisleri | bisleri.com | unknown | wecare@bisleri.co.in | +918866773366 | 85 |
| Nua | nuawoman.com | unknown | care@nuawoman.com | +917615661359 | 85 |
| HealthifyMe | healthifyme.com | unknown | support@healthifyme.com | +919188675477 | 85 |
| Guess India | guess.in | unknown | customercare.india@guess.eu | +917298489522 | 85 |
| Biba | biba.in | unknown | careers@bibaindia.com | +917854071044 | 85 |
| Flipkart | flipkart.com | unknown | app-feedback@flipkart.com | +918851082120 | 85 |
| Myntra | myntra.com | unknown | support@myntra.com | +918242437510 | 85 |
| Decathlon India | decathlon.in | unknown | care.india@decathlon.com | +919495620428 | 85 |

---

## Quality Assessment

| Dimension | Score (0-10) | Notes |
|-----------|--------------|-------|
| Company Name Accuracy | 9/10 | All populated, appear legitimate |
| Website Validity | 10/10 | All HTTPS, valid domains |
| Platform Detection | 0/10 | Completely broken |
| Email Validity | 5/10 | 45.8% coverage |
| Phone Validity | 7/10 | 67% coverage |
| Decision Maker Availability | 0/10 | None found |
| Industry Classification | 8/10 | All classified |
| Technology Detection | 0/10 | Completely broken |
| COMAI Score Accuracy | 4/10 | Scores inflated due to missing tech data |
| Duplicate Rate | 10/10 | 0% duplicates |
| Confidence Score Quality | 5/10 | contact_confidence exists but limited |

**Overall Lead Quality Score: 4.4/10**

---

## Recommendations

1. **CRITICAL:** Fix HTTP client in EcommerceDetector (Cloudflare blocking)
2. **CRITICAL:** Fix contact enrichment pipeline
3. **CRITICAL:** Implement social link extraction
4. **HIGH:** Scale lead volume from 203 to 1000+
5. **HIGH:** Add sales_reason generation
6. **MEDIUM:** Improve product count detection (currently always = 1)
