"""
Notification Management System
=============================

This module handles sound notifications and system alerts for different
contact tiers and message types. Provides cross-platform notification
support with customizable sounds and behaviors.
"""

import os
import asyncio
import platform
from pathlib import Path
from typing import Optional, Dict, Any
import threading
from dataclasses import dataclass

from ..exceptions.custom_exceptions import ConfigurationError


@dataclass
class NotificationConfig:
    """
    Configuration for notification behavior.
    
    Defines how notifications should be played including
    sound files, volume levels, and timing.
    """
    sound_file: Optional[str] = None
    volume: float = 0.7  # 0.0 to 1.0
    duration: float = 2.0  # seconds
    repeat_count: int = 1
    enabled: bool = True


class NotificationManager:
    """
    Cross-platform notification system for contact alerts.
    
    Handles playing notification sounds, system alerts, and visual
    notifications based on contact tier and message importance.
    """
    
    def __init__(self, sounds_directory: str = None):
        """
        Initialize notification manager.
        
        Args:
            sounds_directory (str, optional): Custom sounds directory path
        """
        # Set up paths  
        self.base_path = Path(__file__).parent.parent.parent
        self.sounds_dir = Path(sounds_directory) if sounds_directory else self.base_path / "sounds"
        self.sounds_dir.mkdir(parents=True, exist_ok=True)
        
        # Detect platform for appropriate notification method
        self.platform = platform.system().lower()
        
        # Initialize notification configurations for different tiers
        self.tier_notifications = {
            "main_contacts": NotificationConfig(
                sound_file="vip_notification.wav",
                volume=0.8,
                duration=3.0,
                repeat_count=2,
                enabled=True
            ),
            "time_pass_contacts": NotificationConfig(
                sound_file="casual_notification.wav", 
                volume=0.5,
                duration=1.5,
                repeat_count=1,
                enabled=False  # Usually disabled for casual contacts
            ),
            "not_important": NotificationConfig(
                enabled=False  # No notifications for unimportant contacts
            )
        }
        
        # Initialize sound playing capability
        self._initialize_sound_system()
    
    def _initialize_sound_system(self) -> None:
        """
        Initialize sound playing system based on platform.
        
        Sets up appropriate sound playing mechanisms for different
        operating systems with fallback options.
        """
        self.sound_available = False
        
        try:
            if self.platform == "windows":
                import winsound
                self.sound_method = "winsound"
                self.sound_available = True
                
            elif self.platform == "darwin":  # macOS
                # Check if afplay is available
                if os.system("which afplay > /dev/null 2>&1") == 0:
                    self.sound_method = "afplay"
                    self.sound_available = True
                    
            elif self.platform == "linux":
                # Check for available sound players
                sound_players = ["paplay", "aplay", "play"]
                for player in sound_players:
                    if os.system(f"which {player} > /dev/null 2>&1") == 0:
                        self.sound_method = player
                        self.sound_available = True
                        break
            
            # Fallback: Try to import pygame for cross-platform support
            if not self.sound_available:
                try:
                    import pygame
                    pygame.mixer.init()
                    self.sound_method = "pygame"
                    self.sound_available = True
                except ImportError:
                    pass
                    
        except Exception as e:
            print(f"Warning: Could not initialize sound system: {e}")
            self.sound_available = False
    
    async def play_notification(self, tier: str, message_content: str = "", contact_name: str = "") -> bool:
        """
        Play notification sound for specific contact tier.
        
        Args:
            tier (str): Contact tier name
            message_content (str, optional): Message content for context
            contact_name (str, optional): Contact name for personalization
            
        Returns:
            bool: True if notification was played successfully
        """
        if not self.sound_available:
            return False
        
        notification_config = self.tier_notifications.get(tier)
        if not notification_config or not notification_config.enabled:
            return False
        
        try:
            # Play notification in separate thread to avoid blocking
            sound_thread = threading.Thread(
                target=self._play_sound_sync,
                args=(notification_config, contact_name),
                daemon=True
            )
            sound_thread.start()
            
            # Also show system notification if available
            await self._show_system_notification(tier, message_content, contact_name)
            
            return True
            
        except Exception as e:
            print(f"Error playing notification: {e}")
            return False
    
    def _play_sound_sync(self, config: NotificationConfig, contact_name: str = "") -> None:
        """
        Play sound synchronously in separate thread.
        
        Args:
            config (NotificationConfig): Notification configuration
            contact_name (str, optional): Contact name for logging
        """
        try:
            sound_file = self.sounds_dir / config.sound_file if config.sound_file else None
            
            # If custom sound file doesn't exist, use system default
            if not sound_file or not sound_file.exists():
                sound_file = self._get_default_sound()
            
            if not sound_file:
                return
            
            # Play sound based on available method
            for _ in range(config.repeat_count):
                if self.sound_method == "winsound":
                    import winsound
                    winsound.PlaySound(str(sound_file), winsound.SND_FILENAME)
                    
                elif self.sound_method == "afplay":
                    os.system(f"afplay '{sound_file}'")
                    
                elif self.sound_method in ["paplay", "aplay", "play"]:
                    os.system(f"{self.sound_method} '{sound_file}' > /dev/null 2>&1")
                    
                elif self.sound_method == "pygame":
                    import pygame
                    pygame.mixer.music.load(str(sound_file))
                    pygame.mixer.music.set_volume(config.volume)
                    pygame.mixer.music.play()
                    
                    # Wait for sound to finish
                    while pygame.mixer.music.get_busy():
                        pygame.time.wait(100)
                
                # Brief pause between repeats
                if config.repeat_count > 1:
                    import time
                    time.sleep(0.5)
                    
        except Exception as e:
            print(f"Error in sound playback: {e}")
    
    def _get_default_sound(self) -> Optional[Path]:
        """
        Get default system notification sound.
        
        Returns:
            Optional[Path]: Path to default sound file
        """
        try:
            if self.platform == "windows":
                # Windows system sounds
                system_sounds = [
                    "C:\\Windows\\Media\\notify.wav",
                    "C:\\Windows\\Media\\Windows Notify.wav"
                ]
                for sound in system_sounds:
                    if os.path.exists(sound):
                        return Path(sound)
                        
            elif self.platform == "darwin":
                # macOS system sounds
                system_sounds = [
                    "/System/Library/Sounds/Glass.aiff",
                    "/System/Library/Sounds/Ping.aiff"
                ]
                for sound in system_sounds:
                    if os.path.exists(sound):
                        return Path(sound)
                        
            elif self.platform == "linux":
                # Linux system sounds
                system_sounds = [
                    "/usr/share/sounds/alsa/Front_Left.wav",
                    "/usr/share/sounds/notification.wav"
                ]
                for sound in system_sounds:
                    if os.path.exists(sound):
                        return Path(sound)
                        
        except Exception:
            pass
        
        return None
    
    async def _show_system_notification(self, tier: str, message_content: str, contact_name: str) -> None:
        """
        Show system desktop notification.
        
        Args:
            tier (str): Contact tier
            message_content (str): Message content
            contact_name (str): Contact name
        """
        try:
            title = f"WhatsApp from {contact_name}" if contact_name else "WhatsApp Message"
            
            # Truncate message for notification
            display_message = message_content[:100] + "..." if len(message_content) > 100 else message_content
            
            if self.platform == "windows":
                # Windows 10+ notifications
                try:
                    import win10toast
                    toaster = win10toast.ToastNotifier()
                    toaster.show_toast(
                        title,
                        display_message,
                        duration=5,
                        threaded=True
                    )
                except ImportError:
                    pass
                    
            elif self.platform == "darwin":
                # macOS notifications
                os.system(f'''
                    osascript -e 'display notification "{display_message}" with title "{title}"'
                ''')
                
            elif self.platform == "linux":
                # Linux desktop notifications
                os.system(f'notify-send "{title}" "{display_message}"')
                
        except Exception as e:
            print(f"Error showing system notification: {e}")
    
    def set_tier_notification_config(self, tier: str, config: NotificationConfig) -> None:
        """
        Update notification configuration for specific tier.
        
        Args:
            tier (str): Contact tier name
            config (NotificationConfig): New notification configuration
        """
        self.tier_notifications[tier] = config
    
    def enable_notifications_for_tier(self, tier: str, enabled: bool = True) -> None:
        """
        Enable or disable notifications for specific tier.
        
        Args:
            tier (str): Contact tier name
            enabled (bool): Whether to enable notifications
        """
        if tier in self.tier_notifications:
            self.tier_notifications[tier].enabled = enabled
    
    def test_notification(self, tier: str = "main_contacts") -> bool:
        """
        Test notification system with specified tier.
        
        Args:
            tier (str): Tier to test notification for
            
        Returns:
            bool: True if test was successful
        """
        try:
            asyncio.create_task(
                self.play_notification(
                    tier, 
                    "This is a test notification", 
                    "Test Contact"
                )
            )
            return True
        except Exception as e:
            print(f"Notification test failed: {e}")
            return False
    
    def get_notification_status(self) -> Dict[str, Any]:
        """
        Get current notification system status.
        
        Returns:
            Dict[str, Any]: Notification system status information
        """
        return {
            "sound_available": self.sound_available,
            "platform": self.platform,
            "sound_method": getattr(self, 'sound_method', 'none'),
            "sounds_directory": str(self.sounds_dir),
            "tier_configs": {
                tier: {
                    "enabled": config.enabled,
                    "sound_file": config.sound_file,
                    "volume": config.volume
                }
                for tier, config in self.tier_notifications.items()
            }
        }
