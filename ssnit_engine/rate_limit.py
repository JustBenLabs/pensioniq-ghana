from collections import defaultdict, deque
from math import ceil
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request, status


class RateLimiter:
    """
    Simple in-memory rate limiter for PensionIQ Ghana.

    Note:
    This is suitable for the current single-instance MVP.
    Later, for multiple backend instances, we should move
    rate-limit state to Redis or another shared store.
    """

    def __init__(
        self,
        *,
        name: str,
        limit: int,
        window_seconds: int,
    ):
        self.name = name
        self.limit = limit
        self.window_seconds = window_seconds

        self._requests = defaultdict(deque)
        self._lock = Lock()

    def _get_client_ip(
        self,
        request: Request,
    ) -> str:
        forwarded_for = request.headers.get(
            "x-forwarded-for"
        )

        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        if request.client:
            return request.client.host

        return "unknown"

    def reset(self) -> None:
        """
        Clear all stored rate-limit history.

        Primarily used by automated tests so each
        test starts with a clean limiter state.
        """
        with self._lock:
            self._requests.clear()

    async def __call__(
        self,
        request: Request,
    ) -> None:
        client_ip = self._get_client_ip(request)

        key = (
            self.name,
            client_ip,
        )

        now = monotonic()

        with self._lock:
            timestamps = self._requests[key]

            while (
                timestamps
                and
                now - timestamps[0]
                >= self.window_seconds
            ):
                timestamps.popleft()

            if len(timestamps) >= self.limit:
                retry_after = ceil(
                    self.window_seconds
                    -
                    (
                        now
                        -
                        timestamps[0]
                    )
                )

                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=(
                        "Too many requests. "
                        "Please try again later."
                    ),
                    headers={
                        "Retry-After": str(
                            max(retry_after, 1)
                        )
                    },
                )

            timestamps.append(now)


login_rate_limit = RateLimiter(
    name="login",
    limit=10,
    window_seconds=300,
)

register_rate_limit = RateLimiter(
    name="register",
    limit=5,
    window_seconds=900,
)

forgot_password_rate_limit = RateLimiter(
    name="forgot-password",
    limit=5,
    window_seconds=900,
)

reset_password_rate_limit = RateLimiter(
    name="reset-password",
    limit=5,
    window_seconds=900,
)