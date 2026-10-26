"""Permission grants defined by the health-data service.

Consumers declare the grant in their manifest::

    [[services.v2.consumes]]
    service = "github.com/imbue-openhost/health-data-service-spec"
    shortname = "health"
    version = ">=0.1.0"
    grants = ["read"]

Providers must refuse service calls that don't carry it (see ``readme.md``).
"""

from __future__ import annotations

# Read access to every endpoint of the service: metrics, time series, sleep sessions, and workouts.
READ_GRANT = "read"


class PermissionRequiredError(Exception):
    """A provider refused the call because the consumer lacks a grant.

    ``grant_url`` is the owner-facing approval page the router adds to the 403, when present.
    """

    def __init__(self, required_grant: dict) -> None:
        self.required_grant = required_grant
        self.grant_url: str | None = required_grant.get("grant_url")
        super().__init__(
            f"Health-data provider requires grant {required_grant.get('grant')!r}"
            + (f"; approve it at {self.grant_url}" if self.grant_url else "")
        )


def raise_for_permission_required(status_code: int, body: object) -> None:
    """Raise :class:`PermissionRequiredError` if a response is a ``permission_required`` 403."""
    if status_code != 403 or not isinstance(body, dict) or body.get("error") != "permission_required":
        return
    required_grant = body.get("required_grant")
    raise PermissionRequiredError(required_grant if isinstance(required_grant, dict) else {})
