"""
PhishVision API Server
FastAPI backend for phishing URL detection with:
- Unified label encoding (0=Safe, 1=Phishing)
- Rule-based pre-checks
- Detailed debugging logs
- Confidence scoring
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pickle
import numpy as np
import logging
import time
from typing import Optional
from extractor import extract_features, rule_based_check, get_domain_parts

# ============================================================================
# CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("PhishVision-API")

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="PhishVision API",
    description="AI-powered phishing URL detection",
    version="2.0"
)

# CORS for browser extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# LOAD MODELS
# ============================================================================

models = {}
metadata = None

logger.info("Loading ML models...")
for m in ["gb", "xgb", "rf", "stack"]:
    try:
        models[m] = pickle.load(open(f"model_{m}.pkl", "rb"))
        logger.info(f"  ✅ Loaded model_{m}.pkl")
    except Exception as e:
        logger.error(f"  ❌ Error loading model_{m}.pkl: {e}")

# Load feature names for validation
try:
    feature_names = pickle.load(open("feature_names.pkl", "rb"))
    logger.info(f"  ✅ Loaded feature_names.pkl ({len(feature_names)} features)")
except:
    feature_names = None
    logger.warning("  ⚠️  feature_names.pkl not found")

# Load metadata
try:
    metadata = pickle.load(open("training_metadata.pkl", "rb"))
    logger.info(f"  ✅ Loaded training_metadata.pkl")
    logger.info(f"      Label encoding: {metadata.get('label_encoding', 'unknown')}")
except:
    metadata = None
    logger.warning("  ⚠️  training_metadata.pkl not found")

logger.info(f"Models loaded: {list(models.keys())}")

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class URLRequest(BaseModel):
    url: str
    model: str = "stack"
    debug: bool = False

class PredictionResponse(BaseModel):
    url: str
    verdict: str
    is_phishing: bool
    confidence: float
    model_used: str
    rule_based_flags: Optional[list] = None
    feature_summary: Optional[dict] = None
    debug_info: Optional[dict] = None

# ============================================================================
# PREDICTION ENDPOINT
# ============================================================================

@app.post("/predict", response_model=PredictionResponse)
def predict(request: URLRequest):
    """
    Analyze a URL for phishing indicators.
    
    All models now use UNIFIED labels:
    - 0 = Safe
    - 1 = Phishing
    """
    start_time = time.time()
    url = request.url.strip()
    model_key = request.model.lower()
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🔍 ANALYZING URL: {url}")
    logger.info(f"   Model: {model_key}")
    
    # Validate model
    selected_model = models.get(model_key)
    if not selected_model:
        logger.error(f"   ❌ Model '{model_key}' not found")
        raise HTTPException(status_code=400, detail=f"Model '{model_key}' not found. Available: {list(models.keys())}")
    
    # ========================================================================
    # STEP 1: Rule-Based Pre-Check
    # ========================================================================
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url if url.startswith("http") else "https://" + url)
        domain = parsed.netloc.lower().split(":")[0]
        path = parsed.path
    except:
        domain, path = "", ""
    
    is_phishing_by_rules, rule_reasons = rule_based_check(url, domain, path)
    
    if is_phishing_by_rules:
        logger.warning(f"   ⚠️  RULE-BASED FLAGS: {rule_reasons}")
    
    # ========================================================================
    # STEP 2: Feature Extraction
    # ========================================================================
    logger.debug("   Extracting features...")
    features = extract_features(url, debug=request.debug)
    features_array = np.array(features).reshape(1, -1)
    
    phishing_indicators = features.count(-1)
    safe_indicators = features.count(1)
    suspicious_indicators = features.count(0)
    
    logger.info(f"   Features: Phishing={phishing_indicators}, Safe={safe_indicators}, Suspicious={suspicious_indicators}")
    
    # ========================================================================
    # STEP 3: ML Prediction with CORRECT probability mapping
    # ========================================================================
    logger.debug(f"   Running {model_key.upper()} prediction...")
    
    prediction = selected_model.predict(features_array)[0]
    raw_probabilities = selected_model.predict_proba(features_array)[0]
    
    # ========================================================================
    # CRITICAL FIX: Handle model.classes_ ordering
    # predict_proba() returns probabilities in order of model.classes_
    # We need to find which index corresponds to phishing class
    # ========================================================================
    
    classes = selected_model.classes_
    logger.debug(f"   model.classes_ = {classes}")
    logger.debug(f"   raw_probabilities = {raw_probabilities}")
    
    # UNIFIED ENCODING FOR ALL MODELS:
    # 1 = Phishing, 0 = Safe
    phishing_class = 1
    safe_class = 0
    
    # Find the index of phishing class in model.classes_
    classes_list = list(classes)
    phishing_idx = classes_list.index(phishing_class)
    safe_idx = classes_list.index(safe_class)
    
    # Extract mapped probabilities
    prob_phishing = float(raw_probabilities[phishing_idx])
    prob_safe = float(raw_probabilities[safe_idx])
    
    logger.debug(f"   Mapped: phishing_idx={phishing_idx}, safe_idx={safe_idx}")
    logger.debug(f"   Mapped probabilities: Safe={prob_safe:.4f}, Phishing={prob_phishing:.4f}")
    
    # ========================================================================
    # DECISION LOGIC: Use phishing probability threshold
    # If phishing_prob > 0.4 → mark as phishing (catches edge cases)
    # ========================================================================
    
    PHISHING_THRESHOLD = 0.4
    
    # Primary decision based on probability threshold
    is_phishing = prob_phishing > PHISHING_THRESHOLD
    
    # Calculate confidence (always show confidence for the predicted class)
    if is_phishing:
        confidence = round(prob_phishing * 100, 2)
    else:
        confidence = round(prob_safe * 100, 2)
    
    logger.info(f"   ML Prediction: {'PHISHING' if is_phishing else 'SAFE'}")
    logger.info(f"   Raw prediction value: {prediction}")
    logger.info(f"   model.classes_: {classes}")
    logger.info(f"   Raw probabilities: {raw_probabilities}")
    logger.info(f"   Mapped: P(Safe)={prob_safe:.4f}, P(Phishing)={prob_phishing:.4f}")
    logger.info(f"   Threshold: {PHISHING_THRESHOLD} | P(Phishing) > threshold: {prob_phishing > PHISHING_THRESHOLD}")
    logger.info(f"   Confidence: {confidence}%")
    
    # ========================================================================
    # STEP 4: Combine Rule-Based and ML Results
    # ========================================================================
    final_phishing = is_phishing
    
    # If rule-based flags but ML says safe, consider it suspicious
    if is_phishing_by_rules and not is_phishing:
        # Lower confidence if rules disagree with ML
        confidence = max(confidence - 20, 50)
        logger.warning(f"   ⚠️  Rules disagree with ML - adjusted confidence to {confidence}%")
    
    # If strong rule-based indicators, override ML
    if is_phishing_by_rules and len(rule_reasons) >= 2:
        final_phishing = True
        confidence = min(confidence + 15, 95)
        logger.warning(f"   ⚠️  Multiple rule flags - overriding to PHISHING")
    
    verdict = "Phishing" if final_phishing else "Safe"
    
    # ========================================================================
    # STEP 5: Build Response
    # ========================================================================
    elapsed = round((time.time() - start_time) * 1000, 2)
    
    logger.info(f"   ✅ VERDICT: {verdict} ({confidence}%)")
    logger.info(f"   ⏱️  Time: {elapsed}ms")
    logger.info(f"{'='*60}\n")
    
    response = PredictionResponse(
        url=url,
        verdict=verdict,
        is_phishing=final_phishing,
        confidence=confidence,
        model_used=model_key,
        rule_based_flags=rule_reasons if is_phishing_by_rules else None
    )
    
    # Add debug info if requested
    if request.debug:
        response.feature_summary = {
            "phishing_indicators": phishing_indicators,
            "safe_indicators": safe_indicators,
            "suspicious_indicators": suspicious_indicators,
            "raw_features": features
        }
        response.debug_info = {
            "raw_prediction": int(prediction),
            "model_classes": [int(c) for c in classes],
            "raw_probabilities": [round(float(p), 4) for p in raw_probabilities],
            "mapped_probabilities": {
                "safe": round(prob_safe, 4),
                "phishing": round(prob_phishing, 4)
            },
            "phishing_threshold": PHISHING_THRESHOLD,
            "phishing_prob_exceeds_threshold": prob_phishing > PHISHING_THRESHOLD,
            "processing_time_ms": elapsed,
            "model": model_key,
            "rule_check_triggered": is_phishing_by_rules
        }
    
    return response

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
def health():
    """Check API and model status."""
    return {
        "status": "healthy",
        "models_loaded": list(models.keys()),
        "total_models": len(models),
        "feature_names_loaded": feature_names is not None,
        "metadata_loaded": metadata is not None
    }

# ============================================================================
# DEBUG ENDPOINT
# ============================================================================

@app.post("/debug")
def debug_url(request: URLRequest):
    """Get detailed feature analysis for a URL."""
    from extractor import get_feature_summary
    
    summary = get_feature_summary(request.url)
    features = summary["features"]
    
    # Add feature names
    if feature_names:
        feature_details = [
            {"name": name, "value": val, "indicator": "phishing" if val == -1 else ("suspicious" if val == 0 else "safe")}
            for name, val in zip(feature_names, features)
        ]
    else:
        feature_details = [
            {"index": i, "value": val, "indicator": "phishing" if val == -1 else ("suspicious" if val == 0 else "safe")}
            for i, val in enumerate(features)
        ]
    
    return {
        "url": request.url,
        "risk_score": summary["risk_score"],
        "phishing_indicators": summary["phishing_indicators"],
        "safe_indicators": summary["safe_indicators"],
        "suspicious_indicators": summary["suspicious_indicators"],
        "features": feature_details
    }

# ============================================================================
# BATCH PREDICTION
# ============================================================================

class BatchRequest(BaseModel):
    urls: list
    model: str = "stack"

@app.post("/predict/batch")
def predict_batch(request: BatchRequest):
    """Analyze multiple URLs at once."""
    results = []
    for url in request.urls:
        try:
            result = predict(URLRequest(url=url, model=request.model))
            results.append(result.dict())
        except Exception as e:
            results.append({"url": url, "error": str(e)})
    return {"results": results, "total": len(results)}

# ============================================================================
# STARTUP MESSAGE
# ============================================================================

@app.on_event("startup")
async def startup_event():
    logger.info("\n" + "="*60)
    logger.info("🛡️  PHISHVISION API SERVER STARTED")
    logger.info("="*60)
    logger.info(f"Models: {list(models.keys())}")
    logger.info(f"Label encoding: 0=Safe, 1=Phishing (UNIFIED)")
    logger.info("Endpoints:")
    logger.info("  POST /predict      - Analyze single URL")
    logger.info("  POST /predict/batch - Analyze multiple URLs")
    logger.info("  POST /debug        - Detailed feature analysis")
    logger.info("  GET  /health       - API health check")
    logger.info("  GET  /docs         - Swagger documentation")
    logger.info("="*60 + "\n")