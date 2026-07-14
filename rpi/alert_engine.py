#!/usr/bin/env python3
"""
Alert Engine - In-App Notifications via Firebase
Handles alert delivery to dashboard and optional webhooks.
"""

import logging
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class AlertEngine:
    """
    Manages alert notifications.
    
    Primary delivery: Firebase /alerts/{device_id} (polled by dashboard)
    Secondary: Optional webhook (Slack, Discord, etc.)
    """
    
    def __init__(
        self,
        firebase_listener=None,
        webhook_url: Optional[str] = None,
        webhook_secret: Optional[str] = None
    ):
        self.firebase_listener = firebase_listener
        self.webhook_url = webhook_url
        self.webhook_secret = webhook_secret
        
        # Load webhook config from environment if not provided
        if not self.webhook_url:
            import os
            self.webhook_url = os.getenv('ALERT_WEBHOOK_URL')
            self.webhook_secret = os.getenv('ALERT_WEBHOOK_SECRET')
        
        logger.info("🔔 Alert Engine initialized")
        if self.webhook_url:
            logger.info(f"   Webhook: {self.webhook_url[:50]}...")
    
    def send_notification(self, alert_data: Dict[str, Any]) -> bool:
        """
        Send alert notification.
        
        Primary: Write to Firebase /alerts (handled by firebase_listener)
        Secondary: Send webhook if configured
        
        Args:
            alert_data: Dict with alert information
            
        Returns:
            True if at least one delivery succeeded
        """
        success = True
        
        # 1. Webhook delivery (optional)
        if self.webhook_url:
            if not self._send_webhook(alert_data):
                success = False
        
        # 2. Firebase is handled by firebase_listener.process_reading()
        # which writes to /alerts/{device_id} automatically
        
        return success
    
    def _send_webhook(self, alert_data: Dict[str, Any]) -> bool:
        """Send alert to webhook endpoint"""
        try:
            payload = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'alert': alert_data
            }
            
            headers = {'Content-Type': 'application/json'}
            if self.webhook_secret:
                headers['X-Webhook-Secret'] = self.webhook_secret
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Webhook delivered: {response.status_code}")
                return True
            else:
                logger.warning(f"⚠️ Webhook failed: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("❌ Webhook timeout")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Webhook error: {e}")
            return False
    
    def format_alert_message(self, alert_data: Dict[str, Any]) -> str:
        """Format alert for human-readable display"""
        alert_type = alert_data.get('alert_type', 'unknown')
        fixture = alert_data.get('fixture_name', alert_data.get('fixture_index', 'unknown'))
        confidence = alert_data.get('confidence', 0)
        flow_rate = alert_data.get('details', {}).get('flow_rate', 0)
        duration = alert_data.get('details', {}).get('duration', 0)
        
        icons = {
            'minor_leak': '⚠️',
            'major_leak': '🚨',
            'anomaly': '🔍',
            'hidden_leak': '🕳️',
            'sensor_fault': '🔧'
        }
        
        icon = icons.get(alert_type, '📢')
        
        return (
            f"{icon} *{alert_type.upper().replace('_', ' ')}* detected\n"
            f"   Fixture: {fixture}\n"
            f"   Flow: {flow_rate:.2f} L/min\n"
            f"   Duration: {duration:.0f}s\n"
            f"   Confidence: {confidence:.1%}"
        )


# Slack/Discord specific formatting
def format_for_slack(alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format alert for Slack webhook"""
    return {
        'text': f"Water Meter Alert: {alert_data.get('alert_type', 'unknown')}",
        'blocks': [
            {
                'type': 'header',
                'text': {
                    'type': 'plain_text',
                    'text': f"🚰 Water Leak Alert"
                }
            },
            {
                'type': 'section',
                'fields': [
                    {'type': 'mrkdwn', 'text': f"*Type:*\n{alert_data.get('alert_type', 'unknown')}"},
                    {'type': 'mrkdwn', 'text': f"*Fixture:*\n{alert_data.get('fixture_name', 'unknown')}"},
                    {'type': 'mrkdwn', 'text': f"*Confidence:*\n{alert_data.get('confidence', 0):.1%}"},
                    {'type': 'mrkdwn', 'text': f"*Flow Rate:*\n{alert_data.get('details', {}).get('flow_rate', 0):.2f} L/min"}
                ]
            },
            {
                'type': 'context',
                'elements': [
                    {'type': 'mrkdwn', 'text': f"Device: {alert_data.get('device_id', 'unknown')} | {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"}
                ]
            }
        ]
    }


def format_for_discord(alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format alert for Discord webhook"""
    colors = {
        'minor_leak': 0xFFA500,  # Orange
        'major_leak': 0xFF0000,  # Red
        'anomaly': 0xFFFF00,     # Yellow
        'hidden_leak': 0x800080, # Purple
    }
    
    return {
        'embeds': [{
            'title': '🚰 Water Leak Alert',
            'color': colors.get(alert_data.get('alert_type'), 0x00FF00),
            'fields': [
                {'name': 'Type', 'value': alert_data.get('alert_type', 'unknown'), 'inline': True},
                {'name': 'Fixture', 'value': alert_data.get('fixture_name', 'unknown'), 'inline': True},
                {'name': 'Confidence', 'value': f"{alert_data.get('confidence', 0):.1%}", 'inline': True},
                {'name': 'Flow Rate', 'value': f"{alert_data.get('details', {}).get('flow_rate', 0):.2f} L/min", 'inline': True},
                {'name': 'Duration', 'value': f"{alert_data.get('details', {}).get('duration', 0):.0f}s", 'inline': True},
            ],
            'timestamp': datetime.utcnow().isoformat()
        }]
    }