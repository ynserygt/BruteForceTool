# Gelişmiş Brute-Force Aracı

Bu araç, bir web sayfasındaki giriş formlarına yönelik akıllı bir kaba kuvvet saldırısı (brute-force attack) gerçekleştirmek için tasarlanmıştır. Selenium kullanarak gerçek bir tarayıcıyı otomatize eder ve Cloudflare gibi korumaları aşma potansiyeline sahiptir.

## Özellikler

- **Çift Tarayıcı Desteği**: Hem Chrome hem de Firefox ile çalışabilir.
- **Akıllı Form Tespiti**: Kullanıcı adı, şifre ve gönderim butonu gibi giriş alanlarını otomatik olarak bulur.
- **Iframe Desteği**: Giriş formları `<iframe>` içinde olsa bile onları tespit edebilir.
- **Dinamik Kelime Listesi Filtreleme**: Saldırıya başlamadan önce giriş alanlarının `minlength` ve `maxlength` özelliklerini kontrol eder ve kelime listesini bu kurallara göre filtreleyerek gereksiz denemeleri önler.
- **Hız Sınırlaması (Rate-Limit) Tespiti**: "Çok fazla deneme" veya "Captcha" gibi ifadeleri algıladığında saldırıyı duraklatır, bir süre bekler ve kaldığı yerden devam eder.
- **Görünmez Mod (Headless)**: İsteğe bağlı olarak tarayıcıyı arayüz olmadan çalıştırabilir.
- **Otomatik Kurulum**: Gerekli tarayıcı sürücülerini (`chromedriver`/`geckodriver`) otomatik olarak indirir ve yönetir.

## Gereksinimler

- Python 3.6+
- Google Chrome veya Mozilla Firefox tarayıcısının yüklü olması.

Gerekli Python kütüphanelerini yüklemek için:
```bash
pip install -r requirements.txt
```

## Kullanım

Aracı çalıştırmak için terminalde aşağıdaki komutu kullanın:

```bash
python bruteforce.py [URL] [SEÇENEKLER]
```

### Parametreler

- `url`: (Zorunlu) Saldırının yapılacağı tam giriş sayfası URL'si.
- `-w`, `--wordlist`: (İsteğe bağlı) Kullanıcı adı ve şifre kombinasyonları için kullanılacak kelime listesi dosyasının yolu. Varsayılan olarak `/usr/share/wordlists/rockyou.txt` kullanılır.
- `-b`, `--browser`: (İsteğe bağlı) Kullanılacak tarayıcı. `chrome` ya da `firefox` olabilir. Varsayılan: `firefox`.
- `--headless`: (İsteğe bağlı) Tarayıcıyı görünmez modda çalıştırmak için bu bayrağı ekleyin.
- `--cooldown`: (İsteğe bağlı) Hız sınırlaması tespit edildiğinde beklenecek süre (saniye cinsinden). Varsayılan: `300`.

### Örnek Komut

```bash
# Firefox ile bir siteye saldırı (varsayılan kelime listesiyle)
python bruteforce.py https://example.com/login

# Chrome'u görünmez modda ve özel bir kelime listesiyle kullanma
python bruteforce.py https://testsite.com/signin -b chrome -w /path/to/my/list.txt --headless
```

## Notlar

- Başarılı bir giriş tespit edildiğinde, kimlik bilgileri `credentials.txt` adlı bir dosyaya kaydedilir.
- Bu araç yalnızca yasal ve etik test amaçlı kullanılmalıdır. İzinsiz sistemlere saldırmak yasa dışıdır. 