"""
battery/ekf_soc.py
Extended Kalman Filter for battery State-of-Charge estimation.
"""
import numpy as np
from dataclasses import dataclass, field
from typing import List


@dataclass
class BatteryParams:
    capacity_ah:     float = 75.0    # Battery capacity in Ah
    r_internal:      float = 0.012   # Internal resistance (Ohm)
    q_noise:         float = 1e-5    # Process noise variance
    r_noise:         float = 1e-3    # Measurement noise variance
    initial_soc:     float = 1.0     # Initial SOC estimate (0-1)
    initial_p:       float = 0.01    # Initial state covariance


class BatteryEKF:
    """
    Extended Kalman Filter for SOC estimation.
    State: x = [SOC]  (0 to 1)
    Measurement: terminal voltage V = OCV(SOC) - R_int * I
    """

    def __init__(self, params: BatteryParams = None):
        p = params or BatteryParams()
        self.Q    = p.capacity_ah
        self.R    = p.r_internal
        self.x    = np.array([p.initial_soc])
        self.P    = np.array([[p.initial_p]])
        self.Qn   = np.array([[p.q_noise]])
        self.Rn   = np.array([[p.r_noise]])
        self.history: List[dict] = []

    def ocv(self, soc: float) -> float:
        """Open-circuit voltage from SOC — 4th-order polynomial fit."""
        s = float(np.clip(soc, 0.0, 1.0))
        return 3.2 + 0.9*s - 0.3*s**2 + 0.15*s**3

    def docv_dsoc(self, soc: float) -> float:
        """Jacobian of OCV w.r.t. SOC."""
        s = float(np.clip(soc, 0.0, 1.0))
        return 0.9 - 0.6*s + 0.45*s**2

    def predict(self, current_a: float, dt_s: float = 60.0):
        """Prediction step: advance SOC by coulomb counting."""
        d_soc     = -current_a * dt_s / (self.Q * 3600.0)
        self.x[0] = float(np.clip(self.x[0] + d_soc, 0.0, 1.0))
        self.P    = self.P + self.Qn

    def update(self, v_measured: float, current_a: float) -> float:
        """Update step: correct SOC using measured terminal voltage."""
        soc = self.x[0]
        v_pred = self.ocv(soc) - self.R * current_a
        H      = np.array([[self.docv_dsoc(soc)]])
        S      = H @ self.P @ H.T + self.Rn
        K      = self.P @ H.T / float(S[0, 0])
        innov  = v_measured - v_pred
        self.x = self.x + K.flatten() * innov
        self.x[0] = float(np.clip(self.x[0], 0.0, 1.0))
        self.P = (np.eye(1) - K @ H) @ self.P
        return float(self.x[0])

    def step(self, current_a: float, v_measured: float, dt_s: float = 60.0) -> dict:
        """Run one full predict+update cycle and log the result."""
        self.predict(current_a, dt_s)
        soc_est = self.update(v_measured, current_a)
        record  = {
            "soc_est": round(soc_est * 100, 2),
            "soc_raw": round(self.x[0] * 100, 2),
            "voltage": round(v_measured, 3),
            "current": round(current_a, 1),
            "p_var":   round(float(self.P[0, 0]), 8),
        }
        self.history.append(record)
        return record


def simulate_discharge(
    capacity_ah: float = 75.0,
    initial_soc: float = 0.80,
    discharge_current: float = 60.0,
    steps: int = 20,
    noise_std: float = 0.015,
) -> List[dict]:
    """
    Simulate a discharge test and run EKF, returning step-by-step results.
    """
    params  = BatteryParams(capacity_ah=capacity_ah, initial_soc=initial_soc)
    ekf     = BatteryEKF(params)
    results = []
    true_soc = initial_soc

    for step in range(steps):
        I        = discharge_current + np.random.randn() * 3.0
        true_soc = max(0.0, true_soc - I * 60 / (capacity_ah * 3600))
        v_true   = ekf.ocv(true_soc) - params.r_internal * I
        v_noisy  = v_true + np.random.randn() * noise_std

        rec = ekf.step(I, v_noisy)
        rec["step"]     = step + 1
        rec["true_soc"] = round(true_soc * 100, 2)
        rec["error_pct"]= round(abs(rec["soc_est"] - rec["true_soc"]), 2)
        results.append(rec)

    return results


if __name__ == "__main__":
    results = simulate_discharge()
    print(f"{'Step':>4} {'True SOC':>10} {'Est SOC':>10} {'Voltage':>9} {'Error':>8}")
    print("-" * 48)
    for r in results:
        print(f"{r['step']:>4}  {r['true_soc']:>9.2f}%  "
              f"{r['soc_est']:>9.2f}%  {r['voltage']:>8.3f}V  {r['error_pct']:>7.2f}%")
    print(f"\nFinal SOC estimate: {results[-1]['soc_est']:.1f}%")
    print(f"Mean absolute error: {sum(r['error_pct'] for r in results)/len(results):.3f}%")
