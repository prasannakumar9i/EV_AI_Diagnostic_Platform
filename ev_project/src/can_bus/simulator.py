"""
can_bus/simulator.py
Simulates EV CAN bus messages — no physical hardware required.
Works in Google Colab.
"""
import struct
import time
import random
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CANMessage:
    arbitration_id: int
    data: bytes
    timestamp: float = field(default_factory=time.time)
    channel: str = "vcan0"


class EVCANSimulator:
    """
    Simulates a full EV CAN bus with BMS, motor, charger, and VCU frames.

    Frame IDs follow a typical EV architecture:
      0x100  VCU  — Vehicle Control Unit
      0x300  BMS  — Battery Management System
      0x400  MCU  — Motor Control Unit
      0x500  OBC  — On-Board Charger
      0x600  TPMS — Tyre Pressure Monitoring
    """

    BMS_ID     = 0x300
    MOTOR_ID   = 0x400
    VCU_ID     = 0x100
    CHARGER_ID = 0x500
    TPMS_ID    = 0x600

    def __init__(
        self,
        capacity_ah: float = 75.0,
        initial_soc: float = 0.78,
        nominal_voltage: float = 400.0,
    ):
        self.capacity_ah     = capacity_ah
        self.soc             = initial_soc        # 0.0 – 1.0
        self.voltage         = nominal_voltage * initial_soc
        self.current         = 0.0
        self.batt_temp       = 27.0               # °C
        self.motor_rpm       = 0
        self.motor_temp      = 25.0
        self.charger_power   = 0.0                # kW
        self.tyre_pressures  = [220, 218, 222, 219]  # kPa (FL FR RL RR)

    # ── BMS frame ────────────────────────────────────────────────────────────
    def bms_frame(self, discharge_current: float = 60.0) -> CANMessage:
        """Pack voltage (0.1V), current (0.1A), SOC (%) into 8 bytes."""
        dt = 0.1  # seconds per call
        self.soc   = max(0.0, self.soc - discharge_current * dt / (self.capacity_ah * 3600))
        self.voltage = 300.0 + (self.soc * 120.0) + random.gauss(0, 0.3)
        self.current = discharge_current + random.gauss(0, 2.0)
        self.batt_temp = min(70.0, self.batt_temp + random.uniform(-0.05, 0.12))

        v_raw  = int(self.voltage  * 10) & 0xFFFF
        i_raw  = int(self.current  * 10) & 0xFFFF
        soc_raw = int(self.soc * 100)   & 0xFF
        t_raw  = int(self.batt_temp * 10) & 0xFFFF

        data = struct.pack('>HHBH', v_raw, i_raw, soc_raw, t_raw) + b'\x00'
        return CANMessage(self.BMS_ID, data)

    # ── Motor frame ───────────────────────────────────────────────────────────
    def motor_frame(self, target_rpm: int = 3000) -> CANMessage:
        self.motor_rpm = max(0, min(15000,
            self.motor_rpm + random.randint(-200, 300)))
        self.motor_temp = min(120.0, self.motor_temp + random.uniform(-0.1, 0.2))

        data = struct.pack('>HH', self.motor_rpm, int(self.motor_temp * 10)) + b'\x00\x00\x00\x00'
        return CANMessage(self.MOTOR_ID, data)

    # ── VCU frame ─────────────────────────────────────────────────────────────
    def vcu_frame(self, speed_kph: float = 80.0) -> CANMessage:
        speed_raw  = int(speed_kph * 10) & 0xFFFF
        gear       = 4 if speed_kph > 60 else 3 if speed_kph > 30 else 1
        regen_pct  = random.randint(0, 30)
        data = struct.pack('>HBB', speed_raw, gear, regen_pct) + b'\x00\x00\x00\x00'
        return CANMessage(self.VCU_ID, data)

    # ── Charger frame ─────────────────────────────────────────────────────────
    def charger_frame(self, charging: bool = False, power_kw: float = 50.0) -> CANMessage:
        if charging:
            self.charger_power = power_kw
            self.soc = min(1.0, self.soc + power_kw * 0.1 / (self.capacity_ah * 0.4))
        else:
            self.charger_power = 0.0
        pwr_raw  = int(self.charger_power * 10) & 0xFFFF
        status   = 0x02 if charging else 0x00   # 0=idle 1=connecting 2=charging
        data = struct.pack('>HBB', pwr_raw, status, int(self.soc * 100)) + b'\x00\x00\x00'
        return CANMessage(self.CHARGER_ID, data)

    # ── TPMS frame ────────────────────────────────────────────────────────────
    def tpms_frame(self) -> CANMessage:
        self.tyre_pressures = [
            max(150, p + random.randint(-2, 1)) for p in self.tyre_pressures
        ]
        data = struct.pack('>HHHH', *self.tyre_pressures)
        return CANMessage(self.TPMS_ID, data)

    # ── Decode helpers ────────────────────────────────────────────────────────
    @staticmethod
    def decode_bms(msg: CANMessage) -> dict:
        v, i, soc, t = struct.unpack('>HHBH', msg.data[:7])
        return {
            "voltage_v":    round(v / 10, 1),
            "current_a":    round(i / 10, 1),
            "soc_pct":      soc,
            "batt_temp_c":  round(t / 10, 1),
        }

    @staticmethod
    def decode_motor(msg: CANMessage) -> dict:
        rpm, t = struct.unpack('>HH', msg.data[:4])
        return {"rpm": rpm, "motor_temp_c": round(t / 10, 1)}

    @staticmethod
    def decode_tpms(msg: CANMessage) -> dict:
        fl, fr, rl, rr = struct.unpack('>HHHH', msg.data[:8])
        return {"FL_kPa": fl, "FR_kPa": fr, "RL_kPa": rl, "RR_kPa": rr}


# ── Demo ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    bus = EVCANSimulator(initial_soc=0.75)
    print(f"{'Frame':<5} {'ID':<8} {'Voltage':>9} {'Current':>9} {'SOC':>6} {'Temp':>8}")
    print("-" * 50)
    for i in range(10):
        msg  = bus.bms_frame(discharge_current=80.0)
        dec  = EVCANSimulator.decode_bms(msg)
        print(f"{i+1:<5} 0x{msg.arbitration_id:04X}  "
              f"{dec['voltage_v']:>8.1f}V  {dec['current_a']:>8.1f}A  "
              f"{dec['soc_pct']:>5}%  {dec['batt_temp_c']:>7.1f}°C")
        time.sleep(0.05)
