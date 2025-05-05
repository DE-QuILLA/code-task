from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

service = Service(
    "/app/code-task/etl_scripts/scripts/chromedriver-linux64/chromedriver"
)

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=service, options=options)

try:
    driver.get("https://example.com")
    print("Title:", driver.title)

    # Example: Find an element by tag
    element = driver.find_element(By.TAG_NAME, "h1")
    print("H1 text:", element.text)
except Exception as e:
    print(e)

finally:
    driver.quit()
