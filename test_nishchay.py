import json
import sys
sys.path.insert(0, '.')
from founder_intent_acquisition import detect_nishchay_pattern

# Test with Nishchay data
candidate = {
    'raw_signal': 'Looking for a developer / small studio to help with Tavyn',
    'buying_event': 'looking for a developer',
    'requirement': 'looking for a developer',
    'author_name': 'Nishchay Jaiswal',
    'author_username': 'Nishchay_Jaiswal',
    'product': 'Tavyn - SEO AI Agent',
    'product_url': 'https://tavyn.dev/',
    'company': 'Tavyn',
    'company_url': 'https://tavyn.dev/',
    'linkedin_url': '',
    'x_url': '',
    'email': '',
    'platform_contact': 'Reddit DM',
}

result = detect_nishchay_pattern(candidate)
print(json.dumps(result, indent=2))
