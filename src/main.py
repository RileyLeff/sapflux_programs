#!/usr/bin/env python3
# /// script
# dependencies:
# ///

import argparse
import sys
import importlib # For dynamic module importing

def main():
    parser = argparse.ArgumentParser(
        description="Generate CRBasic code for Implexx Sap Flow Sensors.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""\
Example usage:
  python %(prog)s --logger-type CR200X -n 2 -t 30 -o sapflux_cr200x.cr2
  python %(prog)s --logger-type CR300 -n 5 -t 15

Notes:
  - CR200X generated code uses one DataTable per sensor.
  - CR300 generated code aims for a single comprehensive DataTable.
"""
    )

    # --- Required Arguments ---
    parser.add_argument(
        "--logger-type",
        type=str.upper, # Convert to uppercase for consistent matching
        required=True,
        choices=["CR200X", "CR300"],
        help="Specify the target datalogger type (e.g., CR200X, CR300)."
    )
    parser.add_argument(
        "-n", "--num-sensors",
        type=int,
        required=True,
        help="The number of sensors (N)."
    )
    parser.add_argument(
        "-t", "--measure-interval",
        type=int,
        required=True,
        help="The measurement interval in minutes (T)."
    )

    # --- Optional Arguments ---
    parser.add_argument(
        "-o", "--output",
        metavar="FILENAME",
        type=str,
        help="Optional: Output filename for the generated CRBasic code."
    )
    # Add more optional arguments here if needed later, e.g., for selecting measurements for CR300
    # parser.add_argument(
    #     "--cr300-measurements", # Example of a logger-specific option
    #     type=str,
    #     choices=["standard", "all_20"],
    #     default="all_20",
    #     help="For CR300: Specify which set of measurements to collect (default: all_20)."
    # )

    args = parser.parse_args()

    # --- Basic Input Validation (More specific validation in generator modules) ---
    if args.num_sensors < 1:
        print("Error: Number of sensors must be at least 1.", file=sys.stderr)
        sys.exit(1)
    if args.measure_interval <= 0:
         print("Error: Measurement interval must be a positive integer.", file=sys.stderr)
         sys.exit(1)

    # --- Dynamically select and call the generator module ---
    generated_code = None
    generator_module_name = None
    generator_kwargs = {} # For any future specific arguments

    if args.logger_type == "CR200X":
        generator_module_name = "cr200x_generator"
        # CR200X specific validation (can also be inside the module)
        # MAX_SENSORS_CR200X_ONE_TABLE_PER_SENSOR is 8
        if not (1 <= args.num_sensors <= 8):
            print(f"Error: For CR200X (one table per sensor), "
                  f"number of sensors must be between 1 and 8. Requested: {args.num_sensors}",
                  file=sys.stderr)
            sys.exit(1)
        # MIN_MEASURE_INTERVAL_MINUTES_IMPLEX_CR200X is 15
        if args.measure_interval < 15:
             print(f"Warning: Implexx sensors on CR200X typically recommend a measurement interval of at least 15 minutes. "
                   f"Requested: {args.measure_interval} min.",
                   file=sys.stderr)

    elif args.logger_type == "CR300":
        generator_module_name = "cr300_generator"
        # MAX_SDI12_SENSORS_CR300 is 62
        if not (1 <= args.num_sensors <= 62):
            print(f"Error: Number of sensors for CR300 must be between 1 and 62. Requested: {args.num_sensors}",
                  file=sys.stderr)
            sys.exit(1)
        # MIN_MEASURE_INTERVAL_MINUTES_IMPLEX is 10
        if args.measure_interval < 10:
             print(f"Warning: Implexx sensors recommend a data collect interval of at least 10 minutes. "
                   f"Requested: {args.measure_interval} min.",
                   file=sys.stderr)
        # Example of passing a logger-specific argument if you add one:
        # if hasattr(args, 'cr300_measurements'):
        #    generator_kwargs['measurement_set'] = args.cr300_measurements
    else:
        # Should not be reached due to 'choices' in argparse
        print(f"Error: Unsupported logger type '{args.logger_type}'.", file=sys.stderr)
        sys.exit(1)

    try:
        # Dynamically import the module relative to the current package 'src'
        # The '.' indicates a relative import from the current package.
        # This assumes main.py is part of the 'src' package.
        module = importlib.import_module(f".{generator_module_name}", package=__package__)
        # Call the consistent function name 'generate_code'
        generated_code = module.generate_code(
            num_sensors=args.num_sensors,
            measure_interval_min=args.measure_interval,
            **generator_kwargs
        )
    except ImportError:
        print(f"Error: Could not import generator module '{generator_module_name}'. "
              f"Ensure '{generator_module_name}.py' exists in the 'src' directory.", file=sys.stderr)
        sys.exit(1)
    except AttributeError:
        print(f"Error: The module '{generator_module_name}' does not have a 'generate_code' function.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during code generation with '{generator_module_name}': {e}", file=sys.stderr)
        sys.exit(1)


    # --- Output Handling ---
    if generated_code:
        if "' Error:" in generated_code: # Check if the generator function returned an error string
            print(f"Error from generator module:\n{generated_code}", file=sys.stderr)
            sys.exit(1)

        if args.output:
            try:
                with open(args.output, "w") as f:
                    f.write(generated_code)
                print(f"CRBasic code generated and saved to '{args.output}'.")
            except IOError as e:
                print(f"Error writing to file '{args.output}': {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print(generated_code)
    else:
        print("Error: Code generation failed for an unknown reason.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()