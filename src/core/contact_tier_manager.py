"""
Contact Tier Management System
=============================

This module manages the 3-tier contact categorization system:
1. MAIN CONTACTS - VIP treatment with notifications and informative replies
2. TIME PASS - Casual contacts with basic auto-replies  
3. NOT IMPORTANT - Low priority contacts, log only

Provides functionality to categorize contacts, manage tiers, and determine
appropriate response behavior based on contact importance.
"""

import json
import asyncio
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from ..exceptions.custom_exceptions import ConfigurationError
from ..utils.helpers import sanitize_phone_number, clean_message_text


class ContactTier(Enum):
    """
    Enumeration for contact priority tiers.
    
    Defines the three main categories for contact management
    with clear priority levels for different response behaviors.
    """
    MAIN_CONTACTS = "main_contacts"      # VIP - Full attention
    TIME_PASS = "time_pass_contacts"     # Casual - Basic replies  
    NOT_IMPORTANT = "not_important"      # Low priority - Log only


@dataclass
class ContactSettings:
    """
    Settings configuration for each contact tier.
    
    Defines behavior parameters for how the agent should
    handle contacts in each tier category.
    """
    open_and_read: bool = False
    play_sound: bool = False
    reply_mode: str = "none"  # 'informative_ai', 'template_basic', 'none'
    mark_as_read: bool = False
    priority_level: str = "low"  # 'high', 'medium', 'low'


@dataclass 
class ContactInfo:
    """
    Contact information with tier classification.
    
    Stores contact details along with their assigned tier
    and associated behavior settings.
    """
    name: str
    phone: str
    tier: ContactTier
    settings: ContactSettings
    last_interaction: Optional[str] = None


class ContactTierManager:
    """
    Manages contact categorization and tier-based behaviors.
    
    This class handles:
    - Loading and saving contact tier configurations
    - Categorizing contacts into appropriate tiers
    - Providing tier-specific behavior settings
    - Managing dynamic tier assignments
    - Handling unknown/new contacts
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize contact tier manager.
        
        Args:
            config_path (str, optional): Custom path to contact categories config
        """
        # Set up paths
        self.base_path = Path(__file__).parent.parent.parent
        self.config_path = Path(config_path) if config_path else self.base_path / "data" / "contact_categories.json"
        self.templates_path = self.base_path / "data" / "message_templates.json"
        
        # Initialize data structures
        self.contact_tiers: Dict[str, Any] = {}
        self.message_templates: Dict[str, Any] = {}
        self.contact_cache: Dict[str, ContactInfo] = {}
        
        # Load configurations
        asyncio.create_task(self._load_configurations())
    
    async def _load_configurations(self) -> None:
        """
        Load contact tiers and message templates from configuration files.
        
        Initializes the contact categorization system with default values
        if configuration files don't exist.
        """
        try:
            await self._load_contact_tiers()
            await self._load_message_templates()
        except Exception as e:
            raise ConfigurationError(f"Failed to load contact tier configurations: {str(e)}")
    
    async def _load_contact_tiers(self) -> None:
        """
        Load contact tier configuration from JSON file.
        
        Creates default configuration if file doesn't exist.
        """
        if not self.config_path.exists():
            # Create default configuration
            default_config = {
                "contact_tiers": {
                    "main_contacts": {
                        "description": "VIP contacts - Full attention with notifications",
                        "by_name": [],
                        "by_phone": [],
                        "settings": {
                            "open_and_read": True,
                            "play_sound": True,
                            "reply_mode": "informative_ai",
                            "mark_as_read": True,
                            "priority_level": "high"
                        }
                    },
                    "time_pass_contacts": {
                        "description": "Casual contacts - Basic auto-replies",
                        "by_name": [],
                        "by_phone": [],
                        "settings": {
                            "open_and_read": False,
                            "play_sound": False,
                            "reply_mode": "template_basic",
                            "mark_as_read": True,
                            "priority_level": "medium"
                        }
                    },
                    "not_important": {
                        "description": "Low priority - Log only, no replies",
                        "by_name": [],
                        "by_phone": [],
                        "by_keywords": ["promotion", "spam", "offer"],
                        "settings": {
                            "open_and_read": False,
                            "play_sound": False,
                            "reply_mode": "none",
                            "mark_as_read": False,
                            "priority_level": "low"
                        }
                    }
                },
                "default_settings": {
                    "uncategorized_contacts": "not_important",
                    "new_contact_behavior": "ask_user",
                    "auto_categorize": False
                }
            }
            
            # Create directory and file
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            
            self.contact_tiers = default_config
        else:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.contact_tiers = json.load(f)
    
    async def _load_message_templates(self) -> None:
        """
        Load message templates for different contact tiers.
        
        Creates default templates if file doesn't exist.
        """
        if not self.templates_path.exists():
            # Create default templates
            default_templates = {
                "templates": {
                    "main_contacts": {
                        "greeting": "Hi! Thanks for reaching out. I'm currently using an auto-assistant but I'll respond personally soon! 😊",
                        "informative": "I've received your message and will get back to you shortly with a proper response.",
                        "busy": "I'm currently busy, but I saw your message. Will respond as soon as I'm free! 🚀"
                    },
                    "time_pass_contacts": {
                        "default": "Hey! Thanks for the message. I'll get back to you when I can! 👍",
                        "greeting": "Hello! Auto-reply here - I'll respond when I'm available!"
                    },
                    "not_important": {
                        "none": ""
                    }
                },
                "ai_prompts": {
                    "main_contacts": "You are responding to a VIP contact. Be personal, informative, and helpful.",
                    "time_pass_contacts": "You are responding to a casual contact. Be friendly but brief.",
                    "not_important": "No response needed."
                }
            }
            
            with open(self.templates_path, 'w', encoding='utf-8') as f:
                json.dump(default_templates, f, indent=2)
            
            self.message_templates = default_templates
        else:
            with open(self.templates_path, 'r', encoding='utf-8') as f:
                self.message_templates = json.load(f)
    
    def categorize_contact(self, contact_name: str, phone_number: str = None) -> Tuple[ContactTier, ContactSettings]:
        """
        Categorize a contact into appropriate tier.
        
        Checks contact against all tier criteria and returns the matching
        tier with its associated settings.
        
        Args:
            contact_name (str): Name of the contact
            phone_number (str, optional): Phone number of the contact
            
        Returns:
            Tuple[ContactTier, ContactSettings]: Contact tier and settings
        """
        # Clean inputs
        clean_name = contact_name.lower().strip()
        clean_phone = sanitize_phone_number(phone_number) if phone_number else None
        
        # Check each tier in priority order
        tier_priority = [
            ContactTier.MAIN_CONTACTS,
            ContactTier.TIME_PASS, 
            ContactTier.NOT_IMPORTANT
        ]
        
        for tier in tier_priority:
            if self._is_contact_in_tier(clean_name, clean_phone, tier):
                settings = self._get_tier_settings(tier)
                return tier, settings
        
        # Default handling for uncategorized contacts
        default_tier_name = self.contact_tiers.get("default_settings", {}).get(
            "uncategorized_contacts", "not_important"
        )
        default_tier = ContactTier(default_tier_name)
        default_settings = self._get_tier_settings(default_tier)
        
        return default_tier, default_settings
    
    def _is_contact_in_tier(self, contact_name: str, phone_number: str, tier: ContactTier) -> bool:
        """
        Check if contact belongs to specific tier.
        
        Args:
            contact_name (str): Contact name (already cleaned)
            phone_number (str): Phone number (already cleaned)
            tier (ContactTier): Tier to check against
            
        Returns:
            bool: True if contact belongs to tier
        """
        tier_data = self.contact_tiers.get("contact_tiers", {}).get(tier.value, {})
        
        # Check by name
        tier_names = [name.lower().strip() for name in tier_data.get("by_name", [])]
        if contact_name in tier_names:
            return True
        
        # Check by phone number
        if phone_number:
            tier_phones = [sanitize_phone_number(phone) for phone in tier_data.get("by_phone", [])]
            if phone_number in tier_phones:
                return True
        
        # Check by keywords (mainly for NOT_IMPORTANT tier)
        keywords = tier_data.get("by_keywords", [])
        for keyword in keywords:
            if keyword.lower() in contact_name:
                return True
        
        return False
    
    def _get_tier_settings(self, tier: ContactTier) -> ContactSettings:
        """
        Get settings configuration for specific tier.
        
        Args:
            tier (ContactTier): Contact tier
            
        Returns:
            ContactSettings: Settings for the tier
        """
        tier_data = self.contact_tiers.get("contact_tiers", {}).get(tier.value, {})
        settings_data = tier_data.get("settings", {})
        
        return ContactSettings(
            open_and_read=settings_data.get("open_and_read", False),
            play_sound=settings_data.get("play_sound", False),
            reply_mode=settings_data.get("reply_mode", "none"),
            mark_as_read=settings_data.get("mark_as_read", False),
            priority_level=settings_data.get("priority_level", "low")
        )
    
    def get_contact_info(self, contact_name: str, phone_number: str = None) -> ContactInfo:
        """
        Get comprehensive contact information including tier and settings.
        
        Args:
            contact_name (str): Contact name
            phone_number (str, optional): Contact phone number
            
        Returns:
            ContactInfo: Complete contact information
        """
        # Check cache first
        cache_key = f"{contact_name}:{phone_number or 'no_phone'}"
        if cache_key in self.contact_cache:
            return self.contact_cache[cache_key]
        
        # Categorize contact
        tier, settings = self.categorize_contact(contact_name, phone_number)
        
        # Create contact info
        contact_info = ContactInfo(
            name=contact_name,
            phone=phone_number or "",
            tier=tier,
            settings=settings
        )
        
        # Cache the result
        self.contact_cache[cache_key] = contact_info
        
        return contact_info
    
    def should_reply_to_contact(self, contact_name: str, phone_number: str = None) -> bool:
        """
        Determine if agent should reply to this contact.
        
        Args:
            contact_name (str): Contact name
            phone_number (str, optional): Contact phone number
            
        Returns:
            bool: True if should reply, False otherwise
        """
        contact_info = self.get_contact_info(contact_name, phone_number)
        return contact_info.settings.reply_mode != "none"
    
    def should_play_notification(self, contact_name: str, phone_number: str = None) -> bool:
        """
        Determine if agent should play notification sound.
        
        Args:
            contact_name (str): Contact name
            phone_number (str, optional): Contact phone number
            
        Returns:
            bool: True if should play sound, False otherwise
        """
        contact_info = self.get_contact_info(contact_name, phone_number)
        return contact_info.settings.play_sound
    
    def should_open_and_read(self, contact_name: str, phone_number: str = None) -> bool:
        """
        Determine if agent should open and read the message.
        
        Args:
            contact_name (str): Contact name
            phone_number (str, optional): Contact phone number
            
        Returns:
            bool: True if should open and read, False otherwise
        """
        contact_info = self.get_contact_info(contact_name, phone_number)
        return contact_info.settings.open_and_read
    
    def get_reply_template(self, contact_name: str, phone_number: str = None, template_type: str = "default") -> str:
        """
        Get appropriate message template for contact tier.
        
        Args:
            contact_name (str): Contact name
            phone_number (str, optional): Contact phone number
            template_type (str): Type of template needed
            
        Returns:
            str: Message template text
        """
        contact_info = self.get_contact_info(contact_name, phone_number)
        tier_templates = self.message_templates.get("templates", {}).get(contact_info.tier.value, {})
        
        # Try to get specific template, fall back to default
        return tier_templates.get(template_type) or tier_templates.get("default", "")
    
    def get_ai_prompt(self, contact_name: str, phone_number: str = None) -> str:
        """
        Get AI prompt for generating responses to this contact tier.
        
        Args:
            contact_name (str): Contact name
            phone_number (str, optional): Contact phone number
            
        Returns:
            str: AI system prompt for this tier
        """
        contact_info = self.get_contact_info(contact_name, phone_number)
        return self.message_templates.get("ai_prompts", {}).get(
            contact_info.tier.value, 
            "You are a helpful assistant."
        )
    
    async def add_contact_to_tier(self, contact_name: str, phone_number: str, tier: ContactTier) -> bool:
        """
        Add contact to specific tier.
        
        Args:
            contact_name (str): Contact name
            phone_number (str): Contact phone number
            tier (ContactTier): Target tier
            
        Returns:
            bool: True if successfully added
        """
        try:
            tier_data = self.contact_tiers.setdefault("contact_tiers", {}).setdefault(tier.value, {})
            
            # Add to name list if not already present
            names_list = tier_data.setdefault("by_name", [])
            if contact_name not in names_list:
                names_list.append(contact_name)
            
            # Add to phone list if phone provided and not already present
            if phone_number:
                phones_list = tier_data.setdefault("by_phone", [])
                clean_phone = sanitize_phone_number(phone_number)
                if clean_phone not in phones_list:
                    phones_list.append(clean_phone)
            
            # Save configuration
            await self._save_contact_tiers()
            
            # Clear cache for this contact
            cache_key = f"{contact_name}:{phone_number or 'no_phone'}"
            if cache_key in self.contact_cache:
                del self.contact_cache[cache_key]
            
            return True
            
        except Exception as e:
            raise ConfigurationError(f"Failed to add contact to tier: {str(e)}")
    
    async def remove_contact_from_tier(self, contact_name: str, phone_number: str, tier: ContactTier) -> bool:
        """
        Remove contact from specific tier.
        
        Args:
            contact_name (str): Contact name
            phone_number (str): Contact phone number  
            tier (ContactTier): Source tier
            
        Returns:
            bool: True if successfully removed
        """
        try:
            tier_data = self.contact_tiers.get("contact_tiers", {}).get(tier.value, {})
            
            # Remove from name list
            names_list = tier_data.get("by_name", [])
            if contact_name in names_list:
                names_list.remove(contact_name)
            
            # Remove from phone list
            if phone_number:
                phones_list = tier_data.get("by_phone", [])
                clean_phone = sanitize_phone_number(phone_number)
                if clean_phone in phones_list:
                    phones_list.remove(clean_phone)
            
            # Save configuration
            await self._save_contact_tiers()
            
            # Clear cache
            cache_key = f"{contact_name}:{phone_number or 'no_phone'}"
            if cache_key in self.contact_cache:
                del self.contact_cache[cache_key]
            
            return True
            
        except Exception as e:
            raise ConfigurationError(f"Failed to remove contact from tier: {str(e)}")
    
    async def _save_contact_tiers(self) -> None:
        """
        Save contact tiers configuration to file.
        """
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.contact_tiers, f, indent=2, ensure_ascii=False)
    
    def get_tier_statistics(self) -> Dict[str, int]:
        """
        Get statistics about contacts in each tier.
        
        Returns:
            Dict[str, int]: Count of contacts per tier
        """
        stats = {}
        
        for tier_name, tier_data in self.contact_tiers.get("contact_tiers", {}).items():
            name_count = len(tier_data.get("by_name", []))
            phone_count = len(tier_data.get("by_phone", []))
            stats[tier_name] = {
                "by_name": name_count,
                "by_phone": phone_count,
                "total": name_count + phone_count
            }
        s
        return stats
    
    def clear_contact_cache(self) -> None:
        """
        Clear the contact information cache.
        
        Useful when configuration changes and cache needs refresh.
        """
        self.contact_cache.clear()
