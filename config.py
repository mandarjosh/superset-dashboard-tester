"""
Configuration file for Superset performance testing
Contains all credentials and settings for the test framework
"""

import os

# Superset instance details
SUPERSET_CONFIG = {
    'base_url': "https://reporting.tkosuat.co.uk",
    'username': "superset_consultant@tkos.co.uk",
    'password': "spgjY9jXXbxa66qKs4ou",
    'output_file': "church_finance_R1.xlsx"
}

# Dashboard configurations for different scenarios
DASHBOARD_CONFIG = {
    'scenario_1': {
        'enabled': False,
        'dashboard_id': '8',  # Single dashboard ID for scenario 1
        'iterations': 1  # Number of times to measure this dashboard
    },
    'scenario_2': {
        'enabled': True,
        'dashboard_ids': ['church_finance'],  # List of dashboards for sequential testing
        'iterations_per_dashboard': 6  # Number of times to measure each dashboard
    },
    'scenario_3': {
        'enabled': True,
        'dashboard_ids': ['church_finance'],  # List of dashboards for parallel testing
        'iterations_per_dashboard': 6,  # Number of times to measure each dashboard
        'max_workers': 6  # Maximum number of parallel browser tabs
    },
    'scenario_4': {
        'enabled': True,
        'dashboard_ids': ['church_finance'],  # List of dashboards for refresh testing
        'refresh_count': 6,  # Number of times to refresh each dashboard
        'wait_between_refresh': 1  # Wait time between refreshes in seconds
    },
    'scenario_5': {
        'enabled': False,
        'dashboard_id': '9',  # Single dashboard for chart-by-chart refresh
        'chart_refresh_iterations': 1,  # Number of times to refresh each chart
        'wait_between_refresh': 2  # Wait time between refreshes in seconds
    }
}

# Directories for logs and results
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Browser configuration
BROWSER_CONFIG = {
    'headless': False,  # Set to True for headless execution
    'window_size': (1920, 1080)
}


# ['diocese_finance', '15','17','18', '19','23','church_finance','14','16','20']