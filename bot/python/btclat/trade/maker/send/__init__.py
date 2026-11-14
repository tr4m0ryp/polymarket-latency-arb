"""The sender process: inserts and cancels signed and sent outside the event loop's process."""
from .remote import RemoteOps

__all__ = ["RemoteOps"]
