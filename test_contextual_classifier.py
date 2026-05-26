import unittest
from unittest.mock import MagicMock, patch
from app.services.contextual_classifier import ContextualClassifier
from app.services.classification_service import classification_service
from app.core.config import settings

class TestContextualClassifier(unittest.TestCase):
    
    def setUp(self):
        # Reset singleton if needed or just instantiate fresh
        self.classifier = ContextualClassifier()
        # Ensure we don't actually load a model for this test unless we want to
        # For this test, we assume model file might be missing or we mock it
        
    def test_fallback_when_model_missing(self):
        # If model not found, it should return Unknown/0.0
        # We force enabled=True but _load_model will fail or log warning if file missing
        # The service handles this by setting enabled=False or returning unknown
        
        # Le's simulate a prediction request
        result = self.classifier.predict("some text")
        self.assertEqual(result['clause_type'], "Unknown")
        self.assertEqual(result['clause_confidence'], 0.0)
        self.assertEqual(result['risk_level'], "Unknown")

    def test_caching(self):
        # Mock the valid state where we return a result
        self.classifier.enabled = True
        
        # Inject a fake cache entry for a specific hash
        import hashlib
        text = "cached clause"
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        
        fake_result = {
            "clause_type": "Termination",
            "clause_confidence": 0.95,
            "risk_level": "High",
            "risk_confidence": 0.90
        }
        self.classifier._cache[text_hash] = fake_result
        
        # Predict
        result = self.classifier.predict(text)
        self.assertEqual(result, fake_result)
        
    def test_integration_classification_service_hybrid(self):
        # Test that classification_service uses the classifier when rule score is low
        
        # We need to patch 'app.services.classification_service.contextual_classifier' 
        # because that is the name imported in classification_service.py
        
        with patch('app.services.classification_service.contextual_classifier') as mock_classifier:
            # Configure the mock to return a strong prediction
            mock_classifier.predict.return_value = {
                "clause_type": "Indemnity",
                "clause_confidence": 0.85,
                "risk_level": "Medium",
                "risk_confidence": 0.75
            }
            
            # Use text with NO rule keywords to force fallback to classifier
            text_no_rules = "The provider shall compensate the user for all losses." 
            # Note: "compensate" is in Liability keywords, so rule score might be > 0.
            # But likely < 0.75 (high threshold).
            # Patterns: \bcompensation\b. "compensate" != "compensation".
            # So rule score should be 0.0 or very low.
            
            # Let's ensure rule score is low
            res = classification_service.classify_clause(text_no_rules)
            
            # Verify classifier was called
            mock_classifier.predict.assert_called_once()
            
            # Verify result comes from classifier
            self.assertEqual(res['clause_type'], "Indemnity")
            self.assertEqual(res['confidence_score'], 0.85)
            self.assertEqual(res['risk_level'], "Medium")

if __name__ == '__main__':
    unittest.main()
