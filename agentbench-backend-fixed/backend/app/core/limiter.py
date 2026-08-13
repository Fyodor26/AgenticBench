"""
Shared rate limiter instance.

Lives in its own module (rather than app.main) so it can be imported by
both app.main (to register it on the FastAPI app) and individual routers
(app.api.auth) without creating a circular import.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
