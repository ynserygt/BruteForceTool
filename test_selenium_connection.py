import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from colorama import Fore, init

init(autoreset=True)

# Argümanları al
parser = argparse.ArgumentParser()
parser.add_argument('--no-headless', action='store_true', help='Tarayıcıyı görünür modda çalıştır')
args = parser.parse_args()

url = "https://mgmt.yenihavale.net/login"
print(f"DEBUG: Test edilen URL -> '{url}'")

chrome_options = Options()
# Headless modu argümana göre ayarla
if not args.no_headless:
    chrome_options.add_argument('--headless')
    print("DEBUG: Headless (arka plan) modda çalıştırılıyor.")
else:
    print("DEBUG: Görünür tarayıcı modunda çalıştırılıyor.")

# Stabilite için ekstra ayarlar
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1280x800')

try:
    print("DEBUG: Tarayıcı başlatılıyor...")
    driver = webdriver.Chrome(options=chrome_options)
    # Sayfa yükleme süresini 60 saniyeye çıkar
    driver.set_page_load_timeout(60)
    print(f"DEBUG: {url} adresine gidiliyor...")
    driver.get(url)
    time.sleep(5) # Sayfanın tam yüklenmesi için bekle
    print(f"{Fore.GREEN}BAŞARILI! Sayfa başlığı: {driver.title}")
    print(f"{Fore.GREEN}Sayfa URL: {driver.current_url}")

except Exception as e:
    print(f"{Fore.RED}HATA! Selenium bağlantı kuramadı.")
    print(f"{Fore.RED}Hata mesajı: {e}")
finally:
    try:
        driver.quit()
        print("DEBUG: Tarayıcı kapatıldı.")
    except:
        pass 