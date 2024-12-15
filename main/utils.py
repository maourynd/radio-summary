# main/utils.py

from selenium.webdriver.chrome.options import Options
from selenium import webdriver

def setup_chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    return webdriver.Chrome(options=chrome_options)