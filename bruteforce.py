# --- AI SIGNATURE: FINAL AUTO-FIX BRUTEFORCE ---
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

# URL'yi temizle ve yaygın yazım hatalarını düzelt
args.url = args.url.strip()
if args.url.startswith("http//"):
    args.url = "http://" + args.url[6:]
elif args.url.startswith("https//"):
    args.url = "https://" + args.url[7:]

if not (args.url.startswith("http://") or args.url.startswith("https://")):
    print(f"{Fore.RED}[!] Geçersiz URL formatı. URL http:// veya https:// ile başlamalıdır.")
    exit(1)


combos = []
# ... (kodun geri kalanı aynı) ...
# --- AI SIGNATURE: FINAL AUTO-FIX BRUTEFORCE BITIS --- 