"""9-person outreach test drafts.

Each draft is personalized per company with:
- Exact trigger from job posting
- Evidence-based requirement
- Matching Inowix service
- Outsourcing-fit angle
- CTA
- Source reference
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

DRAFTS = [
    # ============================================================
    # 1. Oliv AI — Hiring Full Stack Engineer (AI Agents for Sales)
    # ============================================================
    {
        "company": "Oliv AI",
        "contact_name": "Founder/CTO",
        "contact_role": "Technical Decision Maker",
        "channel": "linkedin",
        "subject": "Your Full Stack Engineer role at Oliv AI",
        "body": (
            "Hi,\n\n"
            "Saw that Oliv AI is hiring a Full Stack Engineer (3+ Yrs, Remote, 25-45 LPA + equity) "
            "for your AI Agents for Sales Teams platform.\n\n"
            "We're an engineering team at Inowix Technologies. We build AI-powered sales automation "
            "systems — the kind of product you're scaling right now. We've shipped similar agent-based "
            "architectures for sales teams, including LLM integration, pipeline automation, and "
            "real-time conversation handling.\n\n"
            "Given that you're early-stage and growing fast, I thought it may be worth exploring "
            "whether we could support your full-stack development as an extension of your team — "
            "without the 3-month hiring cycle.\n\n"
            "Would you be open to a quick 15-minute technical discussion?\n\n"
            "Best,\n"
            "Vansh\n"
            "Inowix Technologies"
        ),
        "source_url": "https://wellfound.com/role/l/full-stack-engineer/india",
        "beacon_reason": "ACTIVELY HIRING Full Stack Engineer for AI sales agent platform. Early stage, growing fast, 11-50 employees. Remote India, 25-45 LPA + equity.",
        "trigger": "Full Stack Engineer (3+ Yrs, Remote India, 25-45 LPA + equity)",
        "requirement": "Full-stack development for AI-powered sales agent platform. Likely need: LLM integration, real-time pipelines, backend infrastructure.",
        "service_match": "SaaS Development — Dedicated Team / Full-Stack Engineering",
        "outsourcing_angle": "Early-stage startup with equity-based compensation. Hiring full-time is slow and expensive. A dedicated team can ship faster while they focus on product-market fit.",
        "cta": "15-minute technical discovery call",
    },

    # ============================================================
    # 2. Neverinstall — Hiring Full Stack Engineer (Virtual Desktops)
    # ============================================================
    {
        "company": "Neverinstall",
        "contact_name": "Founder/CTO",
        "contact_role": "Technical Decision Maker",
        "channel": "linkedin",
        "subject": "Your Full Stack Engineer role at Neverinstall",
        "body": (
            "Hi,\n\n"
            "Saw that Neverinstall is hiring a Full Stack Engineer (3+ Yrs, Bengaluru, 25-30 LPA) "
            "for your virtual desktop platform.\n\n"
            "We're an engineering team at Inowix Technologies. We build cloud-native platforms "
            "with complex backend architectures — the kind of systems that power virtual desktops, "
            "real-time streaming, and multi-tenant infrastructure. We've delivered similar "
            "products for startups in the compute-as-a-service space.\n\n"
            "Given that you're early-stage and building core product infrastructure, I thought "
            "it may be worth exploring whether we could supplement your engineering capacity "
            "while you focus on product development.\n\n"
            "Would you be open to a quick 15-minute technical discussion?\n\n"
            "Best,\n"
            "Vansh\n"
            "Inowix Technologies"
        ),
        "source_url": "https://wellfound.com/role/l/full-stack-engineer/india",
        "beacon_reason": "ACTIVELY HIRING Full Stack Engineer for virtual desktop platform. Early stage, 11-50 employees. Bengaluru, 25-30 LPA.",
        "trigger": "Full Stack Engineer (3+ Yrs, Bengaluru, 25-30 LPA)",
        "requirement": "Full-stack development for virtual desktop platform. Likely need: cloud infrastructure, real-time streaming, multi-tenant architecture.",
        "service_match": "SaaS Development — Cloud Architecture / Full-Stack Engineering",
        "outsourcing_angle": "Early-stage building complex infrastructure. A dedicated engineering team can accelerate development while they validate product-market fit.",
        "cta": "15-minute technical discovery call",
    },

    # ============================================================
    # 3. Benovymed Healthcare — Hiring AI Conversational Chatbot Developer
    # ============================================================
    {
        "company": "Benovymed Healthcare",
        "contact_name": "CTO/VP Engineering",
        "contact_role": "Technical Decision Maker",
        "channel": "email",
        "subject": "Your AI Conversational Chatbot Developer role at Benovymed",
        "body": (
            "Hi,\n\n"
            "Saw that Benovymed Healthcare is hiring an AI Conversational Chatbot Developer "
            "(1-4 Yrs, across Jaipur + Ludhiana + Delhi). The role requires Python, deep learning, "
            "Rasa, and Dialogflow — and you've posted it in 3 cities, which suggests this is "
            "a growing priority.\n\n"
            "We're an engineering team at Inowix Technologies. We build AI-powered chatbots "
            "and conversational systems — including healthcare-grade patient interaction flows, "
            "appointment booking bots, and symptom qualification engines. We've shipped similar "
            "systems for healthcare providers.\n\n"
            "Given that you're scaling this capability across multiple locations, I thought it "
            "may be worth exploring whether we could deliver this as a managed service — "
            "faster than the hiring cycle, with production-grade AI from day one.\n\n"
            "Would you be open to a quick 15-minute technical discussion?\n\n"
            "Best,\n"
            "Vansh\n"
            "Inowix Technologies"
        ),
        "source_url": "https://www.naukri.com/benovymed-healthcare-jobs-careers-4521446",
        "beacon_reason": "ACTIVELY HIRING AI Conversational Chatbot Developer in 3 cities. Requirements: Python, deep learning, Rasa, Dialogflow. Healthcare company scaling chatbot capability.",
        "trigger": "AI Conversational Chatbot Developer (1-4 Yrs, 3 cities)",
        "requirement": "Python + deep learning + Rasa + Dialogflow chatbot for healthcare. Likely need: patient interaction, appointment booking, symptom qualification.",
        "service_match": "COMAI — AI Chatbot Development (healthcare-grade)",
        "outsourcing_angle": "Hiring across 3 cities suggests urgency. A managed chatbot service delivers production-grade AI without the 3-6 month hiring + training cycle.",
        "cta": "15-minute technical discovery call",
    },

    # ============================================================
    # 4. Twixor — Hiring Chatbot Developer (NLP, Rasa, Cloud)
    # ============================================================
    {
        "company": "Twixor",
        "contact_name": "CTO/Engineering Lead",
        "contact_role": "Technical Decision Maker",
        "channel": "email",
        "subject": "Your Chatbot Developer role at Twixor",
        "body": (
            "Hi,\n\n"
            "Saw that Twixor is hiring a Chatbot Developer (1-5 Yrs, Chennai) with Rasa, "
            "dialogue management, NLP, cloud services, and business process automation.\n\n"
            "We're an engineering team at Inowix Technologies. We build conversational AI "
            "systems with deep NLP capabilities — Rasa-based dialogue engines, intent "
            "classification pipelines, and cloud-native deployment. We've delivered similar "
            "systems for businesses automating customer engagement.\n\n"
            "Given that you're building business process automation through chatbots, I thought "
            "it may be worth exploring whether we could augment your engineering capacity "
            "on this stack — without the overhead of a new hire.\n\n"
            "Would you be open to a quick 15-minute technical discussion?\n\n"
            "Best,\n"
            "Vansh\n"
            "Inowix Technologies"
        ),
        "source_url": "https://www.naukri.com/twixor-jobs-careers-123667045",
        "beacon_reason": "ACTIVELY HIRING Chatbot Developer in Chennai. Requirements: Rasa, dialogue management, NLP, cloud services, business process automation. 2 active job postings.",
        "trigger": "Chatbot Developer (1-5 Yrs, Chennai)",
        "requirement": "Rasa + NLP + cloud-based chatbot for business process automation. Likely need: dialogue management, intent classification, cloud deployment.",
        "service_match": "COMAI — Conversational AI / Chatbot Development",
        "outsourcing_angle": "Building NLP-powered automation requires specialized skills. A dedicated chatbot team delivers faster than hiring, with production-grade dialogue management.",
        "cta": "15-minute technical discovery call",
    },

    # ============================================================
    # 5. BotSpace — Hiring Full Stack Engineer (WhatsApp Platform)
    # ============================================================
    {
        "company": "BotSpace",
        "contact_name": "Founder/CTO",
        "contact_role": "Technical Decision Maker",
        "channel": "linkedin",
        "subject": "Your Full Stack Engineer role at BotSpace",
        "body": (
            "Hi,\n\n"
            "Saw that BotSpace is hiring a Full Stack Engineer (3+ Yrs, Remote India, 6-9 LPA) "
            "for your WhatsApp growth platform — 'We help businesses grow faster with WhatsApp.'\n\n"
            "We're an engineering team at Inowix Technologies. We build WhatsApp automation "
            "systems — Business API integrations, chatbot flows, cart recovery sequences, "
            "and conversational commerce pipelines. We've shipped similar WhatsApp-first "
            "products for D2C brands.\n\n"
            "Given that you're building WhatsApp growth tools, I thought it may be worth "
            "exploring whether we could support your platform development as an extension "
            "of your team — especially on the WhatsApp API integration layer.\n\n"
            "Would you be open to a quick 15-minute technical discussion?\n\n"
            "Best,\n"
            "Vansh\n"
            "Inowix Technologies"
        ),
        "source_url": "https://wellfound.com/role/l/full-stack-engineer/india",
        "beacon_reason": "ACTIVELY HIRING Full Stack Engineer for WhatsApp growth platform. Early stage, 11-50 employees. Remote India.",
        "trigger": "Full Stack Engineer (3+ Yrs, Remote India, 6-9 LPA)",
        "requirement": "Full-stack development for WhatsApp automation platform. Likely need: WhatsApp Business API, chatbot flows, conversation management.",
        "service_match": "COMAI — WhatsApp Automation / Platform Development",
        "outsourcing_angle": "Early-stage WhatsApp platform. A dedicated engineering team can accelerate API integration and flow development while they focus on growth.",
        "cta": "15-minute technical discovery call",
    },

    # ============================================================
    # 6. Autodraft — Hiring Full-Stack + Front-End Engineer (AI Platform)
    # ============================================================
    {
        "company": "Autodraft",
        "contact_name": "Founder/CTO",
        "contact_role": "Technical Decision Maker",
        "channel": "linkedin",
        "subject": "Your Full-Stack + Front-End Engineer roles at Autodraft",
        "body": (
            "Hi,\n\n"
            "Saw that Autodraft is hiring both a Full-Stack Engineer and a Front-End Engineer "
            "(1+ Yrs, Bengaluru, 10-14 LPA) for your AI platform for cartoon animators.\n\n"
            "We're an engineering team at Inowix Technologies. We build AI-powered platforms "
            "with complex frontend requirements — real-time rendering, media processing "
            "pipelines, and creative tool interfaces. We've delivered similar products "
            "for startups building AI-first creative tools.\n\n"
            "Given that you're hiring for two engineering roles simultaneously, I thought "
            "it may be worth exploring whether we could fill both capacity gaps as a "
            "dedicated team — faster than two separate hires.\n\n"
            "Would you be open to a quick 15-minute technical discussion?\n\n"
            "Best,\n"
            "Vansh\n"
            "Inowix Technologies"
        ),
        "source_url": "https://wellfound.com/role/l/full-stack-engineer/india",
        "beacon_reason": "ACTIVELY HIRING Full-Stack Engineer + Front-End Engineer simultaneously. AI platform for animators. Bengaluru, 10-14 LPA. 11-50 employees.",
        "trigger": "Full-Stack Engineer + Front-End Engineer (2 roles, Bengaluru)",
        "requirement": "Full-stack + frontend for AI creative platform. Likely need: React/frontend, media processing, real-time rendering.",
        "service_match": "SaaS Development — Full-Stack + Frontend Engineering",
        "outsourcing_angle": "Hiring 2 engineers simultaneously suggests urgent capacity need. A dedicated team fills both gaps faster than parallel hiring cycles.",
        "cta": "15-minute technical discovery call",
    },

    # ============================================================
    # 7. Relevance Lab — Hiring Chatbot Developer (C#, Microsoft Bot Framework)
    # ============================================================
    {
        "company": "Relevance Lab",
        "contact_name": "VP Engineering/CTO",
        "contact_role": "Technical Decision Maker",
        "channel": "email",
        "subject": "Your Chatbot Developer role at Relevance Lab",
        "body": (
            "Hi,\n\n"
            "Saw that Relevance Lab is hiring a Chatbot Developer (3-11 Yrs, Gurugram) with "
            "C#, Microsoft Bot Framework, web technologies, and architecture.\n\n"
            "We're an engineering team at Inowix Technologies. We build enterprise-grade "
            "chatbot systems — including Microsoft Bot Framework integrations, .NET-based "
            "conversational AI, and Azure-deployed dialogue engines. We've delivered similar "
            "enterprise chatbot solutions.\n\n"
            "Given that you need someone with deep Bot Framework experience (3-11 Yrs), "
            "I thought it may be worth exploring whether we could provide that specialized "
            "capability as a dedicated team — without the 3-6 month search for a senior hire.\n\n"
            "Would you be open to a quick 15-minute technical discussion?\n\n"
            "Best,\n"
            "Vansh\n"
            "Inowix Technologies"
        ),
        "source_url": "https://www.naukri.com/relevance-lab-jobs-careers-1030826",
        "beacon_reason": "ACTIVELY HIRING Chatbot Developer (3-11 Yrs, Gurugram). Requirements: C#, Microsoft Bot Framework, architecture. 113 employee reviews, 3.5 rating.",
        "trigger": "Chatbot Developer (3-11 Yrs, Gurugram)",
        "requirement": "C# + Microsoft Bot Framework + Azure chatbot. Likely need: enterprise-grade conversational AI, architecture design, .NET integration.",
        "service_match": "COMAI — Enterprise Chatbot Development (Bot Framework)",
        "outsourcing_angle": "Senior-level Bot Framework developers (3-11 Yrs) are scarce and expensive. A specialized team provides that depth immediately.",
        "cta": "15-minute technical discovery call",
    },

    # ============================================================
    # 8. S3b Global Technologies — Hiring Chatbot Developer (Gen AI, LLMs)
    # ============================================================
    {
        "company": "S3b Global Technologies",
        "contact_name": "CTO/Engineering Lead",
        "contact_role": "Technical Decision Maker",
        "channel": "email",
        "subject": "Your Chatbot Developer role at S3b Global",
        "body": (
            "Hi,\n\n"
            "Saw that S3b Global Technologies is hiring a Chatbot Developer (5-8 Yrs, "
            "Bengaluru + Gurugram) with Gen AI tools, LLMs, Python, and DevOps.\n\n"
            "We're an engineering team at Inowix Technologies. We build LLM-powered chatbot "
            "systems — RAG pipelines, fine-tuned models, production deployment with DevOps "
            "automation. We've shipped similar Gen AI conversational products.\n\n"
            "Given that you need someone with Gen AI + LLM expertise (5-8 Yrs), I thought "
            "it may be worth exploring whether we could deliver this capability as a managed "
            "service — production-grade Gen AI chatbots without the hiring overhead.\n\n"
            "Would you be open to a quick 15-minute technical discussion?\n\n"
            "Best,\n"
            "Vansh\n"
            "Inowix Technologies"
        ),
        "source_url": "https://www.naukri.com/s3bglobal-technologies-jobs-careers-5012656",
        "beacon_reason": "ACTIVELY HIRING Chatbot Developer (5-8 Yrs, 2 cities). Requirements: Gen AI tools, LLMs, Python, DevOps. Two active job postings.",
        "trigger": "Chatbot Developer (5-8 Yrs, Bengaluru + Gurugram)",
        "requirement": "Gen AI + LLM + Python + DevOps chatbot. Likely need: RAG pipelines, LLM integration, production deployment.",
        "service_match": "COMAI — Gen AI Chatbot Development",
        "outsourcing_angle": "Gen AI + LLM engineers are in high demand. A dedicated team provides production-grade Gen AI capability without the 6-month hiring cycle.",
        "cta": "15-minute technical discovery call",
    },

    # ============================================================
    # 9. Overture Rede — Hiring Chatbot Developers (Azure, ASP.Net, MVC)
    # ============================================================
    {
        "company": "Overture Rede",
        "contact_name": "VP Engineering/CTO",
        "contact_role": "Technical Decision Maker",
        "channel": "email",
        "subject": "Your Chatbot Developers role at Overture Rede",
        "body": (
            "Hi,\n\n"
            "Saw that Overture Rede is hiring Chatbot Developers for Conversational AI "
            "(3-6 Yrs, Mumbai) with Azure, ASP.Net, MVC, and Agile.\n\n"
            "We're an engineering team at Inowix Technologies. We build enterprise chatbot "
            "systems on Microsoft stacks — Azure Bot Service, ASP.Net backend, MVC architecture, "
            "and agile delivery. We've delivered similar conversational AI solutions for "
            "enterprise clients.\n\n"
            "Given that you need Azure + .Net chatbot expertise, I thought it may be worth "
            "exploring whether we could provide that specialized capability as a dedicated "
            "team — faster than the hiring cycle for this niche skillset.\n\n"
            "Would you be open to a quick 15-minute technical discussion?\n\n"
            "Best,\n"
            "Vansh\n"
            "Inowix Technologies"
        ),
        "source_url": "https://www.naukri.com/overture-rede-jobs-careers-634375",
        "beacon_reason": "ACTIVELY HIRING Chatbot Developers for Conversational AI (3-6 Yrs, Mumbai). Requirements: Azure, ASP.Net, MVC, Agile. 32 employee reviews, 3.8 rating.",
        "trigger": "Chatbot Developers for Conversational AI (3-6 Yrs, Mumbai)",
        "requirement": "Azure + ASP.Net + MVC chatbot for enterprise conversational AI. Likely need: Azure Bot Service, .NET backend, agile delivery.",
        "service_match": "COMAI — Enterprise Chatbot (Azure/.Net Stack)",
        "outsourcing_angle": "Azure + .Net chatbot developers are a niche skillset. A specialized team provides that expertise immediately, without the search overhead.",
        "cta": "15-minute technical discovery call",
    },
]


def main():
    output_file = PROJECT_ROOT / "exports" / "outreach_drafts_9_test.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(DRAFTS, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(DRAFTS)} outreach drafts to {output_file}")

    # Print formatted drafts
    for i, draft in enumerate(DRAFTS, 1):
        print(f"\n{'#'*70}")
        print(f"# DRAFT {i}: {draft['company']}")
        print(f"{'#'*70}")
        print(f"\nTO: {draft['contact_name']} ({draft['contact_role']})")
        print(f"CHANNEL: {draft['channel']}")
        print(f"\nSUBJECT: {draft['subject']}")
        print(f"\n{draft['body']}")
        print(f"\n--- METADATA ---")
        print(f"SOURCE: {draft['source_url']}")
        print(f"TRIGGER: {draft['trigger']}")
        print(f"REQUIREMENT: {draft['requirement']}")
        print(f"SERVICE: {draft['service_match']}")
        print(f"OUTSOURCING: {draft['outsourcing_angle']}")


if __name__ == "__main__":
    main()
