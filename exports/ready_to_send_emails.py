"""Ready-to-send email package for the9-person outreach test.

Configure your email client:
- From: vansh@inowix.in
- CC: vanshjhamb9@gmail.com
- Subject and body provided per email below.

Copy-paste each email. Track replies in outreach_tracking_9_test.csv.
"""

# Email configuration
FROM_EMAIL = "vansh@inowix.in"
CC_EMAIL = "vanshjhamb9@gmail.com"

EMAILS = [
    {
        "company": "Oliv AI",
        "to": "careers@olivai.com",
        "channel": "email",
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
        "trigger": "Full Stack Engineer (3+ Yrs, Remote India, 25-45 LPA + equity)",
        "source": "https://wellfound.com/role/l/full-stack-engineer/india",
    },
    {
        "company": "Neverinstall",
        "to": "careers@neverinstall.com",
        "channel": "email",
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
        "trigger": "Full Stack Engineer (3+ Yrs, Bengaluru, 25-30 LPA)",
        "source": "https://wellfound.com/role/l/full-stack-engineer/india",
    },
    {
        "company": "Benovymed Healthcare",
        "to": "hr@benovymed.com",
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
        "trigger": "AI Conversational Chatbot Developer (1-4 Yrs, 3 cities)",
        "source": "https://www.naukri.com/benovymed-healthcare-jobs-careers-4521446",
    },
    {
        "company": "Twixor",
        "to": "careers@twixor.com",
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
        "trigger": "Chatbot Developer (1-5 Yrs, Chennai)",
        "source": "https://www.naukri.com/twixor-jobs-careers-123667045",
    },
    {
        "company": "BotSpace",
        "to": "hello@botspace.com",
        "channel": "email",
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
        "trigger": "Full Stack Engineer (3+ Yrs, Remote India, 6-9 LPA)",
        "source": "https://wellfound.com/role/l/full-stack-engineer/india",
    },
    {
        "company": "Autodraft",
        "to": "careers@autodraft.com",
        "channel": "email",
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
        "trigger": "Full-Stack Engineer + Front-End Engineer (2 roles, Bengaluru)",
        "source": "https://wellfound.com/role/l/full-stack-engineer/india",
    },
    {
        "company": "Relevance Lab",
        "to": "careers@relevancelab.com",
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
        "trigger": "Chatbot Developer (3-11 Yrs, Gurugram)",
        "source": "https://www.naukri.com/relevance-lab-jobs-careers-1030826",
    },
    {
        "company": "S3b Global Technologies",
        "to": "careers@s3bglobal.com",
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
        "trigger": "Chatbot Developer (5-8 Yrs, Bengaluru + Gurugram)",
        "source": "https://www.naukri.com/s3bglobal-technologies-jobs-careers-5012656",
    },
    {
        "company": "Overture Rede",
        "to": "careers@overturerede.com",
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
        "trigger": "Chatbot Developers for Conversational AI (3-6 Yrs, Mumbai)",
        "source": "https://www.naukri.com/overture-rede-jobs-careers-634375",
    },
]
