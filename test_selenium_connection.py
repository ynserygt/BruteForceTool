from selenium import webdriver
from selenium.webdriver.chrome.options import Options

url = "https://mgmt.yenihavale.net/login"
print(f"DEBUG: Test edilen URL -> '{url}'")

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

try:
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)
    driver.get(url)
    print("BAŞARILI! Sayfa başlığı:", driver.title)
    print("Sayfa URL:", driver.current_url)
    driver.quit()
except Exception as e:
    print("HATA! Selenium bağlantı kuramadı.")
    print("Hata mesajı:", e) 