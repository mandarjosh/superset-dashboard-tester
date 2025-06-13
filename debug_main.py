#!/usr/bin/env python3
"""
Debugging version of the main script
"""

print("Starting main script debugging...")

import sys
import time
from config import SUPERSET_CONFIG, DASHBOARD_CONFIG, LOG_DIR
from superset_performance_tester import SupersetPerformanceTester
from scenarios import Scenarios

def main():
    print("Entered main function")
    
    # Create the tester instance
    tester = SupersetPerformanceTester(
        base_url=SUPERSET_CONFIG['base_url'],
        username=SUPERSET_CONFIG['username'],
        password=SUPERSET_CONFIG['password'],
        output_file="debug_output.xlsx",
        log_dir=LOG_DIR
    )
    
    print("Created tester instance")
    
    # Create scenarios instance
    scenarios = Scenarios(tester)
    
    print("Created scenarios instance")
    
    start_time = time.time()
    tester.log(f"Starting performance test with all scenarios")
    
    print("About to run scenarios")
    
    results = {}
    
    try:
        # Run only scenario 1 for debugging
        print("Running scenario 1")
        results['Scenario 1'] = scenarios.scenario_1_single_dashboard(
            DASHBOARD_CONFIG['scenario_1']['dashboard_id'],
            1  # Just 1 iteration for debugging
        )
        
        # Save results to Excel
        tester.save_results_to_excel(results)
        print("Saved results to Excel")
        
    except KeyboardInterrupt:
        print("Test interrupted by user")
        tester.log("Test interrupted by user")
    except Exception as e:
        print(f"Error running test: {str(e)}")
        tester.log(f"Error running test: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Close the persistent driver
        if tester.persistent_driver:
            tester.persistent_driver.quit()
            tester.log("Closed persistent browser")
            print("Closed browser")
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    tester.log(f"Performance test completed in {elapsed_time:.2f} seconds")
    print(f"Performance test completed in {elapsed_time:.2f} seconds")
    
    return 0

if __name__ == "__main__":
    print("Script is being run directly")
    exit_code = main()
    print(f"Script completed with exit code {exit_code}")
    sys.exit(exit_code)
else:
    print("Script was imported, not run directly")