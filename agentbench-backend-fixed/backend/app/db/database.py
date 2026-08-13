"""
Backwards-compatible re-export shim.

The real engine/session/Base now live in app.db.base (see that module for
why). This module is kept because several other modules in the codebase
import `SessionLocal` from `app.db.database` - removing it would mean
touching every call site for no functional benefit.
"""
from app.db.base import Base, SessionLocal, engine  # noqa: F401
