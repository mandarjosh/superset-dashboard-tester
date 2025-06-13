"""
Superset Performance Tester main class
Contains the core functionality for testing Superset dashboard performance
"""

import time
import datetime
import os
import traceback
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys

class SupersetPerformanceTester:
    def __init__(self, base_url, username, password, output_file="dashboard_performance.xlsx", log_dir="logs"):
        """
        Initialize the performance testing framework
        
        Args:
            base_url (str): Base URL of the Superset instance
            username (str): Username for Superset login
            password (str): Password for Superset login
            output_file (str): Path to Excel file for storing results
            log_dir (str): Directory for storing log files
        """
        self.base_url = base_url
        self.username = username
        self.password = password
        self.output_file = output_file
        self.persistent_driver = None  # Shared driver for all tests
        self.log_dir = log_dir
        
        # Create directories if they don't exist
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Initialize log file
        self.log_file = os.path.join(self.log_dir, f"performance_test_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        with open(self.log_file, "w") as f:
            f.write(f"Superset Performance Test started at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Base URL: {base_url}\n")
    
    def log(self, message):
        """Log a message to both console and log file"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        with open(self.log_file, "a") as f:
            f.write(log_message + "\n")
            
    def create_driver(self, headless=False):
        """Create and return a WebDriver instance"""
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        #if headless:
            #options.add_argument("--headless")
        
        driver = webdriver.Chrome(options=options)
        return driver
    
    def get_persistent_driver(self):
        """Get or create a persistent driver and ensure login"""
        if self.persistent_driver is None:
            self.persistent_driver = self.create_driver()
            # Try to login
            if not self.login(self.persistent_driver):
                self.log("ERROR: Failed to login with persistent driver")
                self.persistent_driver.quit()
                self.persistent_driver = None
                return None
        
        return self.persistent_driver
    
    def open_new_tab(self, driver):
        """Open a new tab in the browser and return its handle"""
        # Execute JavaScript to open a new tab
        driver.execute_script("window.open('', '_blank');")
        # Switch to the new tab (it will be the last handle)
        new_tab = driver.window_handles[-1]
        driver.switch_to.window(new_tab)
        return new_tab
    
    def login(self, driver):
        """Handle login to Superset with egaSSO SSO"""
        try:
            self.log(f"Navigating to Superset at {self.base_url}/login/")
            driver.get(f"{self.base_url}/login/")
            
            # Wait for the page to load
            self.log("Waiting for login page to load...")
            time.sleep(5)  # Initial wait
            
            # Look for the "Sign In with egaSSO" link/button
            try:
                # Try various selectors for the SSO button
                sso_button = None
                sso_selectors = [
                    (By.XPATH, "//a[contains(text(), 'SIGN IN WITH EGASSO')]"),
                    (By.XPATH, "//button[contains(text(), 'SIGN IN WITH EGASSO')]"),
                    (By.LINK_TEXT, "SIGN IN WITH EGASSO"),
                    (By.PARTIAL_LINK_TEXT, "EGASSO"),
                    (By.CSS_SELECTOR, ".btn-primary"),
                    (By.CSS_SELECTOR, "a.btn, button.btn")
                ]
                
                for selector_type, selector_value in sso_selectors:
                    try:
                        elements = driver.find_elements(selector_type, selector_value)
                        if elements:
                            sso_button = elements[0]
                            self.log(f"Found SSO button using {selector_type}={selector_value}")
                            break
                    except:
                        continue
                
                if not sso_button:
                    # If we still can't find it, try getting all links and buttons
                    buttons = driver.find_elements(By.TAG_NAME, "button")
                    links = driver.find_elements(By.TAG_NAME, "a")
                    
                    self.log(f"Found {len(buttons)} buttons and {len(links)} links")
                    
                    # Log all buttons and links for debugging
                    for i, button in enumerate(buttons):
                        self.log(f"Button #{i}: text='{button.text}', class='{button.get_attribute('class')}'")
                    
                    for i, link in enumerate(links):
                        self.log(f"Link #{i}: text='{link.text}', href='{link.get_attribute('href')}', class='{link.get_attribute('class')}'")
                    
                    # Try to find the SSO link by filtering
                    for link in links:
                        if "EGASSO" in link.text.upper() or "SIGN IN" in link.text.upper():
                            sso_button = link
                            self.log(f"Found SSO link by text: {link.text}")
                            break
                
                if sso_button:
                    self.log("Clicking SSO button to start authentication...")
                    sso_button.click()
                    
                    # Wait for SSO redirection and authentication process - INCREASED TO 30 SECONDS
                    self.log("Waiting for SSO redirection and authentication...")
                    time.sleep(30)  # Increased from 10 to 30 seconds
                    
                    # Record where we are now
                    current_url = driver.current_url
                    self.log(f"URL after SSO button click: {current_url}")
                    
                    # Now we need to handle the SSO login form, which will depend on your SSO system
                    # This is likely on auth.tkosuat.co.uk based on your previous logs
                    
                    if "auth.tkosuat.co.uk" in current_url:
                        self.log("Redirected to auth.tkosuat.co.uk - handling SSO login form")
                        
                        # Wait for SSO login form to load
                        time.sleep(5)
                        
                        # Try to find username and password fields on the SSO form
                        # This will depend on the specific SSO implementation
                        try:
                            # Find username field
                            username_field = None
                            username_selectors = [
                                (By.ID, "username"),
                                (By.ID, "email"),
                                (By.NAME, "username"),
                                (By.NAME, "email"),
                                (By.CSS_SELECTOR, "input[type='email']"),
                                (By.CSS_SELECTOR, "input[type='text']")
                            ]
                            
                            for selector_type, selector_value in username_selectors:
                                try:
                                    elements = driver.find_elements(selector_type, selector_value)
                                    if elements:
                                        username_field = elements[0]
                                        self.log(f"Found username field on SSO page using {selector_type}={selector_value}")
                                        break
                                except:
                                    continue
                            
                            if username_field:
                                # Enter username
                                username_field.clear()
                                username_field.send_keys(self.username)
                                self.log(f"Entered username on SSO page: {self.username}")
                                
                                # Find password field
                                password_field = None
                                password_selectors = [
                                    (By.ID, "password"),
                                    (By.NAME, "password"),
                                    (By.CSS_SELECTOR, "input[type='password']")
                                ]
                                
                                for selector_type, selector_value in password_selectors:
                                    try:
                                        elements = driver.find_elements(selector_type, selector_value)
                                        if elements:
                                            password_field = elements[0]
                                            self.log(f"Found password field on SSO page using {selector_type}={selector_value}")
                                            break
                                    except:
                                        continue
                                
                                if password_field:
                                    # Enter password
                                    password_field.clear()
                                    password_field.send_keys(self.password)
                                    self.log("Entered password on SSO page")
                                    
                                    # Find login button
                                    login_button = None
                                    button_selectors = [
                                        (By.CSS_SELECTOR, "button[type='submit']"),
                                        (By.CSS_SELECTOR, "input[type='submit']"),
                                        (By.XPATH, "//button[contains(text(), 'Log in') or contains(text(), 'Sign in')]"),
                                        (By.XPATH, "//input[@value='Log in' or @value='Sign in']")
                                    ]
                                    
                                    for selector_type, selector_value in button_selectors:
                                        try:
                                            elements = driver.find_elements(selector_type, selector_value)
                                            if elements:
                                                login_button = elements[0]
                                                self.log(f"Found login button on SSO page using {selector_type}={selector_value}")
                                                break
                                        except:
                                            continue
                                    
                                    if login_button:
                                        # Click login button
                                        login_button.click()
                                        self.log("Clicked login button on SSO page")
                                    else:
                                        # Press Enter on password field
                                        password_field.send_keys(Keys.ENTER)
                                        self.log("Pressed Enter on password field on SSO page")
                                else:
                                    self.log("Could not find password field on SSO page")
                                    return False
                            else:
                                self.log("Could not find username field on SSO page")
                                return False
                        except Exception as sso_error:
                            self.log(f"Error during SSO login: {str(sso_error)}")
                            return False
                    
                    # Wait for the login and redirects to complete - INCREASED TO 30 SECONDS
                    self.log("Waiting for authentication process to complete...")
                    time.sleep(60)  # Increased from 20 to 30 seconds
                    
                    # After successful login, check if we're on the MFA setup page
                    self.log("Checking for MFA setup page...")
                    
                    current_url = driver.current_url
                    page_source = driver.page_source
                    
                    if "setup" in current_url.lower() or "Google Authenticator" in page_source or "validation method" in page_source:
                        self.log("Detected MFA setup page - looking for 'Skip for now' button")
                        try:
                            skip_buttons = driver.find_elements(By.XPATH, 
                                "//button[contains(text(), 'Skip') or contains(text(), 'skip')]")
                            
                            if skip_buttons:
                                self.log("Found Skip button, clicking it")
                                skip_buttons[0].click()
                                time.sleep(5)  # Wait for the skip action to complete
                            else:
                                self.log("No Skip button found on MFA page")
                                # Try to save a screenshot for debugging
                                driver.save_screenshot("mfa_page.png")
                                self.log("Saved MFA page screenshot to mfa_page.png")
                        except Exception as e:
                            self.log(f"Error handling MFA setup page: {str(e)}")
                    
                    # Check if we're logged in successfully
                    current_url = driver.current_url
                    self.log(f"URL after authentication process: {current_url}")
                    
                    # Success is likely if we're redirected back to Superset
                    if "/superset/" in current_url or current_url == self.base_url + "/":
                        self.log("Successfully logged in through SSO!")
                        return True
                    elif "/login/" in current_url:
                        self.log("Still on login page - authentication may have failed")
                        return False
                    else:
                        # We're on some other page - might be successful or might be an MFA page
                        self.log(f"Authentication redirected to unexpected URL: {current_url}")
                        
                        # Check if we're on an MFA page
                        if "mfa" in current_url.lower() or "two-factor" in current_url.lower():
                            self.log("Appears to be on an MFA page - automated MFA not implemented")
                            return False
                        
                        # If not explicitly on login page, we'll assume success
                        self.log("Not on login page, assuming authentication was successful")
                        return True
                else:
                    self.log("Could not find SSO button")
                    return False
                    
            except Exception as e:
                self.log(f"Error during SSO authentication: {str(e)}")
                traceback.print_exc()
                return False
                
        except Exception as e:
            self.log(f"ERROR during login: {str(e)}")
            traceback.print_exc()
            return False

    def count_dashboard_charts(self, driver):
        """
        Count the number of charts in the current dashboard
        
        Args:
            driver: WebDriver instance
            
        Returns:
            int: Number of charts in the dashboard
        """
        try:
            # Wait for charts to be visible
            time.sleep(2)
            
            # Different CSS selectors to try for finding chart elements
            chart_selectors = [
                ".chart-container", 
                ".dashboard-component-chart",
                ".slice_container",
                ".slice-container",
                ".slice-cell",
                ".grid-container .chart"
            ]
            
            chart_count = 0
            
            # Try each selector
            for selector in chart_selectors:
                charts = driver.find_elements(By.CSS_SELECTOR, selector)
                if charts:
                    chart_count = len(charts)
                    self.log(f"Found {chart_count} charts using selector: {selector}")
                    break
            
            # If no charts found, try an alternate approach
            if chart_count == 0:
                # Look for any visualization elements
                viz_elements = driver.find_elements(By.CSS_SELECTOR, "[data-test='dashboard-component-chart']")
                chart_count = len(viz_elements)
                self.log(f"Found {chart_count} charts using data-test attribute")
            
            return chart_count
            
        except Exception as e:
            self.log(f"ERROR counting charts: {str(e)}")
            return 0
    
    def find_chart_elements(self, driver):
        """
        Find all chart elements in the current dashboard
        
        Args:
            driver: WebDriver instance
            
        Returns:
            list: List of chart elements with their IDs or positions
        """
        charts = []
        
        try:
            # Different selectors to try for finding chart containers
            chart_selectors = [
                ".chart-container", 
                ".dashboard-component-chart",
                ".slice_container",
                ".slice-container",
                ".slice-cell",
                ".grid-container .chart"
            ]
            
            # Try each selector
            for selector in chart_selectors:
                chart_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if chart_elements:
                    self.log(f"Found {len(chart_elements)} charts using selector: {selector}")
                    charts = chart_elements
                    break
            
            # If no charts found by conventional selectors, try using data attributes
            if not charts:
                chart_elements = driver.find_elements(By.CSS_SELECTOR, "[data-test='dashboard-component-chart']")
                self.log(f"Found {len(chart_elements)} charts using data-test attribute")
                charts = chart_elements
            
            # If we still don't have any charts, look for any visualization elements
            if not charts:
                self.log("Looking for any possible chart elements...")
                possible_charts = driver.find_elements(By.CSS_SELECTOR, ".dashboard-component")
                filtered_charts = []
                for element in possible_charts:
                    # Try to find characteristics of chart elements
                    if element.get_attribute("class") and "chart" in element.get_attribute("class").lower():
                        filtered_charts.append(element)
                if filtered_charts:
                    self.log(f"Found {len(filtered_charts)} potential chart elements")
                    charts = filtered_charts
            
            return charts
        except Exception as e:
            self.log(f"ERROR finding chart elements: {str(e)}")
            return []
    
    def measure_dashboard_load_time(self, driver, dashboard_id):
        """
        Measure the loading time for a specific dashboard
        
        Args:
            driver: WebDriver instance
            dashboard_id: ID of the dashboard to measure
            
        Returns:
            dict: Data about the load time measurement or None if failed
        """
        try:
            dashboard_url = f"{self.base_url}/superset/dashboard/{dashboard_id}/"
            self.log(f"Navigating to dashboard: {dashboard_url}")
            
            # Record start time
            start_time = datetime.datetime.now()
            start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            
            # Load the dashboard
            driver.get(dashboard_url)
            
            # Wait for dashboard to appear (but don't include this in timing yet)
            self.log(f"Waiting for dashboard {dashboard_id} to load...")
            
            # Wait for dashboard grid or visualization elements to appear
            try:
                WebDriverWait(driver, 90).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".dashboard-grid, .dashboard, .chart-container, .dashboard-component-chart"))
                )
                self.log("Dashboard elements found")
            except TimeoutException:
                self.log("WARNING: Could not detect dashboard elements, continuing with timing anyway")
            
            # Wait for loading indicators to disappear
            self.log("Waiting for loading indicators to disappear...")
            loading_complete = False
            
            try:
                # Check for loading spinners and wait for them to disappear
                loading_spinners = driver.find_elements(By.CSS_SELECTOR, ".loading, .loading-spinner, .spinner")
                if loading_spinners:
                    self.log(f"Found {len(loading_spinners)} loading indicators, waiting for them to disappear...")
                    WebDriverWait(driver, 60).until(
                        lambda driver: not any(spinner.is_displayed() for spinner in driver.find_elements(By.CSS_SELECTOR, ".loading, .loading-spinner, .spinner"))
                    )
                    self.log("All loading indicators have disappeared")
                
                loading_complete = True
                
            except Exception as e:
                self.log(f"Error while waiting for loading indicators: {str(e)}")
                # Use JavaScript to check if page is fully loaded
                try:
                    WebDriverWait(driver, 30).until(
                        lambda driver: driver.execute_script("return document.readyState") == "complete"
                    )
                    loading_complete = True
                except:
                    self.log("Using fallback - assuming page is loaded")
                    loading_complete = True
            
            # Additional intelligent wait for charts to render
            self.log("Checking if charts are fully rendered...")
            charts_loaded = False
            max_chart_wait = 30  # Maximum 30 seconds to wait for charts
            chart_wait_start = time.time()
            
            while (time.time() - chart_wait_start) < max_chart_wait and not charts_loaded:
                try:
                    # Use JavaScript to check if charts appear to be loaded
                    charts_status = driver.execute_script("""
                        var charts = document.querySelectorAll('.chart-container, .dashboard-component-chart');
                        var loadedCharts = 0;
                        var totalCharts = charts.length;
                        
                        for (var i = 0; i < charts.length; i++) {
                            var chart = charts[i];
                            // Check if chart has content (not just loading)
                            if (chart.innerHTML.length > 100 && 
                                !chart.innerHTML.includes('loading') && 
                                !chart.innerHTML.includes('Loading')) {
                                loadedCharts++;
                            }
                        }
                        
                        return {
                            total: totalCharts,
                            loaded: loadedCharts,
                            percentage: totalCharts > 0 ? (loadedCharts / totalCharts) * 100 : 100
                        };
                    """)
                    
                    # Consider charts loaded if 80% or more are loaded, or if we have waited long enough
                    if charts_status['percentage'] >= 80 or (time.time() - chart_wait_start) > 15:
                        charts_loaded = True
                        self.log(f"Charts loading: {charts_status['loaded']}/{charts_status['total']} ({charts_status['percentage']:.1f}%)")
                    else:
                        time.sleep(1)  # Check again in 1 second
                        
                except Exception as e:
                    self.log(f"Error checking chart status: {str(e)}")
                    charts_loaded = True  # Assume loaded if we can't check
            
            # *** RECORD END TIME HERE - AFTER ACTUAL LOADING IS COMPLETE ***
            end_time = datetime.datetime.now()
            end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            
            # Calculate load time in seconds (this is now the ACTUAL load time)
            load_time_seconds = (end_time - start_time).total_seconds()
            
            self.log(f"Dashboard {dashboard_id} ACTUALLY loaded in {load_time_seconds:.2f} seconds")
            
            # NOW do any additional waits for stability (these won't affect the measurement)
            self.log("Additional wait for stability (not included in measurement)...")
            time.sleep(5)  # Reduced from 15 to 5 seconds
            
            # Count the number of charts in this dashboard
            chart_count = self.count_dashboard_charts(driver)
            
            self.log(f"Final result: Dashboard {dashboard_id} loaded in {load_time_seconds:.2f} seconds (Charts: {chart_count})")
            
            # Return data about the measurement
            return {
                'Dashboard ID': dashboard_id,
                'Start Time': start_time_str,
                'End Time': end_time_str,
                'Load Time (seconds)': load_time_seconds,
                'Date': start_time.strftime("%Y-%m-%d"),
                'Timestamp': start_time.strftime("%H:%M:%S"),
                'Chart Count': chart_count
            }
            
        except Exception as e:
            self.log(f"ERROR measuring dashboard {dashboard_id}: {str(e)}")
            traceback.print_exc()
            return None

    # Method 1: Use a custom wait condition instead of invisibility_of_elements_located
    def wait_for_loading_indicators_to_disappear(self, driver, timeout=60):
        """
        Wait for loading indicators to disappear using a custom wait condition
        with improved handling for stale elements
        
        Args:
            driver: WebDriver instance
            timeout: Maximum time to wait in seconds
        """
        self.log("Checking for loading indicators...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Use JavaScript to check for visible loading indicators
                # This avoids stale element issues by checking in a single operation
                visible_count = driver.execute_script("""
                    var spinners = document.querySelectorAll('.loading, .loading-spinner, .spinner');
                    var visibleCount = 0;
                    
                    for (var i = 0; i < spinners.length; i++) {
                        var spinner = spinners[i];
                        if (spinner.offsetParent !== null && 
                            getComputedStyle(spinner).display !== 'none' && 
                            getComputedStyle(spinner).visibility !== 'hidden') {
                            visibleCount++;
                        }
                    }
                    
                    return {
                        total: spinners.length,
                        visible: visibleCount
                    };
                """)
                
                # Log the count on first pass and periodically
                if time.time() - start_time < 1 or int(time.time()) % 5 == 0:
                    self.log(f"Found {visible_count['total']} loading indicators, {visible_count['visible']} visible")
                
                # If no loading indicators or none are visible, we're done
                if visible_count['total'] == 0 or visible_count['visible'] == 0:
                    self.log(f"All loading indicators have disappeared or are hidden (Total: {visible_count['total']}, Visible: {visible_count['visible']})")
                    return True
                
            except Exception as e:
                self.log(f"Error during JavaScript loading indicator check: {str(e)}")
                
                # Fallback to simpler check if JavaScript fails
                try:
                    # Just check if any loading indicators exist
                    loading_spinners = driver.find_elements(By.CSS_SELECTOR, ".loading, .loading-spinner, .spinner")
                    if not loading_spinners:
                        self.log("No loading indicators found (fallback check)")
                        return True
                except Exception as fallback_error:
                    self.log(f"Error during fallback loading indicator check: {str(fallback_error)}")
            
            # Wait before checking again
            time.sleep(1)
        
        # If we got here, we timed out
        self.log(f"Timed out waiting for loading indicators to disappear after {timeout} seconds")
        return False
        
    def wait_for_loading_indicators_alternative(self, driver, timeout=60):
        """
        Alternative method to wait for loading indicators to disappear
        
        Args:
            driver: WebDriver instance
            timeout: Maximum time to wait in seconds
        """
        try:
            WebDriverWait(driver, timeout).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, 
                    ".loading:not([style*='display: none']), .loading-spinner:not([style*='display: none']), .spinner:not([style*='display: none'])"))
            )
            self.log("All loading indicators have disappeared")
            return True
        except Exception as e:
            self.log(f"Error waiting for loading indicators: {str(e)}")
            return False

    def measure_dashboard_refresh(self, driver, dashboard_id, refresh_count=5, wait_between_refresh=2):
        """
        Measure the refresh time for a specific dashboard using the Refresh dashboard button
        
        Args:
            driver: WebDriver instance
            dashboard_id: ID of the dashboard to measure
            refresh_count: Number of times to refresh the dashboard
            wait_between_refresh: Time to wait between refreshes in seconds
            
        Returns:
            list: List of measurements for each refresh
        """
        results = []
        
        try:
            # First navigate to the dashboard
            dashboard_url = f"{self.base_url}/superset/dashboard/{dashboard_id}/"
            self.log(f"Initially navigating to dashboard: {dashboard_url}")
            driver.get(dashboard_url)
            
            # Wait for initial dashboard load (not measured)
            self.log(f"Waiting for dashboard {dashboard_id} to initially load...")
            time.sleep(10)  # Increased initial wait
            
            # Wait for dashboard elements to appear
            try:
                WebDriverWait(driver, 90).until(  # Increased timeout from 60 to 90 seconds
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".dashboard-grid, .dashboard, .chart-container, .dashboard-component-chart"))
                )
                self.log("Dashboard elements found")
            except TimeoutException:
                self.log("WARNING: Could not detect dashboard elements, continuing anyway")
                
            # Wait for loading indicators to disappear (initial load)
            self.wait_for_loading_indicators_to_disappear(driver, 60)
            time.sleep(5)  # Stability wait for initial load
            
            # Count charts only once
            chart_count = self.count_dashboard_charts(driver)
            
            # Perform refreshes
            for i in range(refresh_count):
                self.log(f"Starting refresh {i+1}/{refresh_count} for dashboard {dashboard_id}")
                
                # Record start time JUST BEFORE clicking refresh
                start_time = datetime.datetime.now()
                start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                
                # Try the standalone REFRESH button first
                refresh_clicked = False
                try:
                    refresh_buttons = driver.find_elements(By.XPATH, "//button[text()='REFRESH']")
                    if refresh_buttons:
                        refresh_buttons[0].click()
                        self.log("Clicked REFRESH button by text")
                        refresh_clicked = True
                    else:
                        # Try dropdown menu if standalone button not found
                        menu_buttons = driver.find_elements(By.CSS_SELECTOR, 
                            ".ant-dropdown-trigger, [data-test='header-actions-menu'], button.dropdown-toggle, .more-actions")
                        
                        if menu_buttons:
                            menu_buttons[0].click()
                            self.log("Clicked dropdown menu button")
                            time.sleep(3)  # Increased wait for dropdown to appear
                            
                            # Try multiple ways to find the refresh option
                            # 1. Try by data-test attribute
                            try:
                                refresh_options = driver.find_elements(By.CSS_SELECTOR, "[data-test='refresh-dashboard-menu-item']")
                                if refresh_options:
                                    refresh_options[0].click()
                                    self.log("Clicked refresh option by data-test attribute")
                                    refresh_clicked = True
                            except:
                                pass
                            
                            # 2. Try by exact text matching
                            if not refresh_clicked:
                                try:
                                    refresh_options = driver.find_elements(By.XPATH, "//li[text()='Refresh dashboard']")
                                    if refresh_options:
                                        refresh_options[0].click()
                                        self.log("Clicked 'Refresh dashboard' option by exact text match")
                                        refresh_clicked = True
                                except:
                                    pass
                            
                            # 3. Try by contains text matching
                            if not refresh_clicked:
                                try:
                                    refresh_options = driver.find_elements(By.XPATH, 
                                        "//li[contains(translate(text(), 'REFRESH', 'refresh'), 'refresh')]")
                                    if refresh_options:
                                        refresh_options[0].click()
                                        self.log("Clicked refresh option by contains text")
                                        refresh_clicked = True
                                except:
                                    pass
                            
                            # 4. Try by aria-label
                            if not refresh_clicked:
                                try:
                                    refresh_options = driver.find_elements(By.CSS_SELECTOR, "[aria-label*='refresh' i]")
                                    if refresh_options:
                                        refresh_options[0].click()
                                        self.log("Clicked refresh option by aria-label")
                                        refresh_clicked = True
                                except:
                                    pass
                            
                            # 5. Get all dropdown items and search for "refresh"
                            if not refresh_clicked:
                                try:
                                    dropdown_items = driver.find_elements(By.CSS_SELECTOR, 
                                        ".ant-dropdown-menu-item, .dropdown-item, li, a")
                                    
                                    for item in dropdown_items:
                                        try:
                                            item_text = item.text.strip()
                                            self.log(f"Dropdown item: '{item_text}'")
                                            if "refresh" in item_text.lower() or "refresh dashboard" in item_text.lower():
                                                item.click()
                                                self.log(f"Clicked '{item_text}' option from dropdown items search")
                                                refresh_clicked = True
                                                break
                                        except:
                                            pass
                                except:
                                    pass
                            
                            # If no refresh option was found, close dropdown and use F5
                            if not refresh_clicked:
                                try:
                                    driver.find_element(By.TAG_NAME, "body").click()
                                    self.log("Clicked body to close dropdown as no refresh option was found")
                                except:
                                    pass
                                
                                # Since we couldn't find the refresh option, use F5 key
                                self.log("Could not find refresh option in dropdown, using F5 key")
                                webdriver.ActionChains(driver).send_keys(Keys.F5).perform()
                                refresh_clicked = True
                        else:
                            # No dropdown menu button found, use F5 key
                            self.log("No dropdown menu button found, using F5 key")
                            webdriver.ActionChains(driver).send_keys(Keys.F5).perform()
                            refresh_clicked = True
                            
                except Exception as e:
                    self.log(f"Error clicking refresh: {str(e)}")
                    # Use F5 as a fallback
                    webdriver.ActionChains(driver).send_keys(Keys.F5).perform()
                    refresh_clicked = True
                
                # Wait for refresh to start
                time.sleep(2)
                
                # Wait for charts to reload and loading indicators to disappear
                try:
                    # Wait for loading indicators to appear (confirms refresh started)
                    refresh_started = False
                    for check in range(10):  # Check for 10 seconds
                        loading_indicators = driver.find_elements(By.CSS_SELECTOR, ".loading, .loading-spinner, .spinner")
                        if loading_indicators and any(ind.is_displayed() for ind in loading_indicators):
                            refresh_started = True
                            self.log("Refresh confirmed - loading indicators appeared")
                            break
                        time.sleep(1)
                    
                    # Now wait for loading to complete
                    if refresh_started:
                        # Wait for loading indicators to disappear
                        self.wait_for_loading_indicators_to_disappear(driver, 60)
                    else:
                        # If no loading indicators appeared, wait for charts to be ready
                        WebDriverWait(driver, 60).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".chart-container, .dashboard-component-chart"))
                        )
                    
                    # Additional check for chart content readiness
                    charts_ready = False
                    chart_check_start = time.time()
                    while (time.time() - chart_check_start) < 30 and not charts_ready:  # Max 30 seconds
                        charts_status = driver.execute_script("""
                            var charts = document.querySelectorAll('.chart-container, .dashboard-component-chart');
                            var readyCharts = 0;
                            
                            for (var i = 0; i < charts.length; i++) {
                                var chart = charts[i];
                                if (chart.innerHTML.length > 100 && 
                                    !chart.innerHTML.includes('loading') && 
                                    !chart.innerHTML.includes('Loading')) {
                                    readyCharts++;
                                }
                            }
                            
                            return {
                                total: charts.length,
                                ready: readyCharts,
                                percentage: charts.length > 0 ? (readyCharts / charts.length) * 100 : 100
                            };
                        """)
                        
                        if charts_status['percentage'] >= 80:  # 80% of charts ready
                            charts_ready = True
                            self.log(f"Charts refresh complete: {charts_status['ready']}/{charts_status['total']}")
                        else:
                            time.sleep(1)
                            
                except Exception as e:
                    self.log(f"Error waiting for refresh completion: {str(e)}")
                
                # *** RECORD END TIME HERE - AFTER REFRESH IS ACTUALLY COMPLETE ***
                end_time = datetime.datetime.now()
                end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                
                # Calculate refresh time
                refresh_time_seconds = (end_time - start_time).total_seconds()
                
                self.log(f"Dashboard {dashboard_id} ACTUALLY refreshed in {refresh_time_seconds:.2f} seconds")
                
                # Additional stability wait (not included in measurement)
                time.sleep(3)
                
                # Record this refresh
                results.append({
                    'Dashboard ID': dashboard_id,
                    'Refresh #': i+1,
                    'Start Time': start_time_str,
                    'End Time': end_time_str,
                    'Refresh Time (seconds)': refresh_time_seconds,
                    'Date': start_time.strftime("%Y-%m-%d"),
                    'Timestamp': start_time.strftime("%H:%M:%S"),
                    'Chart Count': chart_count
                })
                
                # Wait between refreshes
                if i < refresh_count - 1:
                    time.sleep(wait_between_refresh)
                        
        except Exception as e:
            self.log(f"ERROR in refresh testing for dashboard {dashboard_id}: {str(e)}")
            traceback.print_exc()
        
        return results
    
    def refresh_individual_chart(self, driver, chart_element, index):
        """
        Refresh an individual chart in a dashboard
        
        Args:
            driver: WebDriver instance
            chart_element: WebElement representing the chart
            index: Chart index for logging purposes
        
        Returns:
            dict: Data about the refresh time or None if failed
        """
        try:
            # Scroll to the chart to make it visible
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", chart_element)
            time.sleep(1)  # Wait for scroll to complete
            
            # Find the menu button (three dots) within this chart 
            # Based on your screenshot, it appears these are available on the charts
            menu_button = chart_element.find_element(By.CSS_SELECTOR, ".ant-dropdown-trigger, .more-options-button, button.more")
            
            # Click the menu button
            menu_button.click()
            self.log(f"Clicked menu button for chart #{index}")
            time.sleep(1)  # Wait for dropdown to appear
            
            # Record start time
            start_time = datetime.datetime.now()
            start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            
            # Look for refresh option in the menu
            refresh_option = driver.find_element(By.XPATH, 
                "//li[contains(@class, 'ant-dropdown-menu-item') and (contains(text(), 'Refresh') or contains(text(), 'refresh'))]")
            refresh_option.click()
            self.log(f"Clicked refresh option for chart #{index}")
            
            # Wait for the chart to refresh
            time.sleep(5)
            
            # Record end time
            end_time = datetime.datetime.now()
            end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            
            # Calculate refresh time
            refresh_time_seconds = (end_time - start_time).total_seconds()
            
            self.log(f"Chart #{index} refreshed in {refresh_time_seconds:.2f} seconds")
            
            return {
                'Chart Index': index,
                'Start Time': start_time_str,
                'End Time': end_time_str,
                'Refresh Time (seconds)': refresh_time_seconds,
                'Date': start_time.strftime("%Y-%m-%d"),
                'Timestamp': start_time.strftime("%H:%M:%S")
            }
        
        except Exception as e:
            self.log(f"ERROR refreshing chart #{index}: {str(e)}")
            
            # Try an alternative approach using browser F5 refresh
            try:
                self.log(f"Trying alternative method for chart #{index}")
                # Click on the chart to ensure it's active
                chart_element.click()
                
                # Record start time
                start_time = datetime.datetime.now()
                start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                
                # Use F5 key to refresh
                webdriver.ActionChains(driver).send_keys(Keys.F5).perform()
                self.log(f"Used F5 key to refresh chart #{index}")
                
                # Wait for refresh
                time.sleep(5)
                
                # Record end time
                end_time = datetime.datetime.now()
                end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                
                # Calculate refresh time
                refresh_time_seconds = (end_time - start_time).total_seconds()
                
                self.log(f"Chart #{index} refreshed in {refresh_time_seconds:.2f} seconds using F5 key")
                
                return {
                    'Chart Index': index,
                    'Start Time': start_time_str,
                    'End Time': end_time_str,
                    'Refresh Time (seconds)': refresh_time_seconds,
                    'Refresh Method': 'F5 Key',
                    'Date': start_time.strftime("%Y-%m-%d"),
                    'Timestamp': start_time.strftime("%H:%M:%S")
                }
                
            except Exception as fallback_error:
                self.log(f"ERROR with fallback refresh method: {str(fallback_error)}")
                return None
            
    def measure_chart_refresh_times(self, driver, dashboard_id, chart_refresh_iterations=3, wait_between_refresh=2):
        """
        Measure the refresh time for each individual chart in a dashboard
        
        Args:
            driver: WebDriver instance
            dashboard_id: ID of the dashboard containing charts
            chart_refresh_iterations: Number of times to refresh each chart
            wait_between_refresh: Time to wait between refreshes in seconds
            
        Returns:
            list: List of measurements for each chart refresh
        """
        all_results = []
        
        try:
            # First navigate to the dashboard
            dashboard_url = f"{self.base_url}/superset/dashboard/{dashboard_id}/"
            self.log(f"Navigating to dashboard for chart refresh test: {dashboard_url}")
            driver.get(dashboard_url)
            
            # Wait for dashboard to fully load
            self.log(f"Waiting for dashboard {dashboard_id} to load...")
            time.sleep(5)
            
            # Wait for dashboard elements
            try:
                WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".dashboard-grid, .dashboard, .chart-container, .dashboard-component-chart"))
                )
                self.log("Dashboard element found")
            except TimeoutException:
                self.log("WARNING: Could not detect dashboard elements, continuing anyway")
            
            # Additional wait for charts to render
            time.sleep(5)
            
            # Find all chart elements
            charts = self.find_chart_elements(driver)
            total_charts = len(charts)
            
            if total_charts == 0:
                self.log(f"No charts found in dashboard {dashboard_id}")
                return all_results
            
            self.log(f"Found {total_charts} charts in dashboard {dashboard_id}")
            
            # Refresh each chart the specified number of times
            for i, chart in enumerate(charts):
                chart_index = i + 1
                self.log(f"Starting refresh test for chart #{chart_index} of {total_charts}")
                
                # Perform multiple refresh iterations for this chart
                for iteration in range(chart_refresh_iterations):
                    self.log(f"Chart #{chart_index}: Refresh iteration {iteration+1}/{chart_refresh_iterations}")
                    
                    # Measure refresh time for this chart
                    result = self.refresh_individual_chart(driver, chart, chart_index)
                    
                    if result:
                        # Add additional info to the result
                        result['Dashboard ID'] = dashboard_id
                        result['Total Charts'] = total_charts
                        result['Iteration'] = iteration + 1
                        all_results.append(result)
                    
                    # Wait between refreshes
                    if iteration < chart_refresh_iterations - 1:
                        time.sleep(wait_between_refresh)
                
                # Wait a bit before moving to the next chart
                time.sleep(1)
            
        except Exception as e:
            self.log(f"ERROR in chart refresh test for dashboard {dashboard_id}: {str(e)}")
            traceback.print_exc()
        
        self.log(f"Completed chart refresh test for dashboard {dashboard_id}: {len(all_results)} measurements collected")
        return all_results
    
    def save_results_to_excel(self, all_scenario_results):
        """
        Save all test results to an Excel file with multiple sheets
        Enhanced with debug logging to identify data loss issues
        """
        self.log(f"Saving results to Excel file: {self.output_file}")
        
        # Debug: Log what we received
        for scenario, results in all_scenario_results.items():
            self.log(f"DEBUG: Scenario '{scenario}' has {len(results) if results else 0} results")
            if results:
                # Count results per dashboard
                dashboard_counts = {}
                for result in results:
                    dashboard_id = result.get('Dashboard ID', 'Unknown')
                    dashboard_counts[dashboard_id] = dashboard_counts.get(dashboard_id, 0) + 1
                
                self.log(f"DEBUG: Dashboard breakdown for {scenario}:")
                for dashboard, count in dashboard_counts.items():
                    self.log(f"  {dashboard}: {count} measurements")
        
        # Check if we have any results to save
        has_results = False
        total_results = 0
        for results in all_scenario_results.values():
            if results and len(results) > 0:
                has_results = True
                total_results += len(results)
        
        self.log(f"DEBUG: Total results across all scenarios: {total_results}")
        
        if not has_results:
            self.log("No results collected, skipping Excel file creation")
            return
            
        try:
            # Create a writer for Excel file
            with pd.ExcelWriter(self.output_file, engine='openpyxl') as writer:
                # Create a summary sheet
                summary_data = []
                
                # Process each scenario's results
                for scenario, results in all_scenario_results.items():
                    if not results:
                        self.log(f"DEBUG: Skipping scenario '{scenario}' - no results")
                        continue
                        
                    self.log(f"DEBUG: Processing scenario '{scenario}' with {len(results)} results")
                    
                    # Convert results to DataFrame
                    df = pd.DataFrame(results)
                    self.log(f"DEBUG: Created DataFrame with shape {df.shape}")
                    self.log(f"DEBUG: DataFrame columns: {list(df.columns)}")
                    
                    # Write detailed results to a sheet
                    sheet_name = f"{scenario} Details"
                    self.log(f"DEBUG: Writing to sheet '{sheet_name}'")
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # For Scenario 5 (Individual Chart Refresh), create chart-specific summary
                    if scenario == 'Scenario 5' and 'Chart Index' in df.columns:
                        self.log("DEBUG: Creating chart-specific summary for Scenario 5")
                        # Calculate summary statistics per chart
                        chart_summaries = []
                        for chart_idx, chart_data in df.groupby('Chart Index'):
                            summary = {
                                'Dashboard ID': chart_data['Dashboard ID'].iloc[0],
                                'Chart Index': chart_idx,
                                'Number of Refreshes': len(chart_data),
                                'Average Refresh Time (s)': chart_data['Refresh Time (seconds)'].mean(),
                                'Min Refresh Time (s)': chart_data['Refresh Time (seconds)'].min(),
                                'Max Refresh Time (s)': chart_data['Refresh Time (seconds)'].max(),
                                'Std Dev Refresh Time (s)': chart_data['Refresh Time (seconds)'].std()
                            }
                            chart_summaries.append(summary)
                        
                        # Create a chart summary sheet for this scenario
                        if chart_summaries:
                            chart_summary_df = pd.DataFrame(chart_summaries)
                            chart_sheet_name = f"{scenario} Chart Summary"
                            self.log(f"DEBUG: Writing chart summary to sheet '{chart_sheet_name}'")
                            chart_summary_df.to_excel(writer, sheet_name=chart_sheet_name, index=False)
                    
                    # Calculate summary statistics per dashboard
                    dashboard_summaries = []
                    group_by_col = 'Dashboard ID'
                    if group_by_col in df.columns:
                        self.log(f"DEBUG: Grouping by '{group_by_col}' for dashboard summaries")
                        dashboard_groups = df.groupby(group_by_col)
                        self.log(f"DEBUG: Found {len(dashboard_groups)} unique dashboards")
                        
                        for dashboard_id, dashboard_data in dashboard_groups:
                            self.log(f"DEBUG: Processing dashboard '{dashboard_id}' with {len(dashboard_data)} measurements")
                            
                            # Determine which time column to use based on scenario
                            if 'Refresh Time (seconds)' in df.columns:
                                time_column = 'Refresh Time (seconds)'
                            else:
                                time_column = 'Load Time (seconds)'
                            
                            self.log(f"DEBUG: Using time column '{time_column}' for dashboard '{dashboard_id}'")
                            
                            summary = {
                                'Scenario': scenario,
                                'Dashboard ID': dashboard_id,
                                'Number of Measurements': len(dashboard_data),
                                f'Average {time_column}': dashboard_data[time_column].mean(),
                                f'Min {time_column}': dashboard_data[time_column].min(),
                                f'Max {time_column}': dashboard_data[time_column].max(),
                                f'Std Dev {time_column}': dashboard_data[time_column].std()
                            }
                            
                            # Add chart count if available
                            if 'Chart Count' in dashboard_data.columns:
                                # Use most frequent chart count in case there are variations
                                chart_count = dashboard_data['Chart Count'].mode()[0]
                                summary['Chart Count'] = chart_count
                            elif 'Total Charts' in dashboard_data.columns:
                                # For Scenario 5, use the Total Charts column
                                chart_count = dashboard_data['Total Charts'].iloc[0]
                                summary['Chart Count'] = chart_count
                            
                            dashboard_summaries.append(summary)
                            summary_data.append(summary)
                            
                            self.log(f"DEBUG: Added summary for dashboard '{dashboard_id}': {len(dashboard_data)} measurements, avg time: {summary[f'Average {time_column}']:.2f}s")
                        
                        # Create a summary sheet for this scenario
                        if dashboard_summaries:
                            summary_df = pd.DataFrame(dashboard_summaries)
                            summary_sheet_name = f"{scenario} Summary"
                            self.log(f"DEBUG: Writing scenario summary to sheet '{summary_sheet_name}' with {len(dashboard_summaries)} rows")
                            summary_df.to_excel(writer, sheet_name=summary_sheet_name, index=False)
                    else:
                        self.log(f"DEBUG: No '{group_by_col}' column found in DataFrame for scenario '{scenario}'")
                
                # Create an overall summary sheet
                if summary_data:
                    overall_summary_df = pd.DataFrame(summary_data)
                    self.log(f"DEBUG: Writing overall summary with {len(summary_data)} rows")
                    overall_summary_df.to_excel(writer, sheet_name="Overall Summary", index=False)
                else:
                    self.log("DEBUG: No summary data to write to overall summary sheet")
            
            self.log(f"Results successfully saved to {self.output_file}")
            
        except Exception as e:
            self.log(f"ERROR saving results to Excel: {str(e)}")
            import traceback
            self.log(f"DEBUG: Full traceback:\n{traceback.format_exc()}")
            traceback.print_exc()

#------------------------------------------------------------------
    def wait_for_dashboard_health_load(self, driver, timeout=30):
            """Simplified loading detection specifically for health checks"""
            try:
                # Simple wait for dashboard elements
                WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 
                        ".dashboard-grid, .dashboard, .chart-container, .dashboard-component-chart"))
                )
                
                # Simple time-based wait for stability
                time.sleep(5)
                
                # Basic check if page is loaded
                ready_state = driver.execute_script("return document.readyState")
                if ready_state == "complete":
                    self.log("Dashboard loaded for health check")
                    return True
                else:
                    self.log("Dashboard still loading for health check")
                    return False
                    
            except Exception as e:
                self.log(f"Error waiting for dashboard health load: {str(e)}")
                return False

    def count_dashboard_charts_simple(self, driver):
        """Simplified chart counting specifically for health checks"""
        try:
            # Wait a moment for charts to appear
            time.sleep(2)
            
            # Try the most common selectors first
            chart_count = 0
            
            # Method 1: Try chart containers
            charts = driver.find_elements(By.CSS_SELECTOR, ".chart-container")
            if charts:
                chart_count = len(charts)
                self.log(f"Found {chart_count} charts using .chart-container")
                return chart_count
            
            # Method 2: Try dashboard component charts
            charts = driver.find_elements(By.CSS_SELECTOR, ".dashboard-component-chart")
            if charts:
                chart_count = len(charts)
                self.log(f"Found {chart_count} charts using .dashboard-component-chart")
                return chart_count
            
            # Method 3: Try data-test attribute
            charts = driver.find_elements(By.CSS_SELECTOR, "[data-test='dashboard-component-chart']")
            if charts:
                chart_count = len(charts)
                self.log(f"Found {chart_count} charts using data-test attribute")
                return chart_count
            
            # Method 4: Use JavaScript as last resort
            try:
                chart_count = driver.execute_script("""
                    var containers = document.querySelectorAll('.chart-container, .dashboard-component-chart, .slice_container');
                    return containers.length;
                """)
                self.log(f"Found {chart_count} charts using JavaScript")
                return chart_count
            except:
                pass
            
            self.log("No charts found with any method")
            return 0
            
        except Exception as e:
            self.log(f"ERROR counting charts for health check: {str(e)}")
            return 0

    def measure_dashboard_health_load(self, driver, dashboard_id):
        """Simplified dashboard load measurement for health checks only"""
        try:
            # CRITICAL: Use correct URL pattern for your instance
            dashboard_url = f"{self.base_url}/superset/dashboard/{dashboard_id}/"
            self.log(f"Health check - navigating to: {dashboard_url}")
            
            start_time = time.time()
            driver.get(dashboard_url)
            
            # Use simplified loading detection
            load_success = self.wait_for_dashboard_health_load(driver, 30)
            
            if not load_success:
                return {
                    'Dashboard ID': dashboard_id,
                    'Status': 'Critical',
                    'Charts Loaded': 0,
                    'Total Charts': 0,
                    'Load Time (s)': 0,
                    'Issues': 'Dashboard failed to load within timeout'
                }
            
            load_time = time.time() - start_time
            
            # Count charts with fallback
            chart_count = self.count_dashboard_charts_simple(driver)
            
            # Simple health determination
            if chart_count == 0:
                status = 'Critical'
                issues = 'No charts found'
            elif load_time < 10:
                status = 'Healthy'
                issues = 'None'
            elif load_time < 20:
                status = 'Warning' 
                issues = f'Slow load time: {load_time:.1f}s'
            else:
                status = 'Critical'
                issues = f'Very slow load time: {load_time:.1f}s'
            
            self.log(f"Health check result for {dashboard_id}: {status} ({chart_count} charts, {load_time:.1f}s)")
            
            return {
                'Dashboard ID': dashboard_id,
                'Status': status,
                'Charts Loaded': chart_count,
                'Total Charts': chart_count,
                'Load Time (s)': round(load_time, 2),
                'Issues': issues
            }
            
        except Exception as e:
            self.log(f"ERROR in health check for dashboard {dashboard_id}: {str(e)}")
            return {
                'Dashboard ID': dashboard_id,
                'Status': 'Critical',
                'Charts Loaded': 0,
                'Total Charts': 0,
                'Load Time (s)': 0,
                'Issues': f'Health check failed: {str(e)}'
            }

    def run_health_check_for_dashboard(self, driver, dashboard_id):
        """Main health check method that ui_connector should call"""
        return self.measure_dashboard_health_load(driver, dashboard_id)

