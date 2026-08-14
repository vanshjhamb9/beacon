"""Source Evidence Validator — CTO Hotfix.

Validates that source URLs point to exact, verifiable original content.
Rejects generic pages, search results, category pages, and placeholders.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse


class SourceStatus(Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    NEEDS_REVIEW = "NEEDS_REVIEW"


@dataclass
class ValidationResult:
    status: SourceStatus
    rejection_reason: str = ""
    platform: str = ""
    url_type: str = ""


# ── GENERIC URL PATTERNS (INSTANT REJECT) ───────────────────────────

REDDIT_GENERIC = [
    r"reddit\.com/r/\w+/?$",  # subreddit page
    r"reddit\.com/r/\w+/top",
    r"reddit\.com/r/\w+/hot",
    r"reddit\.com/r/\w+/new",
    r"reddit\.com/r/\w+/search",
    r"reddit\.com/r/\w+/about",
    r"reddit\.com/r/\w+/wiki",
    r"reddit\.com/user/\w+/?$",  # user page only, no post
]

REDDIT_VALID = [
    r"reddit\.com/r/\w+/comments/",  # exact post
    r"reddit\.com/r/\w+/s/",  # short link
]

LINKEDIN_GENERIC = [
    r"linkedin\.com/company/[^/]+/?$",  # company page only
    r"linkedin\.com/in/[^/]+/?$",  # profile only (no post)
    r"linkedin\.com/search/",  # search page
    r"linkedin\.com/jobs/",  # jobs page
    r"linkedin\.com/feed/",  # feed
    r"linkedin\.com/groups/",  # groups
]

LINKEDIN_VALID = [
    r"linkedin\.com/posts/",  # exact post
    r"linkedin\.com/feed/update/",  # feed update with post
    r"linkedin\.com/pulse/",  # article
]

UPWORK_GENERIC = [
    r"upwork\.com/freelance-jobs/?$",  # category page
    r"upwork\.com/hire/?$",  # hire page
    r"upwork\.com/hire/[^/]+/?$",  # hire category
    r"upwork\.com/freelance-jobs/[^/]+/?$",  # job category
    r"upwork\.com/blog/",  # blog
    r"upwork\.com/resources/",  # resources
]

UPWORK_VALID = [
    r"upwork\.com/jobs/~",  # exact job
    r"upwork\.com/ab/jobs/search/",  # search results (may contain projects)
]

FIVERR_GENERIC = [
    r"fiverr\.com/categories/",  # category
    r"fiverr\.com/search/",  # search
    r"fiverr\.com/ sellers/",  # sellers page
    r"fiverr\.com/",  # homepage
]

FIVERR_VALID = [
    r"fiverr\.com/[^/]+/[^/]+",  # specific gig (needs manual review)
]

PRODUCTHUNT_GENERIC = [
    r"producthunt\.com/?$",  # homepage
    r"producthunt\.com/topics/",  # topics
    r"producthunt\.com/categories/",  # categories
    r"producthunt\.com/lists/",  # lists
]

PRODUCTHUNT_VALID = [
    r"producthunt\.com/posts/",  # exact post
    r"producthunt\.com/products/",  # product page (may contain maker requests)
]

TWITTER_GENERIC = [
    r"(twitter|x)\.com/[^/]+/?$",  # profile only
    r"(twitter|x)\.com/search",  # search
    r"(twitter|x)\.com/hashtag/",  # hashtag
]

TWITTER_VALID = [
    r"(twitter|x)\.com/[^/]+/status/",  # exact tweet
]

INDIEHACKERS_GENERIC = [
    r"indiehackers\.com/?$",  # homepage
    r"indiehackers\.com/products$",  # products list
]

INDIEHACKERS_VALID = [
    r"indiehackers\.com/post/",  # exact post
    r"indiehackers\.com/product/",  # product page with posts
]


def _matches_any(url: str, patterns: list[str]) -> bool:
    """Check if URL matches any regex pattern."""
    for pattern in patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return True
    return False


def _detect_platform(url: str) -> str:
    """Detect the platform from URL."""
    domain = urlparse(url).netloc.lower()
    if "reddit.com" in domain:
        return "reddit"
    elif "linkedin.com" in domain:
        return "linkedin"
    elif "upwork.com" in domain:
        return "upwork"
    elif "fiverr.com" in domain:
        return "fiverr"
    elif "producthunt.com" in domain:
        return "producthunt"
    elif "twitter.com" in domain or "x.com" in domain:
        return "twitter"
    elif "indiehackers.com" in domain:
        return "indiehackers"
    elif "github.com" in domain:
        return "github"
    elif "wellfound.com" in domain or "angel.co" in domain:
        return "wellfound"
    return "other"


def validate_source_url(url: str) -> ValidationResult:
    """Validate a source URL against CTO evidence rules.

    Returns VALID if URL points to exact original content.
    Returns INVALID if URL is generic, placeholder, or unverifiable.
    Returns NEEDS_REVIEW if uncertain.
    """
    if not url or not url.strip():
        return ValidationResult(
            status=SourceStatus.INVALID,
            rejection_reason="MISSING_URL",
            url_type="missing",
        )

    url = url.strip()
    platform = _detect_platform(url)

    # Check for placeholder/synthetic URLs
    placeholder_indicators = [
        "example.com",
        "placeholder",
        "fake",
        "synthetic",
        "generated",
        "todo",
        "xxx",
        "dummy",
    ]
    for indicator in placeholder_indicators:
        if indicator in url.lower():
            return ValidationResult(
                status=SourceStatus.INVALID,
                rejection_reason="PLACEHOLDER_URL",
                platform=platform,
                url_type="placeholder",
            )

    # Platform-specific validation
    if platform == "reddit":
        if _matches_any(url, REDDIT_VALID):
            return ValidationResult(
                status=SourceStatus.VALID,
                platform=platform,
                url_type="exact_post",
            )
        if _matches_any(url, REDDIT_GENERIC):
            return ValidationResult(
                status=SourceStatus.INVALID,
                rejection_reason="GENERIC_REDDIT_URL",
                platform=platform,
                url_type="generic_page",
            )
        return ValidationResult(
            status=SourceStatus.NEEDS_REVIEW,
            platform=platform,
            url_type="unknown_reddit_url",
        )

    elif platform == "linkedin":
        if _matches_any(url, LINKEDIN_VALID):
            return ValidationResult(
                status=SourceStatus.VALID,
                platform=platform,
                url_type="exact_post",
            )
        if _matches_any(url, LINKEDIN_GENERIC):
            return ValidationResult(
                status=SourceStatus.INVALID,
                rejection_reason="GENERIC_LINKEDIN_URL",
                platform=platform,
                url_type="generic_page",
            )
        return ValidationResult(
            status=SourceStatus.NEEDS_REVIEW,
            platform=platform,
            url_type="unknown_linkedin_url",
        )

    elif platform == "upwork":
        if _matches_any(url, UPWORK_VALID):
            return ValidationResult(
                status=SourceStatus.VALID,
                platform=platform,
                url_type="exact_project",
            )
        if _matches_any(url, UPWORK_GENERIC):
            return ValidationResult(
                status=SourceStatus.INVALID,
                rejection_reason="GENERIC_UPWORK_URL",
                platform=platform,
                url_type="generic_page",
            )
        return ValidationResult(
            status=SourceStatus.NEEDS_REVIEW,
            platform=platform,
            url_type="unknown_upwork_url",
        )

    elif platform == "fiverr":
        if _matches_any(url, FIVERR_GENERIC):
            return ValidationResult(
                status=SourceStatus.INVALID,
                rejection_reason="GENERIC_FIVERR_URL",
                platform=platform,
                url_type="generic_page",
            )
        return ValidationResult(
            status=SourceStatus.NEEDS_REVIEW,
            platform=platform,
            url_type="fiverr_gig",
        )

    elif platform == "producthunt":
        if _matches_any(url, PRODUCTHUNT_VALID):
            return ValidationResult(
                status=SourceStatus.VALID,
                platform=platform,
                url_type="exact_post",
            )
        if _matches_any(url, PRODUCTHUNT_GENERIC):
            return ValidationResult(
                status=SourceStatus.INVALID,
                rejection_reason="GENERIC_PRODUCTHUNT_URL",
                platform=platform,
                url_type="generic_page",
            )
        return ValidationResult(
            status=SourceStatus.NEEDS_REVIEW,
            platform=platform,
            url_type="unknown_producthunt_url",
        )

    elif platform == "twitter":
        if _matches_any(url, TWITTER_VALID):
            return ValidationResult(
                status=SourceStatus.VALID,
                platform=platform,
                url_type="exact_tweet",
            )
        if _matches_any(url, TWITTER_GENERIC):
            return ValidationResult(
                status=SourceStatus.INVALID,
                rejection_reason="GENERIC_TWITTER_URL",
                platform=platform,
                url_type="generic_page",
            )
        return ValidationResult(
            status=SourceStatus.NEEDS_REVIEW,
            platform=platform,
            url_type="unknown_twitter_url",
        )

    elif platform == "indiehackers":
        if _matches_any(url, INDIEHACKERS_VALID):
            return ValidationResult(
                status=SourceStatus.VALID,
                platform=platform,
                url_type="exact_post",
            )
        if _matches_any(url, INDIEHACKERS_GENERIC):
            return ValidationResult(
                status=SourceStatus.INVALID,
                rejection_reason="GENERIC_INDIEHACKERS_URL",
                platform=platform,
                url_type="generic_page",
            )
        return ValidationResult(
            status=SourceStatus.NEEDS_REVIEW,
            platform=platform,
            url_type="unknown_indiehackers_url",
        )

    # Non-platform URLs — need manual review
    return ValidationResult(
        status=SourceStatus.NEEDS_REVIEW,
        platform=platform,
        url_type="non_platform_url",
    )
