"""
Configuration for ADK Agent Service
"""

import os
from typing import Dict, Any

class ADKConfig:
    """Configuration class for ADK Agent Service"""
    
    # Model configuration
    DEFAULT_MODEL = "gemini-2.0-flash-exp"  # Using the newer model with better rate limits
    FALLBACK_MODEL = "gemini-1.5-flash"
    
    # Session configuration
    MAX_SESSION_DURATION = 3600  # 1 hour in seconds
    MAX_CONCURRENT_SESSIONS = 100
    
    # Tool configuration
    AVAILABLE_TOOLS = [
        "tavily_search",
        "send_sms"
    ]
    
    # ADK Runner configuration
    ADK_APP_NAME_PREFIX = "adk_platform"
    
    # Logging configuration
    LOG_LEVEL = os.getenv("ADK_LOG_LEVEL", "INFO")
    
    # Performance settings
    MAX_TOKENS_PER_REQUEST = 2048  # Reduced to avoid quota limits
    REQUEST_TIMEOUT = 30  # seconds
    
    @classmethod
    def get_model_config(cls) -> Dict[str, Any]:
        """Get model configuration for ADK agents"""
        return {
            "model": cls.DEFAULT_MODEL,
            "temperature": 0.3,  # Lower temperature for more consistent responses
            "max_tokens": cls.MAX_TOKENS_PER_REQUEST,
            "timeout": cls.REQUEST_TIMEOUT
        }
    
    @classmethod
    def get_runner_config(cls) -> Dict[str, Any]:
        """Get runner configuration for ADK"""
        return {
            "max_concurrent_sessions": cls.MAX_CONCURRENT_SESSIONS,
            "session_timeout": cls.MAX_SESSION_DURATION
        }

# Global ADK configuration instance
adk_config = ADKConfig()
