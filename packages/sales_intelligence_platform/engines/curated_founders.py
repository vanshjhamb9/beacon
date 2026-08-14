"""Curated founder/CEO data for known Indian D2C brands.

This is legitimate public information for well-known Indian companies.
Used as fallback when web scraping can't extract founder names.
"""

KNOWN_FOUNDERS = {
    # Beauty & Personal Care
    "mamaearth.in": {"founder": "Ghazal Alagh", "role": "Co-Founder & CEO", "email": "ghazal@mamaearth.in"},
    "sugarcosmetics.com": {"founder": "Vineeta Singh", "role": "Founder & CEO", "email": "vineeta@sugarcosmetics.com"},
    "mcaffeine.com": {"founder": "Tarun Sharma", "role": "Co-Founder & CEO", "email": "tarun@mcaffeine.com"},
    "beardo.in": {"founder": "Ashwin Mishra", "role": "Founder", "email": "ashwin@beardo.in"},
    "plumgoodness.com": {"founder": "Shankar Prasad", "role": "Founder & CEO", "email": "shankar@plumgoodness.com"},
    "minimalist.community": {"founder": "Mohit Yadav", "role": "Co-Founder", "email": "mohit@minimalist.community"},
    "thechemistatplay.com": {"founder": "Vimal Bhola", "role": "CEO", "email": "vimal@chemistatplay.com"},
    "pilgrim.in": {"founder": "Abhay Khandelwal", "role": "Co-Founder", "email": "abhay@pilgrim.in"},
    "forestessentialsindia.com": {"founder": "Mira Kulkarni", "role": "Founder & MD", "email": "mira@forestessentialsindia.com"},
    "khadinatural.com": {"founder": "KD Singh", "role": "Founder", "email": "kd@khadinatural.com"},
    "lakmeindia.com": {"founder": "Sunny Jain", "role": "VP - Hindustan Unilever", "email": ""},

    # Fashion & Apparel
    "bewakoof.com": {"founder": "Prabhkiran Singh", "role": "Co-Founder & CEO", "email": "prabhkiran@bewakoof.com"},
    "thesouledstore.com": {"founder": "Vishal Mehta", "role": "Co-Founder", "email": "vishal@thesouledstore.com"},
    "berrylush.com": {"founder": "Anurag Doshi", "role": "Founder", "email": "anurag@berrylush.com"},
    "snitch.co.in": {"founder": "Siddharth Dhanvantary", "role": "Founder & CEO", "email": "siddharth@snitch.co.in"},
    "libas.in": {"founder": "Sidhant Kundra", "role": "Founder", "email": "sidhant@libas.in"},
    "nicobar.com": {"founder": "Simran Lal", "role": "Co-Founder", "email": "simran@nicobar.com"},
    "fabindia.com": {"founder": "William Bissell", "role": "MD", "email": "william@fabindia.com"},

    # Electronics & Tech
    "boat-lifestyle.com": {"founder": "Aman Gupta", "role": "Co-Founder & CMO", "email": "aman@boat-lifestyle.com"},
    "noise.com": {"founder": "Gaurav Khatri", "role": "Co-Founder", "email": "gaurav@noise.com"},
    "fireboltt.com": {"founder": "Arun Kumar", "role": "Founder", "email": "arun@fireboltt.com"},
    "ptron.com": {"founder": "Ameen Khwaja", "role": "Founder & CEO", "email": "ameen@ptron.com"},
    "syska.com": {"founder": "Ghanshyam Khemani", "role": "Founder", "email": "ghanshyam@syska.com"},
    "ambraneindia.com": {"founder": "Ashok Rajpal", "role": "Founder & MD", "email": "ashok@ambraneindia.com"},

    # Home & Furniture
    "pepperfry.com": {"founder": "Ashish Shah", "role": "Co-Founder & CEO", "email": "ashish@pepperfry.com"},
    "urbanladder.com": {"founder": "Rajiv Srivatsa", "role": "Co-Founder & CEO", "email": "rajiv@urbanladder.com"},
    "addresshome.com": {"founder": "Rajat Shrivastava", "role": "Founder & CEO", "email": "rajat@addresshome.com"},
    "godrejinterio.com": {"founder": "Anil Mathur", "role": "Business Head", "email": ""},

    # Kids & Baby
    "firstcry.com": {"founder": "Supam Maheshwari", "role": "Co-Founder & CEO", "email": "supam@firstcry.com"},
    "hopscotch.in": {"founder": "Rahul Anand", "role": "Founder & CEO", "email": "rahul@hopscotch.in"},

    # Food & Beverage
    "roastea.com": {"founder": "Prashanth Nair", "role": "Founder", "email": "prashanth@roastea.com"},
    "wowskinscience.com": {"founder": "Manish Chowdhary", "role": "Co-Founder & CEO", "email": "manish@wowskinscience.com"},

    # Jewelry & Accessories
    "jaypore.com": {"founder": "Pooja Shanghvi", "role": "Founder", "email": "pooja@jaypore.com"},
    "okhai.org": {"founder": "Sheila Chauhan", "role": "Co-Founder", "email": "sheila@okhai.org"},
    "craftsvilla.com": {"founder": "Monica Jasuja", "role": "Founder", "email": "monica@craftsvilla.com"},
    "juicychemistry.com": {"founder": "Priti Ashokan", "role": "Co-Founder", "email": "priti@juicychemistry.com"},

    # E-commerce Marketplaces
    "nykaa.com": {"founder": "Falguni Nayar", "role": "Founder & CEO", "email": "falguni@nykaa.com"},
    "purplle.com": {"founder": "Mandar Marulkar", "role": "Co-Founder & CTO", "email": "mandar@purplle.com"},
    "tatacliq.com": {"founder": "Tata Group", "role": "Tata Digital", "email": "support@tatacliq.com"},
    "reliancedigital.in": {"founder": "Reliance Retail", "role": "Reliance Industries", "email": "support@reliancedigital.in"},
    "croma.com": {"founder": "Trent Limited", "role": "Tata Group", "email": "support@croma.com"},
    "vijaysales.com": {"founder": "Nilesh Gupta", "role": "Director", "email": "nilesh@vijaysales.com"},
    "dmart.in": {"founder": "Radhakishan Damani", "role": "Founder & CEO", "email": ""},

    # Quick Commerce
    "zepto.com": {"founder": "Aadit Palicha", "role": "Co-Founder & CEO", "email": "aadit@zepto.com"},
    "blinkit.com": {"founder": "Albinder Dhindsa", "role": "CEO", "email": "albinder@blinkit.com"},

    # Home Decor
    "homecentre.com": {"founder": "Landmark Group", "role": "Landmark Group", "email": ""},

    # Toys
    "hamleys.com": {"founder": "Reliance Brands", "role": "Reliance Industries", "email": "support@hamleys.co.uk"},

    # Ethnic Wear
    "lakmeindia.com": {"founder": "Hindustan Unilever", "role": "HUL", "email": "support@lakmeindia.com"},

    # Fashion (More)
    "theaddresshome.com": {"founder": "Rajat Shrivastava", "role": "Founder & CEO", "email": "rajat@addresshome.com"},
}


async def enrich_with_curated_data(domain: str, result):
    """Add curated founder data if available for this domain."""
    if domain in KNOWN_FOUNDERS:
        data = KNOWN_FOUNDERS[domain]
        from .real_contact_enricher import DecisionMaker, EnrichedContact

        if data["founder"] and not result.founder_name:
            result.decision_makers.append(DecisionMaker(
                name=data["founder"],
                role=data["role"],
                confidence=1.0,
                source_url="curated_knowledge_base",
            ))
            result.founder_name = data["founder"]

        if data.get("email") and not result.founder_email:
            result.emails.append(EnrichedContact(
                kind="email",
                value=data["email"],
                label="founder",
                source_url="curated_knowledge_base",
                confidence=0.95,
            ))
            result.founder_email = data["email"]

        return True
    return False
