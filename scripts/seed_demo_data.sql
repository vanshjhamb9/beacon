INSERT INTO companies (id, name, normalized_name, primary_domain, industry, last_seen_at, signal_frequency, memory_summary, attributes, created_at, updated_at, deleted_at)
VALUES (
  '11111111-1111-1111-1111-111111111111',
  'Acme Logistics',
  'acme logistics',
  'acmelogistics.example',
  'logistics',
  NOW(),
  12,
  'Scaling logistics operator showing automation and support pressure.',
  '{"technology_stack":["Salesforce","OpenAI"]}'::jsonb,
  NOW(), NOW(), NULL
) ON CONFLICT DO NOTHING;

INSERT INTO opportunities (
  id, company_id, company_name, status, recommendation,
  opportunity_score, confidence_score, timing_score, urgency_score, narrative,
  created_from_context_ids, score_breakdown, delta, created_at, updated_at, deleted_at
) VALUES (
  '22222222-2222-2222-2222-222222222222',
  '11111111-1111-1111-1111-111111111111',
  'Acme Logistics',
  'high_intent',
  'contact_within_7_days',
  84, 81, 78, 76,
  'Acme Logistics shows rising automation demand after expansion signals.',
  '[]'::jsonb, '{}'::jsonb,
  '{"direction":"increased","score_change":12,"reason":"New automation pain"}'::jsonb,
  NOW(), NOW(), NULL
) ON CONFLICT DO NOTHING;

INSERT INTO solution_matches (
  id, company_id, opportunity_id, primary_service_key, secondary_service_key,
  cross_sell_service_keys, upsell_service_keys, confidence, reasoning, evidence,
  created_at, updated_at, deleted_at
) VALUES (
  '33333333-3333-3333-3333-333333333333',
  '11111111-1111-1111-1111-111111111111',
  '22222222-2222-2222-2222-222222222222',
  'ai_automation', 'api_integration',
  '["custom_ai_development"]'::jsonb, '["comai"]'::jsonb,
  79.5,
  'AI Automation is the strongest deterministic service match for Acme Logistics.',
  '{"opportunity_score":84,"quality_score":88}'::jsonb,
  NOW(), NOW(), NULL
) ON CONFLICT DO NOTHING;

INSERT INTO buyer_personas (id, company_id, solution_match_id, persona, confidence, explanation, evidence, created_at, updated_at, deleted_at)
VALUES (
  '44444444-4444-4444-4444-444444444444',
  '11111111-1111-1111-1111-111111111111',
  '33333333-3333-3333-3333-333333333333',
  'Operations Head', 82,
  'Workflow and operations pains map to Operations Head ownership.',
  '{}'::jsonb, NOW(), NOW(), NULL
) ON CONFLICT DO NOTHING;

INSERT INTO deal_estimates (
  id, solution_match_id, company_id, opportunity_id, project_size, implementation_complexity,
  estimated_budget_range, priority_level, mrr_potential, one_time_revenue, expansion_potential,
  renewal_potential, strategic_account_value, revenue_score, urgency, closing_probability,
  strategic_importance, expected_sales_cycle_days, explanation, created_at, updated_at, deleted_at
) VALUES (
  '55555555-5555-5555-5555-555555555555',
  '33333333-3333-3333-3333-333333333333',
  '11111111-1111-1111-1111-111111111111',
  '22222222-2222-2222-2222-222222222222',
  'medium','medium','medium','high',
  1800, 22000, 9000, 15000, 46000,
  46, 76, 62, 80, 45,
  'Seeded demo estimate', NOW(), NOW(), NULL
) ON CONFLICT DO NOTHING;

INSERT INTO sales_playbooks (
  id, company_id, opportunity_id, solution_match_id, business_pain, recommended_service,
  why, conversation_angle, decision_maker, expected_outcome, risk, playbook,
  created_at, updated_at, deleted_at
) VALUES (
  '66666666-6666-6666-6666-666666666666',
  '11111111-1111-1111-1111-111111111111',
  '22222222-2222-2222-2222-222222222222',
  '33333333-3333-3333-3333-333333333333',
  'automation: manual ops workflows',
  'AI Automation',
  'Opportunity score and operations pain make AI Automation the best fit now.',
  'Validate whether manual ops workflows are a priority this quarter.',
  'Operations Head',
  'Deliver a medium engagement that reduces ops friction.',
  'Budget ownership may be unclear; confirm decision maker early.',
  '{}'::jsonb, NOW(), NOW(), NULL
) ON CONFLICT DO NOTHING;

INSERT INTO company_profiles (
  id, company_id, industry, business_model, company_stage, growth_pattern, technology_stack,
  digital_maturity, ai_adoption, automation_adoption, hiring_pattern, expansion_pattern,
  innovation_score, support_maturity, operational_maturity, technology_maturity, customer_maturity,
  completeness_score, evidence, created_at, updated_at, deleted_at
) VALUES (
  '77777777-7777-7777-7777-777777777777',
  '11111111-1111-1111-1111-111111111111',
  'logistics','b2b','scaling','expansion','["Salesforce","OpenAI"]'::jsonb,
  72,68,74,'active','regional',70,55,60,72,65,78,'{"seed":true}'::jsonb,
  NOW(), NOW(), NULL
) ON CONFLICT DO NOTHING;

SELECT 'companies' AS t, count(*)::int AS n FROM companies
UNION ALL SELECT 'opportunities', count(*)::int FROM opportunities
UNION ALL SELECT 'solution_matches', count(*)::int FROM solution_matches
UNION ALL SELECT 'services', count(*)::int FROM services;
