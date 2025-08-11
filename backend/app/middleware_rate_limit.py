from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from .redis_client import rate_limit


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit: int = 60, window: int = 60):
        super().__init__(app)
        self.limit = limit
        self.window = window

    async def dispatch(self, request, call_next):
        uid = request.headers.get("x-user-id") or request.client.host
        ok = await rate_limit(f"rate:{uid}:{request.url.path}", self.limit, self.window)
        if not ok:
            return JSONResponse({"error": "rate_limited"}, status_code=429)
        return await call_next(request)