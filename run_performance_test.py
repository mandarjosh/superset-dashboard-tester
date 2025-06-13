#!/usr/bin/env python3
"""
Main script to run Superset performance tests
"""

print("Starting Superset Performance Test...")

import argparse
import sys
import time
print("Basic modules imported")

try:
    from config import SUPERSET_CONFIG, DASHBOARD_CONFIG, LOG_DIR
    from superset_performance_tester import SupersetPerformanceTester
    from scenarios import Scenarios
    print("All modules imported")
except Exception as e:
    print(f"Import error: {str(e)}")
    sys.exit(1)

def parse_arguments():
    """Parse command line arguments"""
    print("Parsing arguments...")
    parser = argparse.ArgumentParser(description='Superset Performance Testing Tool')
    
    parser.add_argument('--url', 
                        help='Superset base URL',
                        default=SUPERSET_CONFIG['base_url'])
    
    parser.add_argument('--username', 
                        help='Superset username',
                        default=SUPERSET_CONFIG['username'])
    
    parser.add_argument('--password', 
                        help='Superset password',
                        default=SUPERSET_CONFIG['password'])
    
    parser.add_argument('--output', 
                        help='Output Excel file path',
                        default=SUPERSET_CONFIG['output_file'])
    
    parser.add_argument('--scenario', 
                        help='Run specific scenario (1-5 or 0 for all)',
                        type=int,
                        choices=[0, 1, 2, 3, 4, 5],
                        default=0)
    
    parser.add_argument('--dashboard-id', 
                        help='Dashboard ID for scenarios 1 and 5',
                        default=None)
    
    parser.add_argument('--iterations', 
                        help='Number of iterations for scenario 1 or chart refresh iterations for scenario 5',
                        type=int,
                        default=None)
    
    args = parser.parse_args()
    print(f"Arguments parsed: {args}")
    return args

def main():
    """Main function to run performance tests"""
    # Parse command line arguments
    args = parse_arguments()
    
    # Override dashboard config with command line arguments if provided
    if args.dashboard_id:
        if args.scenario == 1:
            DASHBOARD_CONFIG['scenario_1']['dashboard_id'] = args.dashboard_id
        elif args.scenario == 5:
            DASHBOARD_CONFIG['scenario_5']['dashboard_id'] = args.dashboard_id
    
    if args.iterations:
        if args.scenario == 1:
            DASHBOARD_CONFIG['scenario_1']['iterations'] = args.iterations
        elif args.scenario == 5:
            DASHBOARD_CONFIG['scenario_5']['chart_refresh_iterations'] = args.iterations
    
    # Create the tester instance
    tester = SupersetPerformanceTester(
        base_url=args.url,
        username=args.username,
        password=args.password,
        output_file=args.output,
        log_dir=LOG_DIR
    )
    
    # Create scenarios instance
    scenarios = Scenarios(tester)
    
    start_time = time.time()
    tester.log(f"Starting performance test with scenario {args.scenario}")
    
    results = {}
    
    try:
        # Run specific scenario or all scenarios
        if args.scenario == 1:
            results['Scenario 1'] = scenarios.scenario_1_single_dashboard(
                DASHBOARD_CONFIG['scenario_1']['dashboard_id'],
                DASHBOARD_CONFIG['scenario_1']['iterations']
            )
        elif args.scenario == 2:
            results['Scenario 2'] = scenarios.scenario_2_sequential_dashboards(
                DASHBOARD_CONFIG['scenario_2']['dashboard_ids'],
                DASHBOARD_CONFIG['scenario_2']['iterations_per_dashboard']
            )
        elif args.scenario == 3:
            results['Scenario 3'] = scenarios.scenario_3_parallel_dashboards(
                DASHBOARD_CONFIG['scenario_3']['dashboard_ids'],
                DASHBOARD_CONFIG['scenario_3']['iterations_per_dashboard'],
                DASHBOARD_CONFIG['scenario_3']['max_workers']
            )
        elif args.scenario == 4:
            results['Scenario 4'] = scenarios.scenario_4_dashboard_refresh(
                DASHBOARD_CONFIG['scenario_4']['dashboard_ids'],
                DASHBOARD_CONFIG['scenario_4']['refresh_count'],
                DASHBOARD_CONFIG['scenario_4']['wait_between_refresh']
            )
        elif args.scenario == 5:
            results['Scenario 5'] = scenarios.scenario_5_chart_refresh(
                DASHBOARD_CONFIG['scenario_5']['dashboard_id'],
                DASHBOARD_CONFIG['scenario_5']['chart_refresh_iterations'],
                DASHBOARD_CONFIG['scenario_5']['wait_between_refresh']
            )
        else:
            # Run all scenarios
            results = scenarios.run_all_scenarios(DASHBOARD_CONFIG)
        
        # Save results to Excel
        tester.save_results_to_excel(results)
        
    except KeyboardInterrupt:
        tester.log("Test interrupted by user")
    except Exception as e:
        tester.log(f"Error running test: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Close the persistent driver
        if tester.persistent_driver:
            tester.persistent_driver.quit()
            tester.log("Closed persistent browser")
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    tester.log(f"Performance test completed in {elapsed_time:.2f} seconds")
    
    return 0

if __name__ == "__main__":
    print("Script is being run directly")
    exit_code = main()
    print(f"Script completed with exit code {exit_code}")
    sys.exit(exit_code)
else:
    print("Script was imported, not run directly")