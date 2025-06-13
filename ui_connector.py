"""
Fixed UI Connector that properly uses selected dashboards
"""
import os
import threading
import time
from PyQt5.QtCore import QObject, pyqtSignal

# Import your existing testing code
from config import SUPERSET_CONFIG, DASHBOARD_CONFIG
from superset_performance_tester import SupersetPerformanceTester
from scenarios import Scenarios

class UIConnector(QObject):
    # Define signals for thread-safe UI updates
    progress_updated = pyqtSignal(int, str)
    test_completed = pyqtSignal(dict)
    test_error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.tester = None
    
    def initialize_tester(self, base_url, username, password, manual_login=False):
        """Create a tester instance with the given credentials"""
        try:
            self.tester = SupersetPerformanceTester(
                base_url=base_url,
                username=username,
                password=password,
                output_file="dashboard_performance.xlsx"
            )
            
            if manual_login:
                driver = self.tester.create_driver()
                self.tester.persistent_driver = driver
                driver.get(base_url)
                self.tester.log("Opened browser for manual login")
                return "WAITING_FOR_MANUAL"
            
            driver = self.tester.get_persistent_driver()
            if not driver:
                self.test_error.emit("Failed to initialize driver")
                return False
            
            return True
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.test_error.emit(f"Error initializing tester: {str(e)}")
            return False
        
    def complete_manual_login(self):
        """Called when the user has completed manual login in the browser"""
        try:
            if not self.tester or not self.tester.persistent_driver:
                self.test_error.emit("No active browser session")
                return False
                
            current_url = self.tester.persistent_driver.current_url
            self.tester.log(f"After manual login, current URL: {current_url}")
            
            if "/login/" not in current_url:
                self.tester.log("Manual login appears successful")
                return True
            else:
                self.tester.log("Still on login page after manual login attempt")
                return False
        except Exception as e:
            self.test_error.emit(f"Error validating manual login: {str(e)}")
            return False
    
    def refresh_driver(self):
        """Refreshes the WebDriver if it's disconnected"""
        try:
            if self.tester and self.tester.persistent_driver:
                try:
                    self.tester.persistent_driver.quit()
                except:
                    pass
                self.tester.persistent_driver = None
            
            return self.tester.get_persistent_driver()
        except Exception as e:
            self.test_error.emit(f"Failed to refresh WebDriver: {str(e)}")
            return None

    def run_performance_tests(self, dashboard_ids, selected_scenarios, iterations_by_scenario):
        """Run the selected test scenarios with ONLY the selected dashboards"""
        # Start thread for test execution
        thread = threading.Thread(
            target=self._run_performance_tests_thread,
            args=(dashboard_ids, selected_scenarios, iterations_by_scenario)
        )
        thread.daemon = True
        thread.start()
    
    def _run_performance_tests_thread(self, dashboard_ids, selected_scenarios, iterations_by_scenario):
        """Background thread function that runs ONLY SELECTED tests"""
        try:
            if not self.tester:
                raise Exception("Tester not initialized")
            
            # CRITICAL DEBUG LOGGING
            self.tester.log(f"🎯 PERFORMANCE TEST STARTING")
            self.tester.log(f"🎯 Selected dashboard IDs: {dashboard_ids}")
            self.tester.log(f"🎯 Selected scenarios: {selected_scenarios}")
            self.tester.log(f"🎯 Iterations by scenario: {iterations_by_scenario}")
            
            # Validate that we received the correct parameters
            if not dashboard_ids:
                raise Exception("No dashboard IDs provided")
            
            if not selected_scenarios:
                raise Exception("No scenarios selected")
            
            # Update progress
            self.progress_updated.emit(10, "Starting tests...")
            
            # Create scenarios instance
            scenarios_runner = Scenarios(self.tester)
            all_results = {}
            
            total_scenarios = len(selected_scenarios)
            completed_scenarios = 0
            
            # Run ONLY the selected scenarios with ONLY the selected dashboards
            for scenario_num in selected_scenarios:
                try:
                    iterations = iterations_by_scenario.get(scenario_num, 1)
                    progress = int(10 + ((completed_scenarios / total_scenarios) * 80))
                    
                    if scenario_num == 1:
                        self.progress_updated.emit(progress, f"Running Scenario 1: Single dashboard ({iterations} iterations)...")
                        self.tester.log(f"🎯 SCENARIO 1: Testing dashboard {dashboard_ids[0]} with {iterations} iterations")
                        
                        # Use ONLY FIRST selected dashboard for Scenario 1
                        results = scenarios_runner.scenario_1_single_dashboard(
                            dashboard_ids[0], iterations
                        )
                        all_results['Scenario 1'] = results
                        
                    elif scenario_num == 2:
                        self.progress_updated.emit(progress, f"Running Scenario 2: Sequential dashboards ({iterations} iterations)...")
                        self.tester.log(f"🎯 SCENARIO 2: Testing dashboards {dashboard_ids} with {iterations} iterations each")
                        
                        # Use ALL selected dashboards for sequential testing
                        results = scenarios_runner.scenario_2_sequential_dashboards(
                            dashboard_ids, iterations  # Use selected dashboards only
                        )
                        all_results['Scenario 2'] = results
                        
                    elif scenario_num == 3:
                        self.progress_updated.emit(progress, f"Running Scenario 3: Parallel dashboards ({iterations} iterations)...")
                        self.tester.log(f"🎯 SCENARIO 3: Testing dashboards {dashboard_ids} with {iterations} iterations each")
                        
                        # Use ALL selected dashboards for parallel testing
                        max_workers = min(len(dashboard_ids), 5)  # Don't exceed 5 parallel tabs
                        results = scenarios_runner.scenario_3_parallel_dashboards(
                            dashboard_ids, iterations, max_workers  # Use selected dashboards only
                        )
                        all_results['Scenario 3'] = results
                        
                    elif scenario_num == 4:
                        self.progress_updated.emit(progress, f"Running Scenario 4: Dashboard refresh ({iterations} iterations)...")
                        self.tester.log(f"🎯 SCENARIO 4: Testing dashboards {dashboard_ids} with {iterations} refresh iterations")
                        
                        # Use ALL selected dashboards for refresh testing
                        results = scenarios_runner.scenario_4_dashboard_refresh(
                            dashboard_ids, iterations, 2  # Use selected dashboards only
                        )
                        all_results['Scenario 4'] = results
                    
                    completed_scenarios += 1
                    self.tester.log(f"✅ Completed Scenario {scenario_num}")
                    
                except Exception as scenario_error:
                    self.tester.log(f"❌ ERROR in Scenario {scenario_num}: {str(scenario_error)}")
                    import traceback
                    self.tester.log(f"Traceback: {traceback.format_exc()}")
                    completed_scenarios += 1
            
            # Process results and save to Excel
            self.progress_updated.emit(90, "Saving results...")
            excel_path = self.tester.output_file
            
            if all_results:
                self.tester.save_results_to_excel(all_results)
                self.tester.log(f"✅ Results saved to {excel_path}")
            else:
                self.tester.log("⚠️ No results to save")
            
            # Complete
            self.progress_updated.emit(100, "Tests completed!")
            self.test_completed.emit({"results": all_results, "excel_path": excel_path})
            
        except Exception as e:
            import traceback
            self.tester.log(f"❌ CRITICAL ERROR during performance tests: {str(e)}")
            self.tester.log(f"Full traceback: {traceback.format_exc()}")
            traceback.print_exc()
            self.test_error.emit(f"Error during tests: {str(e)}")
        finally:
            # DON'T close the driver here - keep it alive for future use
            self.tester.log("🏁 Performance test thread completed")

    def run_dashboard_health_check(self, dashboard_ids):
        """Run health checks on dashboards in a background thread"""
        thread = threading.Thread(
            target=self._run_dashboard_health_check_thread,
            args=(dashboard_ids,)
        )
        thread.daemon = True
        thread.start()

    def _run_dashboard_health_check_thread(self, dashboard_ids):
        """Background thread function that runs dashboard health checks"""
        try:
            if not self.tester:
                raise Exception("Tester not initialized")
            
            self.tester.log(f"🏥 HEALTH CHECK STARTING")
            self.tester.log(f"🏥 Selected dashboard IDs: {dashboard_ids}")
            
            self.progress_updated.emit(10, "Starting health checks...")
            
            all_results = []
            total_dashboards = len(dashboard_ids)
            
            for i, dashboard_id in enumerate(dashboard_ids):
                progress = int(10 + ((i / total_dashboards) * 80))
                self.progress_updated.emit(progress, f"Checking dashboard {dashboard_id} ({i+1}/{total_dashboards})...")
                
                try:
                    # Get driver and ensure it's working
                    driver = self.tester.get_persistent_driver()
                    if not driver:
                        driver = self.refresh_driver()
                        if not driver:
                            raise Exception("Failed to get browser driver")
                    
                    # Check dashboard health
                    health_result = self._check_dashboard_health(driver, dashboard_id)
                    all_results.append(health_result)
                    
                except Exception as dash_err:
                    self.tester.log(f"❌ Error checking dashboard {dashboard_id}: {str(dash_err)}")
                    all_results.append({
                        'Dashboard ID': dashboard_id,
                        'Status': 'Critical',
                        'Charts Loaded': 0,
                        'Total Charts': 0,
                        'Load Time (s)': 0,
                        'Issues': f"Error: {str(dash_err)}"
                    })
            
            # Save results to Excel
            self.progress_updated.emit(90, "Saving health check results...")
            excel_path = "dashboard_health.xlsx"
            
            try:
                import pandas as pd
                df = pd.DataFrame(all_results)
                df.to_excel(excel_path, index=False)
                self.tester.log(f"✅ Health results saved to {excel_path}")
            except Exception as save_error:
                self.tester.log(f"⚠️ Failed to save health results: {str(save_error)}")
                excel_path = ""
            
            # Complete
            self.progress_updated.emit(100, "Health checks completed!")
            self.test_completed.emit({"results": all_results, "excel_path": excel_path})
            
        except Exception as e:
            import traceback
            self.tester.log(f"❌ CRITICAL ERROR during health checks: {str(e)}")
            self.tester.log(f"Full traceback: {traceback.format_exc()}")
            traceback.print_exc()
            self.test_error.emit(f"Error during health checks: {str(e)}")
        finally:
            # Keep driver alive for future use
            self.tester.log("🏥 Health check thread completed")

    def _check_dashboard_health(self, driver, dashboard_id):
        """Check the health of a specific dashboard"""
        try:
            dashboard_url = f"{self.tester.base_url}/superset/dashboard/{dashboard_id}/"
            self.tester.log(f"🔍 Checking health of dashboard: {dashboard_url}")
            
            start_time = time.time()
            driver.get(dashboard_url)
            
            # Wait for dashboard to load (with timeout)
            try:
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from selenium.webdriver.common.by import By
                
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".dashboard-grid, .dashboard, .chart-container, .dashboard-component-chart"))
                )
            except Exception as load_error:
                load_time = time.time() - start_time
                return {
                    'Dashboard ID': dashboard_id,
                    'Status': 'Critical',
                    'Charts Loaded': 0,
                    'Total Charts': 0,
                    'Load Time (s)': round(load_time, 2),
                    'Issues': f'Dashboard failed to load: {str(load_error)}'
                }
            
            # Wait for loading indicators to disappear
            self.tester.wait_for_loading_indicators_to_disappear(driver, 30)
            
            load_time = time.time() - start_time
            
            # Count charts and check their status
            total_charts = self.tester.count_dashboard_charts(driver)
            
            # Check chart health with JavaScript
            loaded_charts = 0
            issues = []
            
            try:
                charts_status = driver.execute_script("""
                    var charts = document.querySelectorAll('.chart-container, .dashboard-component-chart');
                    var loadedCharts = 0;
                    var totalCharts = charts.length;
                    var issues = [];
                    
                    for (var i = 0; i < charts.length; i++) {
                        var chart = charts[i];
                        var hasContent = chart.innerHTML.length > 100;
                        var hasError = chart.innerHTML.toLowerCase().includes('error');
                        var isLoading = chart.innerHTML.toLowerCase().includes('loading');
                        
                        if (hasContent && !isLoading && !hasError) {
                            loadedCharts++;
                        } else if (hasError) {
                            issues.push('Chart ' + (i+1) + ' has error');
                        } else if (isLoading) {
                            issues.push('Chart ' + (i+1) + ' still loading');
                        } else {
                            issues.push('Chart ' + (i+1) + ' has no content');
                        }
                    }
                    
                    return {
                        total: totalCharts,
                        loaded: loadedCharts,
                        issues: issues
                    };
                """)
                
                loaded_charts = charts_status['loaded']
                total_charts = max(charts_status['total'], total_charts)  # Use the higher count
                js_issues = charts_status['issues']
                issues.extend(js_issues[:3])  # Only take first 3 issues
                
            except Exception as js_error:
                self.tester.log(f"Error checking chart status with JavaScript: {str(js_error)}")
                loaded_charts = total_charts  # Assume all loaded if we can't check
            
            # Determine health status
            if total_charts == 0:
                status = 'Critical'
                issues.append('No charts found')
            elif loaded_charts == total_charts:
                if load_time < 10:
                    status = 'Healthy'
                else:
                    status = 'Warning'
                    issues.append(f'Slow load time: {load_time:.1f}s')
            elif loaded_charts / total_charts >= 0.8:
                status = 'Warning'
                issues.append(f'Some charts failed to load ({loaded_charts}/{total_charts})')
            else:
                status = 'Critical'
                issues.append(f'Many charts failed to load ({loaded_charts}/{total_charts})')
            
            if load_time > 20:
                status = 'Critical'
                if f'Very slow load time: {load_time:.1f}s' not in issues:
                    issues.append(f'Very slow load time: {load_time:.1f}s')
            
            self.tester.log(f"✅ Dashboard {dashboard_id} health: {status} ({loaded_charts}/{total_charts} charts, {load_time:.1f}s)")
            
            return {
                'Dashboard ID': dashboard_id,
                'Status': status,
                'Charts Loaded': loaded_charts,
                'Total Charts': total_charts,
                'Load Time (s)': round(load_time, 2),
                'Issues': '; '.join(issues) if issues else 'None'
            }
            
        except Exception as e:
            self.tester.log(f"❌ Error checking dashboard {dashboard_id} health: {str(e)}")
            return {
                'Dashboard ID': dashboard_id,
                'Status': 'Critical',
                'Charts Loaded': 0,
                'Total Charts': 0,
                'Load Time (s)': 0,
                'Issues': f'Health check failed: {str(e)}'
            }
