"""
Browser Automation and Snapshot Utilities for DBSafe

This module provides browser automation capabilities for capturing snapshots
of visualizations and scraping web content. It configures and manages WebDriver
instances for Chrome and Safari browsers with appropriate settings for headless
operation and data extraction.

Copyright (c) 2023-2024
License: Apache License 2.0 (see LICENSE file for details)
"""

import os
import time
from typing import Any, Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

# JavaScript code for snapshot generation
SNAPSHOT_JS = """
    var ele = document.querySelector('div[_echarts_instance_]');
    var mychart = echarts.getInstanceByDom(ele);
    return mychart.getDataURL({
        type: '%s',
        pixelRatio: %s,
        excludeComponents: ['toolbox']
    });
"""

SNAPSHOT_SVG_JS = """
   var element = document.querySelector('div[_echarts_instance_] div');
   return element.innerHTML;
"""


def make_snapshot(
    html_path: str,
    file_type: str,
    pixel_ratio: int = 2,
    delay: int = 2,
    browser: str = "Chrome",
    driver: Any = None,
) -> str:
    """
    Generate a snapshot of an HTML page with ECharts visualizations.
    
    Args:
        html_path: Path to the HTML file or URL to capture
        file_type: Type of file to generate ('svg' or other image formats like 'png')
        pixel_ratio: Resolution multiplier for image output (higher values for better quality)
        delay: Time to wait for rendering in seconds
        browser: Browser to use ('Chrome' or 'Safari')
        driver: Existing WebDriver instance (optional)
        
    Returns:
        Generated snapshot data (base64 encoded for images, SVG markup for SVG)
        
    Raises:
        Exception: If an invalid browser is specified or delay is negative
    """
    if delay < 0:
        raise ValueError("Time travel is not possible: delay must be non-negative")
        
    if not driver:
        if browser == "Chrome":
            driver = get_chrome_driver("temp")  # Default to temp folder
        elif browser == "Safari":
            driver = get_safari_driver()
        else:
            raise ValueError(f"Unsupported browser: {browser}. Use 'Chrome' or 'Safari'.")

    if file_type == "svg":
        snapshot_js = SNAPSHOT_SVG_JS
    else:
        snapshot_js = SNAPSHOT_JS % (file_type, pixel_ratio)

    # Convert local file paths to file:// URLs
    if not html_path.startswith("http"):
        html_path = "file://" + os.path.abspath(html_path)

    # Load the page and wait for rendering
    driver.get(html_path)
    time.sleep(delay)

    # Execute JavaScript to capture the visualization
    return driver.execute_script(snapshot_js)


def get_chrome_driver(folder: str) -> webdriver.Chrome:
    """
    Initialize and configure a Chrome WebDriver instance.
    
    Sets up a Chrome browser with appropriate options for headless operation,
    screen capture, and file downloads.
    
    Args:
        folder: Download folder path for saving files
        
    Returns:
        Configured Chrome WebDriver instance
    """
    options = webdriver.ChromeOptions()
    # Configure browser settings for stability and performance
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--verbose")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-print-preview")
    options.add_argument("--safebrowsing-disable-download-protection")
    options.add_argument("--safebrowsing-disable-extension-blacklist")

    # Configure MIME types for downloads
    mime_types = (
        "application/pdf,"
        "application/vnd.ms-excel,"
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,"
        "application/msword,"
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    # Configure download preferences
    prefs = {
        "download.default_directory": folder,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": False,
        "safebrowsing.disable_download_protection": True,
        "plugins.always_open_pdf_externally": True,
        "profile.default_content_settings.popups": 0,
        "profile.default_content_setting_values.automatic_downloads": 1,
        "profile.content_settings.exceptions.automatic_downloads.*.setting": 1,
        "profile.default_content_setting_values.popups": 0,
        "profile.default_content_setting_values.notifications": 1,
        "profile.managed_default_content_settings.notifications": 1,
        "browser.helperApps.neverAsk.saveToDisk": mime_types,
        "browser.helperApps.neverAsk.openFile": mime_types,
        "pdfjs.disabled": True,
        "download.allow_insecure": True,
    }

    options.add_experimental_option("prefs", prefs)

    # Initialize Chrome driver with WebDriver Manager for automatic driver updates
    service = ChromeService(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    return driver


def get_safari_driver() -> webdriver.Safari:
    """
    Initialize a Safari WebDriver instance.
    
    Note: Safari's WebDriver has fewer configuration options compared to Chrome.
    For advanced scraping and downloading capabilities, Chrome is recommended.
    
    Returns:
        Safari WebDriver instance
    """
    return webdriver.Safari()
