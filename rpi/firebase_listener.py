#!/usr/bin/env python3
"""
Firebase Listener for RPi Backend
Polls Firebase Realtime Database for new readings and runs ML inference.
"""

import pyrebase
import json
import threading
import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class FirebaseListener:
    """
    Pyrebase4-based Firebase listener that polls for new readings.
    Handles authentication, token refresh, and data processing.
    """
    
    def __init__(
        self,
        firebase_config_path: str,
        email: str,
        password: str,
        device_id: str,
        poll_interval: int = 5
    ):
        self.device_id = device_id
        self.email = email
        self.password = password
        self.poll_interval = poll_interval
        self.last_timestamp: Optional[str] = None
        self.running = False
        self.poll_thread: Optional[threading.Thread] = None
        self._detector = None
        self._alert_engine = None
        
        # Load Firebase config
        with open(firebase_config_path, 'r') as f:
            self.firebase_config = json.load(f)
        
        # Initialize Pyrebase4
        self.firebase = pyrebase.initialize_app(self.firebase_config)
        self.auth = self.firebase.auth()
        self.db = self.firebase.database()
        
        # Sign in
        self._sign_in()
        
        # Database references
        self.readings_ref = self.db.child(f"readings/{device_id}")
        self.alerts_ref = self.db.child(f"alerts/{device_id}")
        self.commands_ref = self.db.child(f"commands/{device_id}")
        self.device_ref = self.db.child(f"devices/{device_id}")
    
    def _sign_in(self):
        """Sign in with email/password"""
        try:
            self.user = self.auth.sign_in_with_email_and_password(self.email, self.password)
            self.id_token = self.user['idToken']
            self.refresh_token = self.user['refreshToken']
            logger.info(f"Signed in as {self.email}")
        except Exception as e:
            logger.error(f"Firebase sign-in failed: {e}")
            raise
    
    def _refresh_token(self):
        """Refresh auth token if expired"""
        try:
            self.user = self.auth.refresh(self.refresh_token)
            self.id_token = self.user['idToken']
            logger.debug("Token refreshed successfully")
        except Exception as e:
            logger.warning(f"Token refresh failed, re-authenticating: {e}")
            self._sign_in()
    
    def set_detector(self, detector):
        """Set ML detector for processing readings"""
        self._detector = detector
    
    def set_alert_engine(self, alert_engine):
        """Set alert engine for notifications"""
        self._alert_engine = alert_engine
    
    def start(self):
        """Start polling thread"""
        if self.running:
            logger.warning("Listener already running")
            return
        
        self.running = True
        self.poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.poll_thread.start()
        logger.info(f"Started polling for device {self.device_id} every {self.poll_interval}s")
    
    def stop(self):
        """Stop polling thread"""
        self.running = False
        if self.poll_thread:
            self.poll_thread.join(timeout=5)
        logger.info("Listener stopped")
    
    def _poll_loop(self):
        """Main polling loop"""
        while self.running:
            try:
                self._check_new_readings()
            except Exception as e:
                logger.error(f"Poll error: {e}")
                # Try to refresh token on auth errors
                if "permission" in str(e).lower() or "unauthorized" in str(e).lower():
                    self._refresh_token()
            time.sleep(self.poll_interval)
    
    def _check_new_readings(self):
        """Fetch latest reading from Firebase"""
        # Get most recent reading
        readings = self.readings_ref.order_by_key().limit_to_last(1).get(self.id_token)
        
        if readings and readings.val():
            for ts, data in readings.val().items():
                if ts != self.last_timestamp:
                    self.last_timestamp = ts
                    self.process_reading(data, ts)
    
    def process_reading(self, data: Dict[str, Any], timestamp: str):
        """Process a new reading: extract features, run ML, write alerts"""
        if not self._detector:
            logger.warning("No detector set, skipping ML inference")
            return
        
        try:
            # Extract features for each fixture
            # We'll process fixture 1, 2, 3 separately
            inlet = data.get('inlet', {})
            
            for fixture_idx in [1, 2, 3]:
                fixture_key = f'fixture_{fixture_idx}'
                fixture = data.get(fixture_key, {})
                
                if fixture.get('flow_rate', 0) > 0.01:  # Only process if flowing
                    features = self._extract_features(data, fixture_idx)
                    result = self._detector.predict(features)
                    
                    if result['final'] != 'normal':
                        self._write_alert(result, fixture_idx, data, timestamp)
                        
        except Exception as e:
            logger.error(f"Error processing reading: {e}")
    
    def _extract_features(self, data: Dict[str, Any], fixture_idx: int):
        """Extract 9 features from Firebase reading"""
        import numpy as np
        from datetime import datetime
        
        inlet = data.get('inlet', {})
        fixture = data.get(f'fixture_{fixture_idx}', {})
        
        # 1. flow_rate
        flow_rate = fixture.get('flow_rate', 0)
        
        # 2. duration_seconds (approximate from volume/rate)
        volume = fixture.get('volume', 0)
        duration = volume / max(flow_rate / 60, 0.01) if flow_rate > 0 else 0
        
        # 3-4. Time features
        now = datetime.now()
        hour = now.hour
        day = now.weekday()
        
        # 5. fixture_id
        fixture_id = fixture_idx
        
        # 6. inlet_ratio
        inlet_rate = inlet.get('flow_rate', 0)
        inlet_ratio = inlet_rate / max(flow_rate, 0.01)
        
        # 7. rate_variance (simplified - would need rolling buffer)
        rate_variance = 0
        
        # 8. is_night_time
        is_night = 1 if (hour >= 22 or hour < 5) else 0
        
        # 9. pulse_trend (simplified)
        pulse_trend = 0
        
        return np.array([[
            flow_rate, duration, hour, day, fixture_id,
            inlet_ratio, rate_variance, is_night, pulse_trend
        ]], dtype=np.float32)
    
    def _write_alert(self, result: Dict, fixture_idx: int, data: Dict, timestamp: str):
        """Write alert to Firebase"""
        alert_data = {
            'alert_type': result['final'],
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'confidence': result.get('confidence', 0),
            'fixture_index': fixture_idx,
            'fixture_name': {1: 'bidet', 2: 'kitchen', 3: 'bathroom_shower'}.get(fixture_idx),
            'action': 'monitoring',
            'details': {
                'flow_rate': data.get(f'fixture_{fixture_idx}', {}).get('flow_rate', 0),
                'inlet_flow_rate': data.get('inlet', {}).get('flow_rate', 0),
                'xgboost_class': result['xgboost']['class'],
                'xgboost_confidence': result['xgboost']['confidence'],
                'isolation_forest_anomaly': result['isolation_forest']['anomaly'],
                'isolation_forest_score': result['isolation_forest']['score']
            }
        }
        
        try:
            self.alerts_ref.push(alert_data, self.id_token)
            logger.warning(f"ALERT: {result['final']} on fixture {fixture_idx} (confidence: {result.get('confidence', 0):.2f})")
            
            # Send notification
            if self._alert_engine:
                self._alert_engine.send_notification(alert_data)
                
        except Exception as e:
            logger.error(f"Failed to write alert: {e}")
    
    def get_latest_reading(self) -> Optional[Dict]:
        """Get the most recent reading"""
        try:
            readings = self.readings_ref.order_by_key().limit_to_last(1).get(self.id_token)
            if readings and readings.val():
                return list(readings.val().values())[0]
        except Exception as e:
            logger.error(f"Error getting latest reading: {e}")
        return None
    
    def get_recent_alerts(self, limit: int = 20) -> Optional[Dict]:
        """Get recent alerts"""
        try:
            alerts = self.alerts_ref.order_by_key().limit_to_last(limit).get(self.id_token)
            return alerts.val() if alerts else None
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
        return None
    
    def send_command(self, command: str):
        """Send command to ESP32 via Firebase"""
        try:
            cmd_data = {
                'command': command,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'source': 'dashboard',
                'executed': False
            }
            self.commands_ref.push(cmd_data, self.id_token)
            logger.info(f"Sent command: {command}")
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
    
    def is_connected(self) -> bool:
        """Check if Firebase connection is healthy"""
        try:
            # Try a simple read
            self.db.child('.info/connected').get(self.id_token)
            return True
        except:
            return False
    
    def reconnect(self):
        """Force reconnection"""
        logger.info("Reconnecting to Firebase...")
        self._sign_in()
        logger.info("Reconnected successfully")


# Standalone test
if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    logging.basicConfig(level=logging.INFO)
    
    listener = FirebaseListener(
        firebase_config_path='firebase_config.json',
        email=os.getenv('FIREBASE_EMAIL'),
        password=os.getenv('FIREBASE_PASSWORD'),
        device_id=os.getenv('DEVICE_ID', 'wm_001')
    )
    
    # Test read
    latest = listener.get_latest_reading()
    print(f"Latest reading: {latest}")