#!/bin/bash

# Bash script to generate CRBasic programs for various sensor configurations

# --- Configuration ---
PYTHON_SCRIPT_PATH="src/main.py"
OUTPUT_DIR="generated_programs"
MEASUREMENT_INTERVAL_MIN=30 # Fixed at 30 minutes as requested

# --- Ensure output directory exists ---
mkdir -p "${OUTPUT_DIR}"
if [ ! -d "${OUTPUT_DIR}" ]; then
    echo "Error: Could not create output directory '${OUTPUT_DIR}'."
    exit 1
fi

# --- Python execution command ---
# Change this if you prefer to use python3 directly, e.g., "python3"
PYTHON_RUN_CMD="uv run python -m"

# --- Check if Python script exists ---
if [ ! -f "${PYTHON_SCRIPT_PATH}" ]; then
    echo "Error: Python script not found at '${PYTHON_SCRIPT_PATH}'."
    echo "Please ensure you are in the project root directory."
    exit 1
fi

echo "Starting CRBasic program generation..."
echo "--------------------------------------"

# --- Generate for CR200X ---
LOGGER_TYPE_CR200X="CR200X"
FILE_EXT_CR200X="cr2"
MAX_SENSORS_CR200X=4 # As requested, up to 4 for this script (actual limit is 8)

echo "\nGenerating for ${LOGGER_TYPE_CR200X} (Interval: ${MEASUREMENT_INTERVAL_MIN} min):"
for num_sensors in $(seq 1 ${MAX_SENSORS_CR200X}); do
    output_filename="${OUTPUT_DIR}/sapflux_${num_sensors}sensor_${LOGGER_TYPE_CR200X}_${MEASUREMENT_INTERVAL_MIN}min.${FILE_EXT_CR200X}"
    echo "  Generating: ${num_sensors} sensor(s) -> ${output_filename}"

    uv run python -m src.main \
        --logger-type "${LOGGER_TYPE_CR200X}" \
        -n "${num_sensors}" \
        -t "${MEASUREMENT_INTERVAL_MIN}" \
        -o "${output_filename}"

    if [ $? -eq 0 ]; then
        echo "    Successfully generated ${output_filename}"
    else
        echo "    ERROR generating ${output_filename}"
    fi
done

# --- Generate for CR300 ---
LOGGER_TYPE_CR300="CR300"
FILE_EXT_CR300="cr300" # Or .cr300, depending on compiler preference
MAX_SENSORS_CR300=4 # As requested, up to 4 for this script (actual limit is 62)

echo "\nGenerating for ${LOGGER_TYPE_CR300} (Interval: ${MEASUREMENT_INTERVAL_MIN} min):"
for num_sensors in $(seq 1 ${MAX_SENSORS_CR300}); do
    output_filename="${OUTPUT_DIR}/sapflux_${num_sensors}sensor_${LOGGER_TYPE_CR300}_${MEASUREMENT_INTERVAL_MIN}min.${FILE_EXT_CR300}"
    echo "  Generating: ${num_sensors} sensor(s) -> ${output_filename}"

    uv run python -m src.main \
        --logger-type "${LOGGER_TYPE_CR300}" \
        -n "${num_sensors}" \
        -t "${MEASUREMENT_INTERVAL_MIN}" \
        -o "${output_filename}"

    if [ $? -eq 0 ]; then
        echo "    Successfully generated ${output_filename}"
    else
        echo "    ERROR generating ${output_filename}"
    fi
done

echo "\n--------------------------------------"
echo "All generation tasks complete."
echo "Generated files are in the '${OUTPUT_DIR}/' directory."