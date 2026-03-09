"""
obd/dtc_reader.py
OBD-II DTC database and diagnostic reader for EVs.
"""
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class DTCRecord:
    code: str
    description: str
    severity: str           # LOW | MEDIUM | HIGH | CRITICAL
    system: str             # battery | motor | charging | brakes | safety
    action: str
    safe_to_drive: bool


# ── EV DTC Database ──────────────────────────────────────────────────────────
EV_DTC_DB: Dict[str, DTCRecord] = {
    # Battery / BMS
    "P0A0F": DTCRecord("P0A0F","Battery Pack Overvoltage","HIGH","battery",
                       "Check charger output and BMS firmware version",False),
    "P0A1B": DTCRecord("P0A1B","Battery Temperature Sensor Malfunction","MEDIUM","battery",
                       "Inspect BMS connector pins; replace sensor if open circuit",True),
    "P0A1D": DTCRecord("P0A1D","Cell Voltage Imbalance Detected","HIGH","battery",
                       "Run full cell-balancing cycle; check individual cell voltages",False),
    "P0A80": DTCRecord("P0A80","Replace Hybrid/EV Battery Pack","CRITICAL","battery",
                       "Battery SOH below safe threshold — schedule battery replacement",False),
    "P0AFA": DTCRecord("P0AFA","Battery State of Health Below Threshold","HIGH","battery",
                       "Log SOH trend; plan battery service within 3 months",True),
    "P0C6B": DTCRecord("P0C6B","Battery Cooling System Fault","HIGH","battery",
                       "Check coolant level, pump operation, and thermostat",False),
    "P0A78": DTCRecord("P0A78","Battery Current Sensor Malfunction","MEDIUM","battery",
                       "Calibrate or replace current sensor",True),

    # Motor / Inverter
    "P0B23": DTCRecord("P0B23","Motor Temperature Exceeds Limit","HIGH","motor",
                       "Allow motor to cool; check motor cooling circuit",False),
    "P0B40": DTCRecord("P0B40","Inverter Overcurrent Detected","CRITICAL","motor",
                       "Replace inverter assembly — do not attempt field repair",False),
    "P0B42": DTCRecord("P0B42","Motor Rotor Position Sensor Fault","HIGH","motor",
                       "Inspect resolver/encoder wiring; recalibrate",False),
    "P0B60": DTCRecord("P0B60","Motor Stator Open Circuit","CRITICAL","motor",
                       "Replace motor assembly",False),

    # Charging
    "P0D30": DTCRecord("P0D30","Charging Port Fault — Latch Error","MEDIUM","charging",
                       "Inspect port locking mechanism and pin condition",True),
    "P0D3A": DTCRecord("P0D3A","On-Board Charger Communication Lost","MEDIUM","charging",
                       "Check OBC CAN connection; update OBC firmware",True),
    "P0D50": DTCRecord("P0D50","AC Charging Inlet Overcurrent","HIGH","charging",
                       "Check EVSE cable and charging station output",False),

    # CAN / Communication
    "U0100": DTCRecord("U0100","CAN Bus Lost — ECU Not Responding","MEDIUM","safety",
                       "Check CAN wiring continuity and termination resistors",False),
    "U0110": DTCRecord("U0110","Lost Comm with Drive Motor Control Module","HIGH","motor",
                       "Inspect MCU power supply and CAN harness",False),
    "U0167": DTCRecord("U0167","Lost Comm with Vehicle Immobilizer Control Module","MEDIUM","safety",
                       "Check immobilizer module and key transponder",False),

    # Brakes / Regen
    "C0035": DTCRecord("C0035","Right Front Wheel Speed Sensor Circuit Malfunction","MEDIUM","brakes",
                       "Replace or clean wheel speed sensor",True),
    "C121C": DTCRecord("C121C","Brake Pedal Position Sensor Fault","HIGH","brakes",
                       "Replace brake pedal position sensor",False),
}


def decode_dtc_range(code: str) -> str:
    """Return which system a DTC code belongs to based on prefix."""
    prefix = code[0].upper()
    ranges = {
        'P': 'Powertrain (Engine/Motor/Battery)',
        'C': 'Chassis (Brakes/Steering/Suspension)',
        'B': 'Body (Lights/Doors/HVAC)',
        'U': 'Network/Communication',
    }
    return ranges.get(prefix, 'Unknown')


class DTCReader:
    """Reads and diagnoses DTC codes against the EV database."""

    def __init__(self, db: Dict[str, DTCRecord] = None):
        self.db = db or EV_DTC_DB

    def lookup(self, code: str) -> Optional[DTCRecord]:
        return self.db.get(code.upper().strip())

    def diagnose(self, codes: List[str], print_report: bool = True) -> dict:
        found, unknown = [], []
        safe_to_drive  = True
        highest_sev    = "OK"
        order = {"OK": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

        for code in codes:
            rec = self.lookup(code)
            if rec:
                found.append(rec)
                if not rec.safe_to_drive:
                    safe_to_drive = False
                if order[rec.severity] > order[highest_sev]:
                    highest_sev = rec.severity
            else:
                unknown.append(code)

        report = {
            "total_codes": len(codes),
            "known_codes": len(found),
            "unknown_codes": unknown,
            "highest_severity": highest_sev,
            "safe_to_drive": safe_to_drive,
            "records": found,
        }

        if print_report:
            self._print_report(report)

        return report

    def _print_report(self, report: dict):
        SEV_PAD = {"CRITICAL": "[CRITICAL]", "HIGH": "[HIGH]    ",
                   "MEDIUM":   "[MEDIUM]  ", "LOW":  "[LOW]     ", "OK": "[OK]      "}
        print("=" * 70)
        print(f"  EV DTC DIAGNOSTIC REPORT")
        print(f"  Total codes: {report['total_codes']}  |  "
              f"Highest severity: {report['highest_severity']}  |  "
              f"Safe to drive: {'YES' if report['safe_to_drive'] else 'NO'}")
        print("=" * 70)
        for rec in report["records"]:
            print(f"\n  {SEV_PAD[rec.severity]} {rec.code}  [{rec.system.upper()}]")
            print(f"  Description: {rec.description}")
            print(f"  Action:      {rec.action}")
        if report["unknown_codes"]:
            print(f"\n  UNKNOWN CODES (not in local DB): {', '.join(report['unknown_codes'])}")
        print("=" * 70)


if __name__ == "__main__":
    reader = DTCReader()
    reader.diagnose(["P0A0F", "P0C6B", "U0100", "PZZZZ"])
