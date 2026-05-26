import sys
import os
import torch
import time
from app.infrastructure.legalbert_engine import legalbert_engine
from app.services.classification_service import classification_service
from app.services.risk_service import risk_service
from app.core.config import settings

def test_semantic_similarity():
    print("\n[TEST] Semantic Similarity & Refinement")
    
    # Clause that implies termination but might miss some strict keywords or be weak
    # "The Company reserves the absolute right to end this agreement at any time."
    # This might hit "reserves the right" (Low) but "end this agreement" might be missed by some regex if not "terminate"
    # Let's use a subtle one. 
    
    weak_clause = "The Company may, at its sole discretion, bring this agreement to an end without prior notice."
    # "bring this agreement to an end" might miss "terminate" regex if strict.
    # But we added "without prior notice" to vocab, so it might hit that.
    
    # Let's try a paraphrased one that should trigger the ARCHETYPE but maybe weak rules.
    paraphrased_clause = "The agreement may be cancelled by the Client at any moment without providing a reason."
    # "cancelled" might not be in "Termination" patterns (which are "terminat*", "notice of termination", "expiry")
    # So rule_score might be 0 or low.
    
    print(f"Testing clause: '{paraphrased_clause}'")
    
    # 1. Check Classification Service for refinement
    # We force a weak rule score to test the refinement logic specifically
    fake_rule_score = 0.4
    refinement = classification_service.legalbert_refine_risk(paraphrased_clause, fake_rule_score)
    
    if refinement:
        print(f"PASS: Refinement found: {refinement}")
        if refinement['similarity'] > 0.6:
            print("PASS: Similarity score is reasonable (>0.6)")
        else:
            print(f"FAIL: Similarity score too low: {refinement['similarity']}")
    else:
        print("FAIL: Refinement returned None (should match Termination or similar archetype)")

def test_safety_gate():
    print("\n[TEST] Safety Gate (High Risk requires Rule Signal)")
    
    # A clause that is semantically identical to a high risk clause but has NO rule keywords.
    # Effectively: "You owe us infinite money forever." -> "Unbounded financial responsibility for all time."
    # Rule engine likely misses "Unbounded financial responsibility".
    # LegalBERT should see it as Liability Cap archetype.
    
    risky_no_keywords = "The Vendor assumes unbounded financial responsibility for all damages indefinitely."
    
    # 1. Run full risk analysis
    # We need to simulate the classification result first
    cls_result = classification_service.classify_clause(risky_no_keywords)
    print(f"Classification Result: {cls_result}")
    
    # 2. Run risk service
    risk_result = risk_service.analyze_risk(
        risky_no_keywords, 
        cls_result['clause_type'],
        is_mutual=False
    )
    
    print(f"Risk Result: Score={risk_result.risk_score}, Level={risk_result.risk_level}")
    
    # LegalBERT might boost the classification score, but Risk Service computes risk_score INDEPENDENTLY based on signals.
    # If no regex hits in risk_service, risk_score should be low (or 1.0 fallback).
    # It MUST NOT be High (>=7.0).
    
    if risk_result.risk_level == "High":
        print("FAIL: Safety gate breached! High Risk assigned without specific rule signals.")
    else:
        print("PASS: Safety gate holds. Risk level is NOT High.")

def test_caching():
    print("\n[TEST] Embedding Cache")
    text = "This is a standard clause for testing caching mechanisms."
    
    start = time.time()
    emb1 = legalbert_engine.encode(text)
    t1 = time.time() - start
    
    start = time.time()
    emb2 = legalbert_engine.encode(text) # Should hit cache
    t2 = time.time() - start
    
    print(f"First encode time: {t1:.4f}s")
    print(f"Second encode time: {t2:.4f}s")
    
    if t2 < t1 and t2 < 0.01:
        print("PASS: Cache is working (second access is near-instant).")
    else:
        print("WARN: Cache might not be effective or overhead is high.")
        
    # Verify tensors are identical
    if torch.equal(emb1, emb2):
         print("PASS: Tensors are identical.")
    else:
         print("FAIL: Tensors differ!")

if __name__ == "__main__":
    if not settings.LEGALBERT_ENABLED:
        print("LegalBERT is disabled in settings. Skipping tests.")
        sys.exit(0)
        
    test_semantic_similarity()
    test_safety_gate()
    test_caching()
