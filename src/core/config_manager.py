"""
Configuration Management System
==============================

This module handles all configuration-related operations for the WhatsApp Auto-Agent.
It provides a centralized way to load, validate, and manage configuration settings
from various sources including JSON files, environment variables, and default values.

The ConfigManager class implements the Singleton pattern to ensure consistent
configuration access across the entire application.
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

from ..exceptions.custom_exceptions import ConfigurationError
from ..utils.validators import validate_config_file, validate_skip_list


@dataclass
class BotSettings:
    """
    Data class for bot-specific configuration settings.
    
    This class encapsulates all bot behavior settings with type hints
    and default values, making configuration management more robust.
    """
    name: str = "WhatsApp Auto Agent"
    version: str = "1.0.0"
    auto_reply_enabled: bool = True
    use_ai_responses: bool = True
    fallback_message: str = "Thank you for your message. I'll get back to you soon! 🤖"
    response_templates: Dict[str, str] = field(default_factory=dict)


@dataclass
class AISettings:
    """
    Configuration for AI response generation.
    
    Contains parameters for controlling AI behavior including temperature,
    token limits, and system prompts for consistent response generation.
    """
    temperature: float = 0.7
    max_tokens: int = 150
    system_prompt: str = "You are a helpful WhatsApp assistant."
    context_memory: int = 5
    model_name: str = "gpt-4o"


@dataclass
class BrowserSettings:
    """
    Browser automation configuration settings.
    
    Defines timeouts, retry attempts, and other browser-related parameters
    for robust web automation.
    """
    implicit_wait: int = 10
    explicit_wait: int = 20
    retry_attempts: int = 3
    headless: bool = False
    user_agent: str = ""
    timeout: int = 30


class ConfigManager:
    """
    Centralized configuration management system.
    
    This class implements the Singleton pattern to ensure that configuration
    is loaded once and consistently accessed throughout the application.
    It handles loading from multiple sources with proper precedence.
    
    Configuration Loading Priority:
    1. Environment variables (highest priority)
    2. JSON configuration files
    3. Default values (lowest priority)
    """
    
    _instance: Optional['ConfigManager'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'ConfigManager':
        """
        Implement Singleton pattern for configuration manager.
        
        Ensures only one instance of ConfigManager exists throughout
        the application lifecycle.
        """
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        Initialize configuration manager.
        
        Only performs initialization once, even if called multiple times
        due to Singleton pattern implementation.
        """
        if not self._initialized:
            self._config_data: Dict[str, Any] = {}
            self._skip_list: Dict[str, Any] = {}
            self._env_loaded: bool = False
            
            # Configuration file paths
            self.base_path = Path(__file__).parent.parent.parent
            self.config_path = self.base_path / "config" / "settings.json"
            self.skip_list_path = self.base_path / "data" / "skip_list.json"
            self.env_path = self.base_path / ".env"
            
            # Initialize configuration
            asyncio.create_task(self._initialize_config())
            ConfigManager._initialized = True
    
    async def _initialize_config(self) -> None:
        """
        Initialize configuration from all sources.
        
        Loads configuration with proper error handling and validation.
        This method is called asynchronously to avoid blocking initialization.
        """
        try:
            await self._load_environment_variables()
            await self._load_config_file()
            await self._load_skip_list()
            await self._validate_configuration()
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize configuration: {str(e)}")
    
    async def _load_environment_variables(self) -> None:
        """
        Load configuration from environment variables.
        
        Environment variables take highest precedence and can override
        any settings from configuration files.
        """
        if self.env_path.exists():
            load_dotenv(self.env_path)
            self._env_loaded = True
        
        # Load critical environment variables
        env_config = {
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
            'openai_base_url': os.getenv('OPENAI_BASE_URL'),
            'openai_model': os.getenv('OPENAI_MODEL'),
            'bot_name': os.getenv('BOT_NAME'),
            'reply_delay_min': self._safe_int_convert(os.getenv('REPLY_DELAY_MIN')),
            'reply_delay_max': self._safe_int_convert(os.getenv('REPLY_DELAY_MAX')),
            'cooldown_period': self._safe_int_convert(os.getenv('COOLDOWN_PERIOD')),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'browser_headless': os.getenv('BROWSER_HEADLESS', 'false').lower() == 'true'
        }
        
        # Store non-None values
        self._config_data['environment'] = {k: v for k, v in env_config.items() if v is not None}
    
    async def _load_config_file(self) -> None:
        """
        Load configuration from JSON file.
        
        Validates the configuration file structure and loads settings
        with proper error handling.
        """
        if not self.config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {self.config_path}")
        
        is_valid, error_message, config_data = validate_config_file(str(self.config_path))
        
        if not is_valid:
            raise ConfigurationError(f"Invalid configuration file: {error_message}")
        
        self._config_data['file'] = config_data
    
    async def _load_skip_list(self) -> None:
        """
        Load skip list configuration.
        
        Skip list determines which contacts should be excluded from
        auto-reply functionality.
        """
        if not self.skip_list_path.exists():
            # Create default skip list if it doesn't exist
            default_skip_list = {
                "skip_contacts": {
                    "by_name": [],
                    "by_phone": [],
                    "by_keywords": []
                },
                "skip_groups": [],
                "skip_conditions": {
                    "skip_if_contains": ["urgent", "emergency"],
                    "skip_business_hours": False,
                    "skip_weekends": False
                }
            }
            
            # Create directory if it doesn't exist
            self.skip_list_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.skip_list_path, 'w', encoding='utf-8') as f:
                json.dump(default_skip_list, f, indent=2)
            
            self._skip_list = default_skip_list
        else:
            with open(self.skip_list_path, 'r', encoding='utf-8') as f:
                self._skip_list = json.load(f)
        
        # Validate skip list format
        is_valid, errors = validate_skip_list(self._skip_list)
        if not is_valid:
            raise ConfigurationError(f"Invalid skip list configuration: {'; '.join(errors)}")
    
    async def _validate_configuration(self) -> None:
        """
        Validate the loaded configuration for completeness and correctness.
        
        Performs comprehensive validation to ensure all required settings
        are present and have valid values.
        """
        # Check for required API keys
        if not self.get_openai_api_key():
            raise ConfigurationError("OpenAI API key is required but not found in configuration")
        
        # Validate bot settings
        bot_settings = self.get_bot_settings()
        if not bot_settings.name:
            raise ConfigurationError("Bot name cannot be empty")
        
        # Validate AI settings
        ai_settings = self.get_ai_settings()
        if not (0.0 <= ai_settings.temperature <= 2.0):
            raise ConfigurationError("AI temperature must be between 0.0 and 2.0")
        
        if ai_settings.max_tokens <= 0:
            raise ConfigurationError("AI max_tokens must be positive")
    
    def _safe_int_convert(self, value: str) -> Optional[int]:
        """
        Safely convert string to integer.
        
        Args:
            value (str): String value to convert
            
        Returns:
            Optional[int]: Converted integer or None if conversion fails
        """
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def get_openai_api_key(self) -> str:
        """
        Get OpenAI API key from configuration.
        
        Returns:
            str: OpenAI API key
        """
        return (
            self._config_data.get('environment', {}).get('openai_api_key') or
            os.getenv('OPENAI_API_KEY', '')
        )
    
    def get_openai_base_url(self) -> str:
        """
        Get OpenAI base URL for API calls.
        
        Returns:
            str: Base URL for OpenAI API
        """
        return (
            self._config_data.get('environment', {}).get('openai_base_url') or
            os.getenv('OPENAI_BASE_URL', 'https://api.clarifai.com/v2/ext/openai/v1')
        )
    
    def get_openai_model(self) -> str:
        """
        Get OpenAI model identifier.
        
        Returns:
            str: Model identifier for API calls
        """
        return (
            self._config_data.get('environment', {}).get('openai_model') or
            os.getenv('OPENAI_MODEL', 'https://clarifai.com/openai/chat-completion/models/gpt-4o')
        )
    
    def get_bot_settings(self) -> BotSettings:
        """
        Get consolidated bot settings.
        
        Merges settings from environment variables and configuration file,
        with environment variables taking precedence.
        
        Returns:
            BotSettings: Bot configuration object
        """
        file_bot_settings = self._config_data.get('file', {}).get('bot_settings', {})
        env_settings = self._config_data.get('environment', {})
        
        return BotSettings(
            name=env_settings.get('bot_name') or file_bot_settings.get('name', 'WhatsApp Auto Agent'),
            version=file_bot_settings.get('version', '1.0.0'),
            auto_reply_enabled=file_bot_settings.get('auto_reply_enabled', True),
            use_ai_responses=file_bot_settings.get('use_ai_responses', True),
            fallback_message=file_bot_settings.get('fallback_message', 'Thank you for your message!'),
            response_templates=file_bot_settings.get('response_templates', {})
        )
    
    def get_ai_settings(self) -> AISettings:
        """
        Get AI configuration settings.
        
        Returns:
            AISettings: AI configuration object
        """
        ai_settings = self._config_data.get('file', {}).get('ai_settings', {})
        
        return AISettings(
            temperature=ai_settings.get('temperature', 0.7),
            max_tokens=ai_settings.get('max_tokens', 150),
            system_prompt=ai_settings.get('system_prompt', 'You are a helpful assistant.'),
            context_memory=ai_settings.get('context_memory', 5),
            model_name=self.get_openai_model()
        )
    
    def get_browser_settings(self) -> BrowserSettings:
        """
        Get browser automation settings.
        
        Returns:
            BrowserSettings: Browser configuration object
        """
        browser_settings = self._config_data.get('file', {}).get('browser_settings', {})
        env_settings = self._config_data.get('environment', {})
        
        return BrowserSettings(
            implicit_wait=browser_settings.get('implicit_wait', 10),
            explicit_wait=browser_settings.get('explicit_wait', 20),
            retry_attempts=browser_settings.get('retry_attempts', 3),
            headless=env_settings.get('browser_headless', False),
            user_agent=browser_settings.get('user_agent', ''),
            timeout=browser_settings.get('timeout', 30)
        )
    
    def get_skip_list(self) -> Dict[str, Any]:
        """
        Get skip list configuration.
        
        Returns:
            Dict[str, Any]: Skip list configuration
        """
        return self._skip_list.copy()
    
    def get_reply_delay_range(self) -> tuple[int, int]:
        """
        Get reply delay range for human-like timing.
        
        Returns:
            tuple[int, int]: (min_delay, max_delay) in seconds
        """
        env_settings = self._config_data.get('environment', {})
        return (
            env_settings.get('reply_delay_min', 2),
            env_settings.get('reply_delay_max', 5)
        )
    
    def get_cooldown_period(self) -> int:
        """
        Get cooldown period between messages to same contact.
        
        Returns:
            int: Cooldown period in seconds
        """
        return self._config_data.get('environment', {}).get('cooldown_period', 300)
    
    def is_contact_skipped(self, contact_name: str, phone_number: str = None) -> bool:
        """
        Check if a contact should be skipped based on skip list.
        
        Args:
            contact_name (str): Name of the contact
            phone_number (str, optional): Phone number of the contact
            
        Returns:
            bool: True if contact should be skipped
        """
        skip_contacts = self._skip_list.get('skip_contacts', {})
        
        # Check by name
        skip_names = skip_contacts.get('by_name', [])
        if contact_name.lower() in [name.lower() for name in skip_names]:
            return True
        
        # Check by phone number
        if phone_number:
            skip_phones = skip_contacts.get('by_phone', [])
            if phone_number in skip_phones:
                return True
        
        # Check by keywords
        skip_keywords = skip_contacts.get('by_keywords', [])
        for keyword in skip_keywords:
            if keyword.lower() in contact_name.lower():
                return True
        
        return False
    
    async def reload_configuration(self) -> None:
        """
        Reload configuration from all sources.
        
        Useful for updating configuration without restarting the application.
        """
        await self._initialize_config()
    
    async def update_skip_list(self, new_skip_list: Dict[str, Any]) -> None:
        """
        Update skip list configuration and save to file.
        
        Args:
            new_skip_list (Dict[str, Any]): New skip list configuration
        """
        # Validate new skip list
        is_valid, errors = validate_skip_list(new_skip_list)
        if not is_valid:
            raise ConfigurationError(f"Invalid skip list: {'; '.join(errors)}")
        
        self._skip_list = new_skip_list
        
        # Save to file
        with open(self.skip_list_path, 'w', encoding='utf-8') as f:
            json.dump(new_skip_list, f, indent=2)
