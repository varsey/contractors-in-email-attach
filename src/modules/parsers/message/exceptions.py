"""
Custom exceptions for message processing module.
"""


class MessageNotFoundError(Exception):
    """Exception raised when a message ID is not found in the database."""
    pass


class MessageProcessingError(Exception):
    """Exception raised when message processing fails."""
    pass
