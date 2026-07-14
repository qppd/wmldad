#!/usr/bin/env python3
"""
ML Inference Module for Raspberry Pi
Loads XGBoost + Isolation Forest models and runs real-time inference.
"""

import xgboost as xgb
import joblib
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Any, List, Union

logger = logging.getLogger(__name__)


class LeakDetector:
    """
    Production leak detector combining XGBoost classifier + Isolation Forest.
    Optimized for Raspberry Pi inference.
    """
    
    def __init__(
        self,
        xgb_path: str = 'models/xgboost_model.json',
        iforest_path: str = 'models/isolation_forest.pkl',
        scaler_path: str = 'models/scaler.pkl',
        threshold_path: str = 'models/iso_threshold.pkl',
        confidence_threshold: float = 0.80
    ):
        self.xgb_path = Path(xgb_path)
        self.iforest_path = Path(iforest_path)
        self.scaler_path = Path(scaler_path)
        self.threshold_path = Path(threshold_path)
        self.confidence_threshold = confidence_threshold
        
        self.model_loaded = False
        self.n_features = 9
        self.target_names = ['normal', 'minor_leak', 'major_leak']
        
        self._load_models()
    
    def _load_models(self):
        """Load all model artifacts"""
        try:
            # XGBoost
            self.xgb = xgb.XGBClassifier()
            self.xgb.load_model(str(self.xgb_path))
            
            # Isolation Forest
            self.iso_forest = joblib.load(self.iforest_path)
            
            # Scaler
            self.scaler = joblib.load(self.scaler_path)
            
            # Threshold
            self.iso_threshold = joblib.load(self.threshold_path)
            
            # Get feature count from scaler
            self.n_features = self.scaler.n_features_in_
            
            self.model_loaded = True
            logger.info("✅ All models loaded successfully")
            logger.info(f"   XGBoost: {self.xgb.n_estimators} trees, {self.n_features} features")
            logger.info(f"   Isolation Forest: {self.iso_forest.n_estimators} estimators")
            logger.info(f"   Anomaly threshold: {self.iso_threshold:.4f}")
            logger.info(f"   Confidence threshold: {self.confidence_threshold}")
            
        except Exception as e:
            logger.error(f"❌ Model loading failed: {e}")
            self.model_loaded = False
            raise
    
    def predict(self, features_raw: Union[np.ndarray, List]) -> Dict[str, Any]:
        """
        Run inference on raw features.
        
        Args:
            features_raw: Array of shape (n_features,) or (1, n_features) or (n_samples, n_features)
            
        Returns:
            Dict with xgboost, isolation_forest, final prediction, and confidence
        """
        if not self.model_loaded:
            raise RuntimeError("Models not loaded")
        
        # Ensure 2D array
        features = np.asarray(features_raw, dtype=np.float32)
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        # Validate feature count
        if features.shape[1] != self.n_features:
            raise ValueError(f"Expected {self.n_features} features, got {features.shape[1]}")
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        results = []
        
        for i in range(features_scaled.shape[0]):
            sample = features_scaled[i:i+1]
            
            # 1. XGBoost prediction
            xgb_proba = self.xgb.predict_proba(sample)[0]
            xgb_pred = int(np.argmax(xgb_proba))
            xgb_conf = float(xgb_proba[xgb_pred])
            
            # 2. Isolation Forest anomaly score
            iso_score = float(self.iso_forest.score_samples(sample)[0])
            iso_anomaly = bool(iso_score < self.iso_threshold)
            
            # Build result
            result = {
                'xgboost': {
                    'class': self.target_names[xgb_pred],
                    'confidence': xgb_conf,
                    'probabilities': {
                        name: float(xgb_proba[j]) 
                        for j, name in enumerate(self.target_names)
                    }
                },
                'isolation_forest': {
                    'anomaly': iso_anomaly,
                    'score': iso_score
                }
            }
            
            # Decision logic
            if xgb_conf >= self.confidence_threshold:
                result['final'] = result['xgboost']['class']
                result['confidence'] = xgb_conf
            elif iso_anomaly:
                result['final'] = 'anomaly'
                result['confidence'] = float(1.0 - abs(iso_score))
            else:
                result['final'] = 'uncertain'
                result['confidence'] = xgb_conf
            
            results.append(result)
        
        return results[0] if len(results) == 1 else results
    
    def predict_batch(self, features_batch: np.ndarray) -> List[Dict[str, Any]]:
        """Optimized batch prediction"""
        return self.predict(features_batch)
    
    def warm_up(self, n_warmup: int = 10):
        """Run dummy inferences to warm up (JIT, cache)"""
        dummy = np.zeros((1, self.n_features), dtype=np.float32)
        for _ in range(n_warmup):
            _ = self.predict(dummy)
        logger.info(f"🔥 Warm-up complete ({n_warmup} iterations)")
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get XGBoost feature importance"""
        if not self.model_loaded:
            return {}
        
        importance = self.xgb.feature_importances_
        # Would need feature names from training
        return {f'feature_{i}': float(imp) for i, imp in enumerate(importance)}
    
    def benchmark(self, n_iterations: int = 100) -> Dict[str, float]:
        """Benchmark inference speed"""
        import time
        
        dummy = np.zeros((1, self.n_features), dtype=np.float32)
        
        # Warm up
        self.warm_up(10)
        
        # Benchmark
        start = time.perf_counter()
        for _ in range(n_iterations):
            _ = self.predict(dummy)
        elapsed = time.perf_counter() - start
        
        return {
            'total_time_ms': elapsed * 1000,
            'avg_time_ms': (elapsed / n_iterations) * 1000,
            'iterations': n_iterations,
            'throughput_fps': n_iterations / elapsed
        }


def load_deployment_package(model_dir: str = 'models') -> Dict[str, Any]:
    """
    Load complete deployment package from directory.
    Returns dict with all model components.
    """
    model_dir = Path(model_dir)
    
    detector = LeakDetector(
        xgb_path=model_dir / 'xgboost_model.json',
        iforest_path=model_dir / 'isolation_forest.pkl',
        scaler_path=model_dir / 'scaler.pkl',
        threshold_path=model_dir / 'iso_threshold.pkl'
    )
    
    # Load metadata
    import json
    with open(model_dir / 'metadata.json') as f:
        metadata = json.load(f)
    
    return {
        'detector': detector,
        'metadata': metadata
    }


# Standalone test
if __name__ == '__main__':
    import os
    logging.basicConfig(level=logging.INFO)
    
    # Test with dummy data
    detector = LeakDetector()
    
    # Normal reading features
    normal = np.array([[2.5, 30, 14, 2, 1, 1.1, 0.5, 0, 0.1]], dtype=np.float32)
    result = detector.predict(normal)
    print(f"Normal: {result['final']} (conf: {result['confidence']:.3f})")
    
    # Minor leak features (low flow, long duration)
    minor = np.array([[0.3, 600, 2, 1, 1, 1.2, 0.01, 1, 0.0]], dtype=np.float32)
    result = detector.predict(minor)
    print(f"Minor leak: {result['final']} (conf: {result['confidence']:.3f})")
    
    # Major leak features (high flow)
    major = np.array([[15.0, 120, 10, 3, 2, 1.05, 0.1, 0, 0.0]], dtype=np.float32)
    result = detector.predict(major)
    print(f"Major leak: {result['final']} (conf: {result['confidence']:.3f})")
    
    # Benchmark
    bench = detector.benchmark(100)
    print(f"\nBenchmark: {bench['avg_time_ms']:.2f} ms/inference ({bench['throughput_fps']:.1f} FPS)")