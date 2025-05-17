# cr300_generator.py

import sys

# Constants for CR300 generation
MAX_SDI12_SENSORS_CR300 = 62
# Implexx sensor documentation generally suggests 10-minute intervals as a minimum.
# CR300 can handle faster, but respecting sensor limits is key.
MIN_MEASURE_INTERVAL_MINUTES_IMPLEX = 10
STANDARD_MEASURE_WAIT_SEC_IMPLEX = 100 # ~95s measurement time + buffer
ADDITIONAL_MEASURE_WAIT_SEC_IMPLEX = 2  # Data available immediately after M1-M6 service request

def generate_code(num_sensors, measure_interval_min):
    """
    Generates CRBasic code for CR300 series dataloggers to read
    20 specified measurements from multiple Implexx sap flow sensors (0 to N-1).
    Uses a single data table for all sensors.

    Args:
        num_sensors (int): The number of sensors (1 to MAX_SDI12_SENSORS_CR300).
        measure_interval_min (int): The measurement interval in minutes (>= MIN_MEASURE_INTERVAL_MINUTES_IMPLEX).

    Returns:
        str: The generated CRBasic program as a string, or an error string.
    """

    # --- Module-specific Validation ---
    if not (1 <= num_sensors <= MAX_SDI12_SENSORS_CR300):
        return (f"' Error in cr300_generator: Number of sensors must be between 1 and "
                f"{MAX_SDI12_SENSORS_CR300}.")
    if measure_interval_min < MIN_MEASURE_INTERVAL_MINUTES_IMPLEX:
        # main_cli.py might handle this as a warning; this module can be strict or just note it.
        # Let's return an error for now if it's below the Implexx recommended minimum.
        return (f"' Error in cr300_generator: Implexx sensors recommend a measurement interval of at least "
                f"{MIN_MEASURE_INTERVAL_MINUTES_IMPLEX} minutes.")

    # Define the 20 measurements of interest and their internal variable names
    # (CR300 allows longer, more descriptive names)
    # Grouped by the command sequence that retrieves them
    # Format: (base_var_name, num_values_from_D0, units_for_aliases, D0_indices_to_keep, alias_suffixes)
    # D0_indices_to_keep refers to the 0-indexed position in the D0! response from the sensor
    # Alias_suffixes are the short names for the DataTable FieldNames.
    measurements_config = {
        "Standard_M_D0": { # From M! then D0! (AlphaOuter, AlphaInner)
            "command": "M!", "d_command": "D0!", "pause_sec": STANDARD_MEASURE_WAIT_SEC_IMPLEX,
            "num_D0_values": 5, # Sensor returns 5: SapFlowTotal, SFDOuter, SFDInner, AlphaOuter, AlphaInner
            "data_points": [
                {"index_in_D0": 3, "alias_suffix": "AlpOut", "unit": "ratio"},
                {"index_in_D0": 4, "alias_suffix": "AlpInn", "unit": "ratio"},
            ]
        },
        "Standard_M_D1": { # From M! then D1! (BetaOuter, BetaInner, tMaxTouter, tMaxTinner)
            "command": "M!", "d_command": "D1!", "pause_sec": 0, # Pause already happened after M!
            "num_D1_values": 4, # Sensor returns 4: BetaOuter, BetaInner, tMaxTouter, tMaxTinner
            "data_points": [
                {"index_in_D1": 0, "alias_suffix": "BetOut", "unit": "ratio"},
                {"index_in_D1": 1, "alias_suffix": "BetInn", "unit": "ratio"},
                {"index_in_D1": 2, "alias_suffix": "tMxTout", "unit": "sec"},
                {"index_in_D1": 3, "alias_suffix": "tMxTinn", "unit": "sec"},
            ]
        },
        "M1_OuterTemps": { # From M1! then D0!
            "command": "M1!", "d_command": "D0!", "pause_sec": ADDITIONAL_MEASURE_WAIT_SEC_IMPLEX,
            "num_D0_values": 6, # TpreDsOuter, dTmaxDsOuter, TpostDsOuter, TpreUsOuter, dTmaxUsOuter, TpostUsOuter
            "data_points": [
                {"index_in_D0": 0, "alias_suffix": "TpDsOut", "unit": "degC"},
                {"index_in_D0": 1, "alias_suffix": "dTDsOut", "unit": "degC"},
                {"index_in_D0": 2, "alias_suffix": "TsDsOut", "unit": "degC"},
                {"index_in_D0": 3, "alias_suffix": "TpUsOut", "unit": "degC"},
                {"index_in_D0": 4, "alias_suffix": "dTUsOut", "unit": "degC"},
                {"index_in_D0": 5, "alias_suffix": "TsUsOut", "unit": "degC"},
            ]
        },
        "M2_InnerTemps": { # From M2! then D0!
            "command": "M2!", "d_command": "D0!", "pause_sec": ADDITIONAL_MEASURE_WAIT_SEC_IMPLEX,
            "num_D0_values": 6, # TpreDsInner, dTmaxDsInner, TpostDsInner, TpreUsInner, dTmaxUsInner, TpostUsInner
            "data_points": [
                {"index_in_D0": 0, "alias_suffix": "TpDsInn", "unit": "degC"},
                {"index_in_D0": 1, "alias_suffix": "dTDsInn", "unit": "degC"},
                {"index_in_D0": 2, "alias_suffix": "TsDsInn", "unit": "degC"},
                {"index_in_D0": 3, "alias_suffix": "TpUsInn", "unit": "degC"},
                {"index_in_D0": 4, "alias_suffix": "dTUsInn", "unit": "degC"},
                {"index_in_D0": 5, "alias_suffix": "TsUsInn", "unit": "degC"},
            ]
        },
        "M5_UpstreamMaxT": { # From M5! then D0!
            "command": "M5!", "d_command": "D0!", "pause_sec": ADDITIONAL_MEASURE_WAIT_SEC_IMPLEX,
            "num_D0_values": 2, # tMaxTusOuter, tMaxTusInner
            "data_points": [
                {"index_in_D0": 0, "alias_suffix": "tMxTUsO", "unit": "sec"}, # tMaxTusOuter
                {"index_in_D0": 1, "alias_suffix": "tMxTUsI", "unit": "sec"}, # tMaxTusInner
            ]
        }
    }

    # Helper to get SDI-12 address character (0-9, a-z, A-Z)
    def get_sdi12_address_char(index):
        if 0 <= index <= 9:
            return str(index)
        elif 10 <= index <= 35: # a-z
            return chr(ord('a') + (index - 10))
        elif 36 <= index <= 61: # A-Z
            return chr(ord('A') + (index - 36))
        else:
            raise ValueError("Sensor index out of SDI-12 addressable range (0-61)")

    crbasic_code = []

    # --- File Header ---
    crbasic_code.append("' CR300 Series Datalogger Program")
    crbasic_code.append("' Program to log specified data from Implexx Sap Flow Sensors")
    crbasic_code.append("' Generated by Python Script (cr300_generator.py)")
    crbasic_code.append(f"' Number of Sensors: {num_sensors}")
    crbasic_code.append(f"' Measurement Interval: {measure_interval_min} minutes")
    crbasic_code.append(f"' Implexx Standard Measurement Wait: {STANDARD_MEASURE_WAIT_SEC_IMPLEX} sec")
    crbasic_code.append(f"' Implexx Additional Measurement Wait: {ADDITIONAL_MEASURE_WAIT_SEC_IMPLEX} sec")
    crbasic_code.append("")

    # --- Constants ---
    crbasic_code.append("'--- Constants ---")
    crbasic_code.append(f"Const MEAST_INTERVAL_MIN = {measure_interval_min}")
    crbasic_code.append(f"Const SDI12_PORT = C1 ' Default SDI-12 Port on CR300 (can be C1 or C2)")
    # Note: Implexx guide says 10 min data collect interval. Pause is for measurement completion.
    crbasic_code.append(f"Const STD_MEAS_WAIT_MS = {STANDARD_MEASURE_WAIT_SEC_IMPLEX * 1000}")
    crbasic_code.append(f"Const ADD_MEAS_WAIT_MS = {ADDITIONAL_MEASURE_WAIT_SEC_IMPLEX * 1000}")
    crbasic_code.append("")

    # --- Declare Public Variables ---
    crbasic_code.append("'--- Declare Public Variables ---")
    crbasic_code.append("Public PTemp As Float")
    crbasic_code.append("Public Batt_volt As Float")
    crbasic_code.append("")
    crbasic_code.append("' Variables to hold the 20 measurements per sensor")
    # Create a flat list of all variable names that will be logged
    all_data_points_vars = []
    for i in range(num_sensors):
        sdi_char = get_sdi12_address_char(i)
        for group_key, group_config in measurements_config.items():
            for dp_config in group_config["data_points"]:
                var_name = f"S{sdi_char}_{dp_config['alias_suffix']}"
                crbasic_code.append(f"Public {var_name} As Float : Units {var_name}={dp_config['unit']}")
                all_data_points_vars.append(var_name)
    crbasic_code.append("")

    # Temporary arrays for SDI12Recorder to read into (one per distinct D-command size)
    crbasic_code.append("' Temporary arrays for SDI12Recorder responses")
    crbasic_code.append("Dim TempD_2Val(2) As Float") # For M5
    crbasic_code.append("Dim TempD_4Val(4) As Float") # For M/D1
    crbasic_code.append("Dim TempD_5Val(5) As Float") # For M/D0
    crbasic_code.append("Dim TempD_6Val(6) As Float") # For M1/D0, M2/D0
    crbasic_code.append("")
    crbasic_code.append("Dim SDI12CmdString As String * 10")
    crbasic_code.append("Dim SDI12ReturnCode As Long")
    crbasic_code.append("Dim SDI12ExpectedValues As Long ' For atttn response from M/C commands")
    crbasic_code.append("")


    # --- DataTable Definition ---
    crbasic_code.append("'--- DataTable Definition ---")
    crbasic_code.append("DataTable (SapFlowAll, True, -1)") # True for logging on scan, -1 for fill/stop
    crbasic_code.append(f"  DataInterval (0, MEAST_INTERVAL_MIN, Min, 0)") # 0 offset, log every interval
    crbasic_code.append("  Sample (1, Batt_volt, FP2)")
    crbasic_code.append("  Sample (1, PTemp, FP2)")
    for var_name in all_data_points_vars:
        crbasic_code.append(f"  Sample (1, {var_name}, IEEE4)") # Use IEEE4 for float precision
    crbasic_code.append("EndTable")
    crbasic_code.append("")

    # --- Main Program ---
    crbasic_code.append("'--- Main Program ---")
    crbasic_code.append("SequentialMode ' Ensure instructions complete before next")
    crbasic_code.append("BeginProg")
    crbasic_code.append(f"  Scan (MEAST_INTERVAL_MIN, Min, 0, 0)") # Scan interval, units, buffer, count
    crbasic_code.append("    PanelTemp (PTemp, 273.15)") # 273.15 for Kelvin, or remove for Celsius
    crbasic_code.append("    Battery (Batt_volt)")
    crbasic_code.append("")

    for i in range(num_sensors):
        sdi_char = get_sdi12_address_char(i)
        crbasic_code.append(f"    ' --- Sensor {sdi_char} (Address \"{sdi_char}\") ---")

        # Standard Measurement M! (D0 and D1 parts)
        # Send M!
        crbasic_code.append(f"    SDICmdString = \"{sdi_char}M!\"")
        crbasic_code.append(f"    SDI12Recorder (SDI12ReturnCode, SDI12_PORT, SDI12CmdString, SDI12ExpectedValues, 1.0, 0)")
        crbasic_code.append(f"    If SDI12ReturnCode = 0 Then") # Command sent successfully
        crbasic_code.append(f"      Delay (0, STD_MEAS_WAIT_MS, mSec)") # Wait for measurement
        # Read D0 for M!
        crbasic_code.append(f"      SDICmdString = \"{sdi_char}D0!\"")
        crbasic_code.append(f"      SDI12Recorder (SDI12ReturnCode, SDI12_PORT, SDI12CmdString, TempD_5Val(1), 1.0, 0, -1, 5)") # Read 5 values
        crbasic_code.append(f"      If SDI12ReturnCode = 0 Then")
        crbasic_code.append(f"        S{sdi_char}_AlpOut = TempD_5Val(4) ' AlphaOuter is 4th val (index 3 in 0-indexed thinking, but CRBasic array access is 1-indexed)")
        crbasic_code.append(f"        S{sdi_char}_AlpInn = TempD_5Val(5) ' AlphaInner is 5th val")
        crbasic_code.append(f"      Else")
        crbasic_code.append(f"        S{sdi_char}_AlpOut = NAN : S{sdi_char}_AlpInn = NAN")
        crbasic_code.append(f"      EndIf")
        # Read D1 for M!
        crbasic_code.append(f"      SDICmdString = \"{sdi_char}D1!\"")
        crbasic_code.append(f"      SDI12Recorder (SDI12ReturnCode, SDI12_PORT, SDI12CmdString, TempD_4Val(1), 1.0, 0, -1, 4)") # Read 4 values
        crbasic_code.append(f"      If SDI12ReturnCode = 0 Then")
        crbasic_code.append(f"        S{sdi_char}_BetOut = TempD_4Val(1)")
        crbasic_code.append(f"        S{sdi_char}_BetInn = TempD_4Val(2)")
        crbasic_code.append(f"        S{sdi_char}_tMxTout = TempD_4Val(3)")
        crbasic_code.append(f"        S{sdi_char}_tMxTinn = TempD_4Val(4)")
        crbasic_code.append(f"      Else")
        crbasic_code.append(f"        S{sdi_char}_BetOut = NAN : S{sdi_char}_BetInn = NAN : S{sdi_char}_tMxTout = NAN : S{sdi_char}_tMxTinn = NAN")
        crbasic_code.append(f"      EndIf")
        crbasic_code.append(f"    Else") # M! command failed
        crbasic_code.append(f"      S{sdi_char}_AlpOut = NAN : S{sdi_char}_AlpInn = NAN : S{sdi_char}_BetOut = NAN : S{sdi_char}_BetInn = NAN : S{sdi_char}_tMxTout = NAN : S{sdi_char}_tMxTinn = NAN")
        crbasic_code.append(f"    EndIf")
        crbasic_code.append("")

        # M1! Command
        crbasic_code.append(f"    SDICmdString = \"{sdi_char}M1!\"")
        crbasic_code.append(f"    SDI12Recorder (SDI12ReturnCode, SDI12_PORT, SDI12CmdString, SDI12ExpectedValues, 1.0, 0)")
        crbasic_code.append(f"    If SDI12ReturnCode = 0 Then")
        crbasic_code.append(f"      Delay (0, ADD_MEAS_WAIT_MS, mSec)")
        crbasic_code.append(f"      SDICmdString = \"{sdi_char}D0!\"")
        crbasic_code.append(f"      SDI12Recorder (SDI12ReturnCode, SDI12_PORT, SDI12CmdString, TempD_6Val(1), 1.0, 0, -1, 6)")
        crbasic_code.append(f"      If SDI12ReturnCode = 0 Then")
        crbasic_code.append(f"        S{sdi_char}_TpDsOut = TempD_6Val(1) : S{sdi_char}_dTDsOut = TempD_6Val(2) : S{sdi_char}_TsDsOut = TempD_6Val(3)")
        crbasic_code.append(f"        S{sdi_char}_TpUsOut = TempD_6Val(4) : S{sdi_char}_dTUsOut = TempD_6Val(5) : S{sdi_char}_TsUsOut = TempD_6Val(6)")
        crbasic_code.append(f"      Else")
        crbasic_code.append(f"        S{sdi_char}_TpDsOut = NAN : S{sdi_char}_dTDsOut = NAN : S{sdi_char}_TsDsOut = NAN : S{sdi_char}_TpUsOut = NAN : S{sdi_char}_dTUsOut = NAN : S{sdi_char}_TsUsOut = NAN")
        crbasic_code.append(f"      EndIf")
        crbasic_code.append(f"    Else")
        crbasic_code.append(f"      S{sdi_char}_TpDsOut = NAN : S{sdi_char}_dTDsOut = NAN : S{sdi_char}_TsDsOut = NAN : S{sdi_char}_TpUsOut = NAN : S{sdi_char}_dTUsOut = NAN : S{sdi_char}_TsUsOut = NAN")
        crbasic_code.append(f"    EndIf")
        crbasic_code.append("")

        # M2! Command
        crbasic_code.append(f"    SDICmdString = \"{sdi_char}M2!\"")
        crbasic_code.append(f"    SDI12Recorder (SDI12ReturnCode, SDI12_PORT, SDI12CmdString, SDI12ExpectedValues, 1.0, 0)")
        crbasic_code.append(f"    If SDI12ReturnCode = 0 Then")
        crbasic_code.append(f"      Delay (0, ADD_MEAS_WAIT_MS, mSec)")
        crbasic_code.append(f"      SDICmdString = \"{sdi_char}D0!\"")
        crbasic_code.append(f"      SDI12Recorder (SDI12ReturnCode, SDI12_PORT, SDI12CmdString, TempD_6Val(1), 1.0, 0, -1, 6)")
        crbasic_code.append(f"      If SDI12ReturnCode = 0 Then")
        crbasic_code.append(f"        S{sdi_char}_TpDsInn = TempD_6Val(1) : S{sdi_char}_dTDsInn = TempD_6Val(2) : S{sdi_char}_TsDsInn = TempD_6Val(3)")
        crbasic_code.append(f"        S{sdi_char}_TpUsInn = TempD_6Val(4) : S{sdi_char}_dTUsInn = TempD_6Val(5) : S{sdi_char}_TsUsInn = TempD_6Val(6)")
        crbasic_code.append(f"      Else")
        crbasic_code.append(f"        S{sdi_char}_TpDsInn = NAN : S{sdi_char}_dTDsInn = NAN : S{sdi_char}_TsDsInn = NAN : S{sdi_char}_TpUsInn = NAN : S{sdi_char}_dTUsInn = NAN : S{sdi_char}_TsUsInn = NAN")
        crbasic_code.append(f"      EndIf")
        crbasic_code.append(f"    Else")
        crbasic_code.append(f"      S{sdi_char}_TpDsInn = NAN : S{sdi_char}_dTDsInn = NAN : S{sdi_char}_TsDsInn = NAN : S{sdi_char}_TpUsInn = NAN : S{sdi_char}_dTUsInn = NAN : S{sdi_char}_TsUsInn = NAN")
        crbasic_code.append(f"    EndIf")
        crbasic_code.append("")

        # M5! Command
        crbasic_code.append(f"    SDICmdString = \"{sdi_char}M5!\"")
        crbasic_code.append(f"    SDI12Recorder (SDI12ReturnCode, SDI12_PORT, SDI12CmdString, SDI12ExpectedValues, 1.0, 0)")
        crbasic_code.append(f"    If SDI12ReturnCode = 0 Then")
        crbasic_code.append(f"      Delay (0, ADD_MEAS_WAIT_MS, mSec)")
        crbasic_code.append(f"      SDICmdString = \"{sdi_char}D0!\"")
        crbasic_code.append(f"      SDI12Recorder (SDI12ReturnCode, SDI12_PORT, SDI12CmdString, TempD_2Val(1), 1.0, 0, -1, 2)")
        crbasic_code.append(f"      If SDI12ReturnCode = 0 Then")
        crbasic_code.append(f"        S{sdi_char}_tMxTUsO = TempD_2Val(1)")
        crbasic_code.append(f"        S{sdi_char}_tMxTUsI = TempD_2Val(2)")
        crbasic_code.append(f"      Else")
        crbasic_code.append(f"        S{sdi_char}_tMxTUsO = NAN : S{sdi_char}_tMxTUsI = NAN")
        crbasic_code.append(f"      EndIf")
        crbasic_code.append(f"    Else")
        crbasic_code.append(f"      S{sdi_char}_tMxTUsO = NAN : S{sdi_char}_tMxTUsI = NAN")
        crbasic_code.append(f"    EndIf")
        crbasic_code.append("")

    crbasic_code.append("    CallTable SapFlowAll")
    crbasic_code.append("  NextScan")
    crbasic_code.append("EndProg")

    return "\n".join(crbasic_code)


# Optional: Add a section for direct testing of this module
if __name__ == "__main__":
    print("--- Testing cr300_generator.py directly ---")
    # Test case 1: Valid input
    print("\n--- Test Case 1: 2 sensors, 15 min interval ---")
    test_code_1 = generate_code(num_sensors=2, measure_interval_min=15)
    if "' Error:" in test_code_1:
        print(f"Error in generation: {test_code_1}")
    else:
        print(test_code_1)
        # You could add a check here to see if it compiles using your crbrs tool for CR300
        # For example:
        # with open("temp_cr300_test.cr3", "w") as f:
        #     f.write(test_code_1)
        # print("\n--- CR300 Code (temp_cr300_test.cr3) ---")
        # print("Run with: crbrs compile temp_cr300_test.cr3 (assuming CR300 compiler)")


    print("\n--- Test Case 2: Too many sensors (e.g., 63) ---")
    test_code_2 = generate_code(num_sensors=63, measure_interval_min=15)
    if "' Error:" in test_code_2:
        print(f"Expected Error: {test_code_2}")
    else:
        print("Error: Validation for too many sensors failed for CR300.")
        print(test_code_2)

    print("\n--- Test Case 3: Interval too short (e.g., 5 min) ---")
    test_code_3 = generate_code(num_sensors=1, measure_interval_min=5)
    if "' Error:" in test_code_3:
        print(f"Expected Error: {test_code_3}")
    else:
        print("Error: Validation for interval too short failed for CR300.")
        print(test_code_3)


    print("\n--- Direct module testing complete ---")