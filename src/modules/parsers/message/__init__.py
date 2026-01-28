"""
Message Processing Module

This module provides processors for extracting information from emails:
- INNMessageProcessor (MessageProcessor): Extracts INN (tax identification numbers)
- DateRangeMessageProcessor (MessageProcessor2): Extracts date ranges

Usage:
    from src.modules.parsers.message import MessageProcessor, MessageProcessor2
    
    # Or use the new names:
    from src.modules.parsers.message import INNMessageProcessor, DateRangeMessageProcessor
"""

from .exceptions import MessageNotFoundError, MessageProcessingError
from .index_manager import MessageIndexManager
from .base import BaseMessageProcessor
from .inn_processor import INNMessageProcessor, MessageProcessor
from .date_processor import DateRangeMessageProcessor, MessageProcessor2

__all__ = [
    # New class names
    'INNMessageProcessor',
    'DateRangeMessageProcessor',
    'BaseMessageProcessor',
    'MessageIndexManager',
    
    # Backward compatibility aliases
    'MessageProcessor',
    'MessageProcessor2',
    
    # Exceptions
    'MessageNotFoundError',
    'MessageProcessingError',
]
