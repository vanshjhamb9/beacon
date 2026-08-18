from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, SecretStr, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _env_files() -> tuple[str, ...]:
    """Resolve .env from cwd and repo root so alembic works from apps/api."""
    here = Path(__file__).resolve()
    candidates = [
        Path.cwd() / ".env",
        here.parents[4] / ".env",  # repo root: .../New folder
        here.parents[2] / ".env",  # apps/api
    ]
    found = [str(path) for path in candidates if path.is_file()]
    return tuple(dict.fromkeys(found)) or (".env",)


class FeatureFlags(BaseModel):
    collectors_enabled: bool = True
    source_health_monitoring_enabled: bool = True
    request_tracing_enabled: bool = True


class CollectorSourceConfig(BaseModel):
    enabled: bool = True
    interval_seconds: int = Field(default=300, ge=30)
    max_items: int = Field(default=25, ge=1, le=100)
    rate_limit_per_minute: int = Field(default=30, ge=1, le=600)
    retry_attempts: int = Field(default=3, ge=1, le=10)


class RedditCollectorConfig(CollectorSourceConfig):
    subreddits: list[str] = Field(
        default_factory=lambda: [
            "startups",
            "sales",
            "marketing",
            "SaaS",
            "Entrepreneur",
            "smallbusiness",
            "artificial",
            "MachineLearning",
            "netsec",
            "AskNetsec",
            "cybersecurity",
            "sysadmin",
            "msp",
            "ITManagers",
        ]
    )

    @field_validator("subreddits")
    @classmethod
    def validate_subreddits(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip().lower() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("At least one subreddit must be configured.")
        return cleaned


class FeedCollectorConfig(CollectorSourceConfig):
    feed_urls: list[str]

    @field_validator("feed_urls")
    @classmethod
    def validate_feed_urls(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("At least one feed URL must be configured.")
        return cleaned


class GitHubTrendingCollectorConfig(CollectorSourceConfig):
    topics: list[str] = Field(
        default_factory=lambda: ["saas", "startup", "artificial-intelligence", "automation"]
    )
    rate_limit_per_minute: int = Field(default=8, ge=1, le=30)

    @field_validator("topics")
    @classmethod
    def validate_topics(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip().lower() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("At least one GitHub topic must be configured.")
        return cleaned


class PainSignalCollectorConfig(CollectorSourceConfig):
    subreddits: list[str] = Field(
        default_factory=lambda: [
            "shopify",
            "woocommerce",
            "ecommerce",
            "smallbusiness",
            "customerservice",
            "chatbots",
            "pythonhelp",
            "webdev",
            "startups",
            "netsec",
            "AskNetsec",
            "cybersecurity",
            "sysadmin",
            "msp",
        ]
    )
    rate_limit_per_minute: int = Field(default=10, ge=1, le=60)

    @field_validator("subreddits")
    @classmethod
    def validate_subreddits(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip().lower() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("At least one subreddit must be configured.")
        return cleaned


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_files(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
        extra="ignore",
    )

    app_name: str = "Beacon AI API"
    app_version: str = "0.1.0"
    environment: Literal["local", "test", "staging", "production"] = "local"
    debug: bool = False
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"

    docs_url: str | None = "/docs"
    redoc_url: str | None = "/redoc"
    openapi_url: str | None = "/openapi.json"

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "beacon"
    postgres_user: str = "beacon"
    postgres_password: SecretStr = Field(default=SecretStr("beacon_password"))
    database_url: str | None = None
    database_echo: bool = False
    database_pool_size: int = 5
    database_max_overflow: int = 5

    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_url: str | None = None

    jwt_secret_key: SecretStr = Field(default=SecretStr("change-me-in-production"))
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:3002",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://127.0.0.1:3002",
        ]
    )
    feature_flags: FeatureFlags = Field(default_factory=FeatureFlags)

    collector_stream_name: str = "raw-events"
    collector_consumer_group: str = "raw-event-writers"
    collector_consumer_name: str = "worker-1"
    collector_stream_max_length: int = Field(default=100_000, ge=1_000)
    collector_persist_batch_size: int = Field(default=50, ge=1, le=500)

    reddit_collector: RedditCollectorConfig = Field(default_factory=RedditCollectorConfig)
    rss_collector: FeedCollectorConfig = Field(
        default_factory=lambda: FeedCollectorConfig(
            feed_urls=[
                "https://techcrunch.com/feed/",
                "https://www.theverge.com/rss/index.xml",
                "https://feeds.feedburner.com/venturebeat/SZYF",
                "https://www.saastr.com/feed/",
            ]
        )
    )
    hacker_news_collector: FeedCollectorConfig = Field(
        default_factory=lambda: FeedCollectorConfig(
            feed_urls=[
                "https://hnrss.org/frontpage",
                "https://hnrss.org/newest?q=hiring+OR+funding+OR+launch+OR+SaaS",
            ]
        )
    )
    product_hunt_collector: FeedCollectorConfig = Field(
        default_factory=lambda: FeedCollectorConfig(feed_urls=["https://www.producthunt.com/feed"])
    )
    github_trending_collector: GitHubTrendingCollectorConfig = Field(
        default_factory=GitHubTrendingCollectorConfig
    )
    indie_hackers_collector: FeedCollectorConfig = Field(
        default_factory=lambda: FeedCollectorConfig(
            feed_urls=["https://www.indiehackers.com/feed.xml"],
            interval_seconds=600,
        )
    )
    sec_edgar_collector: FeedCollectorConfig = Field(
        default_factory=lambda: FeedCollectorConfig(
            feed_urls=[
                "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=&company=&dateb=&owner=include&count=40&output=atom"
            ],
            interval_seconds=900,
            rate_limit_per_minute=10,
        )
    )
    devto_collector: FeedCollectorConfig = Field(
        default_factory=lambda: FeedCollectorConfig(
            feed_urls=["https://dev.to/feed"],
            interval_seconds=600,
        )
    )
    pain_signals_collector: PainSignalCollectorConfig = Field(
        default_factory=PainSignalCollectorConfig
    )
    acquisition_alert_failure_threshold: int = Field(default=3, ge=1, le=20)
    acquisition_high_value_opportunity_score: float = Field(default=70.0, ge=0.0, le=100.0)

    builtwith_api_key: SecretStr | None = None
    wappalyzer_api_key: SecretStr | None = None
    crunchbase_api_key: SecretStr | None = None
    enrichment_website_fetch_enabled: bool = True
    enrichment_dns_lookup_enabled: bool = True

    apollo_api_key: SecretStr | None = None
    people_data_labs_api_key: SecretStr | None = None
    decision_discovery_licensed_providers_enabled: bool = False

    # AI Sales Copilot — defaults to grounded (no external LLM required)
    sales_copilot_provider: Literal["openai", "anthropic", "gemini", "openrouter", "grounded"] = "grounded"
    sales_copilot_temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    openai_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None
    gemini_api_key: SecretStr | None = None
    openrouter_api_key: SecretStr | None = None
    openai_model: str = "gpt-4o-mini"
    anthropic_model: str = "claude-3-5-haiku-latest"
    gemini_model: str = "gemini-2.0-flash"
    openrouter_model: str = "openrouter/auto"

    # Communication Gateway — sandbox by default; production send double-gated
    communication_mode: Literal["sandbox", "production"] = "sandbox"
    allow_production_send: bool = False
    communication_encryption_key: SecretStr = Field(default=SecretStr("beacon-dev-only-change-me"))
    gmail_client_id: str | None = None
    gmail_client_secret: SecretStr | None = None
    microsoft_client_id: str | None = None
    microsoft_client_secret: SecretStr | None = None
    microsoft_tenant_id: str = "common"
    meta_whatsapp_token: SecretStr | None = None
    meta_whatsapp_phone_number_id: str | None = None
    meta_whatsapp_business_account_id: str | None = None
    meta_whatsapp_app_secret: SecretStr | None = None
    meta_whatsapp_verify_token: SecretStr | None = None
    calendly_api_key: SecretStr | None = None
    oauth_redirect_uri: str = "http://localhost:8000/api/v1/communication/oauth/callback"
    daily_email_quota: int = Field(default=500, ge=1, le=100_000)
    communication_max_retries: int = Field(default=5, ge=1, le=20)

    # Target Account Intelligence — master brain gate for auto pipeline
    target_account_gate_enabled: bool = True
    target_account_top_tier_threshold: float = Field(default=70.0, ge=0.0, le=100.0)
    target_account_mid_tier_threshold: float = Field(default=50.0, ge=0.0, le=100.0)
    target_account_hunter_threshold: float = Field(default=75.0, ge=0.0, le=100.0)

    # Revenue Hunter Mode — founder BD work queue (A+/A campaign gate)
    revenue_hunter_enabled: bool = True
    revenue_hunter_a_plus_threshold: float = Field(default=85.0, ge=0.0, le=100.0)
    revenue_hunter_a_threshold: float = Field(default=70.0, ge=0.0, le=100.0)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url:
            return self.database_url

        password = self.postgres_password.get_secret_value()
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def celery_broker_url(self) -> str:
        return self.redis_dsn

    @computed_field  # type: ignore[prop-decorator]
    @property
    def celery_result_backend(self) -> str:
        return self.redis_dsn

    @computed_field  # type: ignore[prop-decorator]
    @property
    def redis_dsn(self) -> str:
        if self.redis_url:
            return self.redis_url
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
