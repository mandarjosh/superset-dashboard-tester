#!/usr/bin/env python3
"""
Superset Dashboard Tester - PyQt5 UI
"""
import sys
import os
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                           QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                           QCheckBox, QPushButton, QTableWidget, QFileDialog,
                           QMessageBox, QGroupBox, QFormLayout, QProgressBar, 
                           QTableWidgetItem, QHeaderView, QSpinBox, QScrollArea,
                           QGridLayout, QSizePolicy)  # Added QSizePolicy here
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt

import requests
import time
from selenium.webdriver.common.by import By
import requests

# Import connector to existing code
from ui_connector import UIConnector

class SupersetTester(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Superset Dashboard Tester")
        self.setMinimumSize(800, 600)
        
        # Initialize dashboard_ids before any UI code that uses it
        self.dashboard_ids = self.fetch_dashboard_data()
        self.dashboard_checkboxes = []

        # Initialize the connector
        self.connector = UIConnector()
        
        # Connect signals from connector
        self.connector.progress_updated.connect(self.update_progress)
        self.connector.test_completed.connect(self.route_test_completed)
        self.connector.test_error.connect(self.handle_test_error)
        
        # Set application style
        self.apply_stylesheet()
        
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Add logo and title
        header_layout = QHBoxLayout()
        
        # Logo
        # Logo
        logo = QLabel()
        try:
            pixmap = QPixmap("resources/Woodfrog Logo - wordmark.png")
            if pixmap.isNull():
                raise Exception("Logo couldn't be loaded")
            logo.setPixmap(pixmap.scaled(200, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            #logo.setStyleSheet("background-color: white; padding: 5px; border-radius: 4px;")
        except Exception as e:
            print(f"Error loading logo: {str(e)}")
            # Fallback if logo is not found
            logo.setText("WOODFROG")
            logo.setStyleSheet("font-size: 18px; font-weight: bold; color: #3498db; padding: 5px;")
        
        header_layout.addWidget(logo)
        
        # Title
        #title = QLabel("Dashboard Performance Testing Tool")
        #title.setFont(QFont("Arial", 18, QFont.Bold))
        #title.setStyleSheet("color: #2c3e50;")
        #header_layout.addWidget(title)
        #header_layout.addStretch()

        # Superset Logo (right side)
        superset_logo = QLabel()
        try:
            superset_pixmap = QPixmap("resources/superset.png")
            if superset_pixmap.isNull():
                raise Exception("Superset logo couldn't be loaded")
            # Scale to match the location in the screenshot (larger size, right aligned)
            superset_logo.setPixmap(superset_pixmap.scaled(200, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            # Right-align the logo and add padding
            superset_logo.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            superset_logo.setStyleSheet("padding: 5px; margin-right: 10px;")
        except Exception as e:
            print(f"Error loading superset logo: {str(e)}")
            # Fallback if superset logo is not found
            #superset_logo.setText("SUPERSET")
            #superset_logo.setStyleSheet("font-size: 16px; font-weight: bold; color: #ff4500; padding: 5px;")
        
        header_layout.addWidget(superset_logo)
        
        main_layout.addLayout(header_layout)
        
        # Horizontal separator
        separator = QLabel()
        separator.setFixedHeight(2)
        separator.setStyleSheet("background-color: #3498db;")
        main_layout.addWidget(separator)
        main_layout.addSpacing(10)
        
        # Create tabs
        self.tabs = QTabWidget()
        
        # Create tab widgets
        self.superset_details_tab = self.create_superset_details_tab()
        self.performance_report_tab = self.create_performance_report_tab()
        self.dashboard_health_tab = self.create_dashboard_health_tab()
        
        # Add tabs
        self.tabs.addTab(self.superset_details_tab, "Superset Details")
        self.tabs.addTab(self.performance_report_tab, "Performance Report")
        self.tabs.addTab(self.dashboard_health_tab, "Health of Dashboards")
        
        main_layout.addWidget(self.tabs)
        
        # Status bar
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)
        
    def apply_stylesheet(self):
        """Apply custom styling to the application"""
        # Set global stylesheet
        self.setStyleSheet("""
            /* Make all text black by default */
            * { color: black; }
            
            QMainWindow, QWidget { background-color: #f5f5f5; }
            
            /* Override specific elements that need different colors */
            QPushButton { 
                background-color: #3498db; 
                color: white; 
                border: none; 
                padding: 8px 16px; 
                border-radius: 4px; 
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:disabled { background-color: #bdc3c7; }
            
            QLineEdit { 
                padding: 8px; 
                border: 1px solid #bbb; 
                border-radius: 4px; 
                background-color: white; 
                color: black;
            }
            
            QSpinBox { 
                padding: 8px; 
                border: 1px solid #bbb; 
                border-radius: 4px; 
                background-color: white; 
                color: black;
                padding-right: 25px; /* Make room for buttons on right */
            }

            QSpinBox::up-button {
                background-color: #3498db;
                border: none;
                subcontrol-origin: margin;
                subcontrol-position: right top;
                width: 25px;
                height: 50%;
                border-top-right-radius: 4px;
            }

            QSpinBox::down-button {
                background-color: #3498db;
                border: none;
                subcontrol-origin: margin;
                subcontrol-position: right bottom;
                width: 25px;
                height: 50%;
                border-bottom-right-radius: 4px;
            }

            QSpinBox::up-arrow, QSpinBox::down-arrow {
                width: 8px;
                height: 8px;
                color: white;
            }

            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #2980b9;
            }

            QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {
                background-color: #1f6aa8;
            }
            
            /* Slider styling */
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: #f0f0f0;
                height: 10px;
                border-radius: 4px;
            }
            
            QSlider::handle:horizontal {
                background: #3498db;
                border: 1px solid #3498db;
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            
            QSlider::handle:horizontal:hover {
                background: #2980b9;
            }
            
            QGroupBox { 
                font-weight: bold; 
                border: 1px solid #ddd; 
                border-radius: 4px; 
                margin-top: 12px; 
                padding-top: 20px; 
                color: black;
            }
            
            QTableWidget { 
                border: 1px solid #ddd; 
                border-radius: 4px; 
                alternate-background-color: #f9f9f9; 
                color: black;
            }
            
            QHeaderView::section { 
                background-color: #2c3e50; 
                color: white; 
                padding: 6px; 
            }
            
            QTabBar::tab { 
                background-color: #e0e0e0; 
                color: black; 
                padding: 8px 16px;
            }
            
            QTabBar::tab:selected { 
                background-color: #3498db; 
                color: white; 
            }
            
            QCheckBox, QLabel, QRadioButton { 
                color: black; 
            }
            
            QStatusBar { 
                color: black; 
            }
            
            /* For scroll areas */
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            
            /* For scroll bars */
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background: #3498db;
                min-height: 20px;
                border-radius: 5px;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar:horizontal {
                border: none;
                background: #f0f0f0;
                height: 10px;
                margin: 0px;
            }
            
            QScrollBar::handle:horizontal {
                background: #3498db;
                min-width: 20px;
                border-radius: 5px;
            }
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            
            /* For Progress Bar */
            QProgressBar {
                border: 1px solid #bbb;
                border-radius: 4px;
                text-align: center;
                background-color: #f0f0f0;
                color: black;
            }
            
            QProgressBar::chunk {
                background-color: #3498db;
                width: 10px;
                margin: 0.5px;
            }
        """)
        
    def create_superset_details_tab(self):
        """Create the Superset Details tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Connection details group
        group = QGroupBox("Superset Connection Details")
        form = QFormLayout()
        
        self.url_input = QLineEdit("https://reporting.tkosuat.co.uk")
        self.username_input = QLineEdit("superset_consultant@tkos.co.uk")
        self.password_input = QLineEdit("spgjY9jXXbxa66qKs4ou")
        self.password_input.setEchoMode(QLineEdit.Password)
        
        # Add manual login checkbox
        self.manual_login_checkbox = QCheckBox("Enable manual login (for complex login pages)")
        self.manual_login_checkbox.setChecked(False)
        
        form.addRow("URL:", self.url_input)
        form.addRow("Username:", self.username_input)
        form.addRow("Password:", self.password_input)
        form.addRow("", self.manual_login_checkbox)
        
        group.setLayout(form)
        layout.addWidget(group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Settings")
        test_btn = QPushButton("Test Connection")
        
        # Add a new button for completing manual login
        self.complete_login_btn = QPushButton("I've Completed Login")
        self.complete_login_btn.setEnabled(False)  # Disabled by default
        
        save_btn.clicked.connect(self.save_settings)
        test_btn.clicked.connect(self.test_connection)
        self.complete_login_btn.clicked.connect(self.manual_login_completed)
        
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(test_btn)
        btn_layout.addWidget(self.complete_login_btn)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        # Help text
        help_text = QLabel("Configure your Superset connection details above. For complex login pages with additional steps, enable manual login.")
        help_text.setStyleSheet("color: #7f8c8d; font-style: italic;")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)
        
        tab.setLayout(layout)
        return tab

    def fetch_dashboard_data(self):
        """Fetch dashboard IDs and names from Superset API"""
        try:
            # Check if URL, username and password are set
            url = self.url_input.text()
            username = self.username_input.text()
            password = self.password_input.text()
            manual_login = self.manual_login_checkbox.isChecked()
            
            if not url:
                # If URL isn't set yet, return default list
                return [
                    {"id": "10", "name": "Loading dashboards..."}
                ]
            
            # If using manual login and we have a browser session, try to get dashboards directly
            if manual_login and self.connector.tester and self.connector.tester.persistent_driver:
                try:
                    self.status_label.setText("Fetching dashboards using browser session...")
                    driver = self.connector.tester.persistent_driver
                    
                    # Navigate to the dashboards page
                    driver.get(f"{url}/dashboard/list/")
                    time.sleep(3)  # Wait for page to load
                    
                    # Try to find dashboard elements
                    dashboard_elements = driver.find_elements(By.CSS_SELECTOR, ".dashboard-list-view table tbody tr")
                    
                    if dashboard_elements:
                        dashboards = []
                        for elem in dashboard_elements:
                            try:
                                # Try to extract ID and name from the element
                                link = elem.find_element(By.CSS_SELECTOR, "a")
                                href = link.get_attribute("href")
                                
                                # Extract ID from href
                                dashboard_id = href.split("/")[-1].strip()
                                if dashboard_id.isdigit():
                                    dashboards.append({
                                        "id": dashboard_id,
                                        "name": link.text.strip()
                                    })
                            except Exception as e:
                                print(f"Error extracting dashboard: {e}")
                        
                        if dashboards:
                            self.status_label.setText(f"Found {len(dashboards)} dashboards using browser session")
                            return dashboards
                    
                    # If we couldn't get dashboards from the list page,
                    # try the API using the browser's cookies
                    cookies = driver.get_cookies()
                    
                    # Create a requests session with these cookies
                    import requests
                    session = requests.Session()
                    for cookie in cookies:
                        session.cookies.set(cookie['name'], cookie['value'])
                    
                    # Try API call with the authenticated session
                    api_url = f"{url}/api/v1/dashboard/"
                    response = session.get(api_url)
                    
                    if response.status_code == 200:
                        # Process response as in the original code
                        dashboard_data = response.json()
                        formatted_dashboards = []
                        
                        if "result" in dashboard_data and isinstance(dashboard_data["result"], list):
                            for dashboard in dashboard_data["result"]:
                                if "id" in dashboard and "dashboard_title" in dashboard:
                                    formatted_dashboards.append({
                                        "id": str(dashboard["id"]),
                                        "name": dashboard["dashboard_title"]
                                    })
                        
                        if formatted_dashboards:
                            self.status_label.setText(f"Successfully loaded {len(formatted_dashboards)} dashboards using browser cookies")
                            return formatted_dashboards
                
                except Exception as browser_err:
                    print(f"Error fetching dashboards with browser: {browser_err}")
                    # Fall back to API approach
            
            # Build API URL for standard API approach
            api_url = f"{url}/api/v1/dashboard/"
            
            # Try basic auth first
            response = requests.get(api_url, auth=(username, password))
            
            # If that doesn't work, try token auth
            if response.status_code == 401:
                # Get authentication token 
                auth_url = f"{url}/api/v1/security/login"
                auth_payload = {
                    "password": password,
                    "provider": "db", 
                    "refresh": True,
                    "username": username
                }
                
                headers = {"Content-Type": "application/json"}
                
                # Try the token auth
                auth_response = requests.post(auth_url, json=auth_payload, headers=headers)
                
                # If this also fails, fall back to default dashboard list
                if auth_response.status_code != 200:
                    if hasattr(self, 'status_label'):
                        self.status_label.setText(f"Using default dashboard list (API auth failed)")
                    return [
                        {"id": "10", "name": "Example Dashboard"}
                    ]
                    
                # Extract access token
                access_token = auth_response.json().get("access_token")
                
                if not access_token:
                    if hasattr(self, 'status_label'):
                        self.status_label.setText("Failed to get authentication token")
                    return [
                        {"id": "10", "name": "Example Dashboard"}
                    ]
                    
                # Now fetch dashboards with the token
                dashboard_headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
                
                # Get all dashboards
                response = requests.get(api_url, headers=dashboard_headers)
            
            # Process response
            if response.status_code == 200:
                # Parse the response
                dashboard_data = response.json()
                
                # Extract the dashboard list from the response
                formatted_dashboards = []
                
                # Check if the response has the 'result' key containing dashboard objects
                if "result" in dashboard_data and isinstance(dashboard_data["result"], list):
                    for dashboard in dashboard_data["result"]:
                        # Extract just the id and dashboard_title
                        if "id" in dashboard and "dashboard_title" in dashboard:
                            formatted_dashboards.append({
                                "id": str(dashboard["id"]),
                                "name": dashboard["dashboard_title"]
                            })
                
                # If we didn't find any dashboards in the expected format, check for other possibilities
                if not formatted_dashboards and "ids" in dashboard_data:
                    # If we have dashboard IDs but not full objects, try to match with dashboard_title if available
                    for dashboard_id in dashboard_data["ids"]:
                        # Since we don't have titles in this case, use ID as name
                        formatted_dashboards.append({
                            "id": str(dashboard_id),
                            "name": f"Dashboard {dashboard_id}"
                        })
                
                if formatted_dashboards:
                    if hasattr(self, 'status_label'):
                        self.status_label.setText(f"Successfully loaded {len(formatted_dashboards)} dashboards")
                    return formatted_dashboards
                else:
                    # No dashboards found in the expected format
                    if hasattr(self, 'status_label'):
                        self.status_label.setText("No dashboards found in API response")
                    return [
                        {"id": "10", "name": "Example Dashboard"}
                    ]
            else:
                # Fall back to default dashboards if API call fails
                if hasattr(self, 'status_label'):
                    self.status_label.setText(f"Using default dashboard list (API returned {response.status_code})")
                return [
                    {"id": "10", "name": "Example Dashboard"}
                ]
            
        except Exception as e:
            print(f"Error fetching dashboards: {e}")
            # Provide a fallback set of dashboards to ensure the UI works
            if hasattr(self, 'status_label'):
                self.status_label.setText(f"Using default dashboard list (Error: {str(e)})")
            return [
                {"id": "10", "name": "Example Dashboard"}
            ]

    def create_dashboard_selection_group(self):
        """Reusable dashboard selection group for both tabs."""
        dashboard_group = QGroupBox("Select Dashboard IDs:")
        dashboard_layout = QVBoxLayout()
        dashboard_layout.setSpacing(12)
        dashboard_layout.setContentsMargins(15, 12, 15, 15)

        # Button row
        button_row_layout = QHBoxLayout()
        button_row_layout.setSpacing(15)
        button_style = """
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border: 2px solid {border_color};
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 8px 12px;
                min-width: 80px;
                min-height: 35px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
                border: 2px solid {hover_border};
                transform: translateY(-1px);
            }}
            QPushButton:pressed {{
                background-color: {pressed_color};
                transform: translateY(1px);
            }}
        """
        select_all_btn = QPushButton("✓ Select All")
        select_all_btn.setStyleSheet(button_style.format(
            bg_color="#27ae60", border_color="#229954",
            hover_color="#229954", hover_border="#1e8449",
            pressed_color="#1e8449"
        ))
        deselect_all_btn = QPushButton("✗ Clear All")
        deselect_all_btn.setStyleSheet(button_style.format(
            bg_color="#e74c3c", border_color="#c0392b",
            hover_color="#c0392b", hover_border="#a93226",
            pressed_color="#a93226"
        ))
        select_first_3_btn = QPushButton("⚡ First 3")
        select_first_3_btn.setStyleSheet(button_style.format(
            bg_color="#f39c12", border_color="#e67e22",
            hover_color="#e67e22", hover_border="#d68910",
            pressed_color="#d68910"
        ))
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet(button_style.format(
            bg_color="#3498db", border_color="#2980b9",
            hover_color="#2980b9", hover_border="#1f6aa8",
            pressed_color="#1f6aa8"
        ))

        # --- Fix: Connect buttons to local checkboxes, not global ---
        # We'll return the checkboxes list for each group, and connect the buttons to those.

        # Dashboard checkboxes
        dashboard_scroll = QScrollArea()
        dashboard_scroll.setWidgetResizable(True)
        dashboard_scroll.setFixedHeight(160)
        dashboard_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        dashboard_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        dashboard_scroll.setStyleSheet("""
            QScrollArea {
                border: 2px solid #ddd;
                border-radius: 6px;
                background-color: #fafafa;
            }
            QScrollBar:vertical {
                border: none;
                background: #ecf0f1;
                width: 12px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: #3498db;
                min-height: 25px;
                border-radius: 5px;
                margin: 1px;
            }
            QScrollBar::handle:vertical:hover {
                background: #2980b9;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        dashboard_content = QWidget()
        dashboard_grid = QGridLayout(dashboard_content)
        dashboard_grid.setSpacing(8)
        dashboard_grid.setContentsMargins(12, 12, 12, 12)

        # Create a new list of checkboxes for this group
        checkboxes = []
        col_count = 2
        for i, dashboard in enumerate(self.dashboard_ids):
            row = i // col_count
            col = i % col_count
            dashboard_id = dashboard['id']
            dashboard_name = dashboard['name']
            if len(dashboard_name) > 32:
                display_text = f"{dashboard_id} - {dashboard_name[:29]}..."
            else:
                display_text = f"{dashboard_id} - {dashboard_name}"
            checkbox = QCheckBox(display_text)
            checkbox.setChecked(False)
            checkbox.setMinimumHeight(24)
            checkbox.setStyleSheet("""
                QCheckBox {
                    font-size: 11px;
                    font-weight: bold;
                    color: #2c3e50;
                    padding: 4px;
                    spacing: 10px;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    border-radius: 4px;
                    border: 2px solid #bdc3c7;
                    background-color: white;
                }
                QCheckBox::indicator:hover {
                    border: 2px solid #3498db;
                    background-color: #ecf0f1;
                }
                QCheckBox::indicator:checked {
                    border: 2px solid #27ae60;
                    background-color: #27ae60;
                }
                QCheckBox:hover {
                    background-color: #f8f9fa;
                    border-radius: 4px;
                    padding: 2px;
                }
            """)
            if len(f"{dashboard_id} - {dashboard_name}") > 32:
                checkbox.setToolTip(f"{dashboard_id} - {dashboard_name}")
            checkboxes.append(checkbox)
            dashboard_grid.addWidget(checkbox, row, col)

        dashboard_content.setLayout(dashboard_grid)
        dashboard_scroll.setWidget(dashboard_content)
        dashboard_layout.addWidget(dashboard_scroll)
        dashboard_group.setLayout(dashboard_layout)

        # Button connections use local checkboxes
        select_all_btn.clicked.connect(lambda: [cb.setChecked(True) for cb in checkboxes])
        deselect_all_btn.clicked.connect(lambda: [cb.setChecked(False) for cb in checkboxes])
        select_first_3_btn.clicked.connect(lambda: [cb.setChecked(i < 3) for i, cb in enumerate(checkboxes)])
        refresh_btn.clicked.connect(self.refresh_dashboard_list)

        button_row_layout.addWidget(select_all_btn)
        button_row_layout.addWidget(deselect_all_btn)
        button_row_layout.addWidget(select_first_3_btn)
        button_row_layout.addStretch()
        button_row_layout.addWidget(refresh_btn)
        dashboard_layout.insertLayout(0, button_row_layout)

        # Return both the group and the checkboxes for use in the tab
        return dashboard_group, checkboxes

    def create_performance_report_tab(self):
        """Create the Performance Report tab with independent dashboard selection."""
        tab = QWidget()
        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(25, 20, 25, 25)
        # ===== HEADER SECTION WITH CENTERED TITLE =====
        header_layout = QVBoxLayout()
        header_layout.setSpacing(10)
        title_layout = QHBoxLayout()
        title_layout.addStretch()
        main_title = QLabel("Dashboard Performance Testing Tool")
        main_title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 15px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                            stop:0 #ecf0f1, stop:0.5 #ffffff, stop:1 #ecf0f1);
                border: 2px solid #3498db;
                border-radius: 10px;
                margin: 5px;
            }
        """)
        main_title.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(main_title)
        title_layout.addStretch()
        header_layout.addLayout(title_layout)
        main_layout.addLayout(header_layout)
        # Use local dashboard selection group
        dashboard_group, self.performance_dashboard_checkboxes = self.create_dashboard_selection_group()
        main_layout.addWidget(dashboard_group)
        
        # Test configuration group
        config_group = QGroupBox("Test Configuration")
        config_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                border: 3px solid #3498db;
                border-radius: 12px;
                margin-top: 15px;
                padding-top: 25px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                background-color: #f8f9fa;
            }
        """)
        config_layout = QVBoxLayout()
        config_layout.setSpacing(20)
        config_layout.addWidget(dashboard_group)
        
        # ===== SCENARIOS SECTION =====
        scenario_group = QGroupBox("Select Scenarios to Run:")
        scenario_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #34495e;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                background-color: #ffffff;
            }
        """)
        scenario_layout = QVBoxLayout()
        scenario_layout.setSpacing(12)
        scenario_layout.setContentsMargins(15, 12, 15, 15)
        
        self.scenario_checkboxes = []
        self.scenario_iterations = []
        
        # UI label change only: Scenario 2 -> Scenario 1, Scenario 3 -> Scenario 2, Scenario 4 -> Scenario 3
        scenario_descriptions = [
            ("Scenario 1", "Sequential dashboards"),   # UI label for Scenario 2
            ("Scenario 2", "Parallel dashboards"),     # UI label for Scenario 3
            ("Scenario 3", "Dashboard refresh")        # UI label for Scenario 4
        ]
        
        for i, (scenario_name, description) in enumerate(scenario_descriptions):
            scenario_container = QWidget()
            scenario_container.setFixedHeight(40)
            scenario_row = QHBoxLayout(scenario_container)
            scenario_row.setSpacing(15)
            scenario_row.setContentsMargins(5, 5, 5, 5)
            
            # Scenario checkbox with simple styling
            checkbox = QCheckBox(scenario_name)
            checkbox.setFixedWidth(110)
            checkbox.setChecked(False)
            checkbox.setStyleSheet("""
                QCheckBox {
                    font-size: 12px;
                    font-weight: bold;
                    color: #2c3e50;
                    padding: 2px;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    border-radius: 4px;
                    border: 2px solid #bdc3c7;
                    background-color: white;
                }
                QCheckBox::indicator:hover {
                    border: 2px solid #3498db;
                    background-color: #ecf0f1;
                }
                QCheckBox::indicator:checked {
                    border: 2px solid #3498db;
                    background-color: #3498db;
                }
            """)
            self.scenario_checkboxes.append(checkbox)
            scenario_row.addWidget(checkbox)
            
            # Description
            desc_label = QLabel(description)
            desc_label.setFixedWidth(160)
            desc_label.setStyleSheet("""
                QLabel {
                    color: #7f8c8d;
                    font-style: italic;
                    font-size: 11px;
                    padding: 2px;
                }
            """)
            scenario_row.addWidget(desc_label)
            
            # Iterations label
            iter_label = QLabel("Iterations:")
            iter_label.setFixedWidth(70)
            iter_label.setStyleSheet("""
                QLabel {
                    color: #34495e;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 2px;
                }
            """)
            scenario_row.addWidget(iter_label)
            
            # Spinbox
            iter_input = QSpinBox()
            iter_input.setMinimum(0)
            iter_input.setMaximum(20)
            iter_input.setValue(1)
            iter_input.setFixedSize(80, 32)
            iter_input.setStyleSheet("""
                QSpinBox {
                    font-size: 12px;
                    font-weight: bold;
                    padding: 6px;
                    border: 2px solid #bdc3c7;
                    border-radius: 5px;
                    background-color: white;
                    color: #2c3e50;
                }
                QSpinBox:focus {
                    border: 2px solid #3498db;
                }
                QSpinBox::up-button, QSpinBox::down-button {
                    background-color: #3498db;
                    border: none;
                    width: 20px;
                }
                QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                    background-color: #2980b9;
                }
                QSpinBox::up-arrow, QSpinBox::down-arrow {
                    width: 10px;
                    height: 10px;
                    color: white;
                }
            """)
            self.scenario_iterations.append(iter_input)
            scenario_row.addWidget(iter_input)
            
            scenario_row.addStretch()
            scenario_layout.addWidget(scenario_container)
        
        # Start button
        start_button_layout = QHBoxLayout()
        start_button_layout.addStretch()
        
        self.start_perf_button = QPushButton("🚀 Start Performance Test")
        self.start_perf_button.setFixedSize(220, 45)
        self.start_perf_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 #27ae60, stop:1 #229954);
                color: white;
                border: 3px solid #1e8449;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 #229954, stop:1 #1e8449);
                border: 3px solid #17a2b8;
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 #1e8449, stop:1 #148f39);
                transform: translateY(1px);
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                border: 3px solid #95a5a6;
                color: #7f8c8d;
            }
        """)
        self.start_perf_button.clicked.connect(self.run_performance_test)
        start_button_layout.addWidget(self.start_perf_button)
        start_button_layout.addStretch()
        
        scenario_layout.addLayout(start_button_layout)
        scenario_group.setLayout(scenario_layout)
        config_layout.addWidget(scenario_group)
        
        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)
        
        # Progress bar
        self.progress_layout = QVBoxLayout()
        self.progress_layout.setSpacing(5)
        
        self.progress_label = QLabel("Running tests...")
        self.progress_label.setVisible(False)
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #34495e; 
                font-weight: bold; 
                font-size: 12px;
                padding: 5px;
                background-color: #ecf0f1;
                border-radius: 4px;
            }
        """)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(22)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                text-align: center;
                background-color: #ecf0f1;
                color: #2c3e50;
                font-weight: bold;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                            stop:0 #3498db, stop:1 #2980b9);
                border-radius: 4px;
                margin: 1px;
            }
        """)
        
        self.progress_layout.addWidget(self.progress_label)
        self.progress_layout.addWidget(self.progress_bar)
        main_layout.addLayout(self.progress_layout)
        
        # Results section
        results_group = QGroupBox("Test Results")
        results_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                border: 3px solid #3498db;
                border-radius: 12px;
                margin-top: 15px;
                padding-top: 25px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                background-color: #f8f9fa;
            }
        """)
        results_layout = QVBoxLayout()
        results_layout.setSpacing(10)
        
        # Excel status
        self.excel_status_label = QLabel("")
        self.excel_status_label.setStyleSheet("""
            QLabel {
                color: #27ae60; 
                font-weight: bold; 
                font-size: 11px;
                padding: 5px;
                background-color: #d5f4e6;
                border-radius: 4px;
            }
        """)
        self.excel_status_label.setVisible(False)
        results_layout.addWidget(self.excel_status_label)
        
        # Results table
        self.results_table = QTableWidget(0, 6)
        self.results_table.setHorizontalHeaderLabels([
            "Dashboard ID", "Scenario", "Iterations", "Avg Time (s)", 
            "Min Time (s)", "Max Time (s)"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setMinimumHeight(220)
        
        self.results_table.setStyleSheet("""
            QTableWidget {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                background-color: white;
                gridline-color: #ecf0f1;
                font-size: 11px;
                selection-background-color: #3498db;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 #34495e, stop:1 #2c3e50);
                color: white;
                padding: 10px;
                font-weight: bold;
                border: none;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QTableWidget::item:hover {
                background-color: #ebf3fd;
            }
            QTableWidget::item:alternate {
                background-color: #f8f9fa;
            }
        """)
        
        results_layout.addWidget(self.results_table)
        
        # Download button
        download_layout = QHBoxLayout()
        download_layout.addStretch()
        
        self.download_button = QPushButton("📊 Download Results as Excel")
        self.download_button.setFixedSize(240, 38)
        self.download_button.setEnabled(False)
        self.download_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 #3498db, stop:1 #2980b9);
                color: white;
                border: 2px solid #1f6aa8;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 #2980b9, stop:1 #1f6aa8);
                border: 2px solid #17a2b8;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 #1f6aa8, stop:1 #1a5490);
                transform: translateY(1px);
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                border: 2px solid #95a5a6;
                color: #7f8c8d;
            }
        """)
        self.download_button.clicked.connect(self.download_results)
        download_layout.addWidget(self.download_button)
        
        results_layout.addLayout(download_layout)
        results_group.setLayout(results_layout)
        main_layout.addWidget(results_group)
        
        # Set the content widget in the scroll area
        main_scroll.setWidget(content_widget)
        
        # Main tab layout
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(main_scroll)
        
        return tab

    def create_dashboard_health_tab(self):
        """Create the Dashboard Health tab with independent dashboard selection."""
        tab = QWidget()
        layout = QVBoxLayout()
        intro_text = QLabel("This tab checks if all dashboards are loading properly with all their features.")
        intro_text.setWordWrap(True)
        intro_text.setStyleSheet("color: #2c3e50; font-style: italic;")
        layout.addWidget(intro_text)
        # Use local dashboard selection group
        dashboard_group, self.health_dashboard_checkboxes = self.create_dashboard_selection_group()
        layout.addWidget(dashboard_group)
        
        # Progress bar (initially hidden)
        self.health_progress_layout = QVBoxLayout()
        self.health_progress_label = QLabel("Running health checks...")
        self.health_progress_label.setVisible(False)
        self.health_progress_bar = QProgressBar()
        self.health_progress_bar.setRange(0, 100)
        self.health_progress_bar.setValue(0)
        self.health_progress_bar.setVisible(False)
        self.health_progress_layout.addWidget(self.health_progress_label)
        self.health_progress_layout.addWidget(self.health_progress_bar)
        layout.addLayout(self.health_progress_layout)
        
        # Start button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.start_health_button = QPushButton("Start Health Check")
        self.start_health_button.setFixedWidth(200)
        self.start_health_button.clicked.connect(self.run_health_check)
        button_layout.addWidget(self.start_health_button)
        
        layout.addLayout(button_layout)
        
        # Results section
        results_group = QGroupBox("Dashboard Health Results")
        results_layout = QVBoxLayout()
        
        # Results table
        self.health_table = QTableWidget(0, 5)
        self.health_table.setHorizontalHeaderLabels([
            "Dashboard ID", "Status", "Charts Loaded", "Load Time (s)", "Issues"
        ])
        self.health_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.health_table.setAlternatingRowColors(True)
        results_layout.addWidget(self.health_table)
        
        # Download button
        download_layout = QHBoxLayout()
        download_layout.addStretch()
        
        self.download_health_button = QPushButton("Download Health Report")
        self.download_health_button.setFixedWidth(200)
        self.download_health_button.clicked.connect(self.download_health_report)
        self.download_health_button.setEnabled(False)
        download_layout.addWidget(self.download_health_button)
        
        results_layout.addLayout(download_layout)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        tab.setLayout(layout)
        return tab
    
    def refresh_dashboard_list(self):
        """Refresh the dashboard list from the API"""
        self.status_label.setText("Refreshing dashboard list...")
        
        # Fetch new dashboard data
        new_dashboards = self.fetch_dashboard_data()
        
        # Only proceed if we got data
        if new_dashboards:
            # Update dashboard IDs
            self.dashboard_ids = new_dashboards
            
            # Recreate the dashboard tabs
            current_tab = self.tabs.currentIndex()
            
            # Recreate the tabs with fresh data
            self.tabs.removeTab(1)  # Remove performance tab
            self.tabs.removeTab(1)  # Remove health tab (now at index 1)
            
            # Reset the checkbox list
            self.dashboard_checkboxes = []
            
            # Add fresh tabs
            self.performance_report_tab = self.create_performance_report_tab()
            self.dashboard_health_tab = self.create_dashboard_health_tab()
            
            self.tabs.insertTab(1, self.performance_report_tab, "Performance Report")
            self.tabs.insertTab(2, self.dashboard_health_tab, "Health of Dashboards")
            
            # Switch back to the tab user was viewing
            self.tabs.setCurrentIndex(current_tab)
            
            self.status_label.setText(f"Dashboard list refreshed with {len(self.dashboard_ids)} dashboards")
        else:
            self.status_label.setText("Failed to refresh dashboard list")
    
    # Helper methods (add these to your SupersetTester class if not already present)
    def select_all_dashboards(self):
        """Select all dashboard checkboxes"""
        for checkbox in self.dashboard_checkboxes:
            checkbox.setChecked(True)

    def deselect_all_dashboards(self):
        """Deselect all dashboard checkboxes"""
        for checkbox in self.dashboard_checkboxes:
            checkbox.setChecked(False)

    def select_first_3_dashboards(self):
        """Select only first 3 dashboards"""
        for i, checkbox in enumerate(self.dashboard_checkboxes):
            checkbox.setChecked(i < 3)
    
    # Event handlers
    def save_settings(self):
        """Save Superset connection details"""
        try:
            # Would typically save to a config file
            self.status_label.setText("Settings saved successfully")
            QMessageBox.information(self, "Settings Saved", "Superset connection details have been saved.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save settings: {str(e)}")
    
    def test_connection(self):
        """Test connection to Superset"""
        url = self.url_input.text()
        username = self.username_input.text()
        password = self.password_input.text()
        manual_login = self.manual_login_checkbox.isChecked()
        
        self.status_label.setText("Testing connection...")
        
        # Initialize tester with manual login option
        result = self.connector.initialize_tester(url, username, password, manual_login)
        
        if result == "WAITING_FOR_MANUAL":
            # Show instructions to the user
            QMessageBox.information(self, "Manual Login Required", 
                                "Browser opened for manual login.\n\n"
                                "Please complete the login process in the browser window.\n"
                                "When you're successfully logged in, click the 'I've Completed Login' button.")
            self.status_label.setText("Browser launched. Please complete the login process manually.")
            self.complete_login_btn.setEnabled(True)
        elif result:
            QMessageBox.information(self, "Connection Test", "Successfully connected to Superset!")
            self.status_label.setText("Connected to Superset, fetching dashboards...")
            
            # Fetch dashboards after successful connection
            self.dashboard_ids = self.fetch_dashboard_data()
            
            # Refresh the tabs to show new dashboard data
            self.refresh_dashboard_list()
        else:
            QMessageBox.critical(self, "Connection Test", 
                            "Failed to connect to Superset automatically.\n"
                            "This may be because your login page uses SSO or a custom authentication method.\n"
                            "Try enabling 'Manual login' and attempt again.")
            self.status_label.setText("Connection failed - try manual login")

    def manual_login_completed(self):
        """Called when the user clicks the 'I've completed login' button"""
        if self.connector.complete_manual_login():
            QMessageBox.information(self, "Login Successful", "Manual login completed successfully!")
            self.status_label.setText("Connected to Superset, fetching dashboards...")
            self.complete_login_btn.setEnabled(False)
            
            # Fetch dashboards after successful connection
            self.dashboard_ids = self.fetch_dashboard_data()
            
            # Refresh the tabs to show new dashboard data
            self.refresh_dashboard_list()
        else:
            QMessageBox.warning(self, "Login Issue", "Login doesn't appear to be completed. Please finish the login process in the browser.")
    
    def run_performance_test(self):
        """Run performance tests with updated scenario numbering"""
        # Get test parameters
        url = self.url_input.text()
        username = self.username_input.text()
        password = self.password_input.text()
        
        # Parse dashboard IDs from selected checkboxes (use performance tab checkboxes)
        dashboard_ids = []
        for i, checkbox in enumerate(self.performance_dashboard_checkboxes):
            if checkbox.isChecked():
                dashboard_ids.append(self.dashboard_ids[i]["id"])
        
        if not dashboard_ids:
            QMessageBox.warning(self, "Missing Input", "Please select at least one dashboard ID.")
            return
        
        # Get selected scenarios and their iterations - UPDATED MAPPING
        selected_scenarios = []
        iterations_by_scenario = {}
        
        scenario_mapping = [2, 3, 4]  # Map UI positions to actual scenario numbers
        
        for i, checkbox in enumerate(self.scenario_checkboxes):
            if checkbox.isChecked():
                scenario_num = scenario_mapping[i]  # Map to actual scenario number
                selected_scenarios.append(scenario_num)
                iterations_by_scenario[scenario_num] = self.scenario_iterations[i].value()
        
        if not selected_scenarios:
            QMessageBox.warning(self, "No Scenarios", "Please select at least one test scenario.")
            return
        
        # Initialize tester if not already done
        if not self.connector.tester:
            if not self.connector.initialize_tester(url, username, password):
                QMessageBox.critical(self, "Error", "Failed to initialize tester. Check your credentials.")
                return
        
        # Show progress bar
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.start_perf_button.setEnabled(False)
        
        # Update status with information about which scenarios are running
        scenario_info = ", ".join([f"Scenario {s} ({iterations_by_scenario[s]} iterations)" 
                                for s in selected_scenarios])
        self.status_label.setText(f"Running: {scenario_info}")
        
        # Run tests in background thread
        self.connector.run_performance_tests(dashboard_ids, selected_scenarios, iterations_by_scenario)


    def run_health_check(self):
        """Run health checks on dashboards"""
        # Get test parameters
        url = self.url_input.text()
        username = self.username_input.text()
        password = self.password_input.text()
        
        # Get selected dashboard IDs from checkboxes (use health tab checkboxes)
        dashboard_ids = []
        for i, checkbox in enumerate(self.health_dashboard_checkboxes):
            if checkbox.isChecked():
                dashboard_ids.append(self.dashboard_ids[i]["id"])
        
        if not dashboard_ids:
            QMessageBox.warning(self, "Missing Input", "Please select at least one dashboard ID.")
            return
        
        # Initialize tester if not already done
        if not self.connector.tester:
            if not self.connector.initialize_tester(url, username, password):
                QMessageBox.critical(self, "Error", "Failed to initialize tester. Check your credentials.")
                return
        else:
            # If we already have a tester, we might need to refresh the driver
            if not self.connector.refresh_driver():
                QMessageBox.critical(self, "Error", "Failed to reconnect to browser. Please restart the application.")
                return
        
        # Show progress bar
        self.health_progress_bar.setValue(0)
        self.health_progress_bar.setVisible(True)
        self.health_progress_label.setVisible(True)
        self.start_health_button.setEnabled(False)
        self.status_label.setText(f"Running health checks on {len(dashboard_ids)} dashboards...")
        
        # Run health checks in background thread
        self.connector.run_dashboard_health_check(dashboard_ids)
    
    def update_progress(self, value, message):
        """Update progress bar and status message"""
        current_tab = self.tabs.currentIndex()
        
        if current_tab == 1:  # Performance Report tab
            self.progress_bar.setValue(value)
            self.progress_label.setText(message)
        elif current_tab == 2:  # Health of Dashboards tab
            self.health_progress_bar.setValue(value)
            self.health_progress_label.setText(message)
            
        self.status_label.setText(message)

    def route_test_completed(self, data):
        """Route test completion events to the appropriate handler based on active tab"""
        current_tab = self.tabs.currentIndex()
        
        if current_tab == 1:  # Performance Report tab
            self.handle_test_completed(data)
        elif current_tab == 2:  # Health of Dashboards tab
            self.handle_health_completed(data)
    
    def handle_test_completed(self, data):
        """Handle completion of tests with updated scenario mapping"""
        # Process performance results
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.start_perf_button.setEnabled(True)
        self.download_button.setEnabled(True)
        
        # Defensive: Only call display_performance_results if results is a dict
        results = data.get("results", {})
        if isinstance(results, dict):
            self.display_performance_results(results)
        else:
            # Optionally, clear the table or show a warning
            self.results_table.setRowCount(0)
        
        # Update status
        self.status_label.setText("Performance tests completed successfully")
        
        # Store the excel path for download
        self.performance_excel_path = data.get("excel_path", "")
        
        # Show success message with updated scenario mapping
        scenario_iterations = []
        scenario_mapping = [2, 3, 4]  # DO NOT CHANGE LOGIC

        for i, checkbox in enumerate(self.scenario_checkboxes):
            if checkbox.isChecked():
                scenario_num = scenario_mapping[i]
                iter_count = self.scenario_iterations[i].value()
                # UI label only: show Scenario 1/2/3 instead of 2/3/4
                scenario_label = f"Scenario {i+1}: {iter_count} iterations"
                scenario_iterations.append(scenario_label)
        iterations_summary = ", ".join(scenario_iterations)
        QMessageBox.information(self, "Tests Completed", 
                            f"Performance tests completed successfully.\n\n"
                            f"Settings used: {iterations_summary}\n\n"
                            f"Results are displayed in the table and can be downloaded as Excel.")
        
    def handle_health_completed(self, data):
        """Handle completion of health checks"""
        # Reset UI elements
        self.health_progress_bar.setVisible(False)
        self.health_progress_label.setVisible(False)
        self.start_health_button.setEnabled(True)
        self.download_health_button.setEnabled(True)
        
        # Display results in table
        self.display_health_results(data.get("results", []))
        
        # Store the excel path for download
        self.health_excel_path = data.get("excel_path", "")
        
        # Update status
        self.status_label.setText("Dashboard health checks completed")
        
        # Show success message
        health_counts = {
            "Healthy": 0,
            "Warning": 0,
            "Critical": 0
        }
        
        for result in data.get("results", []):
            status = result.get("Status")
            if status in health_counts:
                health_counts[status] += 1
        
        QMessageBox.information(self, "Health Checks Completed",
                            f"Dashboard health checks completed.\n\n"
                            f"Results summary:\n"
                            f"- Healthy: {health_counts['Healthy']}\n"
                            f"- Warning: {health_counts['Warning']}\n"
                            f"- Critical: {health_counts['Critical']}\n\n"
                            f"Detailed results are in the table and can be downloaded as Excel.")
        
    def display_health_results(self, results):
        """Display health check results in the table"""
        # Clear existing results
        self.health_table.setRowCount(0)
        
        if not results:
            return
        
        # Add results to table
        for row, result in enumerate(results):
            self.health_table.insertRow(row)
            
            # Dashboard ID
            self.health_table.setItem(row, 0, QTableWidgetItem(str(result.get('Dashboard ID', ''))))
            
            # Status with color
            status = result.get('Status', 'Unknown')
            status_item = QTableWidgetItem(status)
            if status == "Healthy":
                status_item.setForeground(Qt.darkGreen)
            elif status == "Warning":
                status_item.setForeground(Qt.darkYellow)
            elif status == "Critical":
                status_item.setForeground(Qt.red)
            self.health_table.setItem(row, 1, status_item)
            
            # Charts loaded
            charts_loaded = f"{result.get('Charts Loaded', 0)}/{result.get('Total Charts', 0)}"
            self.health_table.setItem(row, 2, QTableWidgetItem(charts_loaded))
            
            # Load time
            load_time = result.get('Load Time (s)', 0)
            self.health_table.setItem(row, 3, QTableWidgetItem(f"{load_time:.2f}"))
            
            # Issues
            self.health_table.setItem(row, 4, QTableWidgetItem(result.get('Issues', '')))
    
    def handle_test_error(self, error_message):
        """Handle test errors"""
        # Reset UI elements
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.start_perf_button.setEnabled(True)
        
        # Show error message
        QMessageBox.critical(self, "Error", error_message)
        self.status_label.setText(f"Error: {error_message}")
    
    def display_performance_results(self, results):
        """Display performance test results in the table"""
        # Clear existing results
        self.results_table.setRowCount(0)
        
        if not results:
            return
        
        # Process results by dashboard and scenario
        processed_results = []
        for scenario_name, measurements in results.items():
            if not measurements:
                continue
                
            # Extract scenario number
            scenario_num = int(scenario_name.split()[1]) if len(scenario_name.split()) > 1 else 0
            
            # Group by dashboard ID
            by_dashboard = {}
            for measurement in measurements:
                dashboard_id = measurement.get('Dashboard ID')
                if dashboard_id not in by_dashboard:
                    by_dashboard[dashboard_id] = []
                by_dashboard[dashboard_id].append(measurement)
            
            # Calculate stats for each dashboard
            for dashboard_id, dashboard_measurements in by_dashboard.items():
                # Determine which time column to use
                if 'Refresh Time (seconds)' in dashboard_measurements[0]:
                    time_col = 'Refresh Time (seconds)'
                else:
                    time_col = 'Load Time (seconds)'
                
                # Calculate stats
                times = [m[time_col] for m in dashboard_measurements]
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)
                
                # Get iterations for this specific scenario
                iterations = len(dashboard_measurements)
                if 1 <= scenario_num <= len(self.scenario_iterations):
                    displayed_iterations = self.scenario_iterations[scenario_num-1].value()
                else:
                    displayed_iterations = iterations
                
                # UI label only: replace Scenario 2/3/4 with Scenario 1/2/3 for display
                display_scenario = scenario_name.replace("Scenario 2", "Scenario 1").replace("Scenario 3", "Scenario 2").replace("Scenario 4", "Scenario 3")
                processed_results.append({
                    'Dashboard ID': dashboard_id,
                    'Scenario': display_scenario,
                    'Iterations': displayed_iterations,
                    'Avg Time': avg_time,
                    'Min Time': min_time,
                    'Max Time': max_time
                })
        
        # Add to table with colored text by scenario
        for row, result in enumerate(processed_results):
            self.results_table.insertRow(row)
            
            # Set color based on scenario (use new UI labels)
            scenario = result['Scenario']
            if 'Scenario 1' in scenario:
                color = Qt.blue
            elif 'Scenario 2' in scenario:
                color = Qt.darkGreen
            elif 'Scenario 3' in scenario:
                color = Qt.darkMagenta
            elif 'Scenario 4' in scenario:
                color = Qt.red
            else:
                color = Qt.black
            
            # Add each cell with the appropriate color
            for col, value in enumerate([
                str(result['Dashboard ID']),
                result['Scenario'],
                str(result['Iterations']),
                f"{result['Avg Time']:.2f}",
                f"{result['Min Time']:.2f}",
                f"{result['Max Time']:.2f}"
            ]):
                item = QTableWidgetItem(value)
                item.setForeground(color)
                self.results_table.setItem(row, col, item)
    
    def download_results(self):
        """Download performance results as Excel file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Performance Results", "", "Excel Files (*.xlsx)")
            
        if not filename:
            return
            
        # If the file doesn't end with .xlsx, add it
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'
        
        try:
            # The results should already be saved by the connector
            # Just copy the file to the selected location
            import shutil
            if hasattr(self, 'performance_excel_path'):
                excel_path = self.performance_excel_path
                shutil.copy2(excel_path, filename)
                self.status_label.setText(f"Results saved to {filename}")
                QMessageBox.information(self, "Download Complete", f"Results saved to {filename}")
            else:
                QMessageBox.warning(self, "No Results", "No results available to download.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save results: {str(e)}")

    def download_health_report(self):
        """Download health check results as Excel file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Health Report", "", "Excel Files (*.xlsx)")
            
        if not filename:
            return
            
        # If the file doesn't end with .xlsx, add it
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'
        
        try:
            # Copy the existing file or create a new one from the table data
            import shutil
            if hasattr(self, 'health_excel_path') and os.path.exists(self.health_excel_path):
                shutil.copy2(self.health_excel_path, filename)
            else:
                # Create DataFrame from table data
                data = []
                for row in range(self.health_table.rowCount()):
                    row_data = {}
                    row_data['Dashboard ID'] = self.health_table.item(row, 0).text()
                    row_data['Status'] = self.health_table.item(row, 1).text()
                    row_data['Charts Loaded'] = self.health_table.item(row, 2).text()
                    row_data['Load Time (s)'] = self.health_table.item(row, 3).text()
                    row_data['Issues'] = self.health_table.item(row, 4).text()
                    data.append(row_data)
                
                # Save as Excel
                df = pd.DataFrame(data)
                df.to_excel(filename, index=False)
            
            self.status_label.setText(f"Health report saved to {filename}")
            QMessageBox.information(self, "Download Complete", f"Health report saved to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save health report: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = SupersetTester()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
