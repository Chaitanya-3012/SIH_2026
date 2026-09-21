import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import joblib
from collections import deque

# Re-define model architecture for loading state dict
class LSTMAutoencoder(nn.Module):
    def __init__(self, seq_len=12, num_features=3, embedding_dim=16):
        super(LSTMAutoencoder, self).__init__()
        self.seq_len = seq_len
        self.num_features = num_features
        self.encoder_lstm = nn.LSTM(num_features, embedding_dim, batch_first=True)
        self.decoder_lstm = nn.LSTM(embedding_dim, embedding_dim, batch_first=True)
        self.decoder_fc = nn.Linear(embedding_dim, num_features)

    def forward(self, x):
        _, (hn, _) = self.encoder_lstm(x)
        decoder_input = hn.permute(1, 0, 2).repeat(1, self.seq_len, 1)
        out, _ = self.decoder_lstm(decoder_input)
        out = self.decoder_fc(out)
        return out

class SkyGuardDetector:
    def __init__(self, scaler_path='scaler.joblib', if_path='isolation_forest.joblib', lstm_path='lstm_autoencoder.pth'):
        # 1. Load saved artifacts
        self.scaler = joblib.load(scaler_path)
        self.iso_forest = joblib.load(if_path)

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = LSTMAutoencoder()
        self.model.load_state_dict(torch.load(lstm_path, map_location=self.device))
        self.model.eval()

        # 2. Hardcode optimized calibrated thresholds from the latest pipeline execution
        self.threshold_drift = 25.0
        self.threshold_ensemble = 0.4170

        # 3. Queue to store sliding history for real-time temporal evaluation (Max drift window = 24)
        self.history = deque(maxlen=24)
        self.features = ['temperature', 'sea_level_pressure', 'relative_humidity']

    def update_history(self, record_dict):
        """Append a dictionary of raw values to the rolling state."""
        self.history.append(record_dict)

    def _get_history_df(self):
        df = pd.DataFrame(list(self.history))
        # Handle missing values using forward/backward fill internally
        for col in self.features:
            df[col] = pd.to_numeric(df[col], errors='coerce').ffill().bfill()
        return df

    def detect_anomaly(self, current_record, is_dropout=False):
        """
        Evaluates the current record against the calibrated ensemble.
        current_record: dict containing {'temperature', 'sea_level_pressure', 'relative_humidity'}
        is_dropout: Boolean indicating if there was an actual sensor communication failure/timeout
        """
        self.update_history(current_record)

        # If we don't have enough history to evaluate sequential features, return false
        if len(self.history) < 24:
            return {"is_anomaly": False, "ensemble_score": 0.0, "status": "Warmup Phase"}

        df_history = self._get_history_df()
        scaled_history = self.scaler.transform(df_history[self.features])

        # 1. Isolation Forest Score
        current_scaled = scaled_history[-1].reshape(1, -1)
        if_decision = -self.iso_forest.decision_function(current_scaled)[0]
        # Map score realistically using a scaling min/max from calibration
        if_score = np.clip((if_decision + 0.5) / 1.0, 0.0, 1.0)

        # 2. LSTM Autoencoder Score
        seq_data = scaled_history[-12:].reshape(1, 12, -1) # Last 12 timesteps
        with torch.no_grad():
            seq_torch = torch.tensor(seq_data, dtype=torch.float32).to(self.device)
            reconstructed = self.model(seq_torch)
            mse = torch.mean((seq_torch - reconstructed) ** 2).item()
        lstm_score = np.clip(mse / 2.0, 0.0, 1.0) # Map to [0,1]

        # 3. Physical Consistency Check
        t, r, p = current_record['temperature'], current_record['relative_humidity'], current_record['sea_level_pressure']
        physical_score = 0.0
        if t is None or r is None or p is None or pd.isna(t) or pd.isna(r) or pd.isna(p):
            physical_score = 1.0
        else:
            if t > 40.0 and r > 90.0: physical_score += 0.5
            if r < 1.0 or r > 105.0: physical_score += 0.8
            if p < 920 or p > 1050: physical_score += 0.5
        physical_score = min(physical_score, 1.0)

        # 4. Temporal Stability Check
        stability_score = 0.0
        # Check standard deviation of last 3 steps
        for col in self.features:
            vals = df_history[col].values[-3:]
            if len(vals) == 3 and np.std(vals) == 0.0:
                stability_score += 0.8
        if is_dropout:
            stability_score += 0.6
        stability_score = min(stability_score, 1.0)

        # 5. Drift Check (Slope over last 24 steps)
        slopes = []
        for col in self.features:
            diff = abs(df_history[col].values[-1] - df_history[col].values[0])
            slopes.append(diff)
        max_slope = max(slopes)
        drift_score = np.clip(max_slope / (self.threshold_drift + 1e-8), 0.0, 1.0)

        # Optimized Weighted Ensemble Calculation
        ensemble_score = (0.15 * lstm_score) + (0.15 * if_score) + (0.10 * physical_score) + (0.30 * stability_score) + (0.30 * drift_score)
        is_anomaly = ensemble_score >= self.threshold_ensemble

        return {
            "is_anomaly": bool(is_anomaly),
            "ensemble_score": float(ensemble_score),
            "breakdown": {
                "lstm_score": float(lstm_score),
                "isolation_forest": float(if_score),
                "physical_consistency": float(physical_score),
                "temporal_stability": float(stability_score),
                "drift": float(drift_score)
            }
        }
