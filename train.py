"""
PhishVision Model Training Pipeline
Trains multiple ML models for phishing detection with:
- Unified label encoding (0 = Safe, 1 = Phishing)
- Dataset balancing via SMOTE
- Optimized XGBoost parameters
- Cross-validation and evaluation
"""

import pandas as pd
import numpy as np
import pickle
import warnings
import logging
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

# Try to import SMOTE for oversampling (optional)
try:
    from imblearn.over_sampling import SMOTE
    HAS_SMOTE = True
except ImportError:
    HAS_SMOTE = False
    print("⚠️  imblearn not installed. Dataset balancing disabled. Install with: pip install imbalanced-learn")

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PhishVision-Training")

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    "test_size": 0.2,
    "random_state": 42,
    "use_balancing": True,  # Enable SMOTE oversampling
    "n_estimators_gb": 150,
    "n_estimators_rf": 200,
    "xgb_params": {
        "n_estimators": 200,
        "max_depth": 6,
        "learning_rate": 0.1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "min_child_weight": 1,
        "gamma": 0.1,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
        "random_state": 42,
        "eval_metric": "logloss",
        "use_label_encoder": False
    }
}

# ============================================================================
# DATA LOADING AND PREPROCESSING
# ============================================================================

print("\n" + "="*60)
print("📊 PHISHVISION MODEL TRAINING")
print("="*60)

# Load Data
logger.info("Loading dataset...")
df = pd.read_csv('Phishing.csv')

# Drop index column if exists
if 'index' in df.columns:
    df = df.drop('index', axis=1)

print(f"\n📈 Dataset Info:")
print(f"   Total samples: {len(df)}")
print(f"   Features: {len(df.columns) - 1}")
print(f"   Target column: 'Result'")

# Check class distribution BEFORE conversion
print(f"\n📊 Original Class Distribution:")
original_dist = df['Result'].value_counts()
print(f"   Phishing (-1): {original_dist.get(-1, 0)}")
print(f"   Legitimate (1): {original_dist.get(1, 0)}")

# ============================================================================
# UNIFIED LABEL ENCODING
# Convert: -1 (Phishing) → 1, 1 (Legitimate) → 0
# This makes ALL models use: 0 = Safe, 1 = Phishing
# ============================================================================

print(f"\n🔄 Converting labels to unified format...")
print(f"   Original: -1 = Phishing, 1 = Safe")
print(f"   New:       1 = Phishing, 0 = Safe")

# Map labels: -1 (phishing) -> 1, 1 (safe) -> 0
df['Result'] = df['Result'].map({-1: 1, 1: 0})

print(f"\n📊 New Class Distribution:")
new_dist = df['Result'].value_counts()
print(f"   Phishing (1): {new_dist.get(1, 0)}")
print(f"   Safe (0): {new_dist.get(0, 0)}")

# Separate features and target
X = df.drop('Result', axis=1)
y = df['Result']

# Store feature names for later
FEATURE_NAMES = X.columns.tolist()
print(f"\n📋 Feature Names ({len(FEATURE_NAMES)}):")
for i, name in enumerate(FEATURE_NAMES, 1):
    print(f"   {i:2}. {name}")

# ============================================================================
# TRAIN/TEST SPLIT
# ============================================================================

X_train, X_test, y_train, y_test = train_test_split(
    X, y, 
    test_size=CONFIG["test_size"], 
    random_state=CONFIG["random_state"],
    stratify=y  # Maintain class distribution
)

print(f"\n📂 Train/Test Split:")
print(f"   Training samples: {len(X_train)}")
print(f"   Test samples: {len(X_test)}")

# ============================================================================
# DATASET BALANCING (SMOTE)
# ============================================================================

if CONFIG["use_balancing"] and HAS_SMOTE:
    print(f"\n⚖️  Applying SMOTE oversampling...")
    print(f"   Before - Class 0: {sum(y_train == 0)}, Class 1: {sum(y_train == 1)}")
    
    smote = SMOTE(random_state=CONFIG["random_state"])
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)
    
    print(f"   After  - Class 0: {sum(y_train_balanced == 0)}, Class 1: {sum(y_train_balanced == 1)}")
    X_train, y_train = X_train_balanced, y_train_balanced
else:
    if CONFIG["use_balancing"]:
        print(f"\n⚠️  SMOTE not available, using original distribution")

# ============================================================================
# MODEL TRAINING
# ============================================================================

print("\n" + "="*60)
print("🚀 TRAINING MODELS")
print("="*60)

models = {}

# 1. Gradient Boosting
print("\n1️⃣  Training Gradient Boosting...")
gb = GradientBoostingClassifier(
    n_estimators=CONFIG["n_estimators_gb"],
    max_depth=5,
    learning_rate=0.1,
    random_state=CONFIG["random_state"]
)
gb.fit(X_train, y_train)
models['gb'] = gb
pickle.dump(gb, open('model_gb.pkl', 'wb'))
print(f"   ✅ Saved model_gb.pkl")

# 2. XGBoost (Optimized)
print("\n2️⃣  Training XGBoost (Optimized)...")
xgb = XGBClassifier(**CONFIG["xgb_params"])
xgb.fit(X_train, y_train)
models['xgb'] = xgb
pickle.dump(xgb, open('model_xgb.pkl', 'wb'))
print(f"   ✅ Saved model_xgb.pkl")

# 3. Random Forest
print("\n3️⃣  Training Random Forest...")
rf = RandomForestClassifier(
    n_estimators=CONFIG["n_estimators_rf"],
    max_depth=10,
    min_samples_split=5,
    random_state=CONFIG["random_state"],
    n_jobs=-1
)
rf.fit(X_train, y_train)
models['rf'] = rf
pickle.dump(rf, open('model_rf.pkl', 'wb'))
print(f"   ✅ Saved model_rf.pkl")

# 4. Stacking Ensemble
print("\n4️⃣  Training Stacking Ensemble...")
stack = StackingClassifier(
    estimators=[
        ('gb', GradientBoostingClassifier(n_estimators=100, random_state=CONFIG["random_state"])),
        ('rf', RandomForestClassifier(n_estimators=100, random_state=CONFIG["random_state"])),
        ('xgb', XGBClassifier(n_estimators=100, random_state=CONFIG["random_state"], eval_metric='logloss', use_label_encoder=False))
    ],
    final_estimator=LogisticRegression(max_iter=1000),
    cv=5,
    n_jobs=-1
)
stack.fit(X_train, y_train)
models['stack'] = stack
pickle.dump(stack, open('model_stack.pkl', 'wb'))
print(f"   ✅ Saved model_stack.pkl")

# Save feature names for validation
pickle.dump(FEATURE_NAMES, open('feature_names.pkl', 'wb'))
print(f"\n   ✅ Saved feature_names.pkl")

# ============================================================================
# MODEL EVALUATION
# ============================================================================

print("\n" + "="*60)
print("📊 MODEL EVALUATION")
print("="*60)

for name, model in models.items():
    print(f"\n{'='*40}")
    print(f"Model: {name.upper()}")
    print(f"{'='*40}")
    
    # Predictions
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    # Metrics
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    
    print(f"Accuracy: {accuracy:.4f}")
    print(f"F1 Score: {f1:.4f}")
    
    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    print(f"\nConfusion Matrix:")
    print(f"              Predicted")
    print(f"              Safe  Phish")
    print(f"Actual Safe   {cm[0][0]:4}  {cm[0][1]:4}")
    print(f"Actual Phish  {cm[1][0]:4}  {cm[1][1]:4}")
    
    # Classification Report
    print(f"\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Safe', 'Phishing']))

# ============================================================================
# CROSS-VALIDATION
# ============================================================================

print("\n" + "="*60)
print("🔄 CROSS-VALIDATION (5-Fold)")
print("="*60)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=CONFIG["random_state"])

for name, model in models.items():
    scores = cross_val_score(model, X, y, cv=cv, scoring='f1')
    print(f"{name.upper():8} - F1 Score: {scores.mean():.4f} (+/- {scores.std()*2:.4f})")

# ============================================================================
# FEATURE IMPORTANCE (XGBoost)
# ============================================================================

print("\n" + "="*60)
print("📊 FEATURE IMPORTANCE (XGBoost Top 10)")
print("="*60)

importance = xgb.feature_importances_
indices = np.argsort(importance)[::-1][:10]

for i, idx in enumerate(indices, 1):
    print(f"{i:2}. {FEATURE_NAMES[idx]:30} = {importance[idx]:.4f}")

# ============================================================================
# SAVE TRAINING METADATA
# ============================================================================

metadata = {
    "config": CONFIG,
    "feature_names": FEATURE_NAMES,
    "label_encoding": {"safe": 0, "phishing": 1},
    "training_samples": len(X_train),
    "test_samples": len(X_test),
    "model_files": ["model_gb.pkl", "model_xgb.pkl", "model_rf.pkl", "model_stack.pkl"]
}
pickle.dump(metadata, open('training_metadata.pkl', 'wb'))

print("\n" + "="*60)
print("✅ ALL MODELS TRAINED AND SAVED SUCCESSFULLY!")
print("="*60)
print("\nFiles created:")
print("  - model_gb.pkl (Gradient Boosting)")
print("  - model_xgb.pkl (XGBoost)")
print("  - model_rf.pkl (Random Forest)")
print("  - model_stack.pkl (Stacking Ensemble)")
print("  - feature_names.pkl")
print("  - training_metadata.pkl")
print("\n⚠️  IMPORTANT: All models now use unified labels:")
print("    0 = Safe, 1 = Phishing")
print("="*60 + "\n")