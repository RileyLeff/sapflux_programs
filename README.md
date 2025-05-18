# Sapflux Programs

This repository contains Python scripts designed to generate CRBasic firmware for running Implexx sap flux sensors on Campbell Scientific CR200-series and CR300-series dataloggers.

There are many jailable software crimes committed in this repository.

## Motivations & Goals

This project was born out of a desire to:

1.  **Modernize Development:** Write datalogger code using my standard development environment and tools, rather than being confined to ancient, proprietary, Windows-only software.
2.  **Comprehensively Log Data:** Capture all relevant measurements from the Implexx sap flux sensors.
3.  **Scale Up:** Create CRBasic programs that can be easily adapted for an arbitrary number of sensors (within datalogger limits). The Campbell "Short Cut" program refused many of my demands, even though they were well within sensor/logger capabilities.

## Challenges & Workarounds

Working with older datalogger platforms presents unique challenges:

*   **Development Environment:** To address the first goal, I developed [crbrs](https://github.com/RileyLeff/crbrs) (available on [crates.io](https://crates.io/crates/crbrs)). This tool allows you to install and use Campbell Scientific compilers (hosted [here](https://github.com/RileyLeff/campbell-scientific-compilers)) on macOS, Linux, or Windows, bypassing the need for Campbell's traditional software suite.
*   **CR200X Data Table Limitations:**
    *   **Field Limit:** CR200-series dataloggers impose a strict limit of **16 columns (fields)** per data table. This is a significant constraint when aiming to log comprehensive data (e.g., the 20+ desired measurements from each Implexx sensor plus metadata).
    *   **Table Limit:** There's also a limit on the total number of data tables (often 8).
    *   **Workaround:** For the CR200X, the generator script creates **one data table per sensor**. This means each table contains the metadata and the 9 standard Implexx measurements for that specific sensor, fitting within the 16-field limit. Consequently, with this strategy, the CR200X can support a maximum of 8 sensors. This approach, while necessary, can make data management more cumbersome in the field due to multiple output files.
*   **CR300 Data Table Flexibility:** CR300-series dataloggers have much higher limits on fields per table and total tables. The CR300 generator script leverages this by creating a **single, comprehensive data table** for all sensors and all 20 desired Implexx measurements.
*   **Dynamic Code Generation:** CRBasic itself lacks features for dynamically generating table structures or measurement loops based on a variable number of sensors. To achieve scalability, this project uses Python scripts to dynamically generate the static CRBasic source code.

## Project Structure

The core of this project resides in the `src/` directory:

*   `src/main.py`: The main command-line interface (CLI) script. It parses arguments and calls the appropriate generator module.
*   `src/cr200x_generator.py`: A Python module containing the logic to generate CRBasic code specifically for CR200-series dataloggers.
*   `src/cr300_generator.py`: A Python module containing the logic to generate CRBasic code specifically for CR300-series dataloggers.
*   `generated_programs/`: A suggested directory to store the output `.cr2` or `.cr3` files.

## How-To Guide

To generate CRBasic firmware for your Implexx sap flux sensors:

1.  **Clone the Repository:**
    ```bash
    git clone git@github.com:RileyLeff/sapflux_programs.git sapflux_programs
    cd sapflux_programs
    ```

2.  **Prerequisites:**
    *   Python 3.x
    *   (Optional but Recommended) [UV](https://github.com/astral-sh/uv) for running Python scripts in a managed environment.
    *   (Optional but Recommended for CR200X compilation) [crbrs](https://github.com/RileyLeff/crbrs) installed if you want to compile the generated `.cr2` files from your command line.

3.  **Run the Generation Script:**
    The main script is `src/main.py`. You run it from the **project root directory**.

    **Command Structure:**
    ```bash
    # Using UV (recommended)
    uv run python -m src.main --logger-type <TYPE> -n <NUM_SENSORS> -t <INTERVAL_MIN> [-o <OUTPUT_FILE>]

    # Using system Python 3
    python3 -m src/main.py --logger-type <TYPE> -n <NUM_SENSORS> -t <INTERVAL_MIN> [-o <OUTPUT_FILE>]
    ```

    **Arguments:**
    *   `--logger-type <TYPE>`: **Required.** Specify the target datalogger.
        *   `CR200X`: For CR200-series dataloggers.
        *   `CR300`: For CR300-series dataloggers.
    *   `-n <NUM_SENSORS>`, `--num-sensors <NUM_SENSORS>`: **Required.** The number of sensors.
        *   For `CR200X`: 1 to 8 (due to table limits with the one-table-per-sensor strategy).
        *   For `CR300`: 1 to 62 (full SDI-12 address space).
    *   `-t <INTERVAL_MIN>`, `--measure-interval <INTERVAL_MIN>`: **Required.** The measurement interval in minutes.
        *   Minimum 15 minutes recommended for Implexx sensors to avoid overheating when using heating pulses (like the standard `M!` command). The CR300 script currently collects all 20 measurements, including those from `M!`. The CR200X script collects the 9 standard measurements from `M!`.
    *   `-o <OUTPUT_FILE>`, `--output <OUTPUT_FILE>`: **Optional.** File path to save the generated CRBasic code. If not provided, the code will be printed to standard output. It's recommended to use an appropriate extension (e.g., `.cr2` for CR200X, `.cr3` for CR300).

    **Examples:**
    ```bash
    # Generate code for 3 CR200X sensors, 30-min interval, save to file
    uv run python src/main.py --logger-type CR200X -n 3 -t 30 -o generated_programs/sapflux_3_cr200x.cr2

    # Generate code for 5 CR300 sensors, 15-min interval, print to console
    uv run python src/main.py --logger-type CR300 -n 5 -t 15
    ```

4.  **Compile (Optional, using `crbrs`):**
    If you have `crbrs` installed and configured, you can compile the generated file:
    ```bash
    crbrs compile generated_programs/your_generated_file.cr2 --compiler cr2comp
    # or
    crbrs compile generated_programs/your_generated_file.cr300 --compiler cr300comp
    ```
    Refer to the `crbrs` documentation for installation and configuration details. Otherwise, use Campbell Scientific's software to compile and upload the generated source code file.

## Current Status & Notes

*   **CR200X Generator:**
    *   Generates code to measure the **9 standard Implexx sap flux values** (from the `M!` command sequence).
    *   Creates **one data table per sensor** due to the 16-field-per-table limit.
    *   Supports up to 8 sensors due to the 8-table limit.
    *   The generated code has been tested and compiles successfully.
*   **CR300 Generator:**
    *   Generates code to measure all **20 desired Implexx sap flux values** (from `M!`, `M1!`, `M2!`, `M5!` command sequences).
    *   Creates a **single comprehensive data table** for all sensors.
    *   Supports up to 62 sensors.
    *   The generated code compiles successfully on the CR300. Real-world sensor data acquisition is currently being tested/validated.

Let me know if you have any questions big dog.
