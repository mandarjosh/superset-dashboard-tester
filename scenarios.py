"""
Scenarios for Superset Performance Testing
Contains the implementation of different test scenarios
"""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import datetime
from selenium import webdriver

class Scenarios:
    def __init__(self, tester):
        """
        Initialize scenarios with a reference to the tester
        
        Args:
            tester: Instance of SupersetPerformanceTester
        """
        self.tester = tester
    
    def scenario_1_single_dashboard(self, dashboard_id, iterations=1):
        """
        Scenario 1: Measure loading time of a single dashboard
        
        Args:
            dashboard_id: ID of the dashboard to measure
            iterations: Number of times to repeat the measurement
            
        Returns:
            list: List of measurement data dictionaries
        """
        self.tester.log(f"=== Starting Scenario 1: Single Dashboard {dashboard_id} (Iterations: {iterations}) ===")
        
        results = []
        
        try:
            # Get the persistent driver with login already done
            driver = self.tester.get_persistent_driver()
            if not driver:
                self.tester.log("Failed to get persistent driver, aborting test")
                return results
            
            # Measure the dashboard load time specified number of times
            for i in range(iterations):
                self.tester.log(f"Iteration {i+1}/{iterations} for dashboard {dashboard_id}")
                measurement = self.tester.measure_dashboard_load_time(driver, dashboard_id)
                if measurement:
                    measurement['Iteration'] = i+1
                    measurement['Scenario'] = 'Single Dashboard'
                    results.append(measurement)
            
        except Exception as e:
            self.tester.log(f"ERROR in scenario 1: {str(e)}")
            import traceback
            traceback.print_exc()
        
        self.tester.log(f"=== Completed Scenario 1: {len(results)} measurements collected ===")
        return results
    
    def scenario_2_sequential_dashboards(self, dashboard_ids, iterations_per_dashboard=5):
        """
        Scenario 2: Sequential dashboard testing with PRECISE timing
        NO unnecessary waits - only measures actual load time
        """
        self.tester.log(f"=== Starting Scenario 2: Sequential Dashboards {dashboard_ids} ===")
        self.tester.log(f"Will measure each dashboard {iterations_per_dashboard} times")
        self.tester.log(f"Total measurements: {len(dashboard_ids) * iterations_per_dashboard}")
        
        results = []
        
        try:
            # Get persistent driver - login once
            driver = self.tester.get_persistent_driver()
            if not driver:
                self.tester.log("Failed to get persistent driver, aborting test")
                return results
            
            self.tester.log("Using logged-in session for all measurements")
            
            # Progress tracking
            total_measurements = len(dashboard_ids) * iterations_per_dashboard
            completed = 0
            
            # Test each dashboard
            for dash_idx, dashboard_id in enumerate(dashboard_ids):
                self.tester.log(f"\n--- Dashboard {dash_idx + 1}/{len(dashboard_ids)}: {dashboard_id} ---")
                
                # Multiple iterations per dashboard
                for iteration in range(iterations_per_dashboard):
                    completed += 1
                    progress = (completed / total_measurements) * 100
                    
                    self.tester.log(f"[{completed}/{total_measurements}] {progress:.1f}% - "
                                f"Dashboard: {dashboard_id}, Iteration: {iteration+1}")
                    
                    # Check driver health (quick check, no sleep)
                    try:
                        driver.current_url  # Quick health check
                    except:
                        self.tester.log("Driver died, recovering...")
                        driver = self.tester.recover_driver_session()
                        if not driver:
                            self.tester.log("Failed to recover driver")
                            return results
                    
                    # MEASURE WITH PRECISE TIMING
                    measurement = self.tester.measure_dashboard_load_time(driver, dashboard_id)
                    
                    if measurement:
                        measurement['Iteration'] = iteration + 1
                        measurement['Scenario'] = 'Sequential Dashboards'
                        measurement['Dashboard_Index'] = dash_idx + 1
                        measurement['Total_Dashboards'] = len(dashboard_ids)
                        results.append(measurement)
                        
                        # Quick summary
                        self.tester.log(f"✓ Load time: {measurement['Load Time (seconds)']:.2f}s, "
                                    f"Charts: {measurement['Chart Count']}")
                    else:
                        self.tester.log(f"✗ Failed to measure")
                    
                    # MINIMAL wait between iterations (only if needed for stability)
                    if iteration < iterations_per_dashboard - 1:
                        time.sleep(0.5)  # Half second for browser stability
            
        except Exception as e:
            self.tester.log(f"ERROR in scenario 2: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Summary
        if results:
            avg_time = sum(r['Load Time (seconds)'] for r in results) / len(results)
            self.tester.log(f"\n=== Summary ===")
            self.tester.log(f"Measurements: {len(results)}/{total_measurements}")
            self.tester.log(f"Average load time: {avg_time:.2f}s")
        
        return results
    
    
    def scenario_3_parallel_dashboards(self, dashboard_ids, iterations_per_dashboard=3, max_workers=5):
        """
        Scenario 3: FORCE multiple parallel tabs (ignore UI max_workers limit)
        """
        self.tester.log(f"=== Starting Scenario 3: FORCED Parallel Dashboards {dashboard_ids} ===")
        
        # FORCE at least 5 parallel tabs regardless of max_workers setting
        if max_workers < 2:
            self.tester.log(f"WARNING: max_workers was {max_workers}, forcing to 5 for true parallel testing")
            max_workers = 5
        
        self.tester.log(f"Will test each dashboard with {max_workers} parallel instances, {iterations_per_dashboard} rounds")
        
        all_results = []
        
        try:
            # Get the persistent driver with login already done
            main_driver = self.tester.get_persistent_driver()
            if not main_driver:
                self.tester.log("Failed to get persistent driver, aborting test")
                return all_results
            
            original_tab = main_driver.current_window_handle
            
            # Test each dashboard
            for dashboard_id in dashboard_ids:
                self.tester.log(f"\n=== Testing Dashboard {dashboard_id} with {max_workers} Parallel Instances ===")
                
                # Run multiple rounds of parallel testing for this dashboard
                for round_num in range(iterations_per_dashboard):
                    self.tester.log(f"\n--- Round {round_num + 1}/{iterations_per_dashboard} for Dashboard {dashboard_id} ---")
                    
                    # STEP 1: Open FORCED number of tabs of the SAME dashboard simultaneously
                    tab_info = []
                    
                    self.tester.log(f"STEP 1: FORCING {max_workers} parallel tabs of dashboard {dashboard_id}...")
                    
                    for tab_num in range(max_workers):
                        try:
                            if tab_num == 0:
                                # Use original tab for first instance
                                tab_handle = original_tab
                                main_driver.switch_to.window(original_tab)
                            else:
                                # FORCE new tab creation
                                self.tester.log(f"Creating tab {tab_num + 1} of {max_workers}")
                                main_driver.execute_script("window.open('', '_blank');")
                                
                                # Wait for tab to be created
                                time.sleep(1)
                                
                                # Get the new tab handle
                                all_handles = main_driver.window_handles
                                tab_handle = all_handles[-1]
                                
                                self.tester.log(f"New tab created, switching to tab {tab_num + 1}")
                                main_driver.switch_to.window(tab_handle)
                            
                            # Record start time for this instance
                            start_time = time.time()
                            
                            # Start loading the SAME dashboard in this tab
                            dashboard_url = f"{self.tester.base_url}/superset/dashboard/{dashboard_id}/"
                            
                            self.tester.log(f"Tab {tab_num + 1}: Starting parallel load of dashboard {dashboard_id}")
                            main_driver.get(dashboard_url)
                            
                            tab_info.append({
                                'tab_handle': tab_handle,
                                'dashboard_id': dashboard_id,
                                'start_time': start_time,
                                'tab_number': tab_num + 1,
                                'round': round_num + 1,
                                'parallel_instance': tab_num + 1
                            })
                            
                            # Brief pause between tab creation
                            time.sleep(0.5)
                            
                        except Exception as e:
                            self.tester.log(f"Error creating tab {tab_num + 1} for dashboard {dashboard_id}: {str(e)}")
                            continue
                    
                    self.tester.log(f"STEP 1 COMPLETE: Actually started {len(tab_info)} parallel instances of dashboard {dashboard_id}")
                    
                    # Verify we have multiple tabs
                    current_handles = main_driver.window_handles
                    self.tester.log(f"Browser now has {len(current_handles)} total tabs")
                    
                    # STEP 2: Monitor each tab for completion
                    self.tester.log("STEP 2: Monitoring parallel load completion...")
                    
                    for tab_data in tab_info:
                        try:
                            # Switch to this tab
                            self.tester.log(f"Switching to tab {tab_data['tab_number']} for dashboard {dashboard_id}")
                            main_driver.switch_to.window(tab_data['tab_handle'])
                            
                            # Wait for dashboard to load
                            load_success = False
                            try:
                                WebDriverWait(main_driver, 60).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, 
                                        ".dashboard-grid, .dashboard, .chart-container, .dashboard-component-chart"))
                                )
                                
                                # Wait for loading indicators to disappear
                                try:
                                    loading_indicators = main_driver.find_elements(By.CSS_SELECTOR, ".loading, .loading-spinner, .spinner")
                                    if loading_indicators:
                                        WebDriverWait(main_driver, 30).until_not(
                                            EC.presence_of_element_located((By.CSS_SELECTOR, ".loading, .loading-spinner, .spinner"))
                                        )
                                except:
                                    pass
                                
                                # Additional stability wait
                                time.sleep(3)
                                load_success = True
                                
                            except TimeoutException:
                                self.tester.log(f"Dashboard {dashboard_id} instance {tab_data['parallel_instance']} timed out")
                                load_success = False
                            
                            # Record end time
                            end_time = time.time()
                            load_time = end_time - tab_data['start_time']
                            
                            if load_success:
                                # Count charts
                                chart_count = self.tester.count_dashboard_charts_simple(main_driver)
                                status = 'Success'
                            else:
                                chart_count = 0
                                status = 'Timeout'
                            
                            # Create result with parallel instance info
                            result = {
                                'Dashboard ID': dashboard_id,
                                'Start Time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(tab_data['start_time'])),
                                'End Time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time)),
                                'Load Time (seconds)': round(load_time, 2),
                                'Date': time.strftime("%Y-%m-%d", time.localtime(tab_data['start_time'])),
                                'Timestamp': time.strftime("%H:%M:%S", time.localtime(tab_data['start_time'])),
                                'Chart Count': chart_count,
                                'Round': tab_data['round'],
                                'Parallel Instance': tab_data['parallel_instance'],
                                'Tab': tab_data['tab_number'],
                                'Scenario': 'FORCED Parallel Same Dashboard',
                                'Status': status
                            }
                            
                            all_results.append(result)
                            self.tester.log(f"✓ Dashboard {dashboard_id} Instance {tab_data['parallel_instance']}: {load_time:.2f}s, {chart_count} charts")
                            
                        except Exception as e:
                            self.tester.log(f"Error measuring dashboard {dashboard_id} instance {tab_data.get('parallel_instance', '?')}: {str(e)}")
                            continue
                    
                    # STEP 3: Close extra tabs (keep original)
                    self.tester.log("STEP 3: Cleaning up extra tabs...")
                    
                    tabs_to_close = []
                    for tab_data in tab_info:
                        if tab_data['tab_handle'] != original_tab:
                            tabs_to_close.append(tab_data['tab_handle'])
                    
                    self.tester.log(f"Will close {len(tabs_to_close)} extra tabs")
                    
                    for tab_handle in tabs_to_close:
                        try:
                            main_driver.switch_to.window(tab_handle)
                            main_driver.close()
                            self.tester.log("Closed extra tab")
                        except Exception as e:
                            self.tester.log(f"Error closing tab: {str(e)}")
                    
                    # Return to original tab
                    try:
                        main_driver.switch_to.window(original_tab)
                        remaining_handles = main_driver.window_handles
                        self.tester.log(f"Returned to original tab, {len(remaining_handles)} tabs remaining")
                    except Exception as e:
                        self.tester.log(f"Error returning to original tab: {str(e)}")
                    
                    # Pause between rounds
                    if round_num < iterations_per_dashboard - 1:
                        self.tester.log("Pausing before next round...")
                        time.sleep(3)
            
            # Summary
            if all_results:
                successful = [r for r in all_results if r.get('Status') == 'Success']
                self.tester.log(f"\n=== FORCED PARALLEL TEST SUMMARY ===")
                self.tester.log(f"Total parallel instances tested: {len(all_results)}")
                self.tester.log(f"Successful loads: {len(successful)}")
                self.tester.log(f"Failed loads: {len(all_results) - len(successful)}")
                
                if successful:
                    # Show results by round to see parallel performance
                    by_round = {}
                    for result in successful:
                        round_key = f"Round {result['Round']}"
                        if round_key not in by_round:
                            by_round[round_key] = []
                        by_round[round_key].append(result['Load Time (seconds)'])
                    
                    for round_key, times in by_round.items():
                        avg_time = sum(times) / len(times)
                        min_time = min(times)
                        max_time = max(times)
                        self.tester.log(f"{round_key}: {len(times)} parallel instances, avg: {avg_time:.2f}s, range: {min_time:.2f}s-{max_time:.2f}s")
                
        except Exception as e:
            self.tester.log(f"ERROR in forced parallel test: {str(e)}")
            import traceback
            traceback.print_exc()
        
        self.tester.log(f"=== Completed Scenario 3: {len(all_results)} parallel instances tested ===")
        return all_results
    
    # Also fix the scenario_4_dashboard_refresh method which has the same issue
    def scenario_4_dashboard_refresh(self, dashboard_ids, refresh_count=5, wait_between_refresh=2):
        """
        Scenario 4: Measure refresh time of multiple dashboards
        
        Args:
            dashboard_ids: List of dashboard IDs to measure
            refresh_count: Number of times to refresh each dashboard
            wait_between_refresh: Time to wait between refreshes in seconds
            
        Returns:
            list: List of measurement data dictionaries
        """
        self.tester.log(f"=== Starting Scenario 4: Dashboard Refresh for {dashboard_ids} ===")
        self.tester.log(f"Will refresh each dashboard {refresh_count} times")
        
        all_results = []
        
        try:
            # Get the persistent driver with login already done
            driver = self.tester.get_persistent_driver()
            if not driver:
                self.tester.log("Failed to get persistent driver, aborting test")
                return all_results
            
            # Process each dashboard
            for dashboard_id in dashboard_ids:
                self.tester.log(f"Starting refresh measurements for dashboard {dashboard_id}")
                
                # Perform the refresh test
                refresh_results = self.tester.measure_dashboard_refresh(
                    driver, 
                    dashboard_id, 
                    refresh_count, 
                    wait_between_refresh
                )
                
                # Add scenario info
                for result in refresh_results:
                    result['Scenario'] = 'Dashboard Refresh'
                    all_results.append(result)
                
        except Exception as e:
            self.tester.log(f"ERROR in scenario 4: {str(e)}")
            import traceback
            traceback.print_exc()
        
        self.tester.log(f"=== Completed Scenario 4: {len(all_results)} measurements collected ===")
        return all_results
    
    def scenario_5_chart_refresh(self, dashboard_id, chart_refresh_iterations=3, wait_between_refresh=2):
        """
        Scenario 5: Measure refresh time of individual charts within a single dashboard
        
        Args:
            dashboard_id: ID of the dashboard to test
            chart_refresh_iterations: Number of times to refresh each chart
            wait_between_refresh: Time to wait between refreshes in seconds
            
        Returns:
            list: List of measurement data dictionaries
        """
        self.tester.log(f"=== Starting Scenario 5: Individual Chart Refresh for Dashboard {dashboard_id} ===")
        self.tester.log(f"Will refresh each chart {chart_refresh_iterations} times")
        
        all_results = []
        
        try:
            # Get the persistent driver with login already done
            driver = self.tester.get_persistent_driver()
            if not driver:
                self.tester.log("Failed to get persistent driver, aborting test")
                return all_results
        
            # Use the correct URL path (/superset/ instead of /golgix/)
            dashboard_url = f"{self.tester.base_url}/superset/dashboard/{dashboard_id}/"
            self.tester.log(f"Navigating to dashboard for chart refresh test: {dashboard_url}")
            driver.get(dashboard_url)
            
            # Wait for dashboard to fully load
            self.tester.log(f"Waiting for dashboard {dashboard_id} to load...")
            time.sleep(5)
            
            # Wait for dashboard elements
            try:
                WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".dashboard-grid, .dashboard, .chart-container, .dashboard-component-chart"))
                )
                self.tester.log("Dashboard element found")
            except TimeoutException:
                self.tester.log("WARNING: Could not detect dashboard elements, continuing anyway")
            
            # Wait for loading indicators to disappear
            self.tester.wait_for_loading_indicators_to_disappear(driver, 60)
            
            # Additional wait for charts to fully render
            time.sleep(10)
            
            # Find all chart elements - expanded selectors to ensure charts are found
            chart_selectors = [
                ".chart-container", 
                ".dashboard-component-chart",
                ".slice_container",
                ".slice-container",
                ".dashboard-component", 
                "[data-test='chart-container']",
                ".dashboard-chart",
                ".grid-content",
                ".dashboard__grid-item"
            ]
            
            charts = []
            for selector in chart_selectors:
                found_charts = driver.find_elements(By.CSS_SELECTOR, selector)
                if found_charts:
                    charts = found_charts
                    self.tester.log(f"Found {len(charts)} charts using selector: {selector}")
                    break
            
            if not charts:
                self.tester.log(f"No charts found in dashboard {dashboard_id}")
                return all_results
            
            # Refresh each chart the specified number of times
            for i, chart in enumerate(charts):
                chart_index = i + 1
                self.tester.log(f"Starting refresh test for chart #{chart_index} of {len(charts)}")
                
                # Perform multiple refresh iterations for this chart
                for iteration in range(chart_refresh_iterations):
                    self.tester.log(f"Chart #{chart_index}: Refresh iteration {iteration+1}/{chart_refresh_iterations}")
                    
                    try:
                        # Scroll to make the chart visible
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", chart)
                        time.sleep(1)  # Wait for scroll to complete
                        
                        # Find the menu button (three dots) within this chart
                        # Try multiple selectors to find the menu button
                        menu_button = None
                        menu_selectors = [
                            ".chart-header .dropdown-trigger",
                            ".dashboard-component-menu-trigger",
                            ".dashboard-header .dropdown-trigger",
                            ".chart-controls .dropdown-trigger",
                            ".more-options",
                            ".more-button",
                            ".btn-default", 
                            ".fa-ellipsis-v",
                            ".anticon-more",
                            ".chart-controls .ant-dropdown-trigger",
                            ".ant-dropdown-trigger"
                        ]
                        
                        for selector in menu_selectors:
                            try:
                                # First try to find within this chart
                                menu_buttons = chart.find_elements(By.CSS_SELECTOR, selector)
                                if menu_buttons:
                                    menu_button = menu_buttons[0]
                                    self.tester.log(f"Found menu button for chart #{chart_index} using selector: {selector}")
                                    break
                            except:
                                # If fails, try at document level (some charts have menu outside the chart container)
                                continue
                        
                        # If menu button not found within chart, try to find it nearby
                        if not menu_button:
                            # Get chart position
                            chart_position = chart.location
                            chart_size = chart.size
                            
                            # Find all menu buttons in the document
                            all_menu_buttons = []
                            for selector in menu_selectors:
                                all_menu_buttons.extend(driver.find_elements(By.CSS_SELECTOR, selector))
                            
                            # Find the closest menu button to this chart
                            closest_button = None
                            min_distance = float('inf')
                            
                            for btn in all_menu_buttons:
                                btn_position = btn.location
                                # Calculate distance from button to chart center
                                distance = ((btn_position['x'] - (chart_position['x'] + chart_size['width']/2))**2 + 
                                            (btn_position['y'] - (chart_position['y'] + chart_size['height']/2))**2)**0.5
                                
                                if distance < min_distance:
                                    min_distance = distance
                                    closest_button = btn
                            
                            if closest_button and min_distance < 200:  # Only use if reasonably close to chart
                                menu_button = closest_button
                                self.tester.log(f"Found closest menu button for chart #{chart_index} at distance {min_distance:.2f}px")
                        
                        if not menu_button:
                            # Alternative: try to find three-dot button using JavaScript
                            menu_button = driver.execute_script("""
                                var chart = arguments[0];
                                var buttons = document.querySelectorAll('button');
                                
                                // Find button with three dots (ellipsis) or menu icon
                                for (var i = 0; i < buttons.length; i++) {
                                    var btn = buttons[i];
                                    var rect1 = chart.getBoundingClientRect();
                                    var rect2 = btn.getBoundingClientRect();
                                    
                                    // Check if button is within or near the chart
                                    var horizontalOverlap = !(rect1.right < rect2.left || rect1.left > rect2.right);
                                    var verticalOverlap = !(rect1.bottom < rect2.top || rect1.top > rect2.bottom);
                                    
                                    // Check button content or class
                                    if ((horizontalOverlap && verticalOverlap) || 
                                        (Math.abs(rect1.top - rect2.top) < 50)) {
                                        if (btn.textContent.includes('...') || 
                                            btn.className.includes('dropdown') || 
                                            btn.className.includes('menu') ||
                                            btn.className.includes('more')) {
                                            return btn;
                                        }
                                    }
                                }
                                return null;
                            """, chart)
                        
                        if menu_button:
                            # Record start time before clicking menu
                            start_time = datetime.datetime.now()
                            start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                            
                            # Click the menu button
                            menu_button.click()
                            self.tester.log(f"Clicked menu button for chart #{chart_index}")
                            time.sleep(1)  # Wait for dropdown to appear
                            
                            # Look for "Force refresh" option in the menu
                            force_refresh_found = False
                            refresh_options = [
                                "Force refresh",
                                "Refresh",
                                "refresh",
                                "force refresh"
                            ]
                            
                            for option_text in refresh_options:
                                try:
                                    # Try to find by text content
                                    refresh_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{option_text}')]")
                                    
                                    if refresh_elements:
                                        for element in refresh_elements:
                                            if element.is_displayed():
                                                element.click()
                                                self.tester.log(f"Clicked '{option_text}' option for chart #{chart_index}")
                                                force_refresh_found = True
                                                break
                                    
                                    if force_refresh_found:
                                        break
                                except:
                                    continue
                            
                            if not force_refresh_found:
                                # Try to find by dropdown menu items
                                try:
                                    menu_items = driver.find_elements(By.CSS_SELECTOR, 
                                        ".ant-dropdown-menu-item, .dropdown-item, li.menu-item")
                                    
                                    for item in menu_items:
                                        try:
                                            item_text = item.text.lower()
                                            if "refresh" in item_text:
                                                item.click()
                                                self.tester.log(f"Clicked menu item containing 'refresh' for chart #{chart_index}")
                                                force_refresh_found = True
                                                break
                                        except:
                                            continue
                                except:
                                    self.tester.log(f"Could not find dropdown menu items for chart #{chart_index}")
                            
                            if not force_refresh_found:
                                # Click escape to close the menu and try another approach
                                webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                                self.tester.log(f"Could not find Force refresh option for chart #{chart_index}, using alternative method")
                                
                                # Alternative: try to refresh by executing JavaScript for this specific chart
                                try:
                                    driver.execute_script("""
                                        // Try to find and trigger refresh for this chart
                                        var chart = arguments[0];
                                        var chartId = chart.getAttribute('data-test-chart-id') || 
                                                    chart.getAttribute('data-slice-id') ||
                                                    chart.getAttribute('id');
                                        
                                        // Try to find refresh method on chart object or trigger an event
                                        if (window.dashboardComponents && chartId) {
                                            if (window.dashboardComponents[chartId]) {
                                                if (typeof window.dashboardComponents[chartId].refresh === 'function') {
                                                    window.dashboardComponents[chartId].refresh();
                                                    return true;
                                                }
                                            }
                                        }
                                        
                                        // Dispatch custom refresh event on chart
                                        var event = new CustomEvent('refresh');
                                        chart.dispatchEvent(event);
                                        return true;
                                    """, chart)
                                    self.tester.log(f"Triggered JavaScript refresh for chart #{chart_index}")
                                    force_refresh_found = True
                                except:
                                    self.tester.log(f"Failed to refresh chart #{chart_index} via JavaScript")
                            
                            if not force_refresh_found:
                                self.tester.log(f"Could not find any way to refresh chart #{chart_index}, skipping")
                                continue
                            
                            # Wait for the chart to refresh
                            time.sleep(2)  # Initial wait
                            
                            # Wait for loading indicator to appear and disappear for this chart
                            try:
                                # First wait for loading indicator to appear (confirms refresh started)
                                loading_appeared = False
                                for _ in range(5):  # Try for up to 5 seconds
                                    loading_indicators = chart.find_elements(By.CSS_SELECTOR, ".loading, .loading-spinner, .spinner")
                                    if loading_indicators:
                                        loading_appeared = True
                                        self.tester.log(f"Loading indicator appeared for chart #{chart_index}")
                                        break
                                    time.sleep(1)
                                
                                # If loading indicator appeared, wait for it to disappear
                                if loading_appeared:
                                    for _ in range(60):  # Wait up to 60 seconds
                                        loading_indicators = chart.find_elements(By.CSS_SELECTOR, ".loading, .loading-spinner, .spinner")
                                        if not loading_indicators or not any(indicator.is_displayed() for indicator in loading_indicators):
                                            self.tester.log(f"Loading indicator disappeared for chart #{chart_index}")
                                            break
                                        time.sleep(1)
                            except:
                                # If we can't check loading indicators properly, just wait a reasonable time
                                self.tester.log(f"Unable to check loading indicators for chart #{chart_index}, using fixed wait")
                                time.sleep(15)  # Reasonable wait for chart refresh
                            
                            # Additional wait to ensure chart has fully rendered
                            time.sleep(5)
                            
                            # Record end time
                            end_time = datetime.datetime.now()
                            end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                            
                            # Calculate refresh time
                            refresh_time_seconds = (end_time - start_time).total_seconds()
                            
                            self.tester.log(f"Chart #{chart_index} refreshed in {refresh_time_seconds:.2f} seconds")
                            
                            # Add result
                            result = {
                                'Dashboard ID': dashboard_id,
                                'Chart Index': chart_index,
                                'Start Time': start_time_str,
                                'End Time': end_time_str,
                                'Refresh Time (seconds)': refresh_time_seconds,
                                'Date': start_time.strftime("%Y-%m-%d"),
                                'Timestamp': start_time.strftime("%H:%M:%S"),
                                'Iteration': iteration + 1
                            }
                            
                            all_results.append(result)
                            
                        else:
                            self.tester.log(f"Could not find menu button for chart #{chart_index}, skipping")
                            
                    except Exception as e:
                        self.tester.log(f"ERROR refreshing chart #{chart_index}: {str(e)}")
                        import traceback
                        traceback.print_exc()
                    
                    # Wait between refreshes of the same chart
                    if iteration < chart_refresh_iterations - 1:
                        time.sleep(wait_between_refresh)
                
                # Wait a bit before moving to the next chart
                time.sleep(2)
                
        except Exception as e:
            self.tester.log(f"ERROR in chart refresh test for dashboard {dashboard_id}: {str(e)}")
            import traceback
            traceback.print_exc()
        
        self.tester.log(f"=== Completed Scenario 5: {len(all_results)} measurements collected ===")
        return all_results
    
    
    def run_all_scenarios(self, dashboards_config):
        """
        Run all scenarios with the given dashboard configuration
        
        Args:
            dashboards_config: Dictionary with scenario configuration
            
        Returns:
            dict: Dictionary with results from all scenarios
        """
        all_results = {}
        
        try:
            # Scenario 1: Single dashboard, multiple iterations
            if dashboards_config.get('scenario_1', {}).get('enabled', False):
                self.tester.log("Running Scenario 1 (enabled)")
                config = dashboards_config['scenario_1']
                dashboard_id = config['dashboard_id']
                iterations = config['iterations']
                
                results = self.scenario_1_single_dashboard(dashboard_id, iterations)
                all_results['Scenario 1'] = results
            else:
                self.tester.log("Skipping Scenario 1 (disabled)")
            
            # Scenario 2: Sequential dashboards
            if dashboards_config.get('scenario_2', {}).get('enabled', False):
                self.tester.log("Running Scenario 2 (enabled)")
                config = dashboards_config['scenario_2']
                dashboard_ids = config['dashboard_ids']
                iterations_per_dashboard = config['iterations_per_dashboard']
                
                results = self.scenario_2_sequential_dashboards(dashboard_ids, iterations_per_dashboard)
                all_results['Scenario 2'] = results
            else:
                self.tester.log("Skipping Scenario 2 (disabled)")
            
            # Scenario 3: Parallel dashboards
            if dashboards_config.get('scenario_3', {}).get('enabled', False):
                self.tester.log("Running Scenario 3 (enabled)")
                config = dashboards_config['scenario_3']
                dashboard_ids = config['dashboard_ids']
                iterations_per_dashboard = config['iterations_per_dashboard']
                max_workers = config.get('max_workers', 5)
                
                results = self.scenario_3_parallel_dashboards(dashboard_ids, iterations_per_dashboard, max_workers)
                all_results['Scenario 3'] = results
            else:
                self.tester.log("Skipping Scenario 3 (disabled)")
            
            # Scenario 4: Dashboard refresh
            if dashboards_config.get('scenario_4', {}).get('enabled', False):
                self.tester.log("Running Scenario 4 (enabled)")
                config = dashboards_config['scenario_4']
                dashboard_ids = config['dashboard_ids']
                refresh_count = config['refresh_count']
                wait_between_refresh = config.get('wait_between_refresh', 2)
                
                results = self.scenario_4_dashboard_refresh(dashboard_ids, refresh_count, wait_between_refresh)
                all_results['Scenario 4'] = results
            else:
                self.tester.log("Skipping Scenario 4 (disabled)")
            
            # Scenario 5: Individual chart refresh
            if dashboards_config.get('scenario_5', {}).get('enabled', False):
                self.tester.log("Running Scenario 5 (enabled)")
                config = dashboards_config['scenario_5']
                dashboard_id = config['dashboard_id']
                chart_refresh_iterations = config['chart_refresh_iterations']
                wait_between_refresh = config.get('wait_between_refresh', 2)
                
                results = self.scenario_5_chart_refresh(dashboard_id, chart_refresh_iterations, wait_between_refresh)
                all_results['Scenario 5'] = results
            else:
                self.tester.log("Skipping Scenario 5 (disabled)")
            
        except Exception as e:
            self.tester.log(f"ERROR in run_all_scenarios: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            # Clean up any resources
            pass

        return all_results