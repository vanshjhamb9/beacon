from context_engine.rules.definitions import ContextRule, ContextRuleCatalog, ContextRuleCategory


def default_context_rules() -> ContextRuleCatalog:
    return ContextRuleCatalog(
        [
            ContextRule(
                key="pain.support_pressure",
                name="Support pressure from support or complaint signals",
                category=ContextRuleCategory.PAIN,
                priority=10,
                conditions={"categories": ["customer_support", "customer_complaints"]},
                outputs={"pain": "customer_support", "department": "support"},
                explanation="Support-related signals indicate customer experience or support capacity pressure.",
            ),
            ContextRule(
                key="pain.hiring_scaling",
                name="Scaling pain from hiring signals",
                category=ContextRuleCategory.PAIN,
                priority=20,
                conditions={"categories": ["hiring"], "terms": ["hiring", "open role", "recruiting"]},
                outputs={"pain": "hiring", "department": "operations"},
                explanation="Hiring activity often indicates growth, capacity constraints, or operational scaling.",
            ),
            ContextRule(
                key="goal.expand_market",
                name="Expansion goal from office or market expansion",
                category=ContextRuleCategory.GOAL,
                priority=30,
                conditions={"categories": ["expansion"], "terms": ["office", "market", "expands"]},
                outputs={"goal": "market_expansion"},
                explanation="Expansion signals suggest a goal to enter or scale new markets.",
            ),
            ContextRule(
                key="trigger.capital_event",
                name="Funding as buying trigger",
                category=ContextRuleCategory.TRIGGER,
                priority=40,
                conditions={"categories": ["funding"]},
                outputs={"trigger": "new_budget_window"},
                explanation="Funding events create budget availability and operational change windows.",
            ),
            ContextRule(
                key="impact.technology_change",
                name="Technology migration impact",
                category=ContextRuleCategory.IMPACT,
                priority=50,
                conditions={"categories": ["technology_migration", "ai_adoption", "automation"]},
                outputs={"impact": "technology_operating_model_change"},
                explanation="Technology adoption and migration signals affect operating model and tooling needs.",
            ),
            ContextRule(
                key="stage.solution_exploring",
                name="Solution exploration stage",
                category=ContextRuleCategory.STAGE,
                priority=60,
                conditions={"categories": ["technology_migration", "automation", "ai_adoption"]},
                outputs={"buying_stage": "solution_exploring", "decision_stage": "team_discussion"},
                explanation="Technology change language usually indicates active solution exploration.",
            ),
            ContextRule(
                key="dna.ai_readiness",
                name="AI readiness from AI vendor or AI adoption terms",
                category=ContextRuleCategory.DNA,
                priority=70,
                conditions={"terms": ["ai", "openai", "anthropic", "gemini", "llm"]},
                outputs={"ai_readiness": 18, "innovation_score": 12},
                explanation="AI-related evidence increases AI readiness and innovation posture.",
            ),
        ]
    )
