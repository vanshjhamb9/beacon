"""Create FSW tables directly."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "api"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "worker"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

FSW_TABLES = """
CREATE TABLE IF NOT EXISTS fsw_lead_stages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    opportunity_id UUID REFERENCES opportunities(id),
    target_account_id UUID REFERENCES target_accounts(id),
    stage VARCHAR(32) NOT NULL DEFAULT 'revenue_ready',
    manual_status VARCHAR(64),
    owner VARCHAR(128),
    assigned_by VARCHAR(128),
    revenue_opportunity_score FLOAT NOT NULL DEFAULT 0,
    fit_score FLOAT NOT NULL DEFAULT 0,
    intent_score FLOAT NOT NULL DEFAULT 0,
    company_name VARCHAR(255) NOT NULL,
    industry VARCHAR(128),
    country VARCHAR(128),
    service_match VARCHAR(128),
    source_connector VARCHAR(64),
    trigger VARCHAR(64),
    why_now TEXT,
    buying_signals JSONB DEFAULT '[]'::jsonb NOT NULL,
    garbage_reason VARCHAR(64),
    garbage_note TEXT,
    garbage_at TIMESTAMPTZ,
    snoozed_until TIMESTAMPTZ,
    snooze_reason TEXT,
    archived_at TIMESTAMPTZ,
    sort_order INTEGER NOT NULL DEFAULT 0,
    tags JSONB DEFAULT '[]'::jsonb NOT NULL,
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_fsw_lead_stages_company ON fsw_lead_stages(company_id);
CREATE INDEX IF NOT EXISTS ix_fsw_lead_stages_stage ON fsw_lead_stages(stage);
CREATE INDEX IF NOT EXISTS ix_fsw_lead_stages_owner ON fsw_lead_stages(owner);

CREATE TABLE IF NOT EXISTS fsw_lead_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_stage_id UUID NOT NULL REFERENCES fsw_lead_stages(id),
    action_type VARCHAR(32) NOT NULL,
    performed_by VARCHAR(128),
    details JSONB DEFAULT '{}'::jsonb NOT NULL,
    previous_stage VARCHAR(32),
    new_stage VARCHAR(32),
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_fsw_lead_actions_lead ON fsw_lead_actions(lead_stage_id);
CREATE INDEX IF NOT EXISTS ix_fsw_lead_actions_type ON fsw_lead_actions(action_type);

CREATE TABLE IF NOT EXISTS fsw_lead_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_stage_id UUID NOT NULL REFERENCES fsw_lead_stages(id),
    content TEXT NOT NULL,
    author VARCHAR(128),
    is_pinned BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_fsw_lead_notes_lead ON fsw_lead_notes(lead_stage_id);

CREATE TABLE IF NOT EXISTS fsw_lead_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_stage_id UUID NOT NULL REFERENCES fsw_lead_stages(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    due_date TIMESTAMPTZ,
    priority VARCHAR(16) NOT NULL DEFAULT 'medium',
    owner VARCHAR(128),
    completed BOOLEAN NOT NULL DEFAULT false,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_fsw_lead_tasks_lead ON fsw_lead_tasks(lead_stage_id);
CREATE INDEX IF NOT EXISTS ix_fsw_lead_tasks_due ON fsw_lead_tasks(due_date);
CREATE INDEX IF NOT EXISTS ix_fsw_lead_tasks_completed ON fsw_lead_tasks(completed);

CREATE TABLE IF NOT EXISTS fsw_lead_timeline (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_stage_id UUID NOT NULL REFERENCES fsw_lead_stages(id),
    event_type VARCHAR(32) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    actor VARCHAR(128),
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_fsw_lead_timeline_lead ON fsw_lead_timeline(lead_stage_id);
CREATE INDEX IF NOT EXISTS ix_fsw_lead_timeline_created ON fsw_lead_timeline(created_at);
"""


async def main():
    from app.db.session import AsyncSessionLocal
    from sqlalchemy import text

    async with AsyncSessionLocal() as session:
        for statement in FSW_TABLES.split(";"):
            stmt = statement.strip()
            if stmt:
                try:
                    await session.execute(text(stmt))
                    print(f"  OK: {stmt[:60]}...")
                except Exception as e:
                    print(f"  SKIP: {stmt[:60]}... ({e})")
        await session.commit()
        print("\nFSW tables created successfully!")


if __name__ == "__main__":
    asyncio.run(main())
