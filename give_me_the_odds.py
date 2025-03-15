#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

from millennium_falcon import MillenniumFalcon  # Assuming the class is in a separate file

"""
Assignment title: R2D3
Purpose: Calculate the odds of the Millennium Falcon completing its mission
"""


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        prog="give_me_the_odds",
        description="Calculate the odds of the Millennium Falcon completing its mission.",
        epilog="May the Force be with you!"
    )
    
    # Add required arguments
    parser.add_argument(
        "falcon_config",
        help="Path to the Millennium Falcon configuration JSON file"
    )
    parser.add_argument(
        "empire_data",
        help="Path to the Empire intelligence data JSON file"
    )
    
    # Add optional arguments
    parser.add_argument(
        "-v", "--visualize",
        action="store_true",
        help="Display a visualization of the mission"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Use interactive visualization with hover capabilities"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show detailed calculation information"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Verify files exist
    falcon_path = Path(args.falcon_config)
    empire_path = Path(args.empire_data)
    
    if not falcon_path.exists():
        sys.exit(f"Error: Millennium Falcon configuration file not found: {falcon_path}")
    if not empire_path.exists():
        sys.exit(f"Error: Empire intelligence data file not found: {empire_path}")
    
    try:
        # Initialize the Millennium Falcon with the config file
        falcon = MillenniumFalcon(args.falcon_config)
        
        # Calculate odds and get results
        if args.debug:
            # Make sure this method returns exactly two values
            # odds, debug_info = falcon.calculate_odds_for_cli(args.empire_data)
            odds, debug_info = falcon.calculate_odds_with_debug(args.empire_data)
            
            print(debug_info)
        else:
            # This method should return just one value
            odds = falcon.calculate_odds(args.empire_data)
        
        # Print the final result
        print(f"\nThe odds of successfully completing the mission are: {odds:.2f}%")
        
        # Generate visualization if requested
        if args.visualize:
            if args.interactive:
                falcon.visualize_mission_dynamic(args.empire_data, odds)
            else:
                falcon.visualize_mission(args.empire_data, odds)
                
    except ValueError as e:
        if "too many values to unpack" in str(e):
            sys.exit("Error: The calculate_odds or calculate_odds_with_debug method is returning more values than expected. Please check the implementation.")
        else:
            sys.exit(f"Error: {e}")
    except Exception as e:
        sys.exit(f"Error: {e}")


if __name__ == "__main__":
    main()
    