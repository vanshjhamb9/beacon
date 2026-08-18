"""Shared test utilities."""

from __future__ import annotations

import os

from fastapi.routing import APIRoute


API_PREFIX = os.environ.get("API_PREFIX", "/api/v1")


def get_all_routes(app) -> list[APIRoute]:
    """Recursively flatten all APIRoute objects from an app's routes."""
    routes: list[APIRoute] = []
    seen: set[int] = set()

    def _walk(obj):
        router = obj
        if hasattr(obj, "original_router"):
            router = obj.original_router
        elif hasattr(obj, "routes"):
            router = obj
        else:
            return

        for route in getattr(router, "routes", []):
            rid = id(route)
            if rid in seen:
                continue
            seen.add(rid)
            if isinstance(route, APIRoute):
                routes.append(route)
            else:
                _walk(route)

    _walk(app)
    return routes


def get_route_paths(app) -> set[str]:
    """Get all route paths from an app, including the API prefix."""
    return {API_PREFIX + r.path for r in get_all_routes(app)}


def get_tagged_routes(app, tag: str) -> list[APIRoute]:
    """Get all routes with a specific tag."""
    return [r for r in get_all_routes(app) if r.tags and tag in r.tags]
