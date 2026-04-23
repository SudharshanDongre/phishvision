import pickle
import joblib

models = {
    "model_stack": "model_stack.pkl",
    "model_gb":    "model_gb.pkl",
    "model_xgb":   "model_xgb.pkl",
    "model_rf":    "model_rf.pkl",
}

for name, path in models.items():
    with open(path, "rb") as f:
        model = pickle.load(f)           # load old pickle
    joblib.dump(model, f"{name}.joblib") # save as joblib
    print(f"✓ Saved {name}.joblib")