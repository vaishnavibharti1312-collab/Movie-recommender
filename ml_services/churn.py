import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import pickle
import os
import json
from backend.database import SessionLocal
from backend.models import ChurnPrediction

MODEL_PATH = os.path.join(os.path.dirname(__file__), "churn_model.pkl")

def train_churn_model():
    db = SessionLocal()
    records = db.query(ChurnPrediction).all()
    db.close()
    
    if not records:
        print("No churn records found in database to train on.")
        return None
        
    data = []
    for r in records:
        features = json.loads(r.important_features)
        # Target label: 1 if risk_level is High or Medium, 0 if Low (or based on probability)
        target = 1 if r.churn_probability > 0.4 else 0
        data.append({
            "watch_time": features.get("watch_time", 40),
            "logins": features.get("logins", 10),
            "monthly_charges": features.get("monthly_charges", 14.99),
            "support_complaints": features.get("support_complaints", 0),
            "previous_cancellations": features.get("previous_cancellations", 0),
            "churn": target
        })
        
    df = pd.DataFrame(data)
    feature_cols = ['watch_time', 'logins', 'monthly_charges', 'support_complaints', 'previous_cancellations']
    X = df[feature_cols]
    y = df['churn']
    
    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(X, y)
    
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    print("Random Forest churn model trained and saved successfully!")
    return model

def predict_churn_for_user(user_id: int):
    db = SessionLocal()
    pred_record = db.query(ChurnPrediction).filter(ChurnPrediction.customer_id == user_id).first()
    db.close()
    
    if not pred_record:
        return {
            "customer_id": user_id,
            "churn_probability": 0.25,
            "risk_level": "Low",
            "important_features": [],
            "retention_action": "Standard newsletter engagement."
        }
        
    features = json.loads(pred_record.important_features)
    watch_time = features.get("watch_time", 40)
    logins = features.get("logins", 10)
    monthly_charges = features.get("monthly_charges", 14.99)
    support_complaints = features.get("support_complaints", 0)
    previous_cancellations = features.get("previous_cancellations", 0)
    
    # Calculate model prediction if model exists
    prob = pred_record.churn_probability
    if os.path.exists(MODEL_PATH):
        try:
            with open(MODEL_PATH, "rb") as f:
                model = pickle.load(f)
            input_data = [[watch_time, logins, monthly_charges, support_complaints, previous_cancellations]]
            prob = float(model.predict_proba(input_data)[0][1])
        except Exception:
            pass # Use stored value if model fails
            
    risk = "High" if prob > 0.6 else "Medium" if prob > 0.3 else "Low"
    
    # Identify risk factors
    factors = []
    if watch_time < 20:
        factors.append("Low monthly watch time (< 20 hrs)")
    if logins < 5:
        factors.append("Infrequent logins (< 5 times/month)")
    if support_complaints >= 3:
        factors.append("High support complaints (3+ contacts)")
    if previous_cancellations > 0:
        factors.append("History of previous subscription cancellations")
    if monthly_charges > 15.0:
        factors.append("Premium plan subscription cost pressure")
        
    # Suggest retention action
    if "High support complaints (3+ contacts)" in factors:
        retention = "Initiate proactive VIP customer support outreach to resolve open issues."
    elif "Low monthly watch time (< 20 hrs)" in factors:
        retention = "Trigger personalized content push notification (recommend trending Sci-Fi/Thrillers)."
    elif "Premium plan subscription cost pressure" in factors:
        retention = "Offer a 20% loyalty discount or plan downgrade option for the next billing cycle."
    elif "History of previous subscription cancellations" in factors:
        retention = "Send a feedback survey with a 1-month free subscription voucher."
    else:
        retention = "Standard marketing newsletters and weekly new release updates."
        
    return {
        "customer_id": user_id,
        "churn_probability": round(prob, 2),
        "risk_level": risk,
        "features": features,
        "important_features": factors if factors else ["No major risk factors detected"],
        "retention_action": retention
    }

if __name__ == "__main__":
    train_churn_model()
    # Test predict
    print("Test Predict User 5:", predict_churn_for_user(5))
