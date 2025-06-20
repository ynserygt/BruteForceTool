# Cloudflare Destekli Login Brute Force Aracı

## Özellikler
- Otomatik login formu tespiti
- Kullanıcı adı ve şifre alanı uzunluk analizi
- rockyou.txt veya combo wordlist ile brute force
- Cloudflare koruması algılama ve aşma (cloudscraper, gerekirse Selenium)
- Başarı/başarısızlık otomatik algılama
- Kullanıcı dostu CLI

## Kurulum
```bash
pip install -r requirements.txt
```
Selenium için ayrıca Chrome veya Firefox ve uygun WebDriver (ör: chromedriver) kurulu olmalıdır.

## Kullanım
```bash
python3 bruteforce.py --url "https://hedefsite.com/login" --combo combo_wordlist.txt
```

## Notlar
- Sadece eğitim ve yasal testler için kullanınız!
- Cloudflare koruması çok güçlü ise Selenium ile manuel mod önerilir. 