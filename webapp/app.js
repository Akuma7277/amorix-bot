// ----------------- EARLY TELEGRAM WEBAPP INIT -----------------
const tg = window.Telegram?.WebApp;
if (tg) {
    try {
        tg.ready();
        tg.expand();
    } catch(e) {
        console.warn("Telegram WebApp init warning:", e);
    }
}


// =========================================================================
// KAIRYX INTERACTIVE REGISTRATION: DATE PICKER, CITY DROPDOWN & 6-PHOTO GRID
// =========================================================================

const KAIRYX_MONTHS = {
    uz: ['Yanvar', 'Fevral', 'Mart', 'Aprel', 'May', 'Iyun', 'Iyul', 'Avgust', 'Sentyabr', 'Oktyabr', 'Noyabr', 'Dekabr'],
    ru: ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'],
    en: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
};

const KAIRYX_CITIES = {
    uz: ["Toshkent", "Qoraqalpog'iston", "Andijon", "Buxoro", "Jizzax", "Qashqadaryo", "Navoiy", "Namangan", "Samarqand", "Surxondaryo", "Sirdaryo", "Toshkent viloyati", "Xorazm"],
    ru: ["Ташкент", "Каракалпакстан", "Андижан", "Бухара", "Джизак", "Кашкадарья", "Навои", "Наманган", "Самарканд", "Сурхандарья", "Сырдарья", "Ташкентская область", "Хорезм"],
    en: ["Tashkent", "Karakalpakstan", "Andijan", "Bukhara", "Jizzakh", "Kashkadarya", "Navoi", "Namangan", "Samarkand", "Surkhandarya", "Syrdarya", "Tashkent Region", "Khorezm"]
};

let kairyxDay = 1;
let kairyxMonth = 1;
let kairyxYear = 2004;
let kairyxSelectedCity = "Toshkent";
let kairyxPhotos = [];
let activeSlotIndex = 0;
let selectedRegGender = 'MALE';
let selectedRegTargetGender = 'FEMALE';
let selectedRegInterests = [];

// --- 1. UNIFORM & STABLE DATE OF BIRTH WHEEL PICKER ---
function openKairyxDobPicker() {
    renderKairyxWheels();
    const modal = document.getElementById('kairyxDobModal');
    if (modal) {
        modal.classList.remove('closing');
        modal.style.display = 'flex';
        modal.classList.add('show');
        // Smooth scroll selected items into center
        setTimeout(() => {
            document.querySelector('#kairyxWheelDay .kairyx-wheel-item.selected')?.scrollIntoView({ block: 'center', inline: 'nearest' });
            document.querySelector('#kairyxWheelMonth .kairyx-wheel-item.selected')?.scrollIntoView({ block: 'center', inline: 'nearest' });
            document.querySelector('#kairyxWheelYear .kairyx-wheel-item.selected')?.scrollIntoView({ block: 'center', inline: 'nearest' });
        }, 50);
    }
}

function closeKairyxDobPicker() {
    const modal = document.getElementById('kairyxDobModal');
    if (modal) {
        modal.classList.add('closing');
        setTimeout(() => {
            modal.style.display = 'none';
            modal.classList.remove('show', 'closing');
        }, 220);
    }
}

function renderKairyxWheels() {
    const lang = currentLang || 'uz';
    const months = KAIRYX_MONTHS[lang] || KAIRYX_MONTHS.uz;

    // Day column (1..31)
    const dayCol = document.getElementById('kairyxWheelDay');
    if (dayCol) {
        dayCol.innerHTML = '';
        for (let d = 1; d <= 31; d++) {
            const item = document.createElement('div');
            item.className = `kairyx-wheel-item ${d === kairyxDay ? 'selected' : ''}`;
            item.textContent = d;
            item.onclick = () => {
                selectKairyxDay(d);
                item.scrollIntoView({ behavior: 'smooth', block: 'center' });
            };
            dayCol.appendChild(item);
        }
    }

    // Month column (1..12)
    const monthCol = document.getElementById('kairyxWheelMonth');
    if (monthCol) {
        monthCol.innerHTML = '';
        months.forEach((mName, idx) => {
            const m = idx + 1;
            const item = document.createElement('div');
            item.className = `kairyx-wheel-item ${m === kairyxMonth ? 'selected' : ''}`;
            item.textContent = mName;
            item.onclick = () => {
                selectKairyxMonth(m);
                item.scrollIntoView({ behavior: 'smooth', block: 'center' });
            };
            monthCol.appendChild(item);
        });
    }

    // Year column (2008..1960)
    const yearCol = document.getElementById('kairyxWheelYear');
    if (yearCol) {
        yearCol.innerHTML = '';
        const currentYear = new Date().getFullYear();
        const maxYear = currentYear - 18; // 2008
        for (let y = maxYear; y >= 1960; y--) {
            const item = document.createElement('div');
            item.className = `kairyx-wheel-item ${y === kairyxYear ? 'selected' : ''}`;
            item.textContent = y;
            item.onclick = () => {
                selectKairyxYear(y);
                item.scrollIntoView({ behavior: 'smooth', block: 'center' });
            };
            yearCol.appendChild(item);
        }
    }
}

function selectKairyxDay(day) {
    kairyxDay = day;
    document.querySelectorAll('#kairyxWheelDay .kairyx-wheel-item').forEach(el => {
        el.classList.toggle('selected', parseInt(el.textContent) === day);
    });
}

function selectKairyxMonth(month) {
    kairyxMonth = month;
    const lang = currentLang || 'uz';
    const months = KAIRYX_MONTHS[lang] || KAIRYX_MONTHS.uz;
    const chosenName = months[month - 1];
    document.querySelectorAll('#kairyxWheelMonth .kairyx-wheel-item').forEach(el => {
        el.classList.toggle('selected', el.textContent === chosenName);
    });
}

function selectKairyxYear(year) {
    kairyxYear = year;
    document.querySelectorAll('#kairyxWheelYear .kairyx-wheel-item').forEach(el => {
        el.classList.toggle('selected', parseInt(el.textContent) === year);
    });
}

function confirmKairyxDob() {
    const today = new Date();
    let age = today.getFullYear() - kairyxYear;
    const mDiff = (today.getMonth() + 1) - kairyxMonth;
    if (mDiff < 0 || (mDiff === 0 && today.getDate() < kairyxDay)) {
        age--;
    }

    if (age < 18) {
        alert(currentLang === 'ru' ? "Вам должно быть не менее 18 лет!" : "Siz kamida 18 yoshda bo'lishingiz kerak!");
        return;
    }

    const lang = currentLang || 'uz';
    const months = KAIRYX_MONTHS[lang] || KAIRYX_MONTHS.uz;
    const mName = months[kairyxMonth - 1] || 'Yanvar';

    const dobDisplay = document.getElementById('dobDisplayText');
    if (dobDisplay) {
        dobDisplay.textContent = `${kairyxDay} ${mName} ${kairyxYear} (${age} ${lang === 'ru' ? 'лет' : 'yosh'})`;
    }

    const regAgeInput = document.getElementById('regAge');
    if (regAgeInput) regAgeInput.value = age;

    const bDayInput = document.getElementById('regBirthDay');
    if (bDayInput) bDayInput.value = kairyxDay;

    const bMonthInput = document.getElementById('regBirthMonth');
    if (bMonthInput) bMonthInput.value = kairyxMonth;

    const bYearInput = document.getElementById('regBirthYear');
    if (bYearInput) bYearInput.value = kairyxYear;

    closeKairyxDobPicker();
}

// --- 2. CITY DROPDOWN SELECTION ---
function openKairyxCityModal() {
    const list = document.getElementById('kairyxCityList');
    if (!list) return;
    const lang = currentLang || 'uz';
    const cities = KAIRYX_CITIES[lang] || KAIRYX_CITIES.uz;

    list.innerHTML = '';
    cities.forEach(city => {
        const item = document.createElement('div');
        const isSel = (city === kairyxSelectedCity || (kairyxSelectedCity === "Toshkent" && city === "Ташкент"));
        item.className = `kairyx-city-item ${isSel ? 'selected' : ''}`;
        item.innerHTML = `<span>${city}</span> ${isSel ? '<span class="checkmark">✓</span>' : ''}`;
        item.onclick = () => selectKairyxCity(city);
        list.appendChild(item);
    });

    const modal = document.getElementById('kairyxCityModal');
    if (modal) {
        modal.classList.remove('closing');
        modal.style.display = 'flex';
        modal.classList.add('show');
    }
}

function closeKairyxCityModal() {
    const modal = document.getElementById('kairyxCityModal');
    if (modal) {
        modal.classList.add('closing');
        setTimeout(() => {
            modal.style.display = 'none';
            modal.classList.remove('show', 'closing');
        }, 220);
    }
}

function selectKairyxCity(city) {
    kairyxSelectedCity = city;
    const txt = document.getElementById('selectedCityText');
    if (txt) txt.textContent = city;

    const regCityInput = document.getElementById('regCity');
    if (regCityInput) regCityInput.value = city;

    closeKairyxCityModal();
}

// --- 3. 6-PHOTO GRID LOGIC ---
function handlePhotoSlotClick(index) {
    activeSlotIndex = index;
    if (index < kairyxPhotos.length) {
        if (index > 0) {
            const chosen = kairyxPhotos.splice(index, 1)[0];
            kairyxPhotos.unshift(chosen);
            base64Photo = kairyxPhotos[0];
            renderKairyxPhotoGrid();
        }
    } else {
        const fileInput = document.getElementById('kairyxPhotoInput') || document.getElementById('regPhotoInput');
        if (fileInput) {
            fileInput.value = '';
            fileInput.click();
        }
    }
}

async function onKairyxPhotoSelected(event) {
    const file = event.target.files[0];
    if (!file) return;

    try {
        const compressed = await compressImage(file, 800, 0.75);
        if (activeSlotIndex < kairyxPhotos.length) {
            kairyxPhotos[activeSlotIndex] = compressed;
        } else {
            kairyxPhotos.push(compressed);
        }
        base64Photo = kairyxPhotos[0];
        renderKairyxPhotoGrid();
    } catch (err) {
        alert("Rasm yuklashda xatolik: " + err.message);
    }
}

function removeKairyxPhoto(index, event) {
    if (event) event.stopPropagation();
    if (index >= 0 && index < kairyxPhotos.length) {
        kairyxPhotos.splice(index, 1);
        base64Photo = kairyxPhotos.length > 0 ? kairyxPhotos[0] : "";
        renderKairyxPhotoGrid();
    }
}

function renderKairyxPhotoGrid() {
    const badge = document.getElementById('photoCountBadge');
    if (badge) badge.textContent = `${kairyxPhotos.length}/6`;

    for (let i = 0; i < 6; i++) {
        const slot = document.getElementById(`photoSlot${i}`);
        if (!slot) continue;

        if (i < kairyxPhotos.length) {
            slot.className = 'kairyx-photo-slot filled';
            slot.innerHTML = `
                <img src="${kairyxPhotos[i]}" alt="Photo ${i+1}">
                <button type="button" class="slot-del-btn" onclick="removeKairyxPhoto(${i}, event)">✕</button>
                ${i === 0 ? '<span class="slot-primary-badge">⭐ Asosiy</span>' : ''}
            `;
        } else {
            slot.className = 'kairyx-photo-slot';
            slot.innerHTML = '<span class="plus-icon">+</span>';
        }
    }
}

// --- 4. GENDER & TARGET GENDER SELECTION ---
function selectRegGender(g) {
    selectedRegGender = g;
    const m = document.getElementById('regGenderMale');
    const f = document.getElementById('regGenderFemale');
    const o = document.getElementById('regGenderOther');
    if (m) m.classList.toggle('selected', g === 'MALE');
    if (f) f.classList.toggle('selected', g === 'FEMALE');
    if (o) o.classList.toggle('selected', g === 'OTHER');
}

function selectRegTargetGender(tg) {
    selectedRegTargetGender = tg;
    const f = document.getElementById('regTargetFemale');
    const m = document.getElementById('regTargetMale');
    const a = document.getElementById('regTargetAny');
    if (f) f.classList.toggle('selected', tg === 'FEMALE');
    if (m) m.classList.toggle('selected', tg === 'MALE');
    if (a) a.classList.toggle('selected', tg === 'ANY');
}

// --- 5. INTERESTS INITIALIZATION ---
const AVAILABLE_INTERESTS = ["🎵 Musiqa", "🎬 Filmlar", "✈️ Sayohat", "⚽ Sport", "📚 Kitoblar", "🍳 Pazandalik", "🎮 Video o'yinlar", "📸 Fotografiya", "💻 Dasturlash", "🎨 San'at", "🚗 Avtomobillar", "☕ Qahva"];

function initRegInterests() {
    const container = document.getElementById('regInterestsContainer');
    if (!container) return;
    container.innerHTML = "";
    AVAILABLE_INTERESTS.forEach(intTag => {
        const span = document.createElement('span');
        span.className = "tag-badge tag-selectable" + (selectedRegInterests.includes(intTag) ? " selected" : "");
        span.textContent = intTag;
        span.onclick = () => {
            if (selectedRegInterests.includes(intTag)) {
                selectedRegInterests = selectedRegInterests.filter(i => i !== intTag);
                span.classList.remove('selected');
            } else {
                selectedRegInterests.push(intTag);
                span.classList.add('selected');
            }
        };
        container.appendChild(span);
    });
}

// --- 6. WIZARD STEP NAVIGATION ---
function nextRegStep(currStep) {
    if (currStep === 1) {
        // Step 1 -> Step 2
    } else if (currStep === 2) {
        const age = parseInt(document.getElementById('regAge')?.value || "0");
        if (!age || age < 18) {
            alert(currentLang === 'ru' ? "Сервис доступен только для 18+!" : "18 yoshdan katta bo'lish shart!");
            return;
        }
    } else if (currStep === 3) {
        const name = document.getElementById('regName')?.value.trim();
        const city = document.getElementById('regCity')?.value.trim();
        if (!name || !city) {
            alert(currentLang === 'ru' ? "Заполните имя и город!" : "Ism va shahringizni to'ldiring!");
            return;
        }
    } else if (currStep === 4) {
        // Step 4 -> Step 5
    } else if (currStep === 5) {
        if (!base64Photo && kairyxPhotos.length === 0) {
            alert(currentLang === 'ru' ? "Загрузите хотя бы одно фото (0/6)!" : "Kamida bitta fotosurat yuklang (0/6)!");
            return;
        }
        base64Photo = kairyxPhotos[0] || base64Photo;
    } else if (currStep === 6) {
        const bio = document.getElementById('regBio')?.value.trim();
        if (!bio) {
            alert(currentLang === 'ru' ? "Напишите о себе!" : "O'zingiz haqingizda yozing!");
            return;
        }
        const nameVal = document.getElementById('regName')?.value.trim() || "Ism";
        const ageVal = document.getElementById('regAge')?.value || "22";
        const cityVal = document.getElementById('regCity')?.value.trim() || "Toshkent";
        const summaryPhoto = document.getElementById('summaryPhoto');
        if (summaryPhoto) summaryPhoto.src = base64Photo || getDefaultAvatar(nameVal, selectedRegGender);
        const summaryNameAge = document.getElementById('summaryNameAge');
        if (summaryNameAge) summaryNameAge.textContent = `${nameVal}, ${ageVal}`;
        const gName = selectedRegGender === 'MALE' ? '👨 Erkak' : (selectedRegGender === 'FEMALE' ? '👩 Ayol' : '🌈 Boshqa');
        const summaryDetails = document.getElementById('summaryDetails');
        if (summaryDetails) summaryDetails.textContent = `${cityVal} • ${gName}`;
        const summaryBio = document.getElementById('summaryBio');
        if (summaryBio) summaryBio.textContent = bio;
    }

    const currentEl = document.getElementById(`regStep${currStep}`);
    const nextEl = document.getElementById(`regStep${currStep + 1}`);
    if (currentEl) currentEl.style.display = 'none';
    if (nextEl) nextEl.style.display = 'block';
    updateWizardHeader(currStep + 1);
    if (currStep + 1 === 6) initRegInterests();
}

function prevRegStep(currStep) {
    const currentEl = document.getElementById(`regStep${currStep}`);
    const prevEl = document.getElementById(`regStep${currStep - 1}`);
    if (currentEl) currentEl.style.display = 'none';
    if (prevEl) prevEl.style.display = 'block';
    updateWizardHeader(currStep - 1);
}

function updateWizardHeader(step) {
    const t = I18N[currentLang] || I18N.uz;
    const titles = [t.step1Title, t.step2Title, t.step3Title, t.step4Title, t.step5Title, t.step6Title, t.step7Title];
    const titleEl = document.getElementById('wizardStepTitle');
    if (titleEl) titleEl.textContent = titles[step - 1] || `Qadam ${step}`;
    const countEl = document.getElementById('wizardStepCount');
    if (countEl) countEl.textContent = `${step} / 7`;
    const barEl = document.getElementById('wizardProgressBar');
    if (barEl) barEl.style.width = `${(step / 7) * 100}%`;
}


const API_URL = (window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1"))
    ? window.location.origin
    : "https://amorix-bot-production.up.railway.app";

// ----------------- DEFAULT AVATAR (BASE64 ENCODED TO PREVENT DOM LEAKS) -----------------
function getDefaultAvatar(name = "K", gender = "OTHER") {
    const initial = (name && typeof name === 'string' && name.trim().length > 0) ? name.trim().charAt(0).toUpperCase() : "K";
    const bg1 = gender === 'MALE' ? '#05d9e8' : (gender === 'FEMALE' ? '#ff2a6d' : '#9b00e8');
    const bg2 = gender === 'MALE' ? '#7928ca' : (gender === 'FEMALE' ? '#9b00e8' : '#ff007a');
    
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400"><defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="${bg1}"/><stop offset="100%" stop-color="${bg2}"/></linearGradient></defs><rect width="400" height="400" fill="url(#g)"/><circle cx="200" cy="155" r="65" fill="rgba(255,255,255,0.22)"/><path d="M85 360 C85 260, 315 260, 315 360 Z" fill="rgba(255,255,255,0.22)"/><text x="200" y="175" text-anchor="middle" fill="#ffffff" font-size="64" font-family="sans-serif" font-weight="bold">${initial}</text></svg>`;
    return "data:image/svg+xml;base64," + btoa(unescape(encodeURIComponent(svg)));
}

window.handleImgError = function(img, name = "K", gender = "OTHER") {
    img.onerror = null;
    img.src = getDefaultAvatar(name, gender);
};

// ----------------- MULTI-LANGUAGE I18N (UZ, RU, EN) -----------------
let currentLang = localStorage.getItem("kairyx_lang") || "uz";

const I18N = {
    uz: {
        loadingTitle: "Kairyx yuklanmoqda...",
        loadingSub: "Xavfsiz sessiya tekshirilmoqda",
        step1Title: "Qadam 1: Tilni tanlash",
        step2Title: "Qadam 2: Yoshni tasdiqlash",
        step3Title: "Qadam 3: Shaxsiy ma'lumotlar",
        step4Title: "Qadam 4: Jinsingiz va Qidiruv",
        step5Title: "Qadam 5: Profil surati",
        step6Title: "Qadam 6: Bio va Qiziqishlar",
        step7Title: "Qadam 7: Anketani tasdiqlash",
        reg1Title: "Tilni tanlang / Select Language 🌐",
        reg1Sub: "Ilovadan qaysi tilda foydalanmoqchisiz?",
        reg2Title: "Kairyx-ga xush kelibsiz! 👋",
        reg2Sub: "Platformamiz faqat voyaga yetgan (18+) foydalanuvchilar uchun mo'ljallangan.",
        lblAge: "Tug'ilgan yoshingiz *",
        reg3Title: "O'zingizni tanishtiring ✨",
        lblName: "Ismingiz *",
        namePlaceholder: "Ismingizni kiriting",
        lblCity: "Shahringiz *",
        cityPlaceholder: "Masalan: Toshkent",
        reg4Title: "Jinsingiz va Qidiruv 🚻",
        lblMyGender: "Sizning jinsingiz:",
        genderMale: "Erkak",
        genderFemale: "Ayol",
        genderOther: "Noma'lum",
        lblTargetGender: "Kimni qidiryapsiz?",
        targetFemale: "Ayol",
        targetMale: "Erkak",
        targetAny: "Noma'lum",
        reg5Title: "Profil surati 📸",
        reg5Sub: "Yuzingiz aniq ko'ringan sifatli rasmingizni yuklang.",
        photoPlaceholder: "Rasm tanlash",
        reg6Title: "Qiziqishlar va Bio 🎨",
        lblBio: "O'zingiz haqingizda",
        bioPlaceholder: "Nimaga qiziqasiz, kimni izlayapsiz...",
        lblInterests: "Qiziqishlaringizni tanlang:",
        reg7Title: "Anketani tasdiqlash 📋",
        termsAgree: "Men",
        termsLink: "Foydalanish Qoidalari",
        termsEnd: "ga roziman.",
        btnSubmit: "Arizani yuborish 🚀",
        btnSubmitting: "Yuborilmoqda...",
        btnNext: "Davom etish ➔",
        btnBack: "Orqaga",
        pendingTitle: "Arizangiz ko'rib chiqilmoqda",
        pendingSub: "Profilingiz moderatorlar tekshiruvida. Tasdiqlangach sizga to'liq kirish ochiladi.",
        btnPendingRefresh: "🔄 Qayta tekshirish",
        rejectedTitle: "Arizangiz rad etildi",
        rejectedSub: "Anketangiz Kairyx standartlariga mos kelmadi.",
        bannedTitle: "Profil bloklangan",
        bannedSub: "Qoidalarni buzganlik sababli ushbu hisob muzlatilgan.",
        errorTitle: "Aloqa uzildi",
        btnRetry: "Qayta urinish",
        discoverTitle: "Yangi anketalar",
        btnFilter: "⚡ Filtrlash",
        likesHeader: "Sizga Like bosganlar ⭐",
        matchesHeader: "O'zaro Juftliklar 💖",
        chatsHeader: "Suhbatlar 💬",
        myBioLabel: "O'zim haqimda:",
        myInterestsLabel: "Qiziqishlarim:",
        btnEditProfile: "✏️ Profilni tahrirlash",
        menuLang: "🌐 Tilni o'zgartirish",
        menuBlocked: "🚫 Bloklangan foydalanuvchilar",
        menuRules: "ℹ️ Qoidalar va Xavfsizlik",
        menuDelete: "🗑️ Hisobni o'chirish",
        settingsTitle: "Sozlamalar ⚙️",
        noProfiles: "Hozircha anketalar tugadi",
        noProfilesSub: "Yangi a'zolar qo'shilgach bu yerda ko'rinadi.",
        noLikes: "Hozircha sizga Like bosganlar yo'q.",
        noMatches: "Hozircha juftliklar yo'q. Discover bo'limida Like bosing!",
        noChats: "Suhbatlar mavjud emas.",
        rulesList: [
            "Faqat 18 yoshdan oshganlar foydalanishi mumkin.",
            "Haqiqiy fotosurat va ism kiritilishi talab etiladi.",
            "Spam, reklama, firibgarlik va nojo'ya xatti-harakatlar uchun akkaunt doimiy bloklanadi.",
            "Ikkala tomon ham Like bossagina shaxsiy chat ochiladi."
        ]
    },
    ru: {
        loadingTitle: "Загрузка Kairyx...",
        loadingSub: "Проверка защищенной сессии",
        step1Title: "Шаг 1: Выбор языка",
        step2Title: "Шаг 2: Подтверждение возраста",
        step3Title: "Шаг 3: Личные данные",
        step4Title: "Шаг 4: Пол и предпочтения",
        step5Title: "Шаг 5: Фото профиля",
        step6Title: "Шаг 6: О себе и интересы",
        step7Title: "Шаг 7: Подтверждение анкеты",
        reg1Title: "Выберите язык / Tilni tanlang 🌐",
        reg1Sub: "На каком языке вам удобнее продолжить?",
        reg2Title: "Добро пожаловать в Kairyx! 👋",
        reg2Sub: "Наша платформа предназначена только для совершеннолетних (18+).",
        lblAge: "Ваш возраст *",
        reg3Title: "Расскажите о себе ✨",
        lblName: "Ваше имя *",
        namePlaceholder: "Введите ваше имя",
        lblCity: "Ваш город *",
        cityPlaceholder: "Например: Ташкент",
        reg4Title: "Пол и предпочтения 🚻",
        lblMyGender: "Ваш пол:",
        genderMale: "Мужской",
        genderFemale: "Женский",
        genderOther: "Другой",
        lblTargetGender: "Кого вы ищете?",
        targetFemale: "Девушек",
        targetMale: "Парней",
        targetAny: "Не важно",
        reg5Title: "Фото профиля 📸",
        reg5Sub: "Загрузите качественное фото, где хорошо видно лицо.",
        photoPlaceholder: "Выбрать фото",
        reg6Title: "Интересы и О себе 🎨",
        lblBio: "О себе",
        bioPlaceholder: "Чем увлекаетесь, кого ищете...",
        lblInterests: "Выберите ваши интересы:",
        reg7Title: "Подтверждение анкеты 📋",
        termsAgree: "Я принимаю",
        termsLink: "Правила использования",
        termsEnd: ".",
        btnSubmit: "Отправить анкету 🚀",
        btnSubmitting: "Отправка...",
        btnNext: "Продолжить ➔",
        btnBack: "Назад",
        pendingTitle: "Ваша анкета на проверке",
        pendingSub: "Профиль находится на модерации. После одобрения вам откроется полный доступ.",
        btnPendingRefresh: "🔄 Проверить статус",
        rejectedTitle: "Анкета отклонена",
        rejectedSub: "Ваша анкета не соответствует стандартам качества Kairyx.",
        bannedTitle: "Профиль заблокирован",
        bannedSub: "Аккаунт заблокирован за нарушение правил сообщества.",
        errorTitle: "Связь потеряна",
        btnRetry: "Повторить попытку",
        discoverTitle: "Новые анкеты",
        btnFilter: "⚡ Фильтры",
        likesHeader: "Кому вы понравились ⭐",
        matchesHeader: "Взаимные симпатии 💖",
        chatsHeader: "Сообщения 💬",
        myBioLabel: "О себе:",
        myInterestsLabel: "Мои интересы:",
        btnEditProfile: "✏️ Редактировать профиль",
        menuLang: "🌐 Сменить язык",
        menuBlocked: "🚫 Заблокированные пользователи",
        menuRules: "ℹ️ Правила и безопасность",
        menuDelete: "🗑️ Удалить аккаунт",
        settingsTitle: "Настройки ⚙️",
        noProfiles: "Анкеты закончились",
        noProfilesSub: "Новые пользователи появятся здесь позже.",
        noLikes: "Пока никто не поставил вам лайк.",
        noMatches: "Симпатий пока нет. Ставьте Like в разделе Discover!",
        noChats: "Диалогов пока нет.",
        rulesList: [
            "Сервис доступен только для лиц старше 18 лет.",
            "Требуется настоящее фото и реальное имя.",
            "Спам, оскорбления, мошенничество и непристойное поведение караются вечным баном.",
            "Личный чат открывается только при взаимной симпатии."
        ]
    },
    en: {
        loadingTitle: "Loading Kairyx...",
        loadingSub: "Verifying secure session",
        step1Title: "Step 1: Select Language",
        step2Title: "Step 2: Age Verification",
        step3Title: "Step 3: Personal Information",
        step4Title: "Step 4: Gender & Preferences",
        step5Title: "Step 5: Profile Photo",
        step6Title: "Step 6: Bio & Interests",
        step7Title: "Step 7: Confirmation",
        reg1Title: "Select Language 🌐",
        reg1Sub: "Which language do you prefer to use?",
        reg2Title: "Welcome to Kairyx! 👋",
        reg2Sub: "Our platform is exclusively for adults (18+).",
        lblAge: "Your Age *",
        reg3Title: "Introduce Yourself ✨",
        lblName: "Your Name *",
        namePlaceholder: "Enter your name",
        lblCity: "Your City *",
        cityPlaceholder: "e.g. Tashkent, London",
        reg4Title: "Gender & Preferences 🚻",
        lblMyGender: "Your Gender:",
        genderMale: "Male",
        genderFemale: "Female",
        genderOther: "Other",
        lblTargetGender: "Looking for:",
        targetFemale: "Women",
        targetMale: "Men",
        targetAny: "Anyone",
        reg5Title: "Profile Photo 📸",
        reg5Sub: "Upload a clear photo where your face is well visible.",
        photoPlaceholder: "Choose photo",
        reg6Title: "Bio & Interests 🎨",
        lblBio: "About You",
        bioPlaceholder: "What are you looking for...",
        lblInterests: "Select your interests:",
        reg7Title: "Confirm Profile 📋",
        termsAgree: "I agree to the",
        termsLink: "Terms of Service",
        termsEnd: ".",
        btnSubmit: "Submit Profile 🚀",
        btnSubmitting: "Submitting...",
        btnNext: "Continue ➔",
        btnBack: "Back",
        pendingTitle: "Profile Under Review",
        pendingSub: "Your profile is being reviewed by moderators. Full access will unlock upon approval.",
        btnPendingRefresh: "🔄 Check Status",
        rejectedTitle: "Application Rejected",
        rejectedSub: "Your profile did not meet Kairyx quality standards.",
        bannedTitle: "Profile Suspended",
        bannedSub: "This account has been suspended for rule violations.",
        errorTitle: "Connection Lost",
        btnRetry: "Retry",
        discoverTitle: "Discover New People",
        btnFilter: "⚡ Filters",
        likesHeader: "Who Liked You ⭐",
        matchesHeader: "Mutual Matches 💖",
        chatsHeader: "Conversations 💬",
        myBioLabel: "About Me:",
        myInterestsLabel: "My Interests:",
        btnEditProfile: "✏️ Edit Profile",
        menuLang: "🌐 Change Language",
        menuBlocked: "🚫 Blocked Users",
        menuRules: "ℹ️ Rules & Safety",
        menuDelete: "🗑️ Deactivate Account",
        settingsTitle: "Settings ⚙️",
        noProfiles: "No more profiles right now",
        noProfilesSub: "New members will appear here soon.",
        noLikes: "No likes yet.",
        noMatches: "No matches yet. Swipe and like profiles in Discover!",
        noChats: "No conversations yet.",
        rulesList: [
            "You must be 18 years or older to use Kairyx.",
            "Real photo and genuine identity are strictly required.",
            "Spam, harassment, scams, and illicit behavior result in a permanent ban.",
            "Private chat unlocks only upon mutual like."
        ]
    }
};

function applyTranslations() {
    const t = I18N[currentLang] || I18N.uz;
    if (document.getElementById('txtLoadingTitle')) document.getElementById('txtLoadingTitle').textContent = t.loadingTitle;
    if (document.getElementById('txtLoadingSub')) document.getElementById('txtLoadingSub').textContent = t.loadingSub;
    if (document.getElementById('txtRegStep1Title')) document.getElementById('txtRegStep1Title').textContent = t.reg1Title;
    if (document.getElementById('txtRegStep1Sub')) document.getElementById('txtRegStep1Sub').textContent = t.reg1Sub;
    if (document.getElementById('btnRegNext1')) document.getElementById('btnRegNext1').textContent = t.btnNext;

    if (document.getElementById('txtRegStep2Title')) document.getElementById('txtRegStep2Title').textContent = t.reg2Title;
    if (document.getElementById('txtRegStep2Sub')) document.getElementById('txtRegStep2Sub').textContent = t.reg2Sub;
    if (document.getElementById('lblRegAge')) document.getElementById('lblRegAge').textContent = t.lblAge;
    if (document.getElementById('btnRegBack2')) document.getElementById('btnRegBack2').textContent = t.btnBack;
    if (document.getElementById('btnRegNext2')) document.getElementById('btnRegNext2').textContent = t.btnNext;

    if (document.getElementById('txtRegStep3Title')) document.getElementById('txtRegStep3Title').textContent = t.reg3Title;
    if (document.getElementById('lblRegName')) document.getElementById('lblRegName').textContent = t.lblName;
    if (document.getElementById('regName')) document.getElementById('regName').placeholder = t.namePlaceholder;
    if (document.getElementById('lblRegCity')) document.getElementById('lblRegCity').textContent = t.lblCity;
    if (document.getElementById('regCity')) document.getElementById('regCity').placeholder = t.cityPlaceholder;
    if (document.getElementById('btnRegBack3')) document.getElementById('btnRegBack3').textContent = t.btnBack;
    if (document.getElementById('btnRegNext3')) document.getElementById('btnRegNext3').textContent = t.btnNext;

    if (document.getElementById('txtRegStep4Title')) document.getElementById('txtRegStep4Title').textContent = t.reg4Title;
    if (document.getElementById('lblMyGender')) document.getElementById('lblMyGender').textContent = t.lblMyGender;
    if (document.getElementById('txtGenderMale')) document.getElementById('txtGenderMale').textContent = t.genderMale;
    if (document.getElementById('txtGenderFemale')) document.getElementById('txtGenderFemale').textContent = t.genderFemale;
    if (document.getElementById('txtGenderOther')) document.getElementById('txtGenderOther').textContent = t.genderOther;
    if (document.getElementById('lblTargetGender')) document.getElementById('lblTargetGender').textContent = t.lblTargetGender;
    if (document.getElementById('txtTargetFemale')) document.getElementById('txtTargetFemale').textContent = t.targetFemale;
    if (document.getElementById('txtTargetMale')) document.getElementById('txtTargetMale').textContent = t.targetMale;
    if (document.getElementById('txtTargetAny')) document.getElementById('txtTargetAny').textContent = t.targetAny;
    if (document.getElementById('btnRegBack4')) document.getElementById('btnRegBack4').textContent = t.btnBack;
    if (document.getElementById('btnRegNext4')) document.getElementById('btnRegNext4').textContent = t.btnNext;

    if (document.getElementById('txtRegStep5Title')) document.getElementById('txtRegStep5Title').textContent = t.reg5Title;
    if (document.getElementById('txtRegStep5Sub')) document.getElementById('txtRegStep5Sub').textContent = t.reg5Sub;
    if (document.getElementById('txtPhotoPlaceholder')) document.getElementById('txtPhotoPlaceholder').textContent = t.photoPlaceholder;
    if (document.getElementById('btnRegBack5')) document.getElementById('btnRegBack5').textContent = t.btnBack;
    if (document.getElementById('btnRegNext5')) document.getElementById('btnRegNext5').textContent = t.btnNext;

    if (document.getElementById('txtRegStep6Title')) document.getElementById('txtRegStep6Title').textContent = t.reg6Title;
    if (document.getElementById('lblRegBio')) document.getElementById('lblRegBio').textContent = t.lblBio;
    if (document.getElementById('regBio')) document.getElementById('regBio').placeholder = t.bioPlaceholder;
    if (document.getElementById('lblRegInterests')) document.getElementById('lblRegInterests').textContent = t.lblInterests;
    if (document.getElementById('btnRegBack6')) document.getElementById('btnRegBack6').textContent = t.btnBack;
    if (document.getElementById('btnRegNext6')) document.getElementById('btnRegNext6').textContent = t.btnNext;

    if (document.getElementById('txtRegStep7Title')) document.getElementById('txtRegStep7Title').textContent = t.reg7Title;
    if (document.getElementById('txtTermsAgree')) document.getElementById('txtTermsAgree').textContent = t.termsAgree;
    if (document.getElementById('txtTermsLink')) document.getElementById('txtTermsLink').textContent = t.termsLink;
    if (document.getElementById('txtTermsEnd')) document.getElementById('txtTermsEnd').textContent = t.termsEnd;
    if (document.getElementById('btnRegBack7')) document.getElementById('btnRegBack7').textContent = t.btnBack;
    if (document.getElementById('btnSubmitReg')) document.getElementById('btnSubmitReg').textContent = t.btnSubmit;

    if (document.getElementById('txtPendingTitle')) document.getElementById('txtPendingTitle').textContent = t.pendingTitle;
    if (document.getElementById('txtPendingSub')) document.getElementById('txtPendingSub').textContent = t.pendingSub;
    if (document.getElementById('btnPendingRefresh')) document.getElementById('btnPendingRefresh').textContent = t.btnPendingRefresh;

    if (document.getElementById('txtRejectedTitle')) document.getElementById('txtRejectedTitle').textContent = t.rejectedTitle;
    if (document.getElementById('txtRejectedSub')) document.getElementById('txtRejectedSub').textContent = t.rejectedSub;

    if (document.getElementById('txtBannedTitle')) document.getElementById('txtBannedTitle').textContent = t.bannedTitle;
    if (document.getElementById('txtBannedSub')) document.getElementById('txtBannedSub').textContent = t.bannedSub;

    if (document.getElementById('txtErrorTitle')) document.getElementById('txtErrorTitle').textContent = t.errorTitle;
    if (document.getElementById('btnRetry')) document.getElementById('btnRetry').textContent = t.btnRetry;

    if (document.getElementById('txtDiscoverTitle')) document.getElementById('txtDiscoverTitle').textContent = t.discoverTitle;
    if (document.getElementById('txtBtnFilter')) document.getElementById('txtBtnFilter').textContent = t.btnFilter;
    if (document.getElementById('txtLikesHeader')) document.getElementById('txtLikesHeader').textContent = t.likesHeader;
    if (document.getElementById('txtMatchesHeader')) document.getElementById('txtMatchesHeader').textContent = t.matchesHeader;
    if (document.getElementById('txtChatsHeader')) document.getElementById('txtChatsHeader').textContent = t.chatsHeader;
    if (document.getElementById('lblMyBio')) document.getElementById('lblMyBio').textContent = t.myBioLabel;
    if (document.getElementById('lblMyInterests')) document.getElementById('lblMyInterests').textContent = t.myInterestsLabel;
    if (document.getElementById('btnEditProfile')) document.getElementById('btnEditProfile').textContent = t.btnEditProfile;

    const langNames = { uz: "O'zbekcha", ru: "Русский", en: "English" };
    if (document.getElementById('modalSettingLangVal')) document.getElementById('modalSettingLangVal').textContent = (langNames[currentLang] || "O'zbekcha") + " ➔";

    const rulesUl = document.getElementById('rulesListContent');
    if (rulesUl) {
        rulesUl.innerHTML = "";
        t.rulesList.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item;
            rulesUl.appendChild(li);
        });
    }
}

function selectRegLanguage(lang) {
    currentLang = lang;
    localStorage.setItem("kairyx_lang", lang);
    document.getElementById('optLangUz').classList.toggle('selected', lang === 'uz');
    document.getElementById('optLangRu').classList.toggle('selected', lang === 'ru');
    document.getElementById('optLangEn').classList.toggle('selected', lang === 'en');
    document.getElementById('langCheckUz').style.display = lang === 'uz' ? 'block' : 'none';
    document.getElementById('langCheckRu').style.display = lang === 'ru' ? 'block' : 'none';
    document.getElementById('langCheckEn').style.display = lang === 'en' ? 'block' : 'none';
    applyTranslations();
}

function setAppLanguage(lang) {
    currentLang = lang;
    localStorage.setItem("kairyx_lang", lang);
    applyTranslations();
    closeLanguageModal();
}

// ----------------- GLOBAL STATE & AUTH -----------------

let currentUser = null;
let isAdminUser = false;
let currentView = "";
let previousViewBeforeAdmin = "approvedScreen";
let base64Photo = "";
let base64ReceiptPhoto = "";
let selectedEditInterests = [];
let currentBillingPeriod = "monthly";
let selectedCheckoutPlan = "PREMIUM";
let selectedCheckoutAmount = 49000;
let editBase64Photo = "";

let discoverProfiles = [];
let currentDiscoverIndex = 0;
let previousSwipeProfile = null;
let activeTargetUser = null;
let activeMatchId = null;
let chatPollInterval = null;

function getHeaders() {
    const headers = { "Content-Type": "application/json" };
    if (tg && tg.initData) {
        headers["X-TG-Init-Data"] = tg.initData;
        headers["Authorization"] = "Bearer " + tg.initData;
    } else {
        headers["X-TG-Init-Data"] = "mock_user";
        headers["Authorization"] = "Bearer mock_user";
    }
    return headers;
}

function getQueryParams() {
    const queryParams = new URLSearchParams();
    if (tg && tg.initData) {
        queryParams.append("initData", tg.initData);
    } else {
        queryParams.append("initData", isAdminUser ? "mock_admin" : "mock_user");
    }
    return queryParams.toString();
}

function showView(viewId) {
    currentView = viewId;
    const views = ['verifyingScreen', 'registrationScreen', 'pendingScreen', 'approvedScreen', 'adminScreen', 'rejectedScreen', 'bannedScreen', 'errorScreen'];
    views.forEach(v => {
        const el = document.getElementById(v);
        if (el) el.style.display = (v === viewId) ? 'block' : 'none';
    });

    const adminBtn = document.getElementById('btnHeaderAdmin');
    if (adminBtn) adminBtn.style.display = isAdminUser ? 'block' : 'none';
}

// ----------------- STANDARDIZED SESSION STATE MACHINE & NORMALIZER -----------------
window.sessionState = 'IDLE';

function forceEnterApp() {
    showView('approvedScreen');
    if (typeof populateMyProfile === 'function') populateMyProfile();
    if (typeof switchTab === 'function') switchTab('viewDiscover');
} // IDLE | LOADING | READY | ERROR
let isSessionRequestInFlight = false;

function normalizeSession(payload) {
    if (!payload || payload.success !== true || !payload.user) {
        throw new Error("INVALID_SESSION_RESPONSE");
    }
    const status = String(
        payload.user_status ?? payload.user.status ?? ""
    ).trim().toUpperCase();

    if (!status) throw new Error("SESSION_STATUS_MISSING");

    return {
        ...payload,
        normalizedStatus: status,
        user: payload.user
    };
}

async function verifySession() {
    if (isSessionRequestInFlight) {
        console.warn("[SESSION] Request already in flight, skipping duplicate.");
        return;
    }

    window.sessionState = 'LOADING';
    isSessionRequestInFlight = true;
    showView('verifyingScreen');
    applyTranslations();

    const requestId = "REQ-" + Math.random().toString(36).substring(2, 8).toUpperCase();
    const loadingSub = document.getElementById('txtLoadingSub');
    if (loadingSub) {
        loadingSub.innerHTML = `Xavfsiz sessiya tekshirilmoqda...<br><span style="font-size:11px; opacity:0.6;">Ref: ${requestId}</span>`;
    }

    const rawInitData = tg?.initData || "";
    const hasInitData = rawInitData && rawInitData.length > 5;

    console.info(`[AUTH] Init check - TG Available: ${!!tg}, InitData Present: ${hasInitData} (${rawInitData.length} chars)`);

    // If outside Telegram and no query initData
    if (!hasInitData && !isAdminUser && !window.location.search.includes("initData=")) {
        window.sessionState = 'ERROR';
        isSessionRequestInFlight = false;
        if (loadingSub) {
            loadingSub.innerHTML = `
                <div style="background: rgba(255, 71, 87, 0.12); border: 1px solid rgba(255, 71, 87, 0.3); border-radius: 12px; padding: 14px; margin-top: 15px;">
                    <p style="color: #ff6b81; font-size: 13px; margin: 0 0 10px 0; font-weight: 500;">
                        Telegram sessiyasi topilmadi. Mini App’ni Telegram bot (@Ka1ryx_bot) ichidan qayta oching.
                    </p>
                    <div style="display: flex; gap: 8px; justify-content: center;">
                        <a href="https://t.me/Ka1ryx_bot" class="btn-primary-gradient" style="font-size: 12px; padding: 8px 16px; border-radius: 10px; text-decoration: none;">🤖 Botni ochish</a>
                        <button onclick="forceEnterApp()" class="btn-subtle" style="font-size: 12px; padding: 8px 14px; border-radius: 10px;">⚡ Demo rejim</button>
                    </div>
                </div>
            `;
        }
        return;
    }

    const controller = new AbortController();
    const abortTimeout = setTimeout(() => {
        controller.abort();
    }, 15000);

    try {
        const response = await fetch(`${API_URL}/api/session?${getQueryParams()}`, {
            method: "GET",
            headers: {
                "Accept": "application/json",
                ...getHeaders(),
                "X-Request-ID": requestId
            },
            signal: controller.signal
        });

        clearTimeout(abortTimeout);

        if (response.status === 401) {
            window.sessionState = 'ERROR';
            if (loadingSub) {
                loadingSub.innerHTML = `
                    <div style="color: #ff6b81; margin-top: 12px;">
                        <p style="font-size: 13px; margin: 0 0 10px 0;">⚠️ Sessiya muddati tugagan yoki tasdiqlanmadi.</p>
                        <button onclick="verifySession()" class="btn-primary-gradient" style="font-size: 12px; padding: 8px 18px; border-radius: 10px;">🔄 Qayta urinish</button>
                    </div>
                `;
            }
            return;
        }

        if (response.status === 403) {
            window.sessionState = 'ERROR';
            showView('bannedScreen');
            return;
        }

        if (!response.ok) {
            throw new Error(`HTTP_${response.status}`);
        }

        const rawPayload = await response.json();
        const session = normalizeSession(rawPayload);

        window.sessionState = 'READY';
        currentUser = session.user;
        const status = session.normalizedStatus;
        isAdminUser = (currentUser?.telegram_id === 7992878834) || !!session.is_admin;

        if (session.unread_notifications > 0) {
            const b = document.getElementById('notifBadge');
            if (b) {
                b.textContent = session.unread_notifications;
                b.style.display = 'flex';
            }
        }

        if (session.likes_received_count > 0) {
            const lb = document.getElementById('navLikesBadge');
            if (lb) {
                lb.textContent = session.likes_received_count;
                lb.style.display = 'flex';
            }
        }

        const streakEl = document.getElementById('headerStreakCount');
        if (streakEl) streakEl.textContent = currentUser?.streak_days || 0;

        const adminBtn = document.getElementById('btnHeaderAdmin');
        if (adminBtn) {
            adminBtn.style.display = (currentUser?.telegram_id === 7992878834 || isAdminUser) ? 'flex' : 'none';
        }

        // Strict routing by normalized status
        if (status === 'DRAFT') {
            showView('registrationScreen');
            if (typeof initRegInterests === 'function') initRegInterests();
        } else if (status === 'PENDING_APPROVAL') {
            showView('pendingScreen');
        } else if (status === 'REJECTED') {
            showView('rejectedScreen');
        } else if (status === 'BANNED' || status === 'DELETED') {
            showView('bannedScreen');
        } else if (status === 'APPROVED' || status === 'ACTIVE') {
            showView('approvedScreen');
            if (typeof populateMyProfile === 'function') populateMyProfile();
            if (typeof switchTab === 'function') switchTab('viewDiscover');
        } else {
            throw new Error(`UNKNOWN_STATUS_${status}`);
        }
    } catch (err) {
        clearTimeout(abortTimeout);
        window.sessionState = 'ERROR';
        console.error(`[AUTH_ERROR] Request ID: ${requestId}, Reason:`, err);

        if (loadingSub) {
            loadingSub.innerHTML = `
                <div style="background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 14px; margin-top: 15px;">
                    <p style="color: #ff6b81; font-size: 13px; margin: 0 0 6px 0; font-weight: 600;">
                        Serverga ulanishda muammo yuz berdi.
                    </p>
                    <p style="color: var(--text-muted); font-size: 11px; margin: 0 0 12px 0;">
                        Error ID: ${requestId} (${err.name === 'AbortError' ? 'TIMEOUT_15S' : err.message})
                    </p>
                    <div style="display: flex; gap: 8px; justify-content: center;">
                        <button onclick="verifySession()" class="btn-primary-gradient" style="font-size: 12px; padding: 8px 18px; border-radius: 10px;">🔄 Qayta urinish</button>
                        <button onclick="forceEnterApp()" class="btn-subtle" style="font-size: 12px; padding: 8px 14px; border-radius: 10px;">⚡ Demo rejim</button>
                    </div>
                </div>
            `;
        }
    } finally {
        isSessionRequestInFlight = false;
    }
}


function nextRegStep(currStep) {
    if (currStep === 2) {
        const age = parseInt(document.getElementById('regAge').value);
        if (!age || age < 18) {
            alert(currentLang === 'ru' ? "Сервис доступен только для 18+!" : "18 yoshdan katta bo'lish shart!");
            return;
        }
    } else if (currStep === 3) {
        const name = document.getElementById('regName').value.trim();
        const city = document.getElementById('regCity').value.trim();
        if (!name || !city) {
            alert(currentLang === 'ru' ? "Заполните имя и город!" : "Ism va shahringizni to'ldiring!");
            return;
        }
    } else if (currStep === 5) {
        if (!base64Photo && kairyxPhotos.length === 0) {
            alert(currentLang === 'ru' ? "Загрузите хотя бы одно фото (0/6)!" : "Kamida bitta fotosurat yuklang (0/6)!");
            return;
        }
        base64Photo = kairyxPhotos[0] || base64Photo;
    } else if (currStep === 6) {
        const bio = document.getElementById('regBio').value.trim();
        if (!bio) {
            alert(currentLang === 'ru' ? "Напишите о себе!" : "O'zingiz haqingizda yozing!");
            return;
        }
        const nameVal = document.getElementById('regName').value.trim();
        document.getElementById('summaryPhoto').src = base64Photo || getDefaultAvatar(nameVal, selectedRegGender);
        document.getElementById('summaryNameAge').textContent = `${nameVal}, ${document.getElementById('regAge').value}`;
        const gName = selectedRegGender === 'MALE' ? '👨 Erkak' : (selectedRegGender === 'FEMALE' ? '👩 Ayol' : '🌈 Noma`lum');
        document.getElementById('summaryDetails').textContent = `${document.getElementById('regCity').value.trim()} • ${gName}`;
        document.getElementById('summaryBio').textContent = bio;
    }

    document.getElementById(`regStep${currStep}`).style.display = 'none';
    document.getElementById(`regStep${currStep + 1}`).style.display = 'block';
    updateWizardHeader(currStep + 1);
}

function prevRegStep(currStep) {
    document.getElementById(`regStep${currStep}`).style.display = 'none';
    document.getElementById(`regStep${currStep - 1}`).style.display = 'block';
    updateWizardHeader(currStep - 1);
}

function updateWizardHeader(step) {
    const t = I18N[currentLang] || I18N.uz;
    const titles = [t.step1Title, t.step2Title, t.step3Title, t.step4Title, t.step5Title, t.step6Title, t.step7Title];
    document.getElementById('wizardStepTitle').textContent = titles[step - 1];
    document.getElementById('wizardStepCount').textContent = `${step} / 7`;
    document.getElementById('wizardProgressBar').style.width = `${(step / 7) * 100}%`;
}

async function submitRegistration() {
    const name = document.getElementById('regName')?.value.trim() || "";
    const age = parseInt(document.getElementById('regAge')?.value || "0");
    const city = document.getElementById('regCity')?.value.trim() || "";
    const bio = document.getElementById('regBio')?.value.trim() || "";
    const photo = base64Photo || (kairyxPhotos.length > 0 ? kairyxPhotos[0] : "");

    if (!name || !city || !bio || !photo || age < 18) {
        alert(currentLang === 'ru' ? "Заполните все поля и загрузите фото!" : "Barcha maydonlarni to'ldiring va rasm yuklang!");
        return;
    }

    const finishBtn = document.getElementById('btnRegFinish');
    if (finishBtn) {
        finishBtn.disabled = true;
        finishBtn.textContent = currentLang === 'ru' ? "Регистрация..." : "Ro'yxatdan o'tilmoqda...";
    }

    try {
        const res = await fetch(`${API_URL}/api/register?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({
                name: name,
                age: age,
                gender: selectedRegGender || "MALE",
                target_gender: selectedRegTargetGender || "FEMALE",
                city: city,
                photo: photo,
                bio: bio,
                interests: selectedRegInterests || [],
                language: currentLang || "uz",
                terms_accepted: true
            })
        });

        const data = await res.json();
        if (data && data.success) {
            currentUser = data.user;
            showView('approvedScreen');
            if (typeof populateMyProfile === 'function') populateMyProfile();
            if (typeof switchTab === 'function') switchTab('viewDiscover');
        } else {
            throw new Error(data?.error?.message || "Ro'yxatdan o'tishda xatolik yuz berdi");
        }
    } catch (e) {
        alert("Xatolik: " + e.message);
        if (finishBtn) {
            finishBtn.disabled = false;
            finishBtn.textContent = "Ro'yxatdan o'tish ✨";
        }
    }
}

// ----------------- TAB NAVIGATION -----------------
function switchTab(tabId) {
    const tabs = ['viewDiscover', 'viewLikes', 'viewMatches', 'viewChats', 'viewProfile'];
    tabs.forEach(t => {
        const el = document.getElementById(t);
        if (el) el.style.display = (t === tabId) ? 'block' : 'none';
    });

    const navBtns = {
        'viewDiscover': 'btnNavDiscover',
        'viewLikes': 'btnNavLikes',
        'viewMatches': 'btnNavMatches',
        'viewChats': 'btnNavChats',
        'viewProfile': 'btnNavProfile'
    };

    Object.keys(navBtns).forEach(k => {
        const btn = document.getElementById(navBtns[k]);
        if (btn) {
            if (k === tabId) btn.classList.add('active');
            else btn.classList.remove('active');
        }
    });

    if (tabId === 'viewDiscover') loadDiscoverProfiles();
    if (tabId === 'viewLikes') loadReceivedLikes();
    if (tabId === 'viewMatches') loadMatchesList();
    if (tabId === 'viewChats') loadChatsList();
    if (tabId === 'viewProfile') populateMyProfile();
}

// ----------------- GAMIFICATION: DAILY REWARDS & STREAKS -----------------
async function openDailyRewardModal() {
    document.getElementById('dailyRewardModal').style.display = 'flex';
    const container = document.getElementById('streakGridContainer');
    container.innerHTML = "<p style='grid-column:span 7; color:var(--text-muted); font-size:12px; text-align:center;'>Yuklanmoqda...</p>";

    try {
        const res = await fetch(`${API_URL}/api/rewards/daily/status?${getQueryParams()}`, { method: "GET", headers: getHeaders() });
        const data = await res.json();
        if (data.success) {
            const table = data.rewards_table;
            const cycleDay = data.cycle_day;
            const canClaim = data.can_claim;

            container.innerHTML = "";
            table.forEach(r => {
                const dayNum = r.day;
                const isClaimed = dayNum < cycleDay || (dayNum === cycleDay && !canClaim);
                const isCurrent = dayNum === cycleDay && canClaim;

                const box = document.createElement('div');
                box.className = `streak-day-box ${isCurrent ? 'active' : ''} ${isClaimed ? 'claimed' : ''} ${dayNum === 7 ? 'bonus-day' : ''}`;
                box.innerHTML = `
                    <div style="font-weight:bold; font-size:10px;">${dayNum}-kun</div>
                    <div style="font-size:18px; margin:4px 0;">${dayNum === 7 ? '⭐' : '🎁'}</div>
                    <div style="font-size:9px; font-weight:bold;">${isClaimed ? '✓' : (isCurrent ? 'Olish' : `+${r.xp}XP`)}</div>
                `;
                container.appendChild(box);
            });

            const btn = document.getElementById('btnClaimDailyAction');
            if (canClaim) {
                btn.disabled = false;
                btn.textContent = "🎁 BUGUNGI BONUSNI OLISH";
                btn.style.opacity = "1";
            } else {
                btn.disabled = true;
                btn.textContent = "✓ Bugungi bonus olingan (Ertaga qayting)";
                btn.style.opacity = "0.6";
            }
        }
    } catch(e) { container.innerHTML = e.message; }
}

function closeDailyRewardModal() { document.getElementById('dailyRewardModal').style.display = 'none'; }

async function claimDailyRewardNow() {
    const btn = document.getElementById('btnClaimDailyAction');
    btn.disabled = true;
    btn.textContent = "Qabul qilinmoqda...";

    try {
        const res = await fetch(`${API_URL}/api/rewards/daily/claim?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders()
        });
        const data = await res.json();
        if (data.success) {
            alert(`🎉 Tabriklaymiz! +${data.reward_awarded.xp} XP va +${data.reward_awarded.bonus} ball hisobingizga qo'shildi!`);
            currentUser = data.user;
            populateMyProfile();
            openDailyRewardModal();
        } else {
            alert(data.error?.message || "Xatolik yuz berdi");
            btn.disabled = false;
        }
    } catch(e) {
        alert(e.message);
        btn.disabled = false;
    }
}

// ----------------- LEADERBOARD & MISSIONS -----------------
async function openLeaderboardModal() {
    document.getElementById('leaderboardModal').style.display = 'flex';
    const container = document.getElementById('leaderboardList');
    container.innerHTML = "<p style='color:var(--text-muted); text-align:center;'>Yuklanmoqda...</p>";

    try {
        const res = await fetch(`${API_URL}/api/leaderboard?${getQueryParams()}`, { method: "GET", headers: getHeaders() });
        const data = await res.json();
        if (data.success) {
            const list = data.leaderboard;
            container.innerHTML = "";
            list.forEach(u => {
                const item = document.createElement('div');
                item.className = "glass-panel";
                item.style.cssText = "padding: 12px 14px; display: flex; align-items: center; justify-content: space-between;";
                const medal = u.rank === 1 ? '🥇' : (u.rank === 2 ? '🥈' : (u.rank === 3 ? '🥉' : `#${u.rank}`));
                const userPhoto = (u.photo && u.photo.length > 20) ? u.photo : getDefaultAvatar(u.name);

                item.innerHTML = `
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span style="font-weight:bold; font-size:15px; width:24px; color:var(--accent-gold);">${medal}</span>
                        <img src="${userPhoto}" style="width:40px; height:40px; border-radius:50%; object-fit:cover; border:1.5px solid var(--primary);" onerror="handleImgError(this, '${u.name || "K"}')">
                        <div>
                            <h4 style="margin:0; font-size:14px; color:#fff;">${u.name || 'User'}</h4>
                            <span style="font-size:11px; color:var(--text-muted);">Level ${u.level} • 🔥 ${u.streak_days}d streak</span>
                        </div>
                    </div>
                    <span style="font-weight:bold; font-size:14px; color:var(--accent-green);">${u.xp} XP</span>
                `;
                container.appendChild(item);
            });
        }
    } catch(e) { container.innerHTML = e.message; }
}

function closeLeaderboardModal() { document.getElementById('leaderboardModal').style.display = 'none'; }

async function loadProfileMissions() {
    const container = document.getElementById('profileMissionsList');
    container.innerHTML = "<p style='color:var(--text-muted); font-size:12px;'>Vazifalar tekshirilmoqda...</p>";

    try {
        const res = await fetch(`${API_URL}/api/missions?${getQueryParams()}`, { method: "GET", headers: getHeaders() });
        const data = await res.json();
        if (data.success) {
            container.innerHTML = "";
            data.missions.forEach(m => {
                const item = document.createElement('div');
                item.style.cssText = "background: rgba(255,255,255,0.04); border-radius: 8px; padding: 10px 12px; display: flex; justify-content: space-between; align-items: center;";
                const pct = Math.min(100, Math.round((m.current / m.target) * 100));

                item.innerHTML = `
                    <div style="flex:1; margin-right:10px;">
                        <div style="font-size:13px; font-weight:bold; color:#fff;">${m.title}</div>
                        <div style="font-size:11px; color:var(--text-muted);">${m.desc}</div>
                        <div class="progress-bar-bg" style="height:5px; margin-top:5px;">
                            <div class="progress-bar-fill" style="width:${pct}%;"></div>
                        </div>
                    </div>
                    <span style="font-size:12px; font-weight:bold; color:${m.completed ? 'var(--accent-green)' : 'var(--accent-gold)'};">
                        ${m.completed ? '✓ +'+m.xp+'XP' : `${m.current}/${m.target}`}
                    </span>
                `;
                container.appendChild(item);
            });
        }
    } catch(e) { container.innerHTML = ""; }
}

// ----------------- REFERRAL CENTER -----------------
let globalRefLink = "";
async function openReferralModal() {
    document.getElementById('referralModal').style.display = 'flex';
    const container = document.getElementById('refMilestonesList');
    container.innerHTML = "<p style='color:var(--text-muted);'>Yuklanmoqda...</p>";

    try {
        const res = await fetch(`${API_URL}/api/referral?${getQueryParams()}`, { method: "GET", headers: getHeaders() });
        const data = await res.json();
        if (data.success) {
            globalRefLink = data.referral_link;
            document.getElementById('refLinkText').textContent = data.referral_link;

            container.innerHTML = "";
            data.milestones.forEach(m => {
                const isUnlocked = (data.referral_count >= m.target);
                const item = document.createElement('div');
                item.className = "glass-panel";
                item.style.cssText = "padding: 10px 14px; display: flex; justify-content: space-between; align-items: center;";
                item.innerHTML = `
                    <div>
                        <b>${m.target} ta do'st:</b> ${m.label}
                    </div>
                    <span style="font-weight:bold; color:${isUnlocked ? 'var(--accent-green)' : 'var(--text-muted)'};">
                        ${isUnlocked ? '✓ Olingan' : `${data.referral_count}/${m.target}`}
                    </span>
                `;
                container.appendChild(item);
            });
        }
    } catch(e) { container.innerHTML = e.message; }
}

function closeReferralModal() { document.getElementById('referralModal').style.display = 'none'; }

function copyReferralLink() {
    if (globalRefLink) {
        navigator.clipboard.writeText(globalRefLink);
        alert("Referral havola nusxalandi! Do'stlaringizga yuboring 👥");
    }
}

// ----------------- PAYWALL & RECEIPT PAYMENT CHECKOUT -----------------
function openPaywallModal() {
    document.getElementById('paywallModal').style.display = 'flex';
    updatePaywallPrices();
}
function closePaywallModal() { document.getElementById('paywallModal').style.display = 'none'; }

function toggleBillingPeriod(period) {
    currentBillingPeriod = period;
    document.getElementById('btnBillingMonthly').style.background = (period === 'monthly') ? 'var(--primary-gradient)' : 'rgba(255,255,255,0.06)';
    document.getElementById('btnBillingMonthly').style.color = (period === 'monthly') ? '#fff' : 'var(--text-muted)';
    document.getElementById('btnBillingYearly').style.background = (period === 'yearly') ? 'var(--primary-gradient)' : 'rgba(255,255,255,0.06)';
    document.getElementById('btnBillingYearly').style.color = (period === 'yearly') ? '#fff' : 'var(--text-muted)';
    updatePaywallPrices();
}

function updatePaywallPrices() {
    if (currentBillingPeriod === 'yearly') {
        document.getElementById('priceLabelPremium').textContent = "410,000 UZS / yil";
        document.getElementById('priceLabelVIP').textContent = "710,000 UZS / yil";
    } else {
        document.getElementById('priceLabelPremium').textContent = "49,000 UZS / oy";
        document.getElementById('priceLabelVIP').textContent = "89,000 UZS / oy";
    }
}

function openPaymentCheckoutModal(planTier) {
    closePaywallModal();
    selectedCheckoutPlan = planTier;
    
    if (planTier === "VIP") {
        selectedCheckoutAmount = (currentBillingPeriod === "yearly") ? 710000 : 89000;
        document.getElementById('chkPlanBadge').innerHTML = `👑 VIP STATUS (${currentBillingPeriod === 'yearly' ? '1 Yillik' : '1 Oylik'})`;
        document.getElementById('chkPlanBadge').style.color = "#ff4fbf";
    } else {
        selectedCheckoutAmount = (currentBillingPeriod === "yearly") ? 410000 : 49000;
        document.getElementById('chkPlanBadge').innerHTML = `⭐ PREMIUM (${currentBillingPeriod === 'yearly' ? '1 Yillik' : '1 Oylik'})`;
        document.getElementById('chkPlanBadge').style.color = "var(--accent-gold)";
    }

    document.getElementById('chkAmountBadge').textContent = `${selectedCheckoutAmount.toLocaleString()} UZS`;
    document.getElementById('checkoutCardNumber').textContent = "9860 6004 3347 6527";
    
    base64ReceiptPhoto = "";
    document.getElementById('receiptPhotoPreview').style.display = 'none';
    document.getElementById('receiptPlaceholderText').style.display = 'block';
    document.getElementById('receiptFileInput').value = "";

    document.getElementById('paymentCheckoutModal').style.display = 'flex';
}

function closePaymentCheckoutModal() {
    document.getElementById('paymentCheckoutModal').style.display = 'none';
}

function copyCheckoutCardNumber() {
    navigator.clipboard.writeText("9860600433476527");
    alert("Karta raqami nusxalandi: 9860 6004 3347 6527 💳");
}

const receiptInputEl = document.getElementById('receiptFileInput');
if (receiptInputEl) receiptInputEl.addEventListener('change', async function(e) {
    const file = e.target.files[0];
    if (file) {
        try {
            document.getElementById('receiptPlaceholderText').innerHTML = "<span style='font-size:13px; font-weight:bold; color:var(--primary);'>Chek siqilmoqda...</span>";
            base64ReceiptPhoto = await compressImage(file, 900, 0.8);
            document.getElementById('receiptPhotoPreview').src = base64ReceiptPhoto;
            document.getElementById('receiptPhotoPreview').style.display = 'block';
            document.getElementById('receiptPlaceholderText').style.display = 'none';
        } catch(err) {
            alert("Rasm yuklashda xatolik: " + err.message);
        }
    }
});

async function submitPaymentOrder() {
    if (!base64ReceiptPhoto) {
        alert("To'lov chekini (skrinshot) yuklash majburiy!");
        return;
    }

    const btn = document.getElementById('btnSubmitPaymentReceipt');
    btn.disabled = true;
    btn.textContent = "Yuborilmoqda...";

    try {
        const res = await fetch(`${API_URL}/api/payment/submit?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({
                plan_tier: selectedCheckoutPlan,
                period: currentBillingPeriod,
                amount: selectedCheckoutAmount,
                receipt_photo: base64ReceiptPhoto
            })
        });
        const data = await res.json();
        if (data.success) {
            alert("🎉 To'lov chekingiz muvaffaqiyatli qabul qilindi! Administrator tasdiqlashi bilan obunangiz avtomatik ishga tushadi.");
            closePaymentCheckoutModal();
        } else {
            alert(data.error?.message || "Xatolik yuz berdi");
        }
    } catch(e) {
        alert(e.message);
    } finally {
        btn.disabled = false;
        btn.textContent = "To'lov qildim (Yuborish) 🚀";
    }
}

async function redeemCouponCode() {
    const input = document.getElementById('couponInput');
    const code = input.value.trim().toUpperCase();
    if (!code) {
        alert("Promo kodni kiriting!");
        return;
    }

    try {
        const res = await fetch(`${API_URL}/api/coupons/redeem?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ code: code })
        });
        const data = await res.json();
        if (data.success) {
            alert(data.message);
            input.value = "";
            currentUser = data.user;
            populateMyProfile();
        } else {
            alert(data.error?.message || "Promo kod xato");
        }
    } catch(e) { alert(e.message); }
}

// ----------------- DISCOVERY & SWIPING (WITH SAFE AVATARS & DETAILS) -----------------
async function loadDiscoverProfiles() {
    const container = document.getElementById('cardStackContainer');
    container.innerHTML = `
        <div class="glass-panel" style="padding: 60px 20px; text-align: center; margin-top: 40px;">
            <div class="pulsing-heart" style="font-size: 38px; margin-bottom: 10px;">💖</div>
            <p style="color: var(--text-muted); font-size: 14px;">Yangi anketalar qidirilmoqda...</p>
        </div>
    `;

    const minAge = document.getElementById('filterMinAge')?.value;
    const maxAge = document.getElementById('filterMaxAge')?.value;
    const city = document.getElementById('filterCity')?.value;
    const gender = document.getElementById('filterGender')?.value;

    const q = new URLSearchParams(getQueryParams());
    if (minAge) q.append("min_age", minAge);
    if (maxAge) q.append("max_age", maxAge);
    if (city) q.append("city", city);
    if (gender && gender !== "ANY") q.append("gender", gender);

    try {
        const res = await fetch(`${API_URL}/api/profiles?${q.toString()}`, { method: "GET", headers: getHeaders() });
        const data = await res.json();
        if (data.success) {
            discoverProfiles = data.profiles || [];
            currentDiscoverIndex = 0;
            renderDiscoverCard();
        } else {
            container.innerHTML = `<div class="glass-panel p-4 text-center mt-4"><p class="text-danger">${data.error?.message || "Xatolik"}</p></div>`;
        }
    } catch (e) {
        container.innerHTML = `
            <div class="glass-panel p-4 text-center mt-4">
                <p class="text-danger">Aloqa uzildi: ${e.message}</p>
                <button onclick="loadDiscoverProfiles()" class="btn-primary-gradient mt-2">🔄 Qayta urinish</button>
            </div>
        `;
    }
}

function renderDiscoverCard() {
    const t = I18N[currentLang] || I18N.uz;
    const container = document.getElementById('cardStackContainer');
    if (!discoverProfiles || discoverProfiles.length === 0 || currentDiscoverIndex >= discoverProfiles.length) {
        container.innerHTML = `
            <div class="glass-panel" style="padding: 50px 20px; text-align: center; margin-top: 40px;">
                <div style="font-size: 46px; margin-bottom: 12px;">💫</div>
                <h3 style="color: var(--primary); margin-top: 0; font-size: 20px;">${t.noProfiles}</h3>
                <p style="color: var(--text-muted); font-size: 14px; line-height: 1.5; margin: 8px 0 18px 0;">${t.noProfilesSub}</p>
                <button onclick="loadDiscoverProfiles()" class="btn-primary-gradient">🔄 ${t.btnRetry}</button>
            </div>
        `;
        return;
    }

    const p = discoverProfiles[currentDiscoverIndex];
    if (!p) return;

    activeTargetUser = p;
    const gIcon = p.gender === 'MALE' ? '👨' : (p.gender === 'FEMALE' ? '👩' : '🌈');
    const isVip = (p.plan_tier === 'VIP');
    const isVerified = !!p.is_verified;
    const displayName = (p.name && typeof p.name === 'string' && p.name.trim().length > 0) ? p.name.trim() : "Foydalanuvchi";
    const displayAge = p.age || 20;
    const displayCity = (p.city && typeof p.city === 'string' && p.city.trim().length > 0) ? p.city.trim() : "Toshkent";
    const displayBio = (p.bio && typeof p.bio === 'string' && p.bio.trim().length > 0) ? p.bio.trim() : "Kairyx a'zosi";
    const photoSrc = (p.photo && typeof p.photo === 'string' && p.photo.length > 20) ? p.photo : getDefaultAvatar(displayName, p.gender);

    container.innerHTML = `
        <div class="dating-card">
            <div class="card-image-wrap" onclick="openProfileDetailModal(${p.id})">
                <img src="${photoSrc}" onerror="handleImgError(this, '${displayName}', '${p.gender || "OTHER"}')">
                <div style="position: absolute; top: 12px; left: 12px; display: flex; gap: 6px;">
                    ${isVip ? `<div style="background: var(--vip-gradient); color: #fff; font-size: 10px; font-weight: 800; padding: 4px 10px; border-radius: var(--radius-full); box-shadow: 0 0 12px var(--vip-glow);">👑 VIP</div>` : ''}
                    ${isVerified ? `<div style="background: rgba(5, 217, 232, 0.85); color: #000; font-size: 10px; font-weight: 800; padding: 4px 8px; border-radius: var(--radius-full);">✓ Verified</div>` : ''}
                </div>
                <div class="card-overlay-info">
                    <h2 style="margin: 0; font-size: 24px; color: #fff; display: flex; align-items: center; gap: 6px;">
                        ${displayName}, ${displayAge} ${isVerified ? '🔹' : ''}
                    </h2>
                    <p style="margin: 4px 0 6px 0; color: var(--primary); font-size: 14px; font-weight: bold;">📍 ${displayCity} • ${gIcon}</p>
                    <p style="margin: 0; color: var(--text-sub); font-size: 13px; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">${displayBio}</p>
                </div>
            </div>
            <div class="card-actions-row">
                <button class="btn-action-circle btn-pass" title="Dislike" onclick="handleSwipe(${p.id}, false)">👎</button>
                <button class="btn-action-circle btn-undo" title="Orqaga qaytarish (VIP)" onclick="handleUndoSwipe()">↩️</button>
                <button class="btn-action-circle btn-report" title="Shikoyat" onclick="openReportModal(${p.id})">⚠️</button>
                <button class="btn-action-circle btn-info" title="Batafsil" onclick="openProfileDetailModal(${p.id})">ℹ️</button>
                <button class="btn-action-circle btn-like" title="Like" onclick="handleSwipe(${p.id}, true)">💖</button>
            </div>
        </div>
    `;
}

async function handleSwipe(targetId, isLike) {
    if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');

    previousSwipeProfile = discoverProfiles[currentDiscoverIndex];

    try {
        const res = await fetch(`${API_URL}/api/swipe?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ target_id: targetId, is_like: isLike })
        });
        const data = await res.json();
        if (data.success && data.match) {
            showMatchModal(data.partner, data.match_id);
        }
    } catch (e) {
        console.error("Swipe error:", e);
    }

    currentDiscoverIndex++;
    renderDiscoverCard();
}

function handleUndoSwipe() {
    if (!currentUser?.is_premium && currentUser?.plan_tier !== 'VIP') {
        alert("↩️ Svaypni orqaga qaytarish faqat VIP va Premium foydalanuvchilar uchun ochiq!");
        openPaywallModal();
        return;
    }
    if (currentDiscoverIndex > 0) {
        currentDiscoverIndex--;
        renderDiscoverCard();
        alert("Oldingi anketa qaytarildi ↩️");
    } else {
        alert("Qaytarish uchun oldingi anketa yo'q");
    }
}

function showMatchModal(partner, matchId) {
    const partnerName = (partner?.name && partner.name.length > 0) ? partner.name : "Juftlik";
    document.getElementById('matchPartnerName').textContent = partnerName;
    document.getElementById('matchPartnerAvatar').src = partner?.photo || getDefaultAvatar(partnerName);
    document.getElementById('matchMyAvatar').src = currentUser?.photo || getDefaultAvatar(currentUser?.name);
    document.getElementById('btnMatchChat').onclick = () => {
        closeMatchModal();
        openChatWindow(matchId, partner);
    };
    document.getElementById('matchModal').style.display = 'flex';
}
function closeMatchModal() { document.getElementById('matchModal').style.display = 'none'; }

// ----------------- LIKES RECEIVED -----------------
async function loadReceivedLikes() {
    const t = I18N[currentLang] || I18N.uz;
    const container = document.getElementById('likesList');
    const promo = document.getElementById('likesPremiumPromo');
    const badge = document.getElementById('likesReceivedBadge');
    container.innerHTML = "<p style='color:var(--text-muted); grid-column:span 2; text-align:center;'>Yuklanmoqda...</p>";

    try {
        const res = await fetch(`${API_URL}/api/likes/received?${getQueryParams()}`, { method: "GET", headers: getHeaders() });
        const data = await res.json();

        if (data.success) {
            badge.textContent = data.count || 0;
            const isPrem = !!data.is_premium;
            promo.style.display = isPrem ? 'none' : 'flex';

            if (!data.profiles || data.profiles.length === 0) {
                container.innerHTML = `<p style='color:var(--text-muted); grid-column:span 2; text-align:center; padding:30px 0;'>${t.noLikes}</p>`;
                return;
            }

            container.innerHTML = "";
            data.profiles.forEach(p => {
                const card = document.createElement('div');
                card.className = "glass-panel";
                card.style.cssText = "padding: 12px; text-align: center; position: relative; overflow: hidden;";
                const pName = p.name || "User";
                const photoSrc = (p.photo && p.photo.length > 20) ? p.photo : getDefaultAvatar(pName, p.gender);

                if (!isPrem) {
                    card.innerHTML = `
                        <div style="width: 100%; height: 130px; border-radius: var(--radius-md); overflow: hidden; margin-bottom: 8px; position: relative;">
                            <img src="${photoSrc}" class="blurred-photo" style="width: 100%; height: 100%; object-fit: cover;" onerror="handleImgError(this, '${pName}')">
                            <div style="position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.35);">
                                <span style="font-size: 28px;">⭐</span>
                            </div>
                        </div>
                        <h4 style="margin: 0; font-size: 14px; color: #fff;">${pName}, ${p.age || '?'}</h4>
                        <p style="margin: 2px 0 8px 0; font-size: 12px; color: var(--text-muted);">${p.city || 'Toshkent'}</p>
                        <button onclick="openPaywallModal()" style="width: 100%; background: var(--premium-gradient); color: #000; border: none; padding: 7px; border-radius: var(--radius-sm); font-size: 12px; font-weight: bold; cursor: pointer;">Ochish 🔒</button>
                    `;
                } else {
                    card.innerHTML = `
                        <div style="width: 100%; height: 130px; border-radius: var(--radius-md); overflow: hidden; margin-bottom: 8px; cursor: pointer;" onclick="openProfileDetailModal(${p.id})">
                            <img src="${photoSrc}" style="width: 100%; height: 100%; object-fit: cover;" onerror="handleImgError(this, '${pName}')">
                        </div>
                        <h4 style="margin: 0; font-size: 14px; color: #fff;">${pName}, ${p.age}</h4>
                        <p style="margin: 2px 0 8px 0; font-size: 12px; color: var(--primary); font-weight: bold;">📍 ${p.city || 'Toshkent'}</p>
                        <button onclick="handleSwipe(${p.id}, true)" style="width: 100%; background: var(--primary-gradient); color: #fff; border: none; padding: 7px; border-radius: var(--radius-sm); font-size: 12px; font-weight: bold; cursor: pointer;">💖 Like / Match</button>
                    `;
                }
                container.appendChild(card);
            });
        }
    } catch(e) {
        container.innerHTML = `<p style='color:var(--primary); grid-column:span 2; text-align:center;'>${e.message}</p>`;
    }
}

// ----------------- FILTERS & DETAIL MODALS -----------------
function openFilterModal() { document.getElementById('filterModal').style.display = 'flex'; }
function closeFilterModal() { document.getElementById('filterModal').style.display = 'none'; }
function applyFilters() { closeFilterModal(); loadDiscoverProfiles(); }
function resetFilters() {
    document.getElementById('filterMinAge').value = "";
    document.getElementById('filterMaxAge').value = "";
    document.getElementById('filterCity').value = "";
    document.getElementById('filterGender').value = "ANY";
    closeFilterModal();
    loadDiscoverProfiles();
}

function openProfileDetailModal(userId) {
    const user = discoverProfiles.find(u => u.id === userId) || activeTargetUser;
    if (!user) return;

    const safeName = user.name || "Foydalanuvchi";
    document.getElementById('detailPhoto').src = (user.photo && user.photo.length > 20) ? user.photo : getDefaultAvatar(safeName, user.gender);
    document.getElementById('detailPhoto').onerror = () => { document.getElementById('detailPhoto').src = getDefaultAvatar(safeName, user.gender); };
    document.getElementById('detailNameAge').textContent = `${safeName}, ${user.age || 20}`;
    const gName = user.gender === 'MALE' ? '👨 Erkak' : (user.gender === 'FEMALE' ? '👩 Ayol' : '🌈 Noma`lum');
    document.getElementById('detailCity').textContent = `📍 ${user.city || 'Toshkent'} • ${gName}`;
    document.getElementById('detailBio').textContent = user.bio || "O'zi haqida ma'lumot qoldirmagan.";

    const intContainer = document.getElementById('detailInterests');
    intContainer.innerHTML = "";
    (user.interests || []).forEach(tag => {
        const badge = document.createElement('span');
        badge.className = "tag-badge";
        badge.textContent = tag;
        intContainer.appendChild(badge);
    });

    document.getElementById('btnDetailBlock').onclick = () => blockUser(user.id);
    document.getElementById('btnDetailReport').onclick = () => openReportModal(user.id);

    document.getElementById('profileDetailModal').style.display = 'flex';
}
function closeProfileDetailModal() { document.getElementById('profileDetailModal').style.display = 'none'; }

async function blockUser(targetId) {
    if (!confirm("Foydalanuvchini bloklamoqchimisiz?")) return;
    try {
        const res = await fetch(`${API_URL}/api/user/block?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ target_id: targetId })
        });
        if (res.ok) {
            alert("Foydalanuvchi bloklandi.");
            closeProfileDetailModal();
            loadDiscoverProfiles();
        }
    } catch(e) { alert(e.message); }
}

let reportTargetId = null;
function openReportModal(targetId) {
    reportTargetId = targetId;
    document.getElementById('reportModal').style.display = 'flex';
}
function closeReportModal() { document.getElementById('reportModal').style.display = 'none'; }

async function submitUserReport() {
    if (!reportTargetId) return;
    const reason = document.getElementById('reportReason').value;
    const desc = document.getElementById('reportDesc').value;

    try {
        const res = await fetch(`${API_URL}/api/user/report?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ target_id: reportTargetId, reason: reason, description: desc })
        });
        if (res.ok) {
            alert("Shikoyatingiz qabul qilindi. Moderatorlar ko'rib chiqadi!");
            closeReportModal();
            closeProfileDetailModal();
        }
    } catch(e) { alert(e.message); }
}

// ----------------- MATCHES & CHAT -----------------
async function loadMatchesList() {
    const t = I18N[currentLang] || I18N.uz;
    const container = document.getElementById('matchesList');
    container.innerHTML = "<p style='color: var(--text-muted); grid-column: span 2; text-align: center;'>Yuklanmoqda...</p>";

    try {
        const res = await fetch(`${API_URL}/api/matches?${getQueryParams()}`, { method: "GET", headers: getHeaders() });
        const data = await res.json();
        if (data.success) {
            const matches = data.matches || [];
            if (matches.length === 0) {
                container.innerHTML = `<p style='color: var(--text-muted); grid-column: span 2; text-align: center; padding: 40px 0;'>${t.noMatches}</p>`;
                return;
            }
            container.innerHTML = "";
            matches.forEach(m => {
                const card = document.createElement('div');
                card.className = "glass-panel";
                card.style.cssText = "padding: 14px; text-align: center; cursor: pointer;";
                card.onclick = () => openChatWindow(m.match_id, m.partner);
                const pName = m.partner.name || "Juftlik";
                const pPhoto = (m.partner.photo && m.partner.photo.length > 20) ? m.partner.photo : getDefaultAvatar(pName, m.partner.gender);

                card.innerHTML = `
                    <img src="${pPhoto}" style="width: 72px; height: 72px; object-fit: cover; border-radius: 50%; border: 2.5px solid var(--primary); margin: 0 auto 8px auto; display: block;" onerror="handleImgError(this, '${pName}')">
                    <h4 style="margin: 0; font-size: 15px; color: #fff;">${pName}</h4>
                    <span style="font-size: 12px; color: var(--primary); margin-top: 4px; display: inline-block; font-weight: bold;">💬 Suhbat</span>
                `;
                container.appendChild(card);
            });
        }
    } catch (e) {
        container.innerHTML = `<p style='color: var(--primary); grid-column: span 2; text-align: center;'>Xatolik: ${e.message}</p>`;
    }
}

async function loadChatsList() {
    const t = I18N[currentLang] || I18N.uz;
    const container = document.getElementById('chatsList');
    container.innerHTML = "<p style='color: var(--text-muted); text-align: center;'>Suhbatlar yuklanmoqda...</p>";

    try {
        const res = await fetch(`${API_URL}/api/matches?${getQueryParams()}`, { method: "GET", headers: getHeaders() });
        const data = await res.json();
        if (data.success) {
            const matches = data.matches || [];
            if (matches.length === 0) {
                container.innerHTML = `<p style='color: var(--text-muted); text-align: center; padding: 40px 0;'>${t.noChats}</p>`;
                return;
            }
            container.innerHTML = "";
            matches.forEach(m => {
                const item = document.createElement('div');
                item.className = "glass-panel";
                item.style.cssText = "padding: 12px 16px; display: flex; align-items: center; gap: 12px; cursor: pointer;";
                item.onclick = () => openChatWindow(m.match_id, m.partner);
                const lastTxt = m.last_message ? m.last_message.text : "Yangi juftlik! Suhbatni boshlang.";
                const pName = m.partner.name || "User";
                const pPhoto = (m.partner.photo && m.partner.photo.length > 20) ? m.partner.photo : getDefaultAvatar(pName, m.partner.gender);

                item.innerHTML = `
                    <img src="${pPhoto}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 50%; border: 1.5px solid var(--primary);" onerror="handleImgError(this, '${pName}')">
                    <div style="flex: 1; min-width: 0;">
                        <div style="display: flex; justify-content: space-between;">
                            <h4 style="margin: 0; font-size: 15px; color: #fff;">${pName}</h4>
                        </div>
                        <p style="margin: 3px 0 0 0; font-size: 13px; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${lastTxt}</p>
                    </div>
                `;
                container.appendChild(item);
            });
        }
    } catch (e) {
        container.innerHTML = `<p style='color: var(--primary); text-align: center;'>Xatolik: ${e.message}</p>`;
    }
}

function openChatWindow(matchId, partner) {
    activeMatchId = matchId;
    activeTargetUser = partner;
    const partnerName = partner?.name || "Suhbatdosh";
    const pPhoto = (partner?.photo && partner.photo.length > 20) ? partner.photo : getDefaultAvatar(partnerName);
    document.getElementById('chatPartnerPhoto').src = pPhoto;
    document.getElementById('chatPartnerPhoto').onerror = () => { document.getElementById('chatPartnerPhoto').src = getDefaultAvatar(partnerName); };
    document.getElementById('chatPartnerName').textContent = partnerName;
    document.getElementById('chatOverlay').style.display = 'flex';
    document.getElementById('chatMessages').innerHTML = "";
    loadChatMessages();

    if (chatPollInterval) clearInterval(chatPollInterval);
    chatPollInterval = setInterval(loadChatMessages, 2500);
}

function closeChatWindow() {
    document.getElementById('chatOverlay').style.display = 'none';
    activeMatchId = null;
    if (chatPollInterval) {
        clearInterval(chatPollInterval);
        chatPollInterval = null;
    }
    loadChatsList();
}

async function loadChatMessages() {
    if (!activeMatchId) return;
    try {
        const res = await fetch(`${API_URL}/api/chat/messages?match_id=${activeMatchId}&${getQueryParams()}`, {
            method: "GET",
            headers: getHeaders()
        });
        if (!res.ok) return;
        const data = await res.json();

        if (data.success) {
            const msgs = data.messages || [];
            const container = document.getElementById('chatMessages');
            if (msgs.length === container.children.length) return;

            container.innerHTML = "";
            msgs.forEach(m => {
                const bubble = document.createElement('div');
                const timeStr = new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                if (m.sender_id === 0) {
                    bubble.style.cssText = "align-self: center; background: rgba(255,255,255,0.06); color: var(--text-muted); padding: 6px 14px; border-radius: var(--radius-full); font-size: 11px;";
                    bubble.textContent = m.text;
                } else if (m.sender_id === currentUser.id) {
                    bubble.className = "chat-bubble mine";
                    bubble.innerHTML = `${m.text}<div class="chat-time">${timeStr}</div>`;
                } else {
                    bubble.className = "chat-bubble theirs";
                    bubble.innerHTML = `${m.text}<div class="chat-time">${timeStr}</div>`;
                }
                container.appendChild(bubble);
            });
            container.scrollTop = container.scrollHeight;
        }
    } catch (e) { console.error(e); }
}

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const text = input.value.trim();
    if (!text || !activeMatchId) return;

    input.value = "";
    try {
        const res = await fetch(`${API_URL}/api/chat/send?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ match_id: activeMatchId, text: text })
        });
        if (res.ok) loadChatMessages();
    } catch (e) { console.error(e); }
}

const chatInputEl = document.getElementById('chatInput');
if (chatInputEl) chatInputEl.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendChatMessage();
});

function openChatOptionsMenu() {
    if (!activeTargetUser) return;
    if (confirm("Shikoyat qilishni xohlaysizmi?")) {
        openReportModal(activeTargetUser.id);
    }
}

// ----------------- USER PROFILE & DASHBOARD -----------------
function populateMyProfile() {
    if (!currentUser) return;
    const safeName = currentUser.name || "Mening Profilim";
    document.getElementById('myPhoto').src = (currentUser.photo && currentUser.photo.length > 20) ? currentUser.photo : getDefaultAvatar(safeName, currentUser.gender);
    document.getElementById('myPhoto').onerror = () => { document.getElementById('myPhoto').src = getDefaultAvatar(safeName, currentUser.gender); };
    document.getElementById('myNameAge').textContent = `${safeName}, ${currentUser.age || 20}`;
    const gName = currentUser.gender === 'MALE' ? '👨 Erkak' : (currentUser.gender === 'FEMALE' ? '👩 Ayol' : '🌈 Noma`lum');
    document.getElementById('myCityGender').textContent = `📍 ${currentUser.city || 'Toshkent'} • ${gName}`;
    document.getElementById('myBio').textContent = currentUser.bio || "Mavjud emas";
    document.getElementById('myBalance').textContent = `${currentUser.balance || 0} UZS`;
    document.getElementById('myBonusPoints').textContent = `${currentUser.bonus_points || 0} pts`;
    document.getElementById('myReferralCount').textContent = `${currentUser.referral_count || 0}`;
    document.getElementById('myProfileStreak').textContent = `${currentUser.streak_days || 0}`;

    document.getElementById('myLevelLabel').textContent = `⭐ Level ${currentUser.level || 1}`;
    const prog = currentUser.xp_progress || { current: 0, needed: 200, pct: 0 };
    document.getElementById('myXPLabel').textContent = `${prog.current} / ${prog.needed} XP`;
    document.getElementById('myXPProgressBar').style.width = `${prog.pct}%`;

    const badgesContainer = document.getElementById('myBadgesContainer');
    badgesContainer.innerHTML = "";
    const badges = currentUser.badges || [];
    badges.forEach(b => {
        const span = document.createElement('span');
        span.className = "tag-badge";
        span.style.cssText = "background: rgba(255,183,0,0.14); border-color: var(--accent-gold); color: var(--accent-gold); font-weight: bold;";
        span.textContent = b;
        badgesContainer.appendChild(span);
    });

    const intContainer = document.getElementById('myInterestsList');
    intContainer.innerHTML = "";
    (currentUser.interests || []).forEach(tag => {
        const b = document.createElement('span');
        b.className = "tag-badge";
        b.textContent = tag;
        intContainer.appendChild(b);
    });

    loadProfileMissions();
}

function openEditProfileModal() {
    if (!currentUser) return;
    editBase64Photo = currentUser.photo || "";
    const safeName = currentUser.name || "User";
    const currentAvatar = (currentUser.photo && currentUser.photo.length > 20) 
        ? currentUser.photo 
        : getDefaultAvatar(safeName, currentUser.gender);
    
    document.getElementById('editAvatarPreview').src = currentAvatar;
    document.getElementById('editPhotoStatus').textContent = "JPG, PNG, WEBP (Maks. 5MB)";
    document.getElementById('editPhotoFileInput').value = "";

    document.getElementById('editName').value = currentUser.name || "";
    document.getElementById('editAge').value = currentUser.age || 20;
    document.getElementById('editCity').value = currentUser.city || "";
    document.getElementById('editGender').value = currentUser.gender || "OTHER";
    document.getElementById('editTargetGender').value = currentUser.target_gender || "ANY";
    document.getElementById('editBio').value = currentUser.bio || "";

    selectedEditInterests = [...(currentUser.interests || [])];
    const container = document.getElementById('editInterestsContainer');
    container.innerHTML = "";
    AVAILABLE_INTERESTS.forEach(intTag => {
        const span = document.createElement('span');
        span.className = "tag-badge tag-selectable" + (selectedEditInterests.includes(intTag) ? " selected" : "");
        span.textContent = intTag;
        span.onclick = () => {
            if (selectedEditInterests.includes(intTag)) {
                selectedEditInterests = selectedEditInterests.filter(i => i !== intTag);
                span.classList.remove('selected');
            } else {
                selectedEditInterests.push(intTag);
                span.classList.add('selected');
            }
        };
        container.appendChild(span);
    });

    document.getElementById('editProfileModal').style.display = 'flex';
}
function closeEditProfileModal() { document.getElementById('editProfileModal').style.display = 'none'; }

function handleEditPhotoDeleteClick() {
    const isVip = !!currentUser?.is_premium || currentUser?.plan_tier === 'VIP';
    if (!isVip) {
        alert("⚠️ Rasmni o'chirish — VIP imkoniyati!\n\nVIP obunasini faollashtiring va profilingiz rasmini xohlagancha boshqaring.");
        openPaywallModal();
        return;
    }

    if (!currentUser.photo && (!editBase64Photo || editBase64Photo === "DELETE")) {
        alert("O'chirish uchun profil rasmi mavjud emas.");
        return;
    }

    if (confirm("Rostdan ham profil rasmini o'chirmoqchimisiz?")) {
        editBase64Photo = "DELETE";
        document.getElementById('editAvatarPreview').src = getDefaultAvatar(currentUser.name, currentUser.gender);
        document.getElementById('editPhotoStatus').innerHTML = "<span style='color:var(--accent-gold); font-weight:bold;'>✓ Rasm o'chirildi (Saqlashni bosing)</span>";
    }
}

async function saveProfileEdit() {
    const name = document.getElementById('editName').value.trim();
    const ageStr = document.getElementById('editAge').value.trim();
    const city = document.getElementById('editCity').value.trim();
    const gender = document.getElementById('editGender').value;
    const target_gender = document.getElementById('editTargetGender').value;
    const bio = document.getElementById('editBio').value.trim();

    if (!name) {
        alert("Ismingizni kiriting!");
        return;
    }

    const age = parseInt(ageStr);
    if (!age || isNaN(age) || age < 18 || age > 99) {
        alert("Yosh 18 va 99 oralig'ida bo'lishi shart!");
        return;
    }

    if (!city) {
        alert("Shahringizni kiriting!");
        return;
    }

    const payload = {
        name: name,
        age: age,
        city: city,
        gender: gender,
        target_gender: target_gender,
        bio: bio,
        interests: selectedEditInterests
    };

    if (editBase64Photo === "DELETE") {
        payload.photo = "";
    } else if (editBase64Photo && editBase64Photo.startsWith("data:")) {
        payload.photo = editBase64Photo;
    }

    try {
        const res = await fetch(`${API_URL}/api/profile/update?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
            alert("✓ Profil ma'lumotlari muvaffaqiyatli saqlandi!");
            currentUser = data.user;
            populateMyProfile();
            closeEditProfileModal();
        } else {
            if (data.error?.code === "VIP_REQUIRED") {
                alert("⚠️ " + (data.error?.message || "Rasmni o'chirish faqat VIP foydalanuvchilar uchun!"));
                openPaywallModal();
            } else {
                alert("Xatolik: " + (data.error?.message || "Saqlashda xato yuz berdi"));
            }
        }
    } catch (e) { 
        alert("Aloqa xatosi: " + e.message); 
    }
}

async function openBlockedUsersModal() {
    closeSettingsModal();
    const container = document.getElementById('blockedUsersList');
    container.innerHTML = "<p style='color: var(--text-muted);'>Yuklanmoqda...</p>";
    document.getElementById('blockedUsersModal').style.display = 'flex';

    try {
        const res = await fetch(`${API_URL}/api/user/blocked?${getQueryParams()}`, { method: "GET", headers: getHeaders() });
        const data = await res.json();
        if (data.success) {
            const users = data.blocked_users || [];
            if (users.length === 0) {
                container.innerHTML = "<p style='color: var(--text-muted); font-size: 13px;'>Bloklangan foydalanuvchilar yo'q.</p>";
                return;
            }
            container.innerHTML = "";
            users.forEach(u => {
                const item = document.createElement('div');
                item.style.cssText = "display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid var(--border-subtle);";
                const uName = u.name || "User";
                const uPhoto = (u.photo && u.photo.length > 20) ? u.photo : getDefaultAvatar(uName);
                item.innerHTML = `
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <img src="${uPhoto}" style="width: 38px; height: 38px; object-fit: cover; border-radius: 50%;" onerror="handleImgError(this, '${uName}')">
                        <span style="font-size: 14px; font-weight: bold;">${uName}</span>
                    </div>
                    <button onclick="unblockUser(${u.id})" style="background: rgba(255,255,255,0.08); border: 1px solid var(--border-subtle); color: #fff; padding: 6px 12px; border-radius: var(--radius-sm); font-size: 12px; cursor: pointer;">Blokdan ochish</button>
                `;
                container.appendChild(item);
            });
        }
    } catch (e) { container.innerHTML = e.message; }
}
function closeBlockedUsersModal() { document.getElementById('blockedUsersModal').style.display = 'none'; }

async function unblockUser(targetId) {
    try {
        const res = await fetch(`${API_URL}/api/user/unblock?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ target_id: targetId })
        });
        if (res.ok) openBlockedUsersModal();
    } catch (e) { alert(e.message); }
}

async function confirmDeleteAccount() {
    if (!confirm("DIQQAT: Hisobingizni o'chirmoqchimisiz?")) return;
    try {
        const res = await fetch(`${API_URL}/api/account/delete?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders()
        });
        if (res.ok) {
            alert("Hisobingiz o'chirildi.");
            window.location.reload();
        }
    } catch (e) { alert(e.message); }
}

// Event listener for editProfile photo uploader
const editPhotoInput = document.getElementById('editPhotoFileInput');
if (editPhotoInput) {
    editPhotoInput.addEventListener('change', async function(e) {
        const file = e.target.files[0];
        if (!file) return;

        // Size check (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            alert("Rasm hajmi 5MB dan katta bo'lmasligi kerak!");
            return;
        }

        // Format check
        const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg'];
        if (!allowedTypes.includes(file.type.toLowerCase())) {
            alert("Faqat JPG, PNG yoki WEBP formatidagi rasmlar qabul qilinadi!");
            return;
        }

        try {
            document.getElementById('editPhotoStatus').innerHTML = "<span style='color:var(--primary); font-weight:bold;'>Rasm siqilmoqda...</span>";
            editBase64Photo = await compressImage(file, 800, 0.75);
            document.getElementById('editAvatarPreview').src = editBase64Photo;
            document.getElementById('editPhotoStatus').innerHTML = "<span style='color:var(--accent-green); font-weight:bold;'>✨ Yangi rasm tanlandi</span>";
        } catch(err) {
            alert("Rasm yuklashda xatolik: " + err.message);
            document.getElementById('editPhotoStatus').textContent = "Xatolik: " + err.message;
        }
    });
}

function openRulesModal() {
    closeSettingsModal();
    document.getElementById('rulesModal').style.display = 'flex';
}
function closeRulesModal() { document.getElementById('rulesModal').style.display = 'none'; }

// ----------------- ADMIN DASHBOARD & NAVIGATION -----------------
function openAdminScreen() {
    previousViewBeforeAdmin = currentView || "approvedScreen";
    showView('adminScreen');
    loadAdminData();
}

function closeAdminScreen() {
    if (previousViewBeforeAdmin && previousViewBeforeAdmin !== 'adminScreen') {
        showView(previousViewBeforeAdmin);
    } else {
        showView('approvedScreen');
        switchTab('viewDiscover');
    }
}

function openSettingsModal() { document.getElementById('settingsModal').style.display = 'flex'; }
function closeSettingsModal() { document.getElementById('settingsModal').style.display = 'none'; }

function openLanguageModal() {
    closeSettingsModal();
    document.getElementById('modalLangUz').classList.toggle('selected', currentLang === 'uz');
    document.getElementById('modalLangRu').classList.toggle('selected', currentLang === 'ru');
    document.getElementById('modalLangEn').classList.toggle('selected', currentLang === 'en');
    document.getElementById('modalLangCheckUz').style.display = currentLang === 'uz' ? 'block' : 'none';
    document.getElementById('modalLangCheckRu').style.display = currentLang === 'ru' ? 'block' : 'none';
    document.getElementById('modalLangCheckEn').style.display = currentLang === 'en' ? 'block' : 'none';
    document.getElementById('languageModal').style.display = 'flex';
}
function closeLanguageModal() { document.getElementById('languageModal').style.display = 'none'; }

async function openNotificationsModal() {
    document.getElementById('notificationsModal').style.display = 'flex';
    const container = document.getElementById('notificationsList');
    container.innerHTML = "<p style='color:var(--text-muted);'>Yuklanmoqda...</p>";

    try {
        const res = await fetch(`${API_URL}/api/notifications?${getQueryParams()}`, { method: "GET", headers: getHeaders() });
        const data = await res.json();
        if (data.success) {
            const notifs = data.notifications || [];
            if (notifs.length === 0) {
                container.innerHTML = "<p style='color:var(--text-muted); text-align:center; padding:20px 0;'>Yangi bildirishnomalar yo'q.</p>";
                return;
            }
            container.innerHTML = "";
            notifs.forEach(n => {
                const item = document.createElement('div');
                item.className = "glass-panel";
                item.style.padding = "12px 14px";
                item.innerHTML = `
                    <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                        <h4 style="margin:0; font-size:14px; color:${n.is_read ? '#fff' : 'var(--primary)'};">${n.title}</h4>
                        <span style="font-size:11px; color:var(--text-muted);">${new Date(n.created_at).toLocaleDateString()}</span>
                    </div>
                    <p style="margin:0; font-size:13px; color:var(--text-sub); line-height:1.4;">${n.body || n.text || ''}</p>
                `;
                if (n.deep_link === 'viewLikes') {
                    item.style.cursor = 'pointer';
                    item.onclick = () => { closeNotificationsModal(); switchTab('viewLikes'); };
                }
                container.appendChild(item);
            });
            document.getElementById('notifBadge').style.display = 'none';
        }
    } catch(e) { container.innerHTML = e.message; }
}

function closeNotificationsModal() { document.getElementById('notificationsModal').style.display = 'none'; }

async function markAllNotificationsRead() {
    try {
        await fetch(`${API_URL}/api/notifications/read?${getQueryParams()}`, { method: "POST", headers: getHeaders(), body: "{}" });
        openNotificationsModal();
    } catch(e) {}
}

function openSupportTicketsModal() {
    closeSettingsModal();
    document.getElementById('supportTicketsModal').style.display = 'flex';
    loadUserTickets();
}
function closeSupportTicketsModal() { document.getElementById('supportTicketsModal').style.display = 'none'; }

async function loadUserTickets() {
    const container = document.getElementById('userTicketsList');
    container.innerHTML = "<p style='color:var(--text-muted);'>Murojaatlar yuklanmoqda...</p>";

    try {
        const res = await fetch(`${API_URL}/api/tickets?${getQueryParams()}`, { method: "GET", headers: getHeaders() });
        const data = await res.json();
        if (data.success) {
            const tickets = data.tickets || [];
            if (tickets.length === 0) {
                container.innerHTML = "<p style='color:var(--text-muted); text-align:center; padding:20px 0;'>Hozircha murojaatlar yo'q.</p>";
                return;
            }
            container.innerHTML = "";
            tickets.forEach(t => {
                const item = document.createElement('div');
                item.className = "glass-panel";
                item.style.padding = "12px";
                item.innerHTML = `
                    <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                        <span style="font-weight:bold; font-size:14px; color:var(--primary);">${t.subject}</span>
                        <span style="font-size:12px; color:${t.status === 'ANSWERED' ? 'var(--accent-green)' : 'var(--accent-gold)'};">${t.status}</span>
                    </div>
                    <div style="display:flex; flex-direction:column; gap:6px; margin-top:8px;">
                        ${(t.messages || []).map(m => `
                            <div style="background:${m.is_admin ? 'rgba(255,183,0,0.12)' : 'rgba(255,255,255,0.05)'}; padding:8px 10px; border-radius:6px; font-size:13px;">
                                <b>${m.is_admin ? '🛡️ Support' : 'Siz'}:</b> ${m.text}
                            </div>
                        `).join('')}
                    </div>
                `;
                container.appendChild(item);
            });
        }
    } catch(e) { container.innerHTML = e.message; }
}

function openNewTicketForm() { document.getElementById('newTicketModal').style.display = 'flex'; }
function closeNewTicketForm() { document.getElementById('newTicketModal').style.display = 'none'; }

async function submitNewSupportTicket() {
    const subject = document.getElementById('newTicketSubject').value.trim();
    const category = document.getElementById('newTicketCategory').value;
    const message = document.getElementById('newTicketMessage').value.trim();

    if (!subject || !message) {
        alert("Mavzu va xabarni kiriting!");
        return;
    }

    try {
        const res = await fetch(`${API_URL}/api/tickets/create?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ subject, category, message })
        });
        const data = await res.json();
        if (data.success) {
            alert("Murojaatingiz qabul qilindi!");
            closeNewTicketForm();
            loadUserTickets();
        }
    } catch(e) { alert(e.message); }
}

let currentAdminTab = "payments";

function switchAdminTab(tab) {
    currentAdminTab = tab;
    const sections = ['admSecPayments', 'admSecPending', 'admSecRetention', 'admSecReports', 'admSecTickets', 'admSecUsers', 'admSecBroadcast', 'admSecAudit'];
    sections.forEach(s => {
        const el = document.getElementById(s);
        if (el) el.style.display = (s === `admSec${tab.charAt(0).toUpperCase() + tab.slice(1)}`) ? 'block' : 'none';
    });

    const btns = ['btnAdmTabPayments', 'btnAdmTabPending', 'btnAdmTabRetention', 'btnAdmTabReports', 'btnAdmTabTickets', 'btnAdmTabUsers', 'btnAdmTabBroadcast', 'btnAdmTabAudit'];
    btns.forEach(b => {
        const el = document.getElementById(b);
        if (el) {
            el.style.background = (b === `btnAdmTab${tab.charAt(0).toUpperCase() + tab.slice(1)}`) ? "var(--primary-gradient)" : "rgba(255,255,255,0.06)";
            el.style.color = (b === `btnAdmTab${tab.charAt(0).toUpperCase() + tab.slice(1)}`) ? "#fff" : "var(--text-muted)";
        }
    });

    if (tab === 'payments') loadAdminPayments();
    if (tab === 'pending') loadAdminPending();
    if (tab === 'retention') loadAdminRetention();
    if (tab === 'reports') loadAdminReports();
    if (tab === 'tickets') loadAdminTickets();
    if (tab === 'users') loadAdminUsers();
    if (tab === 'audit') loadAdminAuditLogs();
}

async function loadAdminData() {
    try {
        const res = await fetch(`${API_URL}/api/admin/stats?${getQueryParams()}`, { method: "GET", headers: getHeaders() });
        const data = await res.json();
        if (data.success) {
            document.getElementById('admStatPendingPayments').textContent = data.stats?.pending_payments || 0;
            document.getElementById('admStatPending').textContent = data.stats?.pending || 0;
            document.getElementById('admStatApproved').textContent = data.stats?.approved || 0;
            document.getElementById('admStatPremium').textContent = data.stats?.premium_users || 0;
        }
    } catch (e) {}
    switchAdminTab(currentAdminTab);
}

// ----------------- ADMIN PAYMENTS APPROVAL -----------------
async function loadAdminPayments() {
    const container = document.getElementById('admPaymentsList');
    container.innerHTML = "<p style='color: var(--text-muted);'>To'lovlar yuklanmoqda...</p>";

    try {
        const res = await fetch(`${API_URL}/api/admin/payments?${getQueryParams()}`, { method: "GET", headers: getHeaders() });
        const data = await res.json();
        if (data.success) {
            const orders = data.orders || [];
            if (orders.length === 0) {
                container.innerHTML = "<p style='color: var(--accent-green); text-align:center;'>To'lov cheklari mavjud emas.</p>";
                return;
            }
            container.innerHTML = "";
            orders.forEach(o => {
                const card = document.createElement('div');
                card.className = "glass-panel";
                card.style.padding = "14px";
                const isPending = o.status === 'PENDING';
                const statusColor = isPending ? 'var(--accent-gold)' : (o.status === 'APPROVED' ? 'var(--accent-green)' : '#ff4747');
                const uName = o.user?.name || "User";

                card.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <span style="font-weight:bold; font-size:15px; color:${o.plan_tier === 'VIP' ? '#ff4fbf' : 'var(--accent-gold)'};">
                            ${o.plan_tier === 'VIP' ? '👑 VIP STATUS' : '⭐ PREMIUM'} (${o.period === 'yearly' ? 'Yillik' : 'Oylik'})
                        </span>
                        <span style="font-weight:bold; font-size:12px; color:${statusColor};">${o.status}</span>
                    </div>

                    <div style="display:flex; gap:12px; margin-bottom:10px;">
                        <img src="${o.receipt_photo}" style="width:90px; height:120px; object-fit:cover; border-radius:6px; border:1px solid var(--border-subtle); cursor:pointer;" onclick="window.open('${o.receipt_photo}')" title="Kattalashtirish">
                        <div style="flex:1; font-size:13px;">
                            <p style="margin:0 0 4px 0;"><b>Mijoz:</b> ${uName} (ID: ${o.user ? o.user.id : '?'})</p>
                            <p style="margin:0 0 4px 0;"><b>TG ID:</b> ${o.user ? o.user.telegram_id : '—'}</p>
                            <p style="margin:0 0 4px 0;"><b>Summa:</b> <span style="font-weight:bold; color:var(--accent-green); font-size:15px;">${Number(o.amount).toLocaleString()} UZS</span></p>
                            <p style="margin:0 0 4px 0; color:var(--text-muted); font-size:12px;">Karta: ${o.card_number}</p>
                            <p style="margin:0; color:var(--text-muted); font-size:11px;">${new Date(o.created_at).toLocaleString()}</p>
                        </div>
                    </div>

                    ${isPending ? `
                        <div style="display:flex; gap:8px;">
                            <button onclick="adminApprovePayment(${o.id})" style="flex:2; background:var(--accent-green); color:#000; border:none; padding:10px; border-radius:var(--radius-sm); font-weight:bold; cursor:pointer;">
                                ✅ Tasdiqlash (Obunani yoqish)
                            </button>
                            <button onclick="adminRejectPayment(${o.id})" style="flex:1; background:rgba(255,255,255,0.06); border:1px solid #ff4747; color:#ff4747; padding:10px; border-radius:var(--radius-sm); font-weight:bold; cursor:pointer;">
                                ❌ Rad etish
                            </button>
                        </div>
                    ` : `
                        <div style="font-size:12px; color:var(--text-muted); background:rgba(255,255,255,0.03); padding:8px; border-radius:4px;">
                            Holat: <b>${o.status}</b> ${o.admin_note ? `(Sabab: ${o.admin_note})` : ''}
                        </div>
                    `}
                `;
                container.appendChild(card);
            });
        }
    } catch(e) { container.innerHTML = e.message; }
}

async function adminApprovePayment(orderId) {
    if (!confirm("To'lovni tasdiqlab, obunani faollashtirmoqchimisiz?")) return;
    try {
        const res = await fetch(`${API_URL}/api/admin/payment/approve?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ order_id: orderId })
        });
        const data = await res.json();
        if (data.success) {
            alert("To'lov tasdiqlandi va foydalanuvchiga obuna berildi!");
            loadAdminData();
        } else {
            alert(data.error?.message || "Xatolik");
        }
    } catch(e) { alert(e.message); }
}

async function adminRejectPayment(orderId) {
    const reason = prompt("Rad etish sababini kiriting:", "To'lov cheki mos kelmadi yoki pul tushmadi");
    if (!reason) return;
    try {
        const res = await fetch(`${API_URL}/api/admin/payment/reject?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ order_id: orderId, reason: reason })
        });
        const data = await res.json();
        if (data.success) {
            alert("To'lov rad etildi.");
            loadAdminData();
        } else {
            alert(data.error?.message || "Xatolik");
        }
    } catch(e) { alert(e.message); }
}

async function loadAdminRetention() {
    try {
        const res = await fetch(`${API_URL}/api/admin/retention?${getQueryParams()}`, { method: "GET", headers: getHeaders() });
        const data = await res.json();
        if (data.success) {
            document.getElementById('retDau').textContent = data.metrics?.dau || 0;
            document.getElementById('retWau').textContent = data.metrics?.wau || 0;
            document.getElementById('retMau').textContent = data.metrics?.mau || 0;
            document.getElementById('retStreakUsers').textContent = data.metrics?.streak_3_plus || 0;
        }
    } catch(e) {}
}

async function loadAdminPending() {
    const container = document.getElementById('admPendingList');
    container.innerHTML = "<p style='color: var(--text-muted);'>Arizalar yuklanmoqda...</p>";

    try {
        const res = await fetch(`${API_URL}/api/admin/pending?${getQueryParams()}`, { method: "GET", headers: getHeaders() });
        const data = await res.json();
        if (data.success) {
            const users = data.users || [];
            if (users.length === 0) {
                container.innerHTML = "<p style='color: var(--accent-green); font-weight: bold; text-align: center;'>Kutilayotgan arizalar yo'q!</p>";
                return;
            }
            container.innerHTML = "";
            users.forEach(u => {
                const card = document.createElement('div');
                card.className = "glass-panel";
                card.style.padding = "14px";
                const uName = u.name || "A'zo";
                const uPhoto = (u.photo && u.photo.length > 20) ? u.photo : getDefaultAvatar(uName, u.gender);

                card.innerHTML = `
                    <div style="display: flex; gap: 12px; align-items: center; margin-bottom: 8px;">
                        <img src="${uPhoto}" style="width: 60px; height: 60px; object-fit: cover; border-radius: var(--radius-sm);" onerror="handleImgError(this, '${uName}')">
                        <div>
                            <h4 style="margin: 0; color: var(--primary); font-size: 15px;">${uName}, ${u.age || 20}</h4>
                            <p style="margin: 2px 0 0 0; font-size: 12px; color: var(--text-muted);">${u.city} • ${u.gender}</p>
                        </div>
                    </div>
                    <p style="margin: 0 0 10px 0; font-size: 13px; color: var(--text-sub);">${u.bio || 'Bio mavjud emas'}</p>
                    <div style="display: flex; gap: 8px;">
                        <button onclick="adminApproveUser(${u.id})" style="flex: 1; background: var(--accent-green); color: #000; border: none; padding: 10px; border-radius: var(--radius-sm); font-weight: bold; cursor: pointer;">Tasdiqlash ✅</button>
                        <button onclick="adminRejectUser(${u.id})" style="flex: 1; background: var(--primary); color: #fff; border: none; padding: 10px; border-radius: var(--radius-sm); font-weight: bold; cursor: pointer;">Rad etish ❌</button>
                    </div>
                `;
                container.appendChild(card);
            });
        }
    } catch (e) { container.innerHTML = e.message; }
}

async function adminApproveUser(id) {
    try {
        const res = await fetch(`${API_URL}/api/admin/approve?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ user_id: id })
        });
        if (res.ok) loadAdminData();
    } catch (e) { alert(e.message); }
}

async function adminRejectUser(id) {
    const reason = prompt("Rad etish sababini kiriting:", "Anketa talablarga javob bermaydi");
    if (!reason) return;
    try {
        const res = await fetch(`${API_URL}/api/admin/reject?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ user_id: id, reason: reason })
        });
        if (res.ok) loadAdminData();
    } catch (e) { alert(e.message); }
}

async function loadAdminReports() {
    const container = document.getElementById('admReportsList');
    container.innerHTML = "<p style='color: var(--text-muted);'>Shikoyatlar yuklanmoqda...</p>";

    try {
        const res = await fetch(`${API_URL}/api/admin/reports?${getQueryParams()}`, { method: "GET", headers: getHeaders() });
        const data = await res.json();
        if (data.success) {
            const reports = data.reports || [];
            if (reports.length === 0) {
                container.innerHTML = "<p style='color: var(--accent-green); text-align: center;'>Ochiq shikoyatlar yo'q!</p>";
                return;
            }
            container.innerHTML = "";
            reports.forEach(r => {
                const card = document.createElement('div');
                card.className = "glass-panel";
                card.style.padding = "14px";
                card.innerHTML = `
                    <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                        <span style="color: var(--primary); font-weight: bold; font-size: 14px;">${r.reason}</span>
                        <span style="font-size: 11px; color: var(--text-muted);">${r.status}</span>
                    </div>
                    <p style="margin: 0 0 8px 0; font-size: 13px; color: var(--text-sub);">${r.description || 'Izohsiz'}</p>
                    <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 10px;">
                        Shikoyat qilingan: <b>${r.reported ? r.reported.name : 'Noma`lum'}</b> (ID: ${r.reported ? r.reported.id : '?'})
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <button onclick="adminResolveReport(${r.id}, 'RESOLVE')" style="flex: 1; background: rgba(255,255,255,0.06); border: 1px solid var(--border-subtle); color: #fff; padding: 8px; border-radius: var(--radius-sm); font-size: 12px; cursor: pointer;">Yopish</button>
                        <button onclick="adminResolveReport(${r.id}, 'BAN_USER')" style="flex: 1; background: #ff4747; color: #fff; border: none; padding: 8px; border-radius: var(--radius-sm); font-size: 12px; font-weight: bold; cursor: pointer;">Bloklash ⛔</button>
                    </div>
                `;
                container.appendChild(card);
            });
        }
    } catch (e) { container.innerHTML = e.message; }
}

async function adminResolveReport(id, action) {
    try {
        const res = await fetch(`${API_URL}/api/admin/report/resolve?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ report_id: id, action: action })
        });
        if (res.ok) loadAdminReports();
    } catch (e) { alert(e.message); }
}

async function loadAdminTickets() {
    const container = document.getElementById('admTicketsList');
    container.innerHTML = "<p style='color: var(--text-muted);'>Tiketlar yuklanmoqda...</p>";

    try {
        const res = await fetch(`${API_URL}/api/admin/tickets?${getQueryParams()}`, { method: "GET", headers: getHeaders() });
        const data = await res.json();
        if (data.success) {
            const tickets = data.tickets || [];
            if (tickets.length === 0) {
                container.innerHTML = "<p style='color: var(--accent-green); text-align: center;'>Murojaatlar yo'q!</p>";
                return;
            }
            container.innerHTML = "";
            tickets.forEach(t => {
                const card = document.createElement('div');
                card.className = "glass-panel";
                card.style.padding = "14px";
                card.innerHTML = `
                    <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                        <span style="color: var(--primary); font-weight: bold; font-size: 14px;">${t.subject}</span>
                        <span style="font-size: 11px; color: ${t.status === 'OPEN' ? 'var(--accent-gold)' : 'var(--accent-green)'};">${t.status}</span>
                    </div>
                    <p style="font-size: 12px; color: var(--text-muted); margin: 0 0 8px 0;">Mijoz: ${t.user ? t.user.name : 'User'}</p>
                    <div style="display: flex; flex-direction: column; gap: 4px; margin-bottom: 10px;">
                        ${(t.messages || []).map(m => `
                            <div style="background: rgba(255,255,255,0.04); padding: 6px 10px; border-radius: 4px; font-size: 12px;">
                                <b>${m.is_admin ? '🛡️ Siz' : 'Mijoz'}:</b> ${m.text}
                            </div>
                        `).join('')}
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <button onclick="adminReplyTicketPrompt(${t.id})" style="flex: 2; background: var(--primary-gradient); color: #fff; border: none; padding: 8px; border-radius: var(--radius-sm); font-size: 12px; font-weight: bold; cursor: pointer;">Javob yozish</button>
                        <button onclick="adminCloseTicket(${t.id})" style="flex: 1; background: rgba(255,255,255,0.06); border: 1px solid var(--border-subtle); color: #fff; padding: 8px; border-radius: var(--radius-sm); font-size: 12px; cursor: pointer;">Yopish</button>
                    </div>
                `;
                container.appendChild(card);
            });
        }
    } catch(e) { container.innerHTML = e.message; }
}

async function adminReplyTicketPrompt(ticketId) {
    const text = prompt("Mijozga javob matnini kiriting:");
    if (!text) return;
    try {
        const res = await fetch(`${API_URL}/api/admin/ticket/reply?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ ticket_id: ticketId, text: text })
        });
        if (res.ok) loadAdminTickets();
    } catch(e) { alert(e.message); }
}

async function adminCloseTicket(ticketId) {
    try {
        const res = await fetch(`${API_URL}/api/admin/ticket/status?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ ticket_id: ticketId, status: "CLOSED" })
        });
        if (res.ok) loadAdminTickets();
    } catch(e) { alert(e.message); }
}

let searchTimer = null;
function debounceUserSearch() {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(loadAdminUsers, 400);
}

async function loadAdminUsers() {
    const container = document.getElementById('admUsersList');
    const q = document.getElementById('admUserSearch').value;
    container.innerHTML = "<p style='color: var(--text-muted);'>A'zolar qidirilmoqda...</p>";

    try {
        const res = await fetch(`${API_URL}/api/admin/users?q=${encodeURIComponent(q)}&${getQueryParams()}`, { method: "GET", headers: getHeaders() });
        const data = await res.json();
        if (data.success) {
            const users = data.users || [];
            if (users.length === 0) {
                container.innerHTML = "<p style='color: var(--text-muted); text-align: center;'>Foydalanuvchi topilmadi.</p>";
                return;
            }
            container.innerHTML = "";
            users.forEach(u => {
                const item = document.createElement('div');
                item.className = "glass-panel";
                item.style.cssText = "padding: 12px; display: flex; justify-content: space-between; align-items: center; cursor: pointer;";
                const isBanned = u.status === 'BANNED';
                const uName = u.name || "A'zo";
                const uPhoto = (u.photo && u.photo.length > 20) ? u.photo : getDefaultAvatar(uName, u.gender);
                item.onclick = () => openAdminUserDetail(u.id);
                item.innerHTML = `
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <img src="${uPhoto}" style="width: 42px; height: 42px; object-fit: cover; border-radius: 50%;" onerror="handleImgError(this, '${uName}')">
                        <div>
                            <h4 style="margin: 0; font-size: 14px;">${uName}, ${u.age || '?'}</h4>
                            <span style="font-size: 11px; color: ${isBanned ? '#ff4747' : 'var(--accent-green)'};">${u.status} • ${u.city || ''}</span>
                        </div>
                    </div>
                    <span style="font-size: 13px; color: var(--primary);">Batafsil ➔</span>
                `;
                container.appendChild(item);
            });
        }
    } catch (e) { container.innerHTML = e.message; }
}

async function openAdminUserDetail(userId) {
    document.getElementById('adminUserDetailModal').style.display = 'flex';
    const container = document.getElementById('admDetailContent');
    container.innerHTML = "<p style='color: var(--text-muted);'>Yuklanmoqda...</p>";

    try {
        const res = await fetch(`${API_URL}/api/admin/user/detail?user_id=${userId}&${getQueryParams()}`, { method: "GET", headers: getHeaders() });
        const data = await res.json();
        if (data.success) {
            const u = data.user;
            const uName = u.name || "A'zo";
            const uPhoto = (u.photo && u.photo.length > 20) ? u.photo : getDefaultAvatar(uName, u.gender);
            container.innerHTML = `
                <div style="display: flex; gap: 12px; align-items: center;">
                    <img src="${uPhoto}" style="width: 64px; height: 64px; object-fit: cover; border-radius: 50%; border: 2px solid var(--primary);" onerror="handleImgError(this, '${uName}')">
                    <div>
                        <h3 style="margin: 0; font-size: 17px;">${uName}, ${u.age || '?'}</h3>
                        <p style="margin: 2px 0; color: var(--text-muted); font-size: 12px;">ID: ${u.id} • TG: ${u.telegram_id || '—'}</p>
                        <span style="font-size: 12px; color: var(--accent-green); font-weight: bold;">Status: ${u.status}</span>
                    </div>
                </div>

                <div style="background: rgba(255,255,255,0.04); padding: 12px; border-radius: 8px; font-size: 13px;">
                    <p style="margin: 0 0 4px 0;"><b>Shahar:</b> ${u.city || '—'} • <b>Jinsi:</b> ${u.gender} (Qidiruv: ${u.target_gender})</p>
                    <p style="margin: 0 0 4px 0;"><b>Bio:</b> ${u.bio || '—'}</p>
                    <p style="margin: 0;"><b>Tarif:</b> ${u.plan_tier} • <b>XP:</b> ${u.xp} (Lvl ${u.level}) • <b>Streak:</b> ${u.streak_days}d</p>
                </div>

                <h4 style="margin: 12px 0 6px 0; color: var(--accent-gold);">Statusni o'zgartirish:</h4>
                <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                    <button onclick="adminChangeUserStatus(${u.id}, 'APPROVED')" style="background: var(--accent-green); color: #000; border: none; padding: 8px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; cursor: pointer;">ACTIVE / APPROVED</button>
                    <button onclick="adminChangeUserStatus(${u.id}, 'SUSPENDED')" style="background: var(--accent-gold); color: #000; border: none; padding: 8px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; cursor: pointer;">SUSPEND</button>
                    <button onclick="adminChangeUserStatus(${u.id}, 'BANNED')" style="background: #ff4747; color: #fff; border: none; padding: 8px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; cursor: pointer;">BAN</button>
                </div>

                <h4 style="margin: 14px 0 6px 0; color: var(--accent-gold);">Ichki admin izohi (Note):</h4>
                <div style="display: flex; gap: 6px;">
                    <input type="text" id="admNewNoteInput" placeholder="Izoh yozing..." style="flex: 1; background: rgba(255,255,255,0.06); border: 1px solid var(--border-subtle); border-radius: 4px; padding: 8px; color: #fff; font-size: 13px;">
                    <button onclick="adminAddUserNote(${u.id})" style="background: var(--primary-gradient); color: #fff; border: none; padding: 8px 14px; border-radius: 4px; font-size: 12px; font-weight: bold; cursor: pointer;">Qo'shish</button>
                </div>

                <div style="display: flex; flex-direction: column; gap: 4px; margin-top: 8px;">
                    ${(data.notes || []).map(n => `<div style="font-size: 12px; color: var(--text-muted); background: rgba(255,255,255,0.02); padding: 6px 10px; border-radius: 4px;">• ${n.note} (${new Date(n.created_at).toLocaleDateString()})</div>`).join('')}
                </div>
            `;
        }
    } catch(e) { container.innerHTML = e.message; }
}

function closeAdminUserDetailModal() { document.getElementById('adminUserDetailModal').style.display = 'none'; }

async function adminChangeUserStatus(userId, status) {
    const reason = prompt("Sababini kiriting:", "Admin moderatsiyasi");
    if (!reason) return;
    try {
        const res = await fetch(`${API_URL}/api/admin/user/status?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ user_id: userId, status: status, reason: reason })
        });
        if (res.ok) openAdminUserDetail(userId);
    } catch(e) { alert(e.message); }
}

async function adminAddUserNote(userId) {
    const input = document.getElementById('admNewNoteInput');
    const note = input.value.trim();
    if (!note) return;
    try {
        const res = await fetch(`${API_URL}/api/admin/user/note?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ user_id: userId, note: note })
        });
        if (res.ok) openAdminUserDetail(userId);
    } catch(e) { alert(e.message); }
}

async function sendAdminBroadcast() {
    const title = document.getElementById('broadcastTitle').value.trim();
    const body = document.getElementById('broadcastBody').value.trim();

    if (!title || !body) {
        alert("Sarlavha va matnni kiriting!");
        return;
    }

    try {
        const res = await fetch(`${API_URL}/api/admin/broadcast?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ title, body })
        });
        const data = await res.json();
        if (data.success) {
            alert(`Xabar ${data.sent_count} ta foydalanuvchiga yuborildi!`);
            document.getElementById('broadcastTitle').value = "";
            document.getElementById('broadcastBody').value = "";
        }
    } catch(e) { alert(e.message); }
}

async function loadAdminAuditLogs() {
    const container = document.getElementById('admAuditLogsList');
    container.innerHTML = "<p style='color: var(--text-muted);'>Loglar yuklanmoqda...</p>";

    try {
        const res = await fetch(`${API_URL}/api/admin/audit-logs?${getQueryParams()}`, { method: "GET", headers: getHeaders() });
        const data = await res.json();
        if (data.success) {
            const logs = data.logs || [];
            if (logs.length === 0) {
                container.innerHTML = "<p style='color: var(--text-muted); text-align: center;'>Loglar mavjud emas.</p>";
                return;
            }
            container.innerHTML = "";
            logs.forEach(l => {
                const item = document.createElement('div');
                item.className = "glass-panel";
                item.style.padding = "10px 14px";
                item.innerHTML = `
                    <div style="display: flex; justify-content: space-between; font-size: 13px;">
                        <b style="color: var(--primary);">${l.action}</b>
                        <span style="color: var(--text-muted); font-size: 11px;">${new Date(l.created_at).toLocaleTimeString()}</span>
                    </div>
                    <p style="margin: 3px 0 0 0; font-size: 12px; color: var(--text-sub);">${l.target_type} #${l.target_id || ''}: ${l.new_value || ''}</p>
                `;
                container.appendChild(item);
            });
        }
    } catch(e) { container.innerHTML = e.message; }
}

// ----------------- STARTUP -----------------
if (tg) {
    try {
        tg.ready();
        tg.expand();
    } catch (err) {}
}

// Event listener for editProfile photo uploader
if (editPhotoInput) {
    editPhotoInput.addEventListener('change', async function(e) {
        const file = e.target.files[0];
        if (!file) return;

        // Size check (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            alert("Rasm hajmi 5MB dan katta bo'lmasligi kerak!");
            return;
        }

        // Format check
        const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg'];
        if (!allowedTypes.includes(file.type.toLowerCase())) {
            alert("Faqat JPG, PNG yoki WEBP formatidagi rasmlar qabul qilinadi!");
            return;
        }

        try {
            document.getElementById('editPhotoStatus').innerHTML = "<span style='color:var(--primary); font-weight:bold;'>Rasm siqilmoqda...</span>";
            editBase64Photo = await compressImage(file, 800, 0.75);
            document.getElementById('editAvatarPreview').src = editBase64Photo;
            document.getElementById('editPhotoStatus').innerHTML = "<span style='color:var(--accent-green); font-weight:bold;'>✓ Yangi rasm tanlandi</span>";
        } catch(err) {
            alert("Rasm yuklashda xatolik: " + err.message);
            document.getElementById('editPhotoStatus').textContent = "Xatolik: " + err.message;
        }
    });
}

verifySession();