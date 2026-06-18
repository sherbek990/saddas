# 🎌 Anime Telegram Bot

To'liq ishlaydigan, professional Anime Telegram Bot. Aiogram 3.x asosida yozilgan.

## ✅ Mavjud funksiyalar

1. **Zayavka** — /start orqali ro'yxatdan o'tish, foydalanuvchini bazaga saqlash
2. **Xabar yuborish** — barcha foydalanuvchilarga (broadcast) xabar yuborish
3. **Post yuborish** — bir vaqtning o'zida xohlagancha kanalga post yuborish
4. **Majburiy obuna** — Telegram (real tekshiruv), Instagram va YouTube (maksimal 2 ta) kanallarga ulash
5. **Kontent cheklash** — admin panel orqali har bir animeni cheklash/ochish
6. **Oldinga va Orqaga** — epizodlar orasida navigatsiya tugmalari
7. **Birlamchi sozlamalar** — xush kelibsiz matni, bot nomi, majburiy obuna yoqish/o'chirish
8. **Anime tahrirlash** — nomi, tavsifi, janri, statusi
9. **Rasm/Video tahrirlash** — poster va epizod video/thumbnail almashtirish
10. **Video orqali anime qo'shish** — to'liq FSM bosqichlari orqali yangi epizod qo'shish
11. **Fanadub nomi** — anime qo'shishda fandub guruh nomini kiritish

## 📂 Loyiha tuzilishi

```
anime_bot/
├── bot.py                  # Asosiy ishga tushirish fayli
├── config.py                # Sozlamalar (token, adminlar)
├── requirements.txt
├── .env.example
├── database/
│   └── db.py                # SQLite bilan ishlash (aiosqlite)
├── handlers/
│   ├── start.py             # /start, asosiy menyu
│   ├── navigation.py         # Anime ro'yxati, ko'rish, epizod ijro etish
│   ├── subscription_check.py # Obuna tekshirish callback
│   ├── admin_panel.py        # Admin panel, obuna kanallari
│   ├── anime_manage.py       # Anime/epizod qo'shish, tahrirlash, cheklash
│   ├── post_sender.py        # Broadcast va ko'p-kanalga post yuborish
│   └── settings.py           # Bot sozlamalari
├── keyboards/
│   └── main_kb.py            # Barcha inline/reply tugmalar
├── middlewares/
│   └── subscription.py       # Majburiy obunani avtomatik tekshiruvchi middleware
└── utils/
    ├── states.py              # FSM holatlari
    └── helpers.py             # Yordamchi funksiyalar
```

## 🚀 O'rnatish

### 1. Talablarni o'rnatish

```bash
pip install -r requirements.txt
```

### 2. `.env` faylini sozlash

`.env.example` faylini `.env` deb nomlang va to'ldiring:

```bash
cp .env.example .env
```

```env
BOT_TOKEN=sizning_bot_tokeningiz
ADMIN_IDS=123456789,987654321
SUPER_ADMIN_ID=123456789
DB_PATH=anime_bot.db
```

> Bot tokenini olish: Telegramda [@BotFather](https://t.me/BotFather) ga `/newbot` yuboring.
> O'z ID raqamingizni bilish: [@userinfobot](https://t.me/userinfobot) ga `/start` yuboring.

### 3. Botni ishga tushirish

```bash
python bot.py
```

## 🐳 Docker bilan ishga tushirish

```bash
docker build -t anime-bot .
docker run -d --env-file .env --name anime-bot anime-bot
```

## ⚙️ Admin panel qo'llanmasi

`/admin` buyrug'i orqali admin panelga kirasiz (faqat `.env` da ko'rsatilgan ADMIN_IDS uchun ishlaydi).

### Majburiy obuna kanal qo'shish
- **Admin Panel → Obuna kanallari → ➕ Telegram/Instagram/YouTube**
- Telegram kanal uchun: bot kanalga albatta **admin** qilib qo'shilishi kerak (real tekshiruv uchun)
- Instagram va YouTube uchun faqat link saqlanadi, real obuna tekshirilmaydi (Telegram API orqali imkonsiz), lekin foydalanuvchiga ko'rsatiladi
- YouTube uchun maksimal **2 ta** kanal qo'shish mumkin

### Yangi anime qo'shish
- **Admin Panel → Anime boshqaruv → ➕ Yangi anime**
- Bosqichma-bosqich so'raladi: nomi → fanadub nomi → tavsif → janr → poster (rasm)
- Anime qo'shilgandan keyin unga **📹 Video qo'shish** orqali epizodlar qo'shiladi

### Epizod (video) qo'shish
- Anime detalida **📹 Video qo'shish** tugmasi
- Epizod raqami → sarlavha → video fayl → thumbnail (ixtiyoriy)

### Kontent cheklash
- Anime detalida **🔒 Cheklash / 🔓 Ruxsat berish** tugmasi orqali bir bosishda yoqiladi/o'chiriladi
- Cheklangan anime oddiy foydalanuvchilarga ko'rinmaydi, faqat adminlarga ko'rinadi (🔒 belgisi bilan)

### Post yuborish (bir nechta kanalga bir vaqtda)
1. Botni post yubormoqchi bo'lgan barcha kanallarga **admin** qilib qo'shing
2. Har bir kanaldan istalgan bir postni botga **forward** qiling — bot avtomatik o'sha kanalni ro'yxatga qo'shadi
3. **Admin Panel → Post yuborish → Matn/Rasm/Video** tanlang va kontentni yuboring
4. Bot bir vaqtning o'zida barcha qo'shilgan kanallarga yuboradi

### Hammaga xabar yuborish (broadcast)
- **Admin Panel → Post yuborish → 📢 Hammaga xabar**
- Yubormoqchi bo'lgan xabarni yozing — bot barcha ro'yxatdan o'tgan foydalanuvchilarga yuboradi

## 🔧 Texnik tafsilotlar

- **Framework**: Aiogram 3.4.1 (FSM, Router based)
- **Database**: SQLite (aiosqlite) — kichik va o'rta loyihalar uchun ideal, keyinchalik PostgreSQL'ga osongina ko'chiriladi
- **Middleware**: har bir xabar/callbackda avtomatik obuna tekshiruvi (adminlar uchun istisno)
- **File storage**: Telegram file_id orqali (serverda video/rasm saqlanmaydi, Telegram serverlarida saqlanadi — bu eng tejamkor usul)

## ⚠️ Eslatmalar

- Bot kanalga **admin huquqi** bilan qo'shilmasa, obuna tekshiruvi va post yuborish ishlamaydi
- `ADMIN_IDS` ro'yxatiga kiritilmagan foydalanuvchilar admin panelga kira olmaydi
- Katta hajmdagi (2GB+) video fayllarni yuborishda Telegram Bot API cheklovlariga e'tibor bering (standart 50MB, local Bot API server bilan kattalashtirish mumkin)
