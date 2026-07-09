# AMORIX — Telegram Tanishuv Boti

To'liq funksional tanishuv/tanishtiruv Telegram boti: foydalanuvchi ro'yxatdan o'tish
oqimi (jinsi → telefon → viloyat → tuman → yosh → bo'y → vazn → rasmlar → bio) va
kuchli admin panel bilan.

Bot tokeni va admin ID allaqachon `.env` fayliga kiritilgan — darhol ishga
tushirishingiz mumkin.

## 📁 Loyiha tuzilishi

```
amorix_bot/
├── main.py              # Botni ishga tushiruvchi fayl
├── config.py            # Sozlamalar (token, admin ID, yosh/bo'y chegaralari)
├── database.py          # SQLite bilan ishlash (aiosqlite)
├── keyboards.py         # Barcha inline/reply klaviaturalar
├── states.py            # FSM holatlari
├── locations.py         # Viloyat va tumanlar ro'yxati
├── utils.py             # Majburiy obuna tekshiruvi
├── handlers/
│   ├── user.py          # /start, ro'yxatdan o'tish, profil
│   └── admin.py         # Admin panel
├── requirements.txt
└── .env.example
```

## 🚀 O'rnatish

1. **Python 3.10+** kerak (tekshirish: `python3 --version`)

2. Loyihani ochib, kutubxonalarni o'rnating:
   ```bash
   cd amorix_bot
   pip install -r requirements.txt
   ```

3. `.env` fayli tokeningiz va admin ID'ingiz bilan **allaqachon to'ldirilgan**.
   Boshqa admin qo'shmoqchi bo'lsangiz, `ADMIN_IDS` qatoriga vergul bilan qo'shing:
   ```
   ADMIN_IDS=7992878834,yana_bir_id
   ```

4. Botni ishga tushiring:
   ```bash
   python3 main.py
   ```
   Konsolda "Bot ishga tushdi..." yozuvini ko'rsangiz — tayyor. Endi Telegram'da
   botingizga `/start` yozib sinab ko'ring.

## 👤 Foydalanuvchi oqimi

1. `/start` — botni ishga tushiradi
2. Jinsini tanlaydi (Erkak/Ayol)
3. Telefon raqamini tugma orqali yuboradi (faqat o'zining raqami qabul qilinadi)
4. Viloyatini tanlaydi (14 ta hudud: 12 viloyat + Toshkent shahri + Qoraqalpog'iston)
5. Tuman/shahrini tanlaydi
6. Yoshini kiritadi — **18 yoshdan kichiklar ro'yxatdan o'ta olmaydi**
7. Bo'yi (sm) va vazni (kg) ni kiritadi
8. Kamida 2 ta (ko'pi bilan 5 ta) rasm yuboradi
9. O'zi haqida qisqacha (2-3 gap) yozadi
10. Anketasi tayyor — `/profile` orqali istalgan vaqt ko'ra oladi

## 🛠 Admin panel

Admin (`.env`dagi `ADMIN_IDS`da ko'rsatilgan ID) botga `/admin` yozadi va quyidagilarni
qila oladi:

- **📊 Statistika** — jami/erkak/ayol/bugungi/bloklangan foydalanuvchilar soni
- **👥 Foydalanuvchilar** — ro'yxat (sahifalab), har birining to'liq profili va
  rasmlarini ko'rish, bloklash/blokdan chiqarish
- **📢 Broadcast** — barcha foydalanuvchilarga xabar (matn/rasm/video) yuborish
- **📺 Majburiy kanal** — foydalanuvchi botdan foydalanishdan oldin a'zo bo'lishi
  shart bo'lgan kanalni o'rnatish yoki o'chirish

  > ⚠️ Muhim: majburiy kanal ishlashi uchun **botni o'sha kanalga admin qilib
  > qo'shishingiz** kerak, aks holda bot a'zolikni tekshira olmaydi.

## 🗄 Ma'lumotlar bazasi

SQLite fayli (`bot_database.db`) loyiha papkasida avtomatik yaratiladi. Boshqa
serverga o'tkazish kerak bo'lsa, shu faylni ko'chirsangiz kifoya. Katta miqdordagi
foydalanuvchi (o'n minglab) kutilsa, PostgreSQL'ga o'tish tavsiya etiladi.

## ✏️ Sozlash va o'zgartirish

- **Viloyat/tuman ro'yxati**: `locations.py` faylidagi `REGIONS` lug'atini
  tahrirlang — bu real vaqtda geografik ma'lumot manbai emas, qo'lda yozilgan,
  shuning uchun kerak bo'lsa tuman qo'shish/o'chirish mumkin.
- **Yosh/bo'y/vazn chegaralari**: `config.py` dagi `MIN_AGE`, `MAX_HEIGHT` va
  hokazo qiymatlarni o'zgartiring.
- **Rasm soni**: `config.py` dagi `MIN_PHOTOS` / `MAX_PHOTOS`.

## 🔒 Xavfsizlik bo'yicha eslatmalar

- Bot 18 yoshdan kichik foydalanuvchilarni ro'yxatdan o'tkazmaydi (kiritilgan
  yoshga asoslanadi — bu standart, lekin mutlaq kafolat emas).
- Telefon raqami faqat Telegram'ning o'z "contact share" tugmasi orqali olinadi,
  bu boshqa birovning raqamini yuborishni qiyinlashtiradi.
- Production'da ishlatishdan oldin: foydalanuvchi kelishuvi/qoidalari (foydalanish
  shartlari), shikoyat qilish funksiyasi va moderatsiya jarayonini qo'shishni
  tavsiya qilaman — bular hozircha ushbu kodda yo'q.

## 🖥 Serverda doimiy ishlatish

Kompyuteringiz o'chganda bot ham to'xtaydi. Doimiy ishlashi uchun VPS (masalan
Timeweb, DigitalOcean) da `systemd` yoki `pm2`/`screen`/`tmux` orqali fon
jarayonida ishga tushiring, yoki `nohup python3 main.py &` bilan.
