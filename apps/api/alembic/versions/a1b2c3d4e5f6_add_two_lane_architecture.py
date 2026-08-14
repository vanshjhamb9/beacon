"""Add two-lane architecture with 6-level classification.

Revision ID: a1b2c3d4e5f6
Revises: 07f2c24ee08e
Create Date: 2026-08-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM, JSONB

# revision identifiers
revision = 'a1b2c3d4e5f6'
down_revision = '07f2c24ee08e'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create new enums with IF NOT EXISTS
    
    # Classification enum (6 levels)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE buying_event_classification AS ENUM (
                'ACTIVE_BUYING_EVENT', 'VERIFIED_PAIN', 'ICP_OPPORTUNITY',
                'PARTNER_OPPORTUNITY', 'NURTURE', 'REJECT'
            );
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Business type enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE business_type AS ENUM ('DIRECT_CUSTOMER', 'PARTNER');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Outreach channel enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE outreach_channel AS ENUM (
                'email', 'linkedin', 'whatsapp', 'reddit_dm', 'platform_dm'
            );
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # 2. Add new columns to buying_events table (with IF NOT EXISTS)
    
    # Classification (replaces opportunity_type)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE buying_events ADD COLUMN classification buying_event_classification NOT NULL DEFAULT 'REJECT';
        EXCEPTION WHEN duplicate_column THEN null;
        END $$;
    """)
    
    # Business type (DIRECT_CUSTOMER or PARTNER)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE buying_events ADD COLUMN business_type business_type;
        EXCEPTION WHEN duplicate_column THEN null;
        END $$;
    """)
    
    # Outreach preparation (JSONB for channel-specific drafts)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE buying_events ADD COLUMN outreach_preparation JSONB DEFAULT '{}';
        EXCEPTION WHEN duplicate_column THEN null;
        END $$;
    """)
    
    # CTO test result
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE buying_events ADD COLUMN cto_test_result BOOLEAN NOT NULL DEFAULT false;
        EXCEPTION WHEN duplicate_column THEN null;
        END $$;
    """)
    
    # Pain signals (COMAI-specific)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE buying_events ADD COLUMN pain_signals JSONB DEFAULT '[]';
        EXCEPTION WHEN duplicate_column THEN null;
        END $$;
    """)
    
    # Buying signals (INOWIX-specific)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE buying_events ADD COLUMN buying_signals JSONB DEFAULT '[]';
        EXCEPTION WHEN duplicate_column THEN null;
        END $$;
    """)
    
    # Partner signals
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE buying_events ADD COLUMN partner_signals JSONB DEFAULT '[]';
        EXCEPTION WHEN duplicate_column THEN null;
        END $$;
    """)
    
    # ICP match score
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE buying_events ADD COLUMN icp_match_score FLOAT NOT NULL DEFAULT 0.0;
        EXCEPTION WHEN duplicate_column THEN null;
        END $$;
    """)
    
    # 3. Create outreach_drafts table (if not exists)
    op.execute("""
        CREATE TABLE IF NOT EXISTS outreach_drafts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            buying_event_id UUID NOT NULL REFERENCES buying_events(id),
            channel outreach_channel NOT NULL,
            style VARCHAR(32) NOT NULL,
            subject VARCHAR(500),
            body TEXT NOT NULL,
            personalization_points JSONB DEFAULT '[]',
            evidence_chain JSONB DEFAULT '[]',
            quality_scores JSONB DEFAULT '{}',
            status VARCHAR(32) NOT NULL DEFAULT 'draft',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    
    # 4. Create indexes (if not exists)
    op.execute("""
        DO $$ BEGIN
            CREATE INDEX ix_outreach_drafts_buying_event ON outreach_drafts(buying_event_id);
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE INDEX ix_outreach_drafts_channel ON outreach_drafts(channel);
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE INDEX ix_outreach_drafts_status ON outreach_drafts(status);
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE INDEX ix_buying_events_classification ON buying_events(classification);
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE INDEX ix_buying_events_business_type ON buying_events(business_type);
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # 5. Migrate existing data
    op.execute("""
        UPDATE buying_events 
        SET classification = CASE 
            WHEN opportunity_type = 'DIRECT_CUSTOMER' THEN 'VERIFIED_PAIN'::buying_event_classification
            WHEN opportunity_type = 'PARTNER_OPPORTUNITY' THEN 'PARTNER_OPPORTUNITY'::buying_event_classification
            WHEN opportunity_type = 'NOT_A_BUYING_EVENT' THEN 'REJECT'::buying_event_classification
            ELSE 'REJECT'::buying_event_classification
        END,
        business_type = CASE 
            WHEN opportunity_type = 'DIRECT_CUSTOMER' THEN 'DIRECT_CUSTOMER'::business_type
            WHEN opportunity_type = 'PARTNER_OPPORTUNITY' THEN 'PARTNER'::business_type
            ELSE NULL
        END
        WHERE classification = 'REJECT'::buying_event_classification
    """)
    
    # 6. Clear old false/seed opportunities from active pipeline
    op.execute("""
        UPDATE buying_events 
        SET status = 'DISQUALIFIED',
            disqualification_reason = 'Migrated to two-lane architecture - requires re-evaluation'
        WHERE status = 'VERIFIED'
        AND classification = 'REJECT'::buying_event_classification
    """)


def downgrade():
    # Drop indexes
    op.execute("DROP INDEX IF EXISTS ix_buying_events_business_type")
    op.execute("DROP INDEX IF EXISTS ix_buying_events_classification")
    op.execute("DROP INDEX IF EXISTS ix_outreach_drafts_status")
    op.execute("DROP INDEX IF EXISTS ix_outreach_drafts_channel")
    op.execute("DROP INDEX IF EXISTS ix_outreach_drafts_buying_event")
    
    # Drop tables
    op.execute("DROP TABLE IF EXISTS outreach_drafts")
    
    # Drop columns
    op.execute("ALTER TABLE buying_events DROP COLUMN IF EXISTS icp_match_score")
    op.execute("ALTER TABLE buying_events DROP COLUMN IF EXISTS partner_signals")
    op.execute("ALTER TABLE buying_events DROP COLUMN IF EXISTS buying_signals")
    op.execute("ALTER TABLE buying_events DROP COLUMN IF EXISTS pain_signals")
    op.execute("ALTER TABLE buying_events DROP COLUMN IF EXISTS cto_test_result")
    op.execute("ALTER TABLE buying_events DROP COLUMN IF EXISTS outreach_preparation")
    op.execute("ALTER TABLE buying_events DROP COLUMN IF EXISTS business_type")
    op.execute("ALTER TABLE buying_events DROP COLUMN IF EXISTS classification")
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS outreach_channel")
    op.execute("DROP TYPE IF EXISTS business_type")
    op.execute("DROP TYPE IF EXISTS buying_event_classification")
