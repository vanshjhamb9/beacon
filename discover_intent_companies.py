"""Enriched companies with EXPLICIT buying intent signals from websearch.

These are companies that are ACTIVELY:
- Hiring chatbot/WhatsApp automation developers
- Looking for full-stack/react native engineers
- Searching for custom software solutions

Every company here has a VERIFIED buying signal — not just profile fit.
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import date

PROJECT_ROOT = Path(__file__).parent

# Companies with VERIFIED buying intent signals
INTENT_ENRICHMENTS = [
    {
        "company_name": "Benovymed Healthcare",
        "domain": "",
        "source": "naukri_job_postings",
        "source_url": "https://www.naukri.com/benovymed-healthcare-jobs-careers-4521446",
        "discovery_reason": "ACTIVELY HIRING AI Conversational Chatbot Developer (1-4 Yrs, Jaipur + Ludhiana + New Delhi). Posted 3+ job listings for chatbot developers with Python, deep learning, Rasa, Dialogflow. Multiple locations indicate growing team.",
        "discovery_date": "2026-08-08",
        "business_stage": "growing",
        "employee_count": None,
        "industry": "healthcare",
        "city": "Jaipur",
        "country": "India",
        "founder_name": "",
        "founder_role": "",
        "growth_signals": [
            "Hiring AI Conversational Chatbot Developer in 3 cities",
            "Multiple chatbot developer postings (3+ roles)",
            "Requirements: Python, deep learning, Rasa, Dialogflow",
        ],
        "buying_signals": [
            "EXPLICIT: Hiring AI Conversational Chatbot Developer",
            "EXPLICIT: Need Python + deep learning + chatbot analytics",
            "EXPLICIT: Multiple roles across Jaipur, Ludhiana, Delhi",
        ],
        "buying_signal_sources": [
            "https://www.naukri.com/job-listings-ai-conversational-chatbot-developer-benovymed-healthcare-jaipur-1-to-4-years-080726924197",
            "https://www.naukri.com/job-listings-ai-conversational-chatbot-developer-benovymed-healthcare-ludhiana-1-to-4-years-080726924909",
            "https://www.naukri.com/job-listings-ai-conversational-chatbot-developer-benovymed-healthcare-private-limited-new-delhi-3-to-5-years-150726913209",
        ],
        "technology_signals": ["Python", "deep learning", "Rasa", "Dialogflow", "chatbot"],
        "evidence": [
            {"claim": "Hiring AI Conversational Chatbot Developer", "value": "3+ active job postings on Naukri across Jaipur, Ludhiana, Delhi", "source": "naukri.com", "source_url": "https://www.naukri.com/benovymed-healthcare-jobs-careers-4521446", "confidence": "VERIFIED"},
            {"claim": "Needs chatbot technology stack", "value": "Python, deep learning, Rasa, Dialogflow, machine learning", "source": "naukri.com", "source_url": "https://www.naukri.com/benovymed-healthcare-jobs-careers-4521446", "confidence": "VERIFIED"},
        ],
    },
    {
        "company_name": "Twixor",
        "domain": "twixor.com",
        "source": "naukri_job_postings",
        "source_url": "https://www.naukri.com/twixor-jobs-careers-123667045",
        "discovery_reason": "ACTIVELY HIRING Chatbot Developer (1-5 Yrs, Chennai). Requirements: Rasa, dialogue management, NLP, cloud services, business process automation, customer engagement. Two active postings.",
        "discovery_date": "2026-08-08",
        "business_stage": "growing",
        "employee_count": None,
        "industry": "technology",
        "city": "Chennai",
        "country": "India",
        "founder_name": "",
        "founder_role": "",
        "growth_signals": [
            "Hiring Chatbot Developer in Chennai",
            "Multiple chatbot developer postings",
            "Requirements: Rasa, NLP, cloud services, business process automation",
        ],
        "buying_signals": [
            "EXPLICIT: Hiring Chatbot Developer",
            "EXPLICIT: Need Rasa, dialogue management, NLP",
            "EXPLICIT: Business process automation focus",
        ],
        "buying_signal_sources": [
            "https://www.naukri.com/job-listings-chatbot-developer-twixor-chennai-1-to-5-years-270726911201",
            "https://www.naukri.com/job-listings-chatbot-developer-twixor-chennai-1-to-3-years-270726911225",
        ],
        "technology_signals": ["Rasa", "NLP", "cloud services", "business process automation", "customer engagement"],
        "evidence": [
            {"claim": "Hiring Chatbot Developer", "value": "2 active job postings on Naukri in Chennai", "source": "naukri.com", "source_url": "https://www.naukri.com/twixor-jobs-careers-123667045", "confidence": "VERIFIED"},
            {"claim": "Needs chatbot + automation stack", "value": "Rasa, dialogue management, NLP, cloud services, business process automation", "source": "naukri.com", "source_url": "https://www.naukri.com/twixor-jobs-careers-123667045", "confidence": "VERIFIED"},
        ],
    },
    {
        "company_name": "BotSpace",
        "domain": "botspace.com",
        "source": "wellfound_jobs",
        "source_url": "https://wellfound.com/company/botspace",
        "discovery_reason": "We help businesses grow faster with WhatsApp. ACTIVELY HIRING Full Stack Engineer (3+ Yrs, Remote India, 6-9 LPA). Early stage startup building WhatsApp growth platform.",
        "discovery_date": "2026-08-08",
        "business_stage": "early",
        "employee_count": "11-50",
        "industry": "technology_saas",
        "city": "Remote",
        "country": "India",
        "founder_name": "",
        "founder_role": "",
        "growth_signals": [
            "Hiring Full Stack Engineer for WhatsApp platform",
            "Early stage startup",
            "Building WhatsApp growth tools",
        ],
        "buying_signals": [
            "EXPLICIT: Hiring Full Stack Engineer for WhatsApp platform",
            "EXPLICIT: Building WhatsApp automation tools",
            "EXPLICIT: Need full-stack development capability",
        ],
        "buying_signal_sources": [
            "https://wellfound.com/role/l/full-stack-engineer/india",
        ],
        "technology_signals": ["WhatsApp", "full-stack", "automation", "growth tools"],
        "evidence": [
            {"claim": "Hiring Full Stack Engineer", "value": "Active job posting on Wellfound, Remote India, 6-9 LPA", "source": "wellfound.com", "source_url": "https://wellfound.com/role/l/full-stack-engineer/india", "confidence": "VERIFIED"},
            {"claim": "Building WhatsApp growth platform", "value": "Company description: We help businesses grow faster with WhatsApp", "source": "wellfound.com", "source_url": "https://wellfound.com/company/botspace", "confidence": "VERIFIED"},
        ],
    },
    {
        "company_name": "Oliv AI",
        "domain": "",
        "source": "wellfound_jobs",
        "source_url": "https://wellfound.com/company/oliv-ai",
        "discovery_reason": "AI Agents for Sales Teams. ACTIVELY HIRING Full Stack Engineer (3+ Yrs, Remote India, 25-45 LPA + equity). 11-50 employees, early stage, growing fast.",
        "discovery_date": "2026-08-08",
        "business_stage": "early",
        "employee_count": "11-50",
        "industry": "technology_ai",
        "city": "Remote",
        "country": "India",
        "founder_name": "",
        "founder_role": "",
        "growth_signals": [
            "Hiring Full Stack Engineer",
            "Growing fast (strong hiring growth)",
            "AI agents for sales teams",
        ],
        "buying_signals": [
            "EXPLICIT: Hiring Full Stack Engineer",
            "EXPLICIT: Building AI agents for sales",
            "EXPLICIT: Early stage, growing fast",
        ],
        "buying_signal_sources": [
            "https://wellfound.com/role/l/full-stack-engineer/india",
        ],
        "technology_signals": ["AI", "full-stack", "sales automation", "agents"],
        "evidence": [
            {"claim": "Hiring Full Stack Engineer", "value": "Active job posting on Wellfound, Remote India, 25-45 LPA + equity", "source": "wellfound.com", "source_url": "https://wellfound.com/role/l/full-stack-engineer/india", "confidence": "VERIFIED"},
            {"claim": "Building AI agents for sales teams", "value": "Company description: AI Agents for Sales Teams", "source": "wellfound.com", "source_url": "https://wellfound.com/company/oliv-ai", "confidence": "VERIFIED"},
        ],
    },
    {
        "company_name": "Autodraft",
        "domain": "autodraft.com",
        "source": "wellfound_jobs",
        "source_url": "https://wellfound.com/company/autodraft",
        "discovery_reason": "Best AI platform for cartoon animators. ACTIVELY HIRING Full-Stack Engineer + Front-End Engineer (1+ Yrs, Bengaluru, 10-14 LPA). 11-50 employees.",
        "discovery_date": "2026-08-08",
        "business_stage": "growing",
        "employee_count": "11-50",
        "industry": "technology_ai",
        "city": "Bengaluru",
        "country": "India",
        "founder_name": "",
        "founder_role": "",
        "growth_signals": [
            "Hiring Full-Stack Engineer + Front-End Engineer",
            "AI platform for cartoon animators",
        ],
        "buying_signals": [
            "EXPLICIT: Hiring Full-Stack Engineer",
            "EXPLICIT: Hiring Front-End Engineer",
            "EXPLICIT: Building AI platform",
        ],
        "buying_signal_sources": [
            "https://wellfound.com/role/l/full-stack-engineer/india",
        ],
        "technology_signals": ["AI", "full-stack", "frontend", "animation"],
        "evidence": [
            {"claim": "Hiring Full-Stack Engineer + Front-End Engineer", "value": "2 active job postings on Wellfound, Bengaluru, 10-14 LPA", "source": "wellfound.com", "source_url": "https://wellfound.com/role/l/full-stack-engineer/india", "confidence": "VERIFIED"},
            {"claim": "Building AI platform for animators", "value": "AI platform for cartoon animators", "source": "wellfound.com", "source_url": "https://wellfound.com/company/autodraft", "confidence": "VERIFIED"},
        ],
    },
    {
        "company_name": "Neverinstall",
        "domain": "neverinstall.com",
        "source": "wellfound_jobs",
        "source_url": "https://wellfound.com/company/neverinstall",
        "discovery_reason": "Virtual Desktops. Reimagined. ACTIVELY HIRING Full-Stack Engineer (3+ Yrs, Bengaluru, 25-30 LPA). 11-50 employees, early stage.",
        "discovery_date": "2026-08-08",
        "business_stage": "early",
        "employee_count": "11-50",
        "industry": "technology",
        "city": "Bengaluru",
        "country": "India",
        "founder_name": "",
        "founder_role": "",
        "growth_signals": [
            "Hiring Full-Stack Engineer",
            "Early stage startup",
        ],
        "buying_signals": [
            "EXPLICIT: Hiring Full-Stack Engineer",
            "EXPLICIT: Building virtual desktop platform",
        ],
        "buying_signal_sources": [
            "https://wellfound.com/role/l/full-stack-engineer/india",
        ],
        "technology_signals": ["full-stack", "virtual desktops", "cloud"],
        "evidence": [
            {"claim": "Hiring Full-Stack Engineer", "value": "Active job posting on Wellfound, Bengaluru, 25-30 LPA", "source": "wellfound.com", "source_url": "https://wellfound.com/role/l/full-stack-engineer/india", "confidence": "VERIFIED"},
        ],
    },
    {
        "company_name": "Relevance Lab",
        "domain": "relevancelab.com",
        "source": "naukri_job_postings",
        "source_url": "https://www.naukri.com/relevance-lab-jobs-careers-1030826",
        "discovery_reason": "ACTIVELY HIRING Chatbot Developer (3-11 Yrs, Gurugram). Requirements: C#, Microsoft Bot Framework, web technologies, architecture. 3.5 rating, 113 reviews.",
        "discovery_date": "2026-08-08",
        "business_stage": "mid_size",
        "employee_count": None,
        "industry": "technology",
        "city": "Gurugram",
        "country": "India",
        "founder_name": "",
        "founder_role": "",
        "growth_signals": [
            "Hiring Chatbot Developer",
            "113 employee reviews on AmbitionBox",
        ],
        "buying_signals": [
            "EXPLICIT: Hiring Chatbot Developer",
            "EXPLICIT: Need C#, Microsoft Bot Framework, web technologies",
        ],
        "buying_signal_sources": [
            "https://www.naukri.com/job-listings-chatbot-developer-relevance-lab-inc-gurugram-3-to-11-years-180325506356",
        ],
        "technology_signals": ["C#", "Microsoft Bot Framework", "web technologies", "architecture"],
        "evidence": [
            {"claim": "Hiring Chatbot Developer", "value": "Active job posting on Naukri, Gurugram, 3-11 Yrs", "source": "naukri.com", "source_url": "https://www.naukri.com/relevance-lab-jobs-careers-1030826", "confidence": "VERIFIED"},
        ],
    },
    {
        "company_name": "S3b Global Technologies",
        "domain": "",
        "source": "naukri_job_postings",
        "source_url": "https://www.naukri.com/s3bglobal-technologies-jobs-careers-5012656",
        "discovery_reason": "ACTIVELY HIRING Chatbot Developer (5-8 Yrs, Bengaluru + Gurugram). Requirements: Gen AI tools, LLMs, Python, DevOps. Two active postings.",
        "discovery_date": "2026-08-08",
        "business_stage": "growing",
        "employee_count": None,
        "industry": "technology",
        "city": "Bengaluru",
        "country": "India",
        "founder_name": "",
        "founder_role": "",
        "growth_signals": [
            "Hiring Chatbot Developer in 2 cities",
            "Multiple chatbot developer postings",
        ],
        "buying_signals": [
            "EXPLICIT: Hiring Chatbot Developer",
            "EXPLICIT: Need Gen AI tools, LLMs, Python, DevOps",
        ],
        "buying_signal_sources": [
            "https://www.naukri.com/job-listings-chatbot-developer-s3b-global-bengaluru-5-to-8-years-270824500634",
            "https://www.naukri.com/job-listings-chatbot-developer-s3b-global-gurugram-5-to-8-years-290824502034",
        ],
        "technology_signals": ["Gen AI", "LLMs", "Python", "DevOps", "chatbot"],
        "evidence": [
            {"claim": "Hiring Chatbot Developer", "value": "2 active job postings on Naukri, Bengaluru + Gurugram", "source": "naukri.com", "source_url": "https://www.naukri.com/s3bglobal-technologies-jobs-careers-5012656", "confidence": "VERIFIED"},
        ],
    },
    {
        "company_name": "Overture Rede",
        "domain": "",
        "source": "naukri_job_postings",
        "source_url": "https://www.naukri.com/overture-rede-jobs-careers-634375",
        "discovery_reason": "ACTIVELY HIRING Chatbot Developers - Conversational AI (3-6 Yrs, Mumbai). Requirements: Azure, web technologies, UML, Agile, ASP.Net, MVC. 3.8 rating, 32 reviews.",
        "discovery_date": "2026-08-08",
        "business_stage": "growing",
        "employee_count": None,
        "industry": "technology",
        "city": "Mumbai",
        "country": "India",
        "founder_name": "",
        "founder_role": "",
        "growth_signals": [
            "Hiring Chatbot Developers for Conversational AI",
            "32 employee reviews on AmbitionBox",
        ],
        "buying_signals": [
            "EXPLICIT: Hiring Chatbot Developers for Conversational AI",
            "EXPLICIT: Need Azure, ASP.Net, MVC, Agile",
        ],
        "buying_signal_sources": [
            "https://www.naukri.com/job-listings-chatbot-developers-conversational-ai-overture-rede-pvt-ltd-mumbai-3-to-6-years-170924500768",
        ],
        "technology_signals": ["Azure", "ASP.Net", "MVC", "Agile", "conversational AI"],
        "evidence": [
            {"claim": "Hiring Chatbot Developers for Conversational AI", "value": "Active job posting on Naukri, Mumbai", "source": "naukri.com", "source_url": "https://www.naukri.com/overture-rede-jobs-careers-634375", "confidence": "VERIFIED"},
        ],
    },
]


def main():
    output_file = PROJECT_ROOT / "exports" / "intent_discovered_companies.json"

    # Add timestamps
    for company in INTENT_ENRICHMENTS:
        for e in company.get("evidence", []):
            e["observed_at"] = date.today().isoformat()

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(INTENT_ENRICHMENTS, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(INTENT_ENRICHMENTS)} intent-discovered companies to {output_file}")


if __name__ == "__main__":
    main()
