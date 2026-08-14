"""
FOUNDER INTENT ACQUISITION LAYER
Finds fresh, identifiable, contactable founders with real development needs.
Hands off to existing V9 verification pipeline.
"""

import json
import re
import sys
import io
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ============================================================
# CONFIGURATION
# ============================================================

OUTPUT_DIR = Path('exports/founder_intent_acquisition')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Service catalog (from Inowix)
SERVICE_CATALOG = {
    'COMAI': [
        'whatsapp chatbot', 'whatsapp automation', 'ai customer support',
        'ecommerce ai', 'product recommendations', 'cart recovery',
        'lead capture', 'shopify ai', 'woocommerce ai',
    ],
    'SAAS_DEVELOPMENT': [
        'saas mvp', 'ai saas', 'backend', 'api', 'cloud',
        'dedicated team', 'saas developer', 'full stack developer',
        'react developer', 'next.js developer', 'typescript developer',
        'node.js developer', 'python developer',
    ],
    'CUSTOM_SOFTWARE': [
        'web application', 'mobile app', 'dashboard', 'crm', 'erp',
        'ai automation', 'integrations', 'modernization', 'legacy',
        'software developed', 'app developer', 'web developer',
    ],
}

# Negative signals (immediate reject)
NEGATIVE_SIGNALS = [
    'co-founder', 'co founder', 'technical co-founder', 'tech co-founder',
    'looking for a co-founder', 'need a co-founder', 'startup co-founder',
    'for hire', 'available for work', 'looking for work', 'open to work',
    'developer for hire', 'freelance developer', 'my skills', 'portfolio',
    'hire me', 'agency needs', 'no agencies', 'how much does it cost',
    'what is the best way', 'any recommendations', 'suggestions?', 'advice?',
    'i built', 'how do i build', 'tutorial', 'blog post', 'article',
    'funding announcement', 'product launch', 'success story',
]

# High-value buying signals
BUYING_SIGNALS = [
    'looking for a developer', 'need a developer', 'need someone to build',
    'need an agency', 'need a studio', 'need help building',
    'looking for an agency', 'looking for a studio', 'need an mvp',
    'need software developed', 'looking for a technical team',
    'need react native developer', 'need saas built', 'need whatsapp automation',
    'seeking developer', 'need full stack developer', 'need backend developer',
    'need frontend developer', 'need mobile developer', 'hire a developer',
    'hire a team', 'looking for someone to build', 'need someone to develop',
    'looking for a dev team', 'need technical help', 'need help launching',
    'need to rebuild our app', 'looking for React developer',
    'looking for mobile developer', 'looking for SaaS developer',
    'need help with my saas', 'need help scaling development',
    'need technical partner on a paid basis', 'looking for contractors',
    'looking for freelance developers', 'need an external development team',
    'our developer left', 'need someone to take over',
    'looking for help integrating', 'need someone to build the backend',
    'need someone to build the mobile app', 'falling behind on development',
    "can't keep up with feature requests", 'launch is coming and we need help',
    'need to ship this faster', 'looking for someone to finish the MVP',
    'looking for help with our next version', 'need to rebuild the product',
]

# ============================================================
# NISHCHAY PATTERN DETECTOR
# ============================================================

def detect_nishchay_pattern(candidate: dict) -> dict:
    """
    Detect the "Nishchay Pattern" - high-value acquisition signal.
    
    Pattern: FOUNDER + ACTIVE PRODUCT + RECENT DEVELOPMENT NEED + 
             EXPLICIT EXTERNAL HELP + TIMELINE + BUDGET + 
             IDENTIFIABLE PERSON + CONTACT CHANNEL
    """
    signals = {
        'has_founder': False,
        'has_product': False,
        'has_development_need': False,
        'has_external_help': False,
        'has_timeline': False,
        'has_budget': False,
        'has_identifiable_person': False,
        'has_contact_channel': False,
        'score': 0,
        'matched': False,
    }

    # Check all available text fields
    text = f"{candidate.get('raw_signal', '')} {candidate.get('buying_event', '')} {candidate.get('requirement', '')}".lower()

    # Check founder signal
    if candidate.get('author_name') or candidate.get('author_username'):
        signals['has_founder'] = True
        signals['score'] += 1

    # Check product signal
    if candidate.get('product') or candidate.get('product_url'):
        signals['has_product'] = True
        signals['score'] += 1

    # Check development need
    need_keywords = ['need', 'looking for', 'seeking', 'require', 'help with']
    if any(kw in text for kw in need_keywords):
        signals['has_development_need'] = True
        signals['score'] += 1

    # Check external help intent
    external_keywords = ['agency', 'studio', 'freelance', 'contractor', 'external', 'outsource']
    if any(kw in text for kw in external_keywords):
        signals['has_external_help'] = True
        signals['score'] += 1

    # Check timeline
    timeline_keywords = ['asap', 'urgent', 'deadline', 'launching', 'weeks', 'days', 'month', 'launching in', 'timeline']
    if any(kw in text for kw in timeline_keywords):
        signals['has_timeline'] = True
        signals['score'] += 1

    # Check budget
    budget_keywords = ['budget', 'paid', 'contract', 'paying', 'rates', 'price', 'mrr', 'revenue', 'dollars', 'usd']
    if any(kw in text for kw in budget_keywords):
        signals['has_budget'] = True
        signals['score'] += 1

    # Check identifiable person
    if candidate.get('author_name') and candidate.get('linkedin_url'):
        signals['has_identifiable_person'] = True
        signals['score'] += 1
    elif candidate.get('author_name') and candidate.get('company_url'):
        signals['has_identifiable_person'] = True
        signals['score'] += 1

    # Check contact channel
    if candidate.get('email') or candidate.get('linkedin_url') or candidate.get('platform_contact'):
        signals['has_contact_channel'] = True
        signals['score'] += 1

    # Determine if pattern matches (need at least 6/8 signals)
    if signals['score'] >= 6:
        signals['matched'] = True

    return signals


# ============================================================
# SERVICE MATCHER
# ============================================================

def match_service(text: str) -> dict:
    """Match text against Inowix service catalog."""
    text_lower = text.lower()
    matches = []

    for unit, services in SERVICE_CATALOG.items():
        for service in services:
            if service in text_lower:
                matches.append({
                    'business_unit': unit,
                    'service': service,
                    'confidence': 0.8,
                })

    # Additional tech stack matching
    tech_keywords = {
        'SAAS_DEVELOPMENT': ['typescript', 'next.js', 'supabase', 'react', 'node.js', 'python', 'vue.js', 'angular'],
        'CUSTOM_SOFTWARE': ['web app', 'mobile app', 'api', 'database', 'cloud', 'aws', 'gcp', 'azure'],
    }

    for unit, keywords in tech_keywords.items():
        for kw in keywords:
            if kw in text_lower:
                matches.append({
                    'business_unit': unit,
                    'service': kw,
                    'confidence': 0.6,
                })

    if matches:
        # Return best match (highest confidence first)
        matches.sort(key=lambda x: x['confidence'], reverse=True)
        return matches[0]
    return None


# ============================================================
# FRESHNESS CLASSIFIER
# ============================================================

def classify_freshness(published_at: str) -> dict:
    """Classify freshness based on published_at timestamp."""
    if not published_at:
        return {'freshness': 'UNKNOWN', 'age_days': None, 'confidence': 'LOW'}

    try:
        # Parse various date formats
        now = datetime.now(timezone.utc)
        
        # Try ISO format
        try:
            pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        except:
            # Try Reddit format
            pub_date = datetime.strptime(published_at[:10], '%Y-%m-%d').replace(tzinfo=timezone.utc)

        if pub_date.tzinfo is None:
            pub_date = pub_date.replace(tzinfo=timezone.utc)

        age_days = (now - pub_date).days

        if age_days <= 7:
            freshness = 'HOT'
        elif age_days <= 30:
            freshness = 'CURRENT'
        elif age_days <= 60:
            freshness = 'AGING'
        else:
            freshness = 'LOW_PRIORITY'

        return {
            'freshness': freshness,
            'age_days': age_days,
            'confidence': 'HIGH',
            'published_at': pub_date.isoformat(),
        }
    except Exception as e:
        return {'freshness': 'UNKNOWN', 'age_days': None, 'confidence': 'LOW', 'error': str(e)}


# ============================================================
# NEGATIVE SIGNAL CHECKER
# ============================================================

def check_negative_signals(text: str) -> dict:
    """Check for negative signals that indicate non-buyers."""
    text_lower = text.lower()
    matched = []

    for signal in NEGATIVE_SIGNALS:
        if signal in text_lower:
            matched.append(signal)

    return {
        'has_negative': len(matched) > 0,
        'signals': matched,
        'count': len(matched),
    }


# ============================================================
# BUYING EVENT EXTRACTOR
# ============================================================

def extract_buying_event(candidate: dict) -> dict:
    """Extract the specific buying event from a candidate."""
    text = f"{candidate.get('title', '')} {candidate.get('content', '')}".lower()

    # Find matching buying signals
    matched_signals = []
    for signal in BUYING_SIGNALS:
        if signal in text:
            matched_signals.append(signal)

    # Extract requirement
    requirement = None
    for signal in matched_signals:
        requirement = signal
        break

    # Extract budget if mentioned
    budget = None
    budget_patterns = [
        r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',
        r'budget[:\s]+(\d+)',
        r'(\d+)\s*(?:usd|dollars)',
        r'(\d+)\s*(?:per hour|/hr|ph)',
    ]
    for pattern in budget_patterns:
        match = re.search(pattern, text)
        if match:
            budget = match.group(0)
            break

    # Extract timeline
    timeline = None
    timeline_patterns = [
        r'(\d+)\s*(?:weeks?|days?|months?)',
        r'launching\s+in\s+(\d+)',
        r'deadline[:\s]+(\d+)',
        r'asap',
        r'urgent',
    ]
    for pattern in timeline_patterns:
        match = re.search(pattern, text)
        if match:
            timeline = match.group(0)
            break

    return {
        'buying_event': requirement,
        'matched_signals': matched_signals,
        'requirement': requirement,
        'budget': budget,
        'timeline': timeline,
        'outsourcing_intent': any(kw in text for kw in ['agency', 'studio', 'freelance', 'contractor', 'external', 'outsource']),
    }


# ============================================================
# CANDIDATE PROCESSOR
# ============================================================

def process_candidate(raw_candidate: dict) -> dict:
    """Process a raw candidate through the acquisition pipeline."""
    
    # Build candidate object
    candidate = {
        'opportunity_id': raw_candidate.get('id', ''),
        'source': raw_candidate.get('source', ''),
        'source_url': raw_candidate.get('url', ''),
        'source_post_id': raw_candidate.get('post_id', ''),
        'published_at': raw_candidate.get('published_at', ''),
        'observed_at': datetime.now(timezone.utc).isoformat(),

        'author_username': raw_candidate.get('author', ''),
        'author_name': raw_candidate.get('author_name', ''),
        'author_profile_url': raw_candidate.get('author_profile_url', ''),

        'company': raw_candidate.get('company', ''),
        'company_url': raw_candidate.get('company_url', ''),
        'product': raw_candidate.get('product', ''),
        'product_url': raw_candidate.get('product_url', ''),

        'raw_signal': raw_candidate.get('title', ''),
        'buying_event': '',
        'requirement': '',
        'budget': '',
        'timeline': '',

        'outsourcing_intent': False,
        'outsourcing_evidence': [],

        'identity_confidence': 'LOW',
        'identity_evidence': [],

        'email': '',
        'email_status': '',
        'email_evidence': [],

        'linkedin_url': '',
        'linkedin_status': '',

        'x_url': '',
        'x_status': '',

        'platform_contact': '',
        'contactability': 'NONE',

        'service_match': '',
        'service_match_confidence': '',

        'freshness': '',
        'acquisition_priority': '',

        'handoff_to_v9': False,
        'rejection_reason': '',
    }

    # Step 1: Check negative signals
    text = f"{raw_candidate.get('title', '')} {raw_candidate.get('content', '')}"
    neg_check = check_negative_signals(text)
    if neg_check['has_negative']:
        candidate['rejection_reason'] = f"NEGATIVE_SIGNALS: {', '.join(neg_check['signals'])}"
        return candidate

    # Step 2: Extract buying event
    buying_event = extract_buying_event(raw_candidate)
    if not buying_event['buying_event']:
        candidate['rejection_reason'] = 'NO_BUYING_EVENT'
        return candidate

    candidate['buying_event'] = buying_event['buying_event']
    candidate['requirement'] = buying_event['requirement']
    candidate['budget'] = buying_event['budget']
    candidate['timeline'] = buying_event['timeline']
    candidate['outsourcing_intent'] = buying_event['outsourcing_intent']
    candidate['outsourcing_evidence'] = buying_event['matched_signals']

    # Step 3: Check freshness
    freshness = classify_freshness(candidate['published_at'])
    candidate['freshness'] = freshness['freshness']

    if freshness['freshness'] == 'LOW_PRIORITY':
        candidate['rejection_reason'] = f"STALE: {freshness.get('age_days', '?')} days old"
        return candidate

    # Step 4: Match service
    service_match = match_service(text)
    if service_match:
        candidate['service_match'] = service_match['business_unit']
        candidate['service_match_confidence'] = service_match['confidence']
    else:
        candidate['rejection_reason'] = 'NO_SERVICE_MATCH'
        return candidate

    # Step 5: Identity confidence
    identity_signals = []
    if candidate['author_username']:
        identity_signals.append('username')
    if candidate['author_name']:
        identity_signals.append('real_name')
    if candidate['company']:
        identity_signals.append('company')
    if candidate['company_url']:
        identity_signals.append('company_url')
    if candidate['linkedin_url']:
        identity_signals.append('linkedin')
    if candidate['x_url']:
        identity_signals.append('x_profile')

    if len(identity_signals) >= 2:
        candidate['identity_confidence'] = 'HIGH'
    elif len(identity_signals) >= 1:
        candidate['identity_confidence'] = 'MEDIUM'
    else:
        candidate['identity_confidence'] = 'LOW'

    candidate['identity_evidence'] = identity_signals

    # Step 6: Contactability
    contact_signals = []
    if candidate['email']:
        contact_signals.append('email')
    if candidate['linkedin_url']:
        contact_signals.append('linkedin')
    if candidate['x_url']:
        contact_signals.append('x_profile')
    if candidate['platform_contact']:
        contact_signals.append('platform_dm')
    if candidate['company_url']:
        contact_signals.append('company_website')

    if len(contact_signals) >= 2:
        candidate['contactability'] = 'HIGH'
    elif len(contact_signals) >= 1:
        candidate['contactability'] = 'MEDIUM'
    else:
        candidate['contactability'] = 'NONE'

    # Step 7: Nishchay pattern (pass full text for better detection)
    nishchay_input = {**candidate, 'raw_signal': f"{candidate.get('raw_signal', '')} {raw_candidate.get('content', '')}"}
    nishchay = detect_nishchay_pattern(nishchay_input)
    candidate['nishchay_pattern'] = nishchay

    # Step 8: Acquisition priority
    priority_score = 0
    if candidate['freshness'] == 'HOT':
        priority_score += 3
    elif candidate['freshness'] == 'CURRENT':
        priority_score += 2
    if candidate['identity_confidence'] == 'HIGH':
        priority_score += 2
    elif candidate['identity_confidence'] == 'MEDIUM':
        priority_score += 1
    if candidate['contactability'] == 'HIGH':
        priority_score += 2
    elif candidate['contactability'] == 'MEDIUM':
        priority_score += 1
    if candidate['outsourcing_intent']:
        priority_score += 2
    if nishchay['matched']:
        priority_score += 3

    if priority_score >= 8:
        candidate['acquisition_priority'] = 'CRITICAL'
    elif priority_score >= 6:
        candidate['acquisition_priority'] = 'HIGH'
    elif priority_score >= 4:
        candidate['acquisition_priority'] = 'MEDIUM'
    else:
        candidate['acquisition_priority'] = 'LOW'

    # Step 9: Handoff to V9
    if (candidate['buying_event'] and
        candidate['outsourcing_intent'] and
        candidate['identity_confidence'] in ['HIGH', 'MEDIUM'] and
        candidate['contactability'] in ['HIGH', 'MEDIUM'] and
        candidate['freshness'] in ['HOT', 'CURRENT'] and
        candidate['service_match']):
        candidate['handoff_to_v9'] = True

    return candidate


# ============================================================
# REPORT GENERATOR
# ============================================================

def generate_reports(candidates: list[dict]):
    """Generate acquisition reports."""
    
    # Separate by status
    handoff = [c for c in candidates if c.get('handoff_to_v9')]
    rejected = [c for c in candidates if c.get('rejection_reason')]
    pending = [c for c in candidates if not c.get('handoff_to_v9') and not c.get('rejection_reason')]

    # Nishchay pattern matches
    nishchay_matches = [c for c in candidates if c.get('nishchay_pattern', {}).get('matched')]

    # Source breakdown
    sources = {}
    for c in candidates:
        src = c.get('source', 'unknown')
        sources[src] = sources.get(src, 0) + 1

    # Rejection breakdown
    rejection_reasons = {}
    for c in rejected:
        reason = c.get('rejection_reason', 'unknown')
        base_reason = reason.split(':')[0]
        rejection_reasons[base_reason] = rejection_reasons.get(base_reason, 0) + 1

    # Write JSON
    with open(OUTPUT_DIR / 'acquisition_candidates.json', 'w', encoding='utf-8') as f:
        json.dump(candidates, f, indent=2, default=str, ensure_ascii=False)

    with open(OUTPUT_DIR / 'acquisition_rejected.json', 'w', encoding='utf-8') as f:
        json.dump(rejected, f, indent=2, default=str, ensure_ascii=False)

    with open(OUTPUT_DIR / 'acquisition_handoff_v9.json', 'w', encoding='utf-8') as f:
        json.dump(handoff, f, indent=2, default=str, ensure_ascii=False)

    with open(OUTPUT_DIR / 'acquisition_nishchay_matches.json', 'w', encoding='utf-8') as f:
        json.dump(nishchay_matches, f, indent=2, default=str, ensure_ascii=False)

    # Write report
    report = []
    report.append('# FOUNDER INTENT ACQUISITION REPORT')
    report.append(f'\nGenerated: {datetime.now(timezone.utc).isoformat()}')
    report.append(f'\n## Summary')
    report.append(f'- Total candidates processed: {len(candidates)}')
    report.append(f'- HANDED TO V9: {len(handoff)}')
    report.append(f'- REJECTED: {len(rejected)}')
    report.append(f'- PENDING: {len(pending)}')
    report.append(f'- NISHCHAY PATTERN MATCHES: {len(nishchay_matches)}')

    report.append(f'\n## Source Breakdown')
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        report.append(f'- {src}: {count}')

    report.append(f'\n## Rejection Breakdown')
    for reason, count in sorted(rejection_reasons.items(), key=lambda x: -x[1]):
        report.append(f'- {reason}: {count}')

    if handoff:
        report.append(f'\n## HANDED TO V9 (ACQUISITION_READY)')
        for c in handoff:
            report.append(f'\n### {c["raw_signal"][:80]}')
            report.append(f'- Source: {c["source"]}')
            report.append(f'- URL: {c["source_url"]}')
            report.append(f'- Author: {c["author_username"]}')
            report.append(f'- Buying Event: {c["buying_event"]}')
            report.append(f'- Service: {c["service_match"]}')
            report.append(f'- Freshness: {c["freshness"]}')
            report.append(f'- Identity: {c["identity_confidence"]}')
            report.append(f'- Contactability: {c["contactability"]}')
            report.append(f'- Priority: {c["acquisition_priority"]}')
            report.append(f'- CTO Test: {"YES - Vansh could contact" if c["contactability"] in ["HIGH","MEDIUM"] else "NO"}')

    if nishchay_matches:
        report.append(f'\n## NISHCHAY PATTERN MATCHES')
        for c in nishchay_matches:
            report.append(f'\n### {c["raw_signal"][:80]}')
            report.append(f'- Score: {c["nishchay_pattern"]["score"]}/8')
            report.append(f'- Has Founder: {c["nishchay_pattern"]["has_founder"]}')
            report.append(f'- Has Product: {c["nishchay_pattern"]["has_product"]}')
            report.append(f'- Has Development Need: {c["nishchay_pattern"]["has_development_need"]}')
            report.append(f'- Has External Help: {c["nishchay_pattern"]["has_external_help"]}')
            report.append(f'- Has Timeline: {c["nishchay_pattern"]["has_timeline"]}')
            report.append(f'- Has Budget: {c["nishchay_pattern"]["has_budget"]}')
            report.append(f'- Has Identifiable Person: {c["nishchay_pattern"]["has_identifiable_person"]}')
            report.append(f'- Has Contact Channel: {c["nishchay_pattern"]["has_contact_channel"]}')

    report.append(f'\n## CTO Quality Test')
    report.append(f'\nFor every ACQUISITION_READY candidate:')
    report.append(f'> "If I were Vansh, could I realistically contact this person today about')
    report.append(f'> the exact problem they publicly expressed?"')
    report.append(f'\n- Handoff to V9: {len(handoff)} candidates')
    report.append(f'- If V9 marks SALES_READY: personalized outreach + founder approval')
    report.append(f'- If V9 marks NEEDS_RESEARCH: more identity/contact work')
    report.append(f'- If V9 marks REJECTED: discard')

    with open(OUTPUT_DIR / 'acquisition_report.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    print(f'\nReports generated:')
    print(f'  {OUTPUT_DIR / "acquisition_candidates.json"}')
    print(f'  {OUTPUT_DIR / "acquisition_rejected.json"}')
    print(f'  {OUTPUT_DIR / "acquisition_handoff_v9.json"}')
    print(f'  {OUTPUT_DIR / "acquisition_nishchay_matches.json"}')
    print(f'  {OUTPUT_DIR / "acquisition_report.md"}')


# ============================================================
# MAIN
# ============================================================

def run_acquisition(candidates: list[dict]):
    """Run acquisition pipeline on candidates."""
    print(f'{"="*60}')
    print(f'FOUNDER INTENT ACQUISITION LAYER')
    print(f'{"="*60}')
    print(f'Processing {len(candidates)} candidates...')

    processed = []
    for c in candidates:
        result = process_candidate(c)
        processed.append(result)

    # Summary
    handoff = [c for c in processed if c.get('handoff_to_v9')]
    rejected = [c for c in processed if c.get('rejection_reason')]
    nishchay = [c for c in processed if c.get('nishchay_pattern', {}).get('matched')]

    print(f'\n{"="*60}')
    print(f'RESULTS')
    print(f'{"="*60}')
    print(f'Total processed: {len(processed)}')
    print(f'HANDED TO V9: {len(handoff)}')
    print(f'REJECTED: {len(rejected)}')
    print(f'NISHCHAY PATTERN MATCHES: {len(nishchay)}')

    if handoff:
        print(f'\n--- HANDED TO V9 ---')
        for h in handoff:
            print(f'\n  {h["raw_signal"][:60]}')
            print(f'    Source: {h["source"]}')
            print(f'    Buying Event: {h["buying_event"]}')
            print(f'    Service: {h["service_match"]}')
            print(f'    Freshness: {h["freshness"]}')
            print(f'    Identity: {h["identity_confidence"]}')
            print(f'    Contactability: {h["contactability"]}')
            print(f'    Priority: {h["acquisition_priority"]}')

    if nishchay:
        print(f'\n--- NISHCHAY PATTERN MATCHES ---')
        for n in nishchay:
            print(f'\n  {n["raw_signal"][:60]}')
            print(f'    Score: {n["nishchay_pattern"]["score"]}/8')
            print(f'    Signals: {[k for k, v in n["nishchay_pattern"].items() if v and k != "score" and k != "matched"]}')

    # Generate reports
    generate_reports(processed)

    return processed


if __name__ == '__main__':
    # Load candidates from file if provided
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            candidates = json.load(f)
        run_acquisition(candidates)
    else:
        print('Usage: python founder_intent_acquisition.py <candidates.json>')
        print('Or import and call run_acquisition(candidates)')
