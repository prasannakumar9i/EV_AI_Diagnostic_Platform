"""
ml/models.py
Predictive maintenance models for EV battery and motor health.
  - XGBoost battery failure predictor
  - Isolation Forest anomaly detector
  - LSTM Autoencoder for charging pattern analysis
"""
import os
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

FEATURES = [
    "cycle_count", "soh_pct", "capacity_fade_pct",
    "avg_charge_temp_c", "max_discharge_c_rate",
    "voltage_spread_mv", "internal_resistance_mohm",
    "calendar_age_days", "fast_charge_ratio",
    "deep_discharge_count",
]


# ─────────────────────────────────────────────────────────────────────────────
# DATASET GENERATOR
# ─────────────────────────────────────────────────────────────────────────────
def generate_battery_dataset(n: int = 6000, seed: int = 42) -> pd.DataFrame:
    """Generate a realistic synthetic EV battery dataset with failure labels."""
    np.random.seed(seed)
    cycles   = np.random.randint(0, 1600, n)
    soh      = np.clip(100 - cycles * 0.025 + np.random.normal(0, 3, n), 40, 100)

    df = pd.DataFrame({
        "cycle_count":              cycles,
        "soh_pct":                  soh.round(1),
        "capacity_fade_pct":        (100 - soh).round(1),
        "avg_charge_temp_c":        np.random.normal(34, 10, n).clip(5, 80).round(1),
        "max_discharge_c_rate":     np.random.uniform(0.3, 3.2, n).round(2),
        "voltage_spread_mv":        np.random.exponential(14, n).clip(1, 160).round(1),
        "internal_resistance_mohm": (8 + cycles * 0.012 + np.random.normal(0, 2, n)).clip(5, 55).round(1),
        "calendar_age_days":        np.random.randint(10, 1600, n),
        "fast_charge_ratio":        np.random.beta(2, 5, n).round(3),
        "deep_discharge_count":     np.random.poisson(cycles * 0.002, n),
    })

    score = (
        (df.soh_pct < 75).astype(float) * 0.50 +
        (df.avg_charge_temp_c > 45).astype(float) * 0.30 +
        (df.voltage_spread_mv > 80).astype(float) * 0.35 +
        (df.internal_resistance_mohm > 28).astype(float) * 0.40 +
        (df.cycle_count > 1200).astype(float) * 0.30 +
        np.random.uniform(0, 0.15, n)
    )
    df["failure_within_30_days"] = (score > 0.70).astype(int)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# XGBOOST BATTERY FAILURE PREDICTOR
# ─────────────────────────────────────────────────────────────────────────────
class BatteryFailurePredictor:
    """XGBoost binary classifier: predict battery failure within 30 days."""

    def __init__(self):
        self.model  = None
        self.feats  = FEATURES
        self._threshold = 0.5

    def train(self, df: pd.DataFrame) -> dict:
        from xgboost import XGBClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import roc_auc_score, classification_report

        X, y = df[self.feats], df["failure_within_30_days"]
        Xtr, Xte, ytr, yte = train_test_split(
            X, y, test_size=0.2, stratify=y, random_state=42)

        scale = (ytr == 0).sum() / max(1, (ytr == 1).sum())
        self.model = XGBClassifier(
            n_estimators       = 300,
            max_depth          = 5,
            learning_rate      = 0.05,
            scale_pos_weight   = scale,
            random_state       = 42,
            eval_metric        = "logloss",
            early_stopping_rounds = 20,
        )
        self.model.fit(Xtr, ytr, eval_set=[(Xte, yte)], verbose=50)

        yp    = self.model.predict(Xte)
        yprob = self.model.predict_proba(Xte)[:, 1]
        auc   = roc_auc_score(yte, yprob)
        report = classification_report(yte, yp, output_dict=True)

        # Feature importance
        fi = pd.Series(self.model.feature_importances_, index=self.feats)
        fi = fi.sort_values(ascending=False)

        logger.info(f"XGBoost trained | AUC={auc:.4f}")
        print(f"\nROC-AUC: {auc:.4f}")
        print(f"Top features:\n{fi.head(5).to_string()}")

        return {"auc": auc, "report": report, "feature_importance": fi.to_dict()}

    def predict(self, vehicle: dict) -> dict:
        """Predict failure risk for a single vehicle."""
        X    = pd.DataFrame([vehicle])[self.feats]
        prob = float(self.model.predict_proba(X)[0, 1])
        level = ("CRITICAL" if prob > 0.75 else "HIGH" if prob > 0.5
                 else "MEDIUM" if prob > 0.25 else "LOW")
        return {
            "failure_probability": round(prob, 4),
            "risk_level":          level,
            "recommend_service":   prob > 0.5,
        }

    def save(self, path: str):
        import joblib
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.model, path)
        logger.info(f"Model saved: {path}")

    def load(self, path: str):
        import joblib
        self.model = joblib.load(path)
        logger.info(f"Model loaded: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# ISOLATION FOREST ANOMALY DETECTOR
# ─────────────────────────────────────────────────────────────────────────────
class EVAnomalyDetector:
    """Isolation Forest trained on healthy vehicle data."""

    def __init__(self, contamination: float = 0.05):
        self.contamination = contamination
        self.model  = None
        self.scaler = None
        self.feats  = ["cycle_count", "soh_pct", "avg_charge_temp_c",
                       "voltage_spread_mv", "internal_resistance_mohm"]

    def train(self, df: pd.DataFrame):
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import MinMaxScaler

        healthy       = df[df["failure_within_30_days"] == 0][self.feats]
        self.scaler   = MinMaxScaler()
        X_sc          = self.scaler.fit_transform(healthy)
        self.model    = IsolationForest(
            n_estimators  = 200,
            contamination = self.contamination,
            random_state  = 42,
        )
        self.model.fit(X_sc)
        logger.info("Isolation Forest trained on healthy samples")

    def score(self, df: pd.DataFrame) -> pd.DataFrame:
        X_sc          = self.scaler.transform(df[self.feats])
        labels        = self.model.predict(X_sc)       # 1=normal -1=anomaly
        scores        = self.model.score_samples(X_sc)
        result        = df.copy()
        result["anomaly"]       = (labels == -1).astype(int)
        result["anomaly_score"] = scores
        return result

    def check_vehicle(self, sensor_data: dict) -> dict:
        """Real-time check for a single vehicle."""
        X   = pd.DataFrame([{f: sensor_data.get(f, 0) for f in self.feats}])
        X_sc = self.scaler.transform(X)
        lbl  = self.model.predict(X_sc)[0]
        sc   = float(self.model.score_samples(X_sc)[0])
        return {
            "is_anomaly":     bool(lbl == -1),
            "anomaly_score":  round(sc, 4),
            "status":         "ANOMALY DETECTED" if lbl == -1 else "Normal",
        }


# ─────────────────────────────────────────────────────────────────────────────
# LSTM AUTOENCODER
# ─────────────────────────────────────────────────────────────────────────────
class LSTMAutoencoder:
    """
    LSTM Autoencoder for detecting anomalous charging sessions.
    Input: (batch, seq_len, n_features) — e.g., (B, 60, 5)
    Features: voltage, current, temperature, soc, power
    """

    def __init__(self, n_features: int = 5, hidden: int = 32, layers: int = 1):
        self.n_features = n_features
        self.hidden     = hidden
        self.layers     = layers
        self.model      = None
        self.mean: Optional[np.ndarray] = None
        self.std:  Optional[np.ndarray] = None
        self.threshold: Optional[float] = None

    def _build_model(self):
        import torch.nn as nn

        class _Model(nn.Module):
            def __init__(self, n_feat, hid, nl):
                super().__init__()
                self.enc = nn.LSTM(n_feat, hid, nl, batch_first=True)
                self.dec = nn.LSTM(hid,    hid, nl, batch_first=True)
                self.out = nn.Linear(hid, n_feat)

            def forward(self, x):
                _, (h, c)   = self.enc(x)
                dec_in      = x.new_zeros(x.shape)
                dec_out, _  = self.dec(dec_in, (h, c))
                return self.out(dec_out)

        return _Model(self.n_features, self.hidden, self.layers)

    @staticmethod
    def generate_sessions(n: int, seq_len: int = 60,
                          anomaly: bool = False) -> np.ndarray:
        """Generate synthetic charging sessions."""
        sessions = []
        for _ in range(n):
            t       = np.linspace(0, 1, seq_len)
            voltage = 3.2 + 0.8 * (1 - np.exp(-3 * t)) + np.random.normal(0, 0.01, seq_len)
            current = 100 * np.exp(-2 * t) + np.random.normal(0, 2, seq_len)
            temp    = 25 + 15 * t + np.random.normal(0, 0.5, seq_len)
            soc     = 100 * t + np.random.normal(0, 1, seq_len)
            power   = voltage * current / 1000

            if anomaly:
                spike = np.random.randint(20, 50)
                current[spike:spike + 5] *= 2.5
                temp[spike:spike + 5]    += 22

            sessions.append(np.stack([voltage, current, temp, soc, power], axis=1))

        return np.array(sessions, dtype=np.float32)

    def train(self, sessions: np.ndarray, epochs: int = 40, lr: float = 1e-3):
        import torch
        import torch.nn as nn

        self.mean = sessions.mean(axis=(0, 1))
        self.std  = sessions.std(axis=(0, 1)) + 1e-8
        X         = torch.tensor((sessions - self.mean) / self.std)

        self.model = self._build_model()
        opt    = torch.optim.Adam(self.model.parameters(), lr=lr)
        loss_fn = nn.MSELoss()

        self.model.train()
        for ep in range(epochs):
            opt.zero_grad()
            recon = self.model(X)
            loss  = loss_fn(recon, X)
            loss.backward()
            opt.step()
            if (ep + 1) % 10 == 0:
                logger.info(f"  Epoch {ep+1}/{epochs}  Loss: {loss.item():.6f}")

        # Set threshold = 3x average training reconstruction error
        with torch.no_grad():
            recon   = self.model(X)
            errors  = ((recon - X) ** 2).mean(dim=(1, 2)).numpy()
        self.threshold = float(errors.mean() * 3)
        logger.info(f"Threshold set: {self.threshold:.6f}")

    def detect(self, sessions: np.ndarray) -> dict:
        import torch, torch.nn as nn
        X      = torch.tensor((sessions - self.mean) / self.std)
        loss_fn = torch.nn.MSELoss()
        with torch.no_grad():
            recon  = self.model(X)
            errors = ((recon - X) ** 2).mean(dim=(1, 2)).numpy()
        labels = (errors > self.threshold).astype(int)
        return {
            "errors":    errors.tolist(),
            "labels":    labels.tolist(),
            "threshold": self.threshold,
            "n_anomaly": int(labels.sum()),
        }

    def save(self, path: str):
        import torch
        torch.save({
            "model_state": self.model.state_dict(),
            "mean":        self.mean,
            "std":         self.std,
            "threshold":   self.threshold,
            "config": {"n_features": self.n_features,
                       "hidden": self.hidden, "layers": self.layers},
        }, path)
        logger.info(f"LSTM AE saved: {path}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Generating dataset...")
    df = generate_battery_dataset(1000)
    print(f"Dataset: {len(df)} rows | failure rate: {df.failure_within_30_days.mean()*100:.1f}%")

    print("\nTraining XGBoost...")
    predictor = BatteryFailurePredictor()
    predictor.train(df)

    print("\nTest prediction:")
    result = predictor.predict({
        "cycle_count": 900, "soh_pct": 72, "capacity_fade_pct": 28,
        "avg_charge_temp_c": 50, "max_discharge_c_rate": 2.8,
        "voltage_spread_mv": 95, "internal_resistance_mohm": 30,
        "calendar_age_days": 1200, "fast_charge_ratio": 0.65,
        "deep_discharge_count": 18,
    })
    print(result)
