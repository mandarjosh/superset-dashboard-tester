Superset Dashboard Performance Testing Tool
This application provides a graphical user interface for testing the performance of Superset dashboards. It integrates a PyQt5-based UI with your existing Python testing framework to create a user-friendly testing experience.
Features

Connection Management: Easily configure Superset connection details
Performance Testing: Run various performance test scenarios
Customizable Testing: Select specific dashboards and test scenarios
Interactive UI: User-friendly interface with progress tracking
Results Visualization: View and export test results

Project Structure
Copysuperset_dashboard_tester/
├── main.py                         # Main PyQt5 application
├── ui_connector.py                 # Bridge between UI and testing code
├── resources/                      # UI resources
│   └── logo.png                    # Your company logo
├── run_performance_test.py         # Original testing script
├── scenarios.py                    # Test scenarios implementation
├── superset_performance_tester.py  # Core testing functionality
├── config.py                       # Configuration settings
├── run_tester.bat                  # Windows launcher
├── run_tester.sh                   # Mac/Linux launcher 
└── requirements.txt                # Dependencies
Setup Instructions
Prerequisites

Python 3.6 or higher
Chrome browser and Chrome WebDriver for Selenium tests

Installation

Clone or download this repository
Create and activate a Python virtual environment:
Copypython -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install required dependencies:
Copypip install -r requirements.txt

Place your company logo in the resources folder (named "logo.png")
Run the application:

On Mac/Linux: ./run_tester.sh
On Windows: Double-click run_tester.bat



Using the Application
1. Superset Details Tab

Enter your Superset server URL, username, and password
Click "Test Connection" to verify connectivity
Save settings for future use

2. Performance Report Tab

Enter dashboard IDs to test (comma-separated)
Set the number of test iterations
Select which test scenarios to run:

Scenario 1: Single dashboard load time
Scenario 2: Sequential dashboards load time
Scenario 3: Parallel dashboards load time
Scenario 4: Dashboard refresh time


Click "Start Performance Test" to begin testing
View results in the table and download as Excel

Development Notes

The UI is built with PyQt5
Tests run in background threads to keep the UI responsive
The ui_connector.py file integrates the UI with your existing testing framework
The application uses signals to communicate between the testing thread and the UI

Troubleshooting

If the connection test fails, verify your Superset credentials and server URL
If tests don't run properly, check the Chrome WebDriver installation
For UI issues, make sure PyQt5 is correctly installed in your environment