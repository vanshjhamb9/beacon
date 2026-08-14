"""
AI Reply Drafter for Beacon
Generates contextual replies to outreach responses.
"""
from datetime import datetime
from typing import Optional


class AIReplyDrafter:
    """Generates contextual replies to outreach responses."""

    def __init__(self):
        self.templates = {
            "positive_interest": {
                "keywords": ["interested", "tell me more", "sounds good", "yes", "let's talk"],
                "template": "Thank you for your interest! I'd be happy to discuss how we can help with {requirement}. Would you be available for a quick 15-minute call this week? Let me know what time works best for you.",
            },
            "question": {
                "keywords": ["what", "how", "when", "where", "why", "can you", "do you"],
                "template": "Great question! {answer_placeholder} Happy to provide more details if needed. Would you like to hop on a quick call to discuss further?",
            },
            "pricing_inquiry": {
                "keywords": ["price", "cost", "budget", "how much", "rate"],
                "template": "Thanks for asking about pricing! Our rates depend on the scope and complexity of the project. For a typical {project_type} like yours, we typically work within a range that aligns with your budget. Would you be open to a quick call to discuss your specific needs and provide a tailored quote?",
            },
            "timeline_inquiry": {
                "keywords": ["timeline", "how long", "when can you start", "deadline"],
                "template": "Great question about timelines! For a project like {requirement}, we typically need {estimated_timeline}. We can start as soon as you're ready. Would you like to discuss the timeline in more detail on a call?",
            },
            "technical_question": {
                "keywords": ["technology", "stack", "framework", "language", "api", "database"],
                "template": "Excellent technical question! {technical_answer} We have extensive experience with the technologies relevant to your project. Would you like to discuss the technical approach in more detail?",
            },
            "meeting_request": {
                "keywords": ["call", "meeting", "zoom", "chat", "discuss"],
                "template": "Absolutely! I'd love to connect. You can book a time that works for you here: {calendly_link} or let me know your availability and I'll set something up.",
            },
            "not_interested": {
                "keywords": ["not interested", "no thanks", "pass", "not now", "busy"],
                "template": "No problem at all! If your needs change in the future, feel free to reach out. Best of luck with your project!",
            },
            "generic_positive": {
                "keywords": [],
                "template": "Thank you for your response! I'm glad this is relevant to your needs. Would you like to discuss how we can help with {requirement}? Happy to hop on a quick call at your convenience.",
            },
        }

    def draft_reply(
        self,
        reply_content: str,
        context: Optional[dict] = None,
    ) -> dict:
        """Draft a reply based on the incoming message and context."""
        context = context or {}
        reply_lower = reply_content.lower()

        # Find matching template
        for category, config in self.templates.items():
            if category == "generic_positive":
                continue
            if any(keyword in reply_lower for keyword in config["keywords"]):
                return self._generate_reply(
                    config["template"],
                    context,
                    category,
                )

        # Default to generic positive
        return self._generate_reply(
            self.templates["generic_positive"]["template"],
            context,
            "generic_positive",
        )

    def _generate_reply(
        self,
        template: str,
        context: dict,
        category: str,
    ) -> dict:
        """Generate reply from template with context."""
        requirement = context.get("requirement", "your project")
        project_type = context.get("project_type", "software development project")
        estimated_timeline = context.get("estimated_timeline", "4-8 weeks")
        calendly_link = context.get("calendly_link", "https://calendly.com/inowix")
        technical_answer = context.get("technical_answer", "We use modern, scalable technologies.")

        reply = template.format(
            requirement=requirement,
            project_type=project_type,
            estimated_timeline=estimated_timeline,
            calendly_link=calendly_link,
            technical_answer=technical_answer,
            answer_placeholder="I'd be happy to elaborate on that point.",
        )

        return {
            "reply": reply,
            "category": category,
            "confidence": 0.85,
            "personalization_points": [
                f"Based on your interest in {requirement}",
                "Tailored to your specific needs",
            ],
        }

    def analyze_sentiment(self, content: str) -> dict:
        """Analyze sentiment of incoming message."""
        content_lower = content.lower()

        positive_words = ["interested", "great", "good", "excellent", "love", "happy", "yes", "thanks"]
        negative_words = ["not interested", "no thanks", "pass", "busy", "spam", "stop"]
        question_words = ["what", "how", "when", "where", "why", "can you", "do you"]

        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        question_count = sum(1 for word in question_words if word in content_lower)

        if negative_count > positive_count:
            sentiment = "negative"
        elif question_count > 0:
            sentiment = "questioning"
        elif positive_count > 0:
            sentiment = "positive"
        else:
            sentiment = "neutral"

        return {
            "sentiment": sentiment,
            "positive_score": positive_count,
            "negative_score": negative_count,
            "question_score": question_count,
        }
