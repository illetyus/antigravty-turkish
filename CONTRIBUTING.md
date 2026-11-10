# Antigravity Türkçe Yerelleştirme Katkı Kılavuzu (CONTRIBUTING)

Google Antigravity Türkçe Yama projesine katkıda bulunmak istediğiniz için teşekkür ederiz!

Bu proje, Google Antigravity 2.0 masaüstü arayüzünü eksiksiz, dinamik ve performans kaybı olmaksızın Türkçe'ye kavuşturmayı amaçlar.

---

## 1. Mimari Genel Bakış

Sistem 3 temel bileşenden oluşur:
1. **`tr-dictionary.json`**: Tüm birebir metin eşleşmelerini (`exact`) ve dinamik şablonları (`patterns`) tutan merkezi UTF-8 JSON veri tabanı.
2. **`build_locale.py`**: JSON sözlüğü okuyarak tarayıcı/Electron DOM ortamında reaktif çalışan `tr-locale.js` dosyasını üreten kalıcı derleyici.
3. **`patch_asar.py`**: Antigravity'nin `app.asar` arşivini güvenli SHA256 blok kontrolüyle mühürleyen paketleme motoru.

---

## 2. Yeni Terim veya Çeviri Ekleme

Eğer arayüzde İngilizce kalmış bir alan fark ederseniz:

1. `tr-dictionary.json` dosyasını UTF-8 olarak açın.
2. Statik bir başlık/metin ise `exact` nesnesi altına ekleyin:
   ```json
   "New Feature Label": "Yeni Özellik Etiketi"
   ```
3. Değişken içeren dinamik bir ifade ise (`5 conversations`, `3 days left` vb.) `patterns` dizisine regex olarak ekleyin:
   ```json
   {
     "regex": "^(\\d+)\\s+items?\\s+found$",
     "replace": "$1 öğe bulundu"
   }
   ```
4. Derleyiciyi çalıştırın:
   ```powershell
   python build_locale.py
   ```
5. Test paketini çalıştırarak doğrulayın:
   ```powershell
   python test_tr_patch.py
   ```

---

## 3. Kod ve Test Standartları

- Tüm dosya ve kaynak kodlar **UTF-8** kodlamasında olmalıdır.
- Kod veya Monaco Editor blokları içindeki metinler çevrilmemelidir (`isProtected` filtresi korunmalıdır).
- Yapılan her değişiklikten sonra `test_tr_patch.py` içindeki tüm testler (`14/14`) yeşil geçmelidir.

---

## 4. Pull Request (PR) Süreci

1. Depoyu fork'layın ve yeni bir dal (branch) açın (`git checkout -b feature/yeni-terimler`).
2. Değişikliklerinizi yapıp `test_tr_patch.py` ile doğrulayın.
3. Açıklayıcı bir commit mesajı ile commit'leyin (`git commit -m "feat: ayarlardaki yeni bildirim başlıkları eklendi"`).
4. GitHub üzerinden bir Pull Request gönderin.
