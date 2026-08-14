"""
PROCESS RAW EVENTS PIPELINE
Processes 6,328 raw events from PostgreSQL through qualification gates.
Outputs: SALES_READY, NEEDS_RESEARCH, REJECTED
"""

import psycopg2
import json
import sys
import io
import re
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ============================================================
# CONFIGURATION
# ============================================================

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'dbname': 'beacon',
    'user': 'beacon',
    'password': 'beacon_password'
}

OUTPUT_DIR = Path('exports/full_pipeline')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# INTENT PATTERNS (from v9_buyer_first_discovery.py)
# ============================================================

BUYING_INTENT_KEYWORDS = {
    'COMAI': {
        'keywords': [
            'need whatsapp bot', 'looking for whatsapp automation', 'whatsapp automation for ecommerce',
            'automate whatsapp', 'whatsapp customer support', 'whatsapp sales bot',
            'need chatbot', 'looking for chatbot', 'ai chatbot for ecommerce',
            'customer support automation', 'automate customer support',
            'need shopify automation', 'shopify ai', 'shopify chatbot',
            'woocommerce automation', 'cart recovery', 'lead capture bot',
        ],
        'services': ['comai_whatsapp', 'comai_chatbot', 'comai_shopify'],
    },
    'SAAS_DEVELOPMENT': {
        'keywords': [
            'need saas developer', 'looking for saas developer', 'saas mvp developer',
            'build saas', 'saas backend', 'saas api', 'saas infrastructure',
            'need full stack', 'looking for full stack', 'full stack developer',
            'need backend developer', 'backend developer needed',
            'need react developer', 'looking for react developer',
            'need next.js developer', 'nextjs developer',
            'need typescript developer', 'typescript developer needed',
            'need node.js developer', 'nodejs developer',
            'need python developer', 'python developer needed',
            'saas product development', 'saas technical co-founder',
            'mvp developer', 'mvp development', 'build mvp',
            'need developer for saas', 'developer for saas product',
        ],
        'services': ['saas_dev_team', 'saas_product', 'saas_mvp'],
    },
    'CUSTOM_SOFTWARE': {
        'keywords': [
            'need software developed', 'need software developer', 'looking for software developer',
            'need web developer', 'looking for web developer', 'web developer needed',
            'need app developer', 'looking for app developer', 'app developer needed',
            'need mobile developer', 'mobile app development',
            'need api developer', 'api development',
            'need ai developer', 'ai development', 'machine learning developer',
            'need automation', 'business automation', 'process automation',
            'need custom software', 'custom software development',
            'need erp developer', 'erp development',
            'need crm developer', 'crm development',
            'need dashboard', 'dashboard development',
            'need legacy modernization', 'modernize legacy',
        ],
        'services': ['custom_web', 'custom_app', 'custom_ai', 'custom_erp', 'custom_crm'],
    },
}

# Buyer identity signals
BUYER_SIGNALS = [
    'i need', 'looking for', 'need help', 'need someone', 'need a developer',
    'need a team', 'need an agency', 'need a company', 'need a freelancer',
    'anyone know', 'any recommendations', 'suggestions?', 'advice?',
    'budget:', 'timeline:', 'deadline:', 'asap', 'urgent',
    'willing to pay', 'paying', 'budget available', 'funded',
    'startup', 'founder', 'ceo', 'cto', 'vp engineering',
    'our company', 'my company', 'my startup', 'my business',
    'we are building', 'we are launching', 'we need', 'we are looking',
    'i am building', 'i am launching', 'i am looking', 'i am building',
]

# Job seeker / agency / competitor signals (REJECT)
REJECT_SIGNALS = [
    'co-founder', 'co founder', 'technical co-founder', 'tech co-founder',
    'looking for a co-founder', 'need a co-founder', 'startup co-founder',
    'no agencies', 'agency needs', 'agency hiring',
    'developer for hire', 'freelance developer', 'available for work',
    'looking for work', 'open to work', 'job search', 'hire me',
    'i am a developer', 'my skills include', 'portfolio:',
    'hiring chatbot developer', 'hiring ai developer', 'hiring full stack',
    'hiring backend', 'hiring frontend', 'hiring react',
    'we are hiring', 'we are looking for a developer to hire',
    'job posting', 'job description', 'apply now',
    'our team is hiring', 'join our team', 'career page',
]

# ============================================================
# QUALIFICATION GATES
# ============================================================

def check_buyer_identity(text):
    """Check if the text is from a buyer (not a job seeker/agency/competitor)."""
    text_lower = text.lower()

    # Check reject signals first
    for signal in REJECT_SIGNALS:
        if signal in text_lower:
            return False, f'REJECT: {signal}'

    # Check buyer signals
    for signal in BUYER_SIGNALS:
        if signal in text_lower:
            return True, f'BUYER: {signal}'

    return False, 'NO_BUYER_SIGNAL'


def check_service_match(text):
    """Match text against service patterns."""
    text_lower = text.lower()
    matches = []

    for unit, config in BUYING_INTENT_KEYWORDS.items():
        for keyword in config['keywords']:
            if keyword in text_lower:
                matches.append({
                    'business_unit': unit,
                    'services': config['services'],
                    'matched_keyword': keyword,
                    'confidence': 0.8,
                })

    return matches


def check_company_project(text):
    """Check if there's a company or project mentioned."""
    text_lower = text.lower()
    signals = []

    company_patterns = [
        r'my startup', r'my company', r'my business', r'our startup', r'our company',
        r'we are building', r'we are launching', r'we are developing',
        r'i am building', r'i am launching', r'i am developing',
        r'founded by', r'co-founder of', r'cto of', r'ceo of',
    ]

    for pattern in company_patterns:
        if re.search(pattern, text_lower):
            signals.append(pattern)

    return len(signals) > 0, signals


def check_currentness(published_at):
    """Check if the event is recent (within 30 days)."""
    if not published_at:
        return False, 'NO_DATE'

    now = datetime.now(timezone.utc)
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)

    age_days = (now - published_at).days

    if age_days <= 7:
        return True, f'{age_days}d_old'
    elif age_days <= 30:
        return True, f'{age_days}d_old'
    else:
        return False, f'{age_days}d_old_TOO_OLD'


def check_contact_available(metadata):
    """Check if contact information is available."""
    if not metadata:
        return False, 'NO_METADATA'

    author = metadata.get('author', '')
    subreddit = metadata.get('subreddit', '')
    reddit_id = metadata.get('reddit_id', '')

    if author and subreddit and reddit_id:
        return True, f'REDDIT_DM:{author}'

    return False, 'NO_CONTACT'


def check_evidence_consistency(title, content, metadata):
    """Check if evidence is consistent across sources."""
    signals = []

    if title:
        signals.append('title_present')
    if content and len(content) > 50:
        signals.append('content_present')
    if metadata and metadata.get('author'):
        signals.append('author_present')
    if metadata and metadata.get('subreddit'):
        signals.append('subreddit_present')

    return len(signals) >= 3, signals


# ============================================================
# MAIN PIPELINE
# ============================================================

def process_events():
    """Process all raw events through the pipeline."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Fetch all events
    cur.execute("""
        SELECT id, source, title, content, url, published_at, metadata, created_at
        FROM raw_events
        ORDER BY created_at DESC
    """)

    events = cur.fetchall()
    print(f'Loaded {len(events)} raw events')

    results = {
        'SALES_READY': [],
        'NEEDS_RESEARCH': [],
        'REJECTED': [],
    }

    stats = {
        'total': len(events),
        'by_source': {},
        'rejected_reasons': {},
    }

    for event in events:
        event_id, source, title, content, url, published_at, metadata, created_at = event

        # Parse metadata
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except:
                metadata = {}

        # Combine text for analysis
        text = f'{title or ""} {content or ""}'.strip()
        text_lower = text.lower()

        # Track source stats
        stats['by_source'][source] = stats['by_source'].get(source, 0) + 1

        # ============================================================
        # STAGE 1: REJECT obvious non-buyers
        # ============================================================

        is_buyer, buyer_reason = check_buyer_identity(text)
        if not is_buyer:
            results['REJECTED'].append({
                'id': event_id,
                'source': source,
                'title': title,
                'url': url,
                'reason': buyer_reason,
            })
            stats['rejected_reasons'][buyer_reason] = stats['rejected_reasons'].get(buyer_reason, 0) + 1
            continue

        # ============================================================
        # STAGE 2: CHECK service match
        # ============================================================

        service_matches = check_service_match(text)
        if not service_matches:
            results['REJECTED'].append({
                'id': event_id,
                'source': source,
                'title': title,
                'url': url,
                'reason': 'NO_SERVICE_MATCH',
            })
            stats['rejected_reasons']['NO_SERVICE_MATCH'] = stats['rejected_reasons'].get('NO_SERVICE_MATCH', 0) + 1
            continue

        # ============================================================
        # STAGE 3: CHECK company/project
        # ============================================================

        has_company, company_signals = check_company_project(text)

        # ============================================================
        # STAGE 4: CHECK currentness
        # ============================================================

        is_current, currentness_reason = check_currentness(published_at)

        # ============================================================
        # STAGE 5: CHECK contact availability
        # ============================================================

        has_contact, contact_reason = check_contact_available(metadata)

        # ============================================================
        # STAGE 6: CHECK evidence consistency
        # ============================================================

        is_consistent, consistency_signals = check_evidence_consistency(title, content, metadata)

        # ============================================================
        # CLASSIFICATION
        # ============================================================

        # Calculate gates passed
        gates_passed = 0
        gates_total = 6

        if is_buyer:
            gates_passed += 1
        if service_matches:
            gates_passed += 1
        if has_company:
            gates_passed += 1
        if is_current:
            gates_passed += 1
        if has_contact:
            gates_passed += 1
        if is_consistent:
            gates_passed += 1

        # Determine classification
        if gates_passed >= 5:
            classification = 'SALES_READY'
        elif gates_passed >= 3:
            classification = 'NEEDS_RESEARCH'
        else:
            classification = 'REJECTED'

        # Build opportunity record
        opportunity = {
            'id': event_id,
            'source': source,
            'title': title,
            'content': (content or '')[:500],
            'url': url,
            'published_at': str(published_at) if published_at else None,
            'author': metadata.get('author', ''),
            'subreddit': metadata.get('subreddit', ''),
            'score': metadata.get('score', 0),
            'num_comments': metadata.get('num_comments', 0),
            'service_matches': service_matches,
            'has_company': has_company,
            'company_signals': company_signals,
            'is_current': is_current,
            'currentness_reason': currentness_reason,
            'has_contact': has_contact,
            'contact_reason': contact_reason,
            'is_consistent': is_consistent,
            'consistency_signals': consistency_signals,
            'gates_passed': gates_passed,
            'gates_total': gates_total,
            'classification': classification,
            'processed_at': datetime.now(timezone.utc).isoformat(),
        }

        results[classification].append(opportunity)

    # ============================================================
    # OUTPUT
    # ============================================================

    print(f'\n{"="*60}')
    print(f'PIPELINE RESULTS')
    print(f'{"="*60}')
    print(f'Total events processed: {stats["total"]}')
    print(f'SALES_READY: {len(results["SALES_READY"])}')
    print(f'NEEDS_RESEARCH: {len(results["NEEDS_RESEARCH"])}')
    print(f'REJECTED: {len(results["REJECTED"])}')
    print(f'\nBy source:')
    for source, count in sorted(stats['by_source'].items(), key=lambda x: -x[1]):
        print(f'  {source}: {count}')
    print(f'\nRejection reasons:')
    for reason, count in sorted(stats['rejected_reasons'].items(), key=lambda x: -x[1]):
        print(f'  {reason}: {count}')

    # Save results
    output_file = OUTPUT_DIR / 'pipeline_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str, ensure_ascii=False)
    print(f'\nResults saved to: {output_file}')

    # Save SALES_READY details
    if results['SALES_READY']:
        sales_ready_file = OUTPUT_DIR / 'SALES_READY_leads.json'
        with open(sales_ready_file, 'w', encoding='utf-8') as f:
            json.dump(results['SALES_READY'], f, indent=2, default=str, ensure_ascii=False)
        print(f'SALES_READY leads saved to: {sales_ready_file}')

    # Save NEEDS_RESEARCH details
    if results['NEEDS_RESEARCH']:
        needs_research_file = OUTPUT_DIR / 'NEEDS_RESEARCH_leads.json'
        with open(needs_research_file, 'w', encoding='utf-8') as f:
            json.dump(results['NEEDS_RESEARCH'], f, indent=2, default=str, ensure_ascii=False)
        print(f'NEEDS_RESEARCH leads saved to: {needs_research_file}')

    # Generate report
    generate_report(results, stats)

    cur.close()
    conn.close()

    return results


def generate_report(results, stats):
    """Generate markdown report."""
    report = []
    report.append('# Pipeline Processing Report')
    report.append(f'\nGenerated: {datetime.now(timezone.utc).isoformat()}')
    report.append(f'\n## Summary')
    report.append(f'- Total events processed: {stats["total"]}')
    report.append(f'- SALES_READY: {len(results["SALES_READY"])}')
    report.append(f'- NEEDS_RESEARCH: {len(results["NEEDS_RESEARCH"])}')
    report.append(f'- REJECTED: {len(results["REJECTED"])}')
    report.append(f'\n## By Source')
    for source, count in sorted(stats['by_source'].items(), key=lambda x: -x[1]):
        report.append(f'- {source}: {count}')
    report.append(f'\n## Rejection Reasons')
    for reason, count in sorted(stats['rejected_reasons'].items(), key=lambda x: -x[1]):
        report.append(f'- {reason}: {count}')

    if results['SALES_READY']:
        report.append(f'\n## SALES_READY Leads')
        for lead in results['SALES_READY']:
            report.append(f'\n### {lead["title"][:80]}')
            report.append(f'- Source: {lead["source"]}')
            report.append(f'- URL: {lead["url"]}')
            report.append(f'- Author: {lead["author"]}')
            report.append(f'- Gates: {lead["gates_passed"]}/{lead["gates_total"]}')
            report.append(f'- Service: {lead["service_matches"][0]["business_unit"] if lead["service_matches"] else "N/A"}')
            report.append(f'- Contact: {lead["contact_reason"]}')

    if results['NEEDS_RESEARCH']:
        report.append(f'\n## NEEDS_RESEARCH Leads')
        for lead in results['NEEDS_RESEARCH']:
            report.append(f'\n### {lead["title"][:80]}')
            report.append(f'- Source: {lead["source"]}')
            report.append(f'- URL: {lead["url"]}')
            report.append(f'- Author: {lead["author"]}')
            report.append(f'- Gates: {lead["gates_passed"]}/{lead["gates_total"]}')
            report.append(f'- Service: {lead["service_matches"][0]["business_unit"] if lead["service_matches"] else "N/A"}')

    report_file = OUTPUT_DIR / 'PIPELINE_REPORT.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    print(f'\nReport saved to: {report_file}')


if __name__ == '__main__':
    process_events()
