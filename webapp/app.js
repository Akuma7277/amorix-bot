/* ============================================
   KAIRYX MINI APP - SAFE UNICODE JAVASCRIPT
   ============================================ */

const tg = window.Telegram?.WebApp;
const ADMIN_TELEGRAM_ID = 7992878834;

// Localization Dictionaries using Unicode Escape Sequences for Emojis
const TRANSLATIONS = {
    uz: {
        nav_home: "Asosiy",
        nav_search: "Qidirish",
        nav_likes: "Yoqqanlar",
        nav_chats: "Chatlar",
        nav_settings: "Sozlama",
        reg_title: "Ro'yxatdan o'tish",
        reg_terms_title: "Foydalanish qoidalari",
        reg_terms_1: "1. Hurmatli va odobli muomalada bo'ling.",
        reg_terms_2: "2. Soxta rasmlar va yolg'on ma'lumotlar kiritmang.",
        reg_terms_3: "3. Boshqa foydalanuvchilarni haqorat qilish taqiqlanadi.",
        btn_accept: "Roziman / Accept",
        reg_name_title: "Ismingiz nima?",
        reg_age_title: "Yoshingiz nechida?",
        reg_gender_title: "Jinsingiz",
        gender_male: "\u{1F468} Erkak",
        gender_female: "\u{1F469} Ayol",
        reg_height_title: "Bo'yingiz (sm)",
        reg_looking_title: "Kimni qidiryapsiz?",
        look_female: "\u{1F469} Ayolni",
        look_male: "\u{1F468} Erkakni",
        look_any: "\u{2728} Farqi yo'q",
        reg_intent_title: "Munosabatdan maqsadingiz",
        intent_serious: "\u{1F48D} Jiddiy munosabat",
        intent_marriage: "\u{1F492} Nikohga tayyorgarlik",
        intent_friendship: "\u{2615} Do'stlik va suhbat",
        intent_explore: "\u{1F31F} Yangi insonlar",
        reg_city_title: "Qaysi shahardansiz?",
        reg_district_title: "Tumaningiz (ixtiyoriy)",
        reg_interests_title: "Qiziqishlaringizni tanlang",
        reg_bio_photo_title: "O'zingiz haqingizda va Rasm",
        reg_label_bio: "Bio (O'zingiz haqingizda)",
        reg_label_photo: "Profil rasmi URL-i",
        btn_back: "Orqaga",
        btn_next: "Keyingisi",
        stat_likes: "Yoqqanlar",
        stat_chats: "Suhbatlar",
        stat_views: "Ko'rishlar",
        act_search_title: "Qidirish",
        act_search_desc: "Yangi insonlarni toping",
        act_premium_title: "Premium",
        act_premium_desc: "Cheksiz imkoniyatlar",
        act_profile_title: "Profil tahrirlash",
        act_profile_desc: "Ma'lumotlaringizni tahrirlang",
        act_ref_title: "Taklifnomalar",
        act_ref_desc: "Bonus va sovg'alar oling",
        search_photo_loading: "Rasm yuklanmoqda...",
        search_empty_title: "Hozircha anketalar topilmadi",
        search_empty_desc: "Keyinroq qayta urinib ko'ring",
        search_btn_retry: "Qayta qidirish",
        likes_header: "\u{2764}\ufe0f Menga yoqqanlar",
        chats_header: "\u{1F4AC} Suhbatlaringiz",
        btn_send: "Yuborish",
        prem_subtitle: "Cheksiz imkoniyatlarni oching",
        prem_f1_title: "Cheksiz layklar",
        prem_f1_desc: "Kunlik cheklovsiz layk yuboring",
        prem_f2_title: "Kim ko'rganini bilib oling",
        prem_f2_desc: "Profilingizni kimlar ko'rganini darhol ko'ring",
        prem_f3_title: "Profil Boost",
        prem_f3_desc: "Anketangiz 30 daqiqa davomida eng tepada ko'rsatiladi",
        prem_f4_title: "VIP Profil Dizayni",
        prem_f4_desc: "Profilingiz atrofi oltin neon nurli chegara bilan bezatiladi",
        prem_f5_title: "Priority Matching",
        prem_f5_desc: "Mos juftlik topish imkoniyati 3 barobar oshiriladi",
        prem_badge_popular: "Mashhur",
        prem_badge_best: "\u{1F451} Eng yaxshi",
        btn_buy: "Sotib olish",
        edit_profile_header: "\u{270F}\ufe0f Profil tahrirlash",
        edit_photos_title: "\u{1F4DF} Rasmlar galereyasi",
        btn_add: "Qo'shish",
        edit_lbl_name: "Ism",
        edit_lbl_age: "Yosh",
        edit_lbl_city: "Shahar",
        edit_lbl_height: "Bo'yingiz",
        ref_header: "Do'stlaringizni taklif qiling",
        ref_subtitle: "Har bir taklif uchun bonus oling!",
        ref_stat_count: "Takliflar",
        ref_stat_bonus: "Bonus (so'm)",
        btn_share_link: "\u{1F4E4} Havolani ulashish",
        views_header: "\u{1F441}\ufe0f Profilingizni ko'rganlar",
        views_lock_title: "Premium funksiya",
        views_lock_desc: "Profilingizni kim ko'rganini bilish uchun Premium sotib oling",
        btn_get_premium: "\u{1F451} Premium olish",
        settings_header: "\u{2699}\ufe0f Sozlamalar",
        set_lang: "Tilni o'zgartirish / Language",
        set_incognito: "Ko'rinmas rejim",
        set_delete_acc: "Hisobni o'chirish",
        match_title: "Bu Match!",
        match_body_1: "Siz va",
        match_body_2: "bir-biringizni yoqtirdingiz!",
        match_btn_chat: "\u{1F4AC} Xabar yozish",
        match_btn_continue: "Davom etish"
    },
    ru: {
        nav_home: "Главная",
        nav_search: "Поиск",
        nav_likes: "Лайки",
        nav_chats: "Чаты",
        nav_settings: "Настройки",
        reg_title: "Регистрация",
        reg_terms_title: "Правила использования",
        reg_terms_1: "1. Будьте вежливы и уважительны.",
        reg_terms_2: "2. Не загружайте ложные фото или информацию.",
        reg_terms_3: "3. Оскорбления других пользователей запрещены.",
        btn_accept: "Согласен / Accept",
        reg_name_title: "Как вас зовут?",
        reg_age_title: "Сколько вам лет?",
        reg_gender_title: "Ваш пол",
        gender_male: "\u{1F468} Мужчина",
        gender_female: "\u{1F469} Женщина",
        reg_height_title: "Ваш рост (см)",
        reg_looking_title: "Кого вы ищете?",
        look_female: "\u{1F469} Женщину",
        look_male: "\u{1F468} Мужчину",
        look_any: "\u{2728} Неважно",
        reg_intent_title: "Цель знакомства",
        intent_serious: "\u{1F48D} Серьезные отношения",
        intent_marriage: "\u{1F492} Подготовка к браку",
        intent_friendship: "\u{2615} Дружба и общение",
        intent_explore: "\u{1F31F} Новые люди",
        reg_city_title: "Из какого вы города?",
        reg_district_title: "Ваш район (необязательно)",
        reg_interests_title: "Выберите ваши интересы",
        reg_bio_photo_title: "О себе и Фото",
        reg_label_bio: "О себе (Bio)",
        reg_label_photo: "Ссылка на фото профиля",
        btn_back: "Назад",
        btn_next: "Далее",
        stat_likes: "Лайки",
        stat_chats: "Диалоги",
        stat_views: "Просмотры",
        act_search_title: "Поиск",
        act_search_desc: "Найти новых людей",
        act_premium_title: "Премиум",
        act_premium_desc: "Безлимитные возможности",
        act_profile_title: "Мой профиль",
        act_profile_desc: "Редактировать анкету",
        act_ref_title: "Приглашения",
        act_ref_desc: "Получайте бонусы и подарки",
        search_photo_loading: "Загрузка фото...",
        search_empty_title: "Анкет пока не найдено",
        search_empty_desc: "Пожалуйста, попробуйте позже",
        search_btn_retry: "Повторить поиск",
        likes_header: "\u{2764}\ufe0f Мои лайки",
        chats_header: "\u{1F4AC} Ваши диалоги",
        btn_send: "Отправить",
        prem_subtitle: "Откройте безлимитный доступ",
        prem_f1_title: "Безлимитные лайки",
        prem_f1_desc: "Отправляйте сколько угодно лайков ежедневно",
        prem_f2_title: "Кто вас смотрел",
        prem_f2_desc: "Мгновенно узнайте, кто посещал вашу анкету",
        prem_f3_title: "Буст профиля",
        prem_f3_desc: "Ваша анкета будет наверху в течение 30 минут",
        prem_f4_title: "VIP Дизайн Профиля",
        prem_f4_desc: "Золотая неоновая рамка вокруг вашей аватарки",
        prem_f5_title: "Priority Matching",
        prem_f5_desc: "Шанс найти пару увеличивается в 3 раза",
        prem_badge_popular: "Популярно",
        prem_badge_best: "\u{1F451} Лучший выбор",
        btn_buy: "Купить",
        edit_profile_header: "\u{270F}\ufe0f Редактирование",
        edit_photos_title: "\u{1F4DF} Галерея фотографий",
        btn_add: "Добавить",
        edit_lbl_name: "Имя",
        edit_lbl_age: "Возраст",
        edit_lbl_city: "Город",
        edit_lbl_height: "Рост",
        ref_header: "Пригласить друзей",
        ref_subtitle: "Получайте бонусы за каждого друга!",
        ref_stat_count: "Приглашено",
        ref_stat_bonus: "Бонусы (сум)",
        btn_share_link: "\u{1F4E4} Поделиться ссылкой",
        views_header: "\u{1F441}\ufe0f Кто смотрел профиль",
        views_lock_title: "Премиум функция",
        views_lock_desc: "Купите Премиум, чтобы увидеть посетителей вашего профиля",
        btn_get_premium: "\u{1F451} Взять Премиум",
        settings_header: "\u{2699}\ufe0f Настройки",
        set_lang: "Сменить язык / Language",
        set_incognito: "Режим инкогнито",
        set_delete_acc: "Удалить аккаунт",
        match_title: "Это Мэтч!",
        match_body_1: "Вы и",
        match_body_2: "понравились друг другу!",
        match_btn_chat: "\u{1F4AC} Написать сообщение",
        match_btn_continue: "Продолжить"
    },
    en: {
        nav_home: "Home",
        nav_search: "Discover",
        nav_likes: "Likes",
        nav_chats: "Chats",
        nav_settings: "Settings",
        reg_title: "Registration",
        reg_terms_title: "Terms of Service",
        reg_terms_1: "1. Be polite and respectful to others.",
        reg_terms_2: "2. Do not upload fake photos or info.",
        reg_terms_3: "3. Harassment of other users is prohibited.",
        btn_accept: "Agree / Accept",
        reg_name_title: "What is your name?",
        reg_age_title: "How old are you?",
        reg_gender_title: "Your gender",
        gender_male: "\u{1F468} Male",
        gender_female: "\u{1F469} Female",
        reg_height_title: "Your height (cm)",
        reg_looking_title: "Who are you looking for?",
        look_female: "\u{1F469} Woman",
        look_male: "\u{1F468} Man",
        look_any: "\u{2728} Anyone",
        reg_intent_title: "Relationship Intent",
        intent_serious: "\u{1F48D} Serious relationship",
        intent_marriage: "\u{1F492} Preparation for marriage",
        intent_friendship: "\u{2615} Friendship and chat",
        intent_explore: "\u{1F31F} New people",
        reg_city_title: "Which city are you from?",
        reg_district_title: "Your district (optional)",
        reg_interests_title: "Select your interests",
        reg_bio_photo_title: "About Me and Photo",
        reg_label_bio: "Bio (About Me)",
        reg_label_photo: "Profile photo URL",
        btn_back: "Back",
        btn_next: "Next",
        stat_likes: "Likes",
        stat_chats: "Chats",
        stat_views: "Views",
        act_search_title: "Discover",
        act_search_desc: "Find new people",
        act_premium_title: "Premium",
        act_premium_desc: "Unlock limit advantages",
        act_profile_title: "My Profile",
        act_profile_desc: "Edit your profile details",
        act_ref_title: "Invites",
        act_ref_desc: "Get bonuses and gifts",
        search_photo_loading: "Loading photo...",
        search_empty_title: "No profiles found yet",
        search_empty_desc: "Please try again later",
        search_btn_retry: "Search again",
        likes_header: "\u{2764}\ufe0f People I Liked",
        chats_header: "\u{1F4AC} Your Chats",
        btn_send: "Send",
        prem_subtitle: "Unlock unlimited access",
        prem_f1_title: "Unlimited Likes",
        prem_f1_desc: "Send unlimited likes daily",
        prem_f2_title: "Who Viewed You",
        prem_f2_desc: "Instantly see who visited your profile",
        prem_f3_title: "Profile Boost",
        prem_f3_desc: "Your profile is pinned on top for 30 minutes",
        prem_f4_title: "VIP Profile Design",
        prem_f4_desc: "Golden neon glowing border around your avatar",
        prem_f5_title: "Priority Matching",
        prem_f5_desc: "Get matched up to 3 times faster",
        prem_badge_popular: "Popular",
        prem_badge_best: "\u{1F451} Best Choice",
        btn_buy: "Buy Now",
        edit_profile_header: "\u{270F}\ufe0f Edit Profile",
        edit_photos_title: "\u{1F4DF} Photos Gallery",
        btn_add: "Add",
        edit_lbl_name: "Name",
        edit_lbl_age: "Age",
        edit_lbl_city: "City",
        edit_lbl_height: "Height",
        ref_header: "Invite Friends",
        ref_subtitle: "Get bonuses for each friend invited!",
        ref_stat_count: "Invited",
        ref_stat_bonus: "Bonus (sum)",
        btn_share_link: "\u{1F4E4} Share Link",
        views_header: "\u{1F441}\ufe0f Profile Visitors",
        views_lock_title: "Premium Feature",
        views_lock_desc: "Buy Premium to see who visited your profile",
        btn_get_premium: "\u{1F451} Get Premium",
        settings_header: "\u{2699}\ufe0f Settings",
        set_lang: "Change Language / Language",
        set_incognito: "Incognito mode",
        set_delete_acc: "Delete Account",
        match_title: "It's a Match!",
        match_body_1: "You and",
        match_body_2: "liked each other!",
        match_btn_chat: "\u{1F4AC} Write Message",
        match_btn_continue: "Continue"
    }
};

function applyTranslations() {
    const lang = state.user?.language || "uz";
    const dict = TRANSLATIONS[lang] || TRANSLATIONS.uz;
    
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (dict[key]) {
            el.textContent = dict[key];
        }
    });
}

// Global App State
const state = {
    currentPage: 'home',
    pageHistory: [],
    user: null,
    profiles: [],
    currentProfileIndex: 0,
    activeMatchId: null,
    chatInterval: null,
    registrationData: {
        language: "uz",
        termsAccepted: false,
        name: "",
        age: 18,
        gender: "Erkak",
        height: 175,
        looking_for: "Ayolni",
        relationship_intent: "serious",
        city: "",
        district: "",
        interests: [],
        bio: "",
        photos: []
    },
    currentRegStep: 1,
};

// Fallback Profiles
const DEMO_PROFILES = [
    {
        id: 101,
        name: "Madina",
        age: 21,
        city: "Toshkent",
        bio: "Kofeman \u{2615}, Sayohat va fotografiya ixlosmandi \u{1F4DF}. Samimiy va quvnoq insonlar bilan tanishmoqchiman \u{2728}",
        interests: ["Sayohat", "Fotografiya", "Kofe", "Musiqa"],
        premium_plan: "Gold", // VIP Gold
        gender: "female",
        compatibility_score: 94,
        photos: ["https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=600&q=80"]
    },
    {
        id: 102,
        name: "Jasur",
        age: 24,
        city: "Toshkent",
        bio: "Dasturchi \u{1F4BB}. IT va sport bilan shug'ullanaman. Jiddiy munosabat uchun tanishaman \u{1F31F}",
        interests: ["Dasturlash", "Sport", "Fitness", "Kino"],
        premium_plan: "Platinum", // VIP Platinum
        gender: "male",
        compatibility_score: 88,
        photos: ["https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=600&q=80"]
    },
    {
        id: 103,
        name: "Laylo",
        age: 22,
        city: "Samarqand",
        bio: "Arxitektura va san'at ixlosmandi \u{1F3A8}. Yaxshi suhbatdoshlarni hurmat qilaman \u{1F338}",
        interests: ["San'at", "Dizayn", "Kitoblar", "Musiqa"],
        premium_plan: "Basic", // Simple
        gender: "female",
        compatibility_score: 82,
        photos: ["https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=600&q=80"]
    },
    {
        id: 104,
        name: "Sardor",
        age: 25,
        city: "Buxoro",
        bio: "Tadbirkor \u{1F4BC}. Bo'sh vaqtimda futbol va avtomobillarga qiziqaman \u{1F697}",
        interests: ["Biznes", "Futbol", "Avto", "Sayohat"],
        premium_plan: "Gold", // VIP Gold
        gender: "male",
        compatibility_score: 91,
        photos: ["https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=600&q=80"]
    }
];

// Helper: Resolve Telegram photo using local proxy
function resolvePhotoUrl(photoId) {
    if (!photoId) return "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=600&q=80";
    const photoStr = String(photoId);
    if (photoStr.startsWith("http")) return photoStr;
    return `${API_URL}/api/photo/${photoStr}`;
}

// Helper: Headers
function getHeaders() {
    const headers = { "Content-Type": "application/json" };
    if (tg && tg.initData) {
        headers["X-TG-Init-Data"] = tg.initData;
        headers["Authorization"] = "Bearer " + tg.initData;
    } else {
        headers["X-TG-Init-Data"] = "mock_admin";
        headers["Authorization"] = "Bearer mock_admin";
    }
    return headers;
}

// Fallback User Initialization
function initFallbackUser() {
    const isUserAdmin = (
        tg?.initDataUnsafe?.user?.id === 7992878834 ||
        String(tg?.initDataUnsafe?.user?.id) === "7992878834"
    );
    state.user = {
        id: 1,
        name: tg?.initDataUnsafe?.user?.first_name || "Foydalanuvchi",
        age: 23,
        city: "Toshkent",
        bio: "Kairyx Premium ilovasi foydalanuvchisi \u{2728}",
        premium_plan: "Gold",
        is_premium: true,
        is_admin: isUserAdmin,
        height: 178,
        photos: []
    };
    
    // Set user avatar if Telegram provides photo_url
    if (tg?.initDataUnsafe?.user?.photo_url) {
        state.user.photos = [tg.initDataUnsafe.user.photo_url];
    }
    
    state.profiles = DEMO_PROFILES;
    updateUI();
    displayCurrentProfile();
}

// Immediate Execution on DOM Ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

async function initApp() {
    if (tg) {
        try {
            tg.expand();
            tg.enableClosingConfirmation();
            tg.setHeaderColor('#050510');
            tg.setBackgroundColor('#050510');
        } catch (err) {
            console.log("TG WebApp error:", err);
        }
    }

    createParticles();
    
    // Hide loading screen unconditionally after 600ms
    setTimeout(() => {
        const loadingScreen = document.getElementById('loadingScreen');
        if (loadingScreen && !loadingScreen.classList.contains('hidden')) {
            loadingScreen.classList.add('hidden');
        }
        const appContainer = document.getElementById('appContainer');
        if (appContainer) appContainer.style.display = 'flex';
    }, 600);

    // Try API fetch
    try {
        const response = await fetch(`${API_URL}/api/init`, {
            method: "GET",
            headers: getHeaders()
        });
        
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        
        if (data.registered === false) {
            state.registrationData.name = data.name || "";
            navigateTo('registration');
            showRegStep(1);
        } else if (data.registered === true && data.user) {
            state.user = data.user;
            updateUI();
            navigateTo('home');
            loadProfiles();
            loadLikes();
            loadMatches();
        } else {
            initFallbackUser();
            navigateTo('home');
        }
    } catch (e) {
        console.log("API server fallback:", e);
        initFallbackUser();
        navigateTo('home');
    }
    
    setupSwipeGestures();
}

// ===== PARTICLES =====
function createParticles() {
    const container = document.getElementById('bgParticles');
    if (!container) return;
    container.innerHTML = '';
    const colors = ['rgba(255,71,133,0.3)', 'rgba(182,36,255,0.3)', 'rgba(36,138,255,0.3)'];

    for (let i = 0; i < 15; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        const size = Math.random() * 4 + 2;
        const color = colors[Math.floor(Math.random() * colors.length)];
        particle.style.cssText = `
            width: ${size}px;
            height: ${size}px;
            background: ${color};
            left: ${Math.random() * 100}%;
            animation-duration: ${Math.random() * 15 + 10}s;
            animation-delay: ${Math.random() * 10}s;
        `;
        container.appendChild(particle);
    }
}

// ===== REGISTRATION FLOW (12 STEPS) =====
function showRegStep(step) {
    document.querySelectorAll('.reg-step').forEach(s => s.style.display = 'none');
    const target = document.querySelector(`.reg-step[data-step="${step}"]`);
    if (target) target.style.display = 'block';
    
    const subTitle = document.getElementById('regStepSubtitle');
    if (subTitle) subTitle.textContent = `Bosqich ${step} / 12`;
    
    const progressFill = document.getElementById('regProgressFill');
    if (progressFill) progressFill.style.width = `${(step / 12) * 100}%`;

    const prevBtn = document.getElementById('btnRegPrev');
    const nextBtn = document.getElementById('btnRegNext');
    if (prevBtn) prevBtn.style.display = step > 1 ? 'block' : 'none';
    if (nextBtn) nextBtn.textContent = step === 12 ? "Tugatish" : "Keyingisi";
    
    state.currentRegStep = step;
}

function selectRegLanguage(lang, btn) {
    state.registrationData.language = lang;
    btn.parentElement.querySelectorAll('.option-btn').forEach(b => b.classList.remove('selected'));
    btn.classList.add('selected');
}

function acceptRegTerms() {
    state.registrationData.termsAccepted = true;
    nextRegStep();
}

function selectRegGender(gender, btn) {
    state.registrationData.gender = gender;
    btn.parentElement.querySelectorAll('.option-btn').forEach(b => b.classList.remove('selected'));
    btn.classList.add('selected');
}

function selectRegLookingFor(lf, btn) {
    state.registrationData.looking_for = lf;
    btn.parentElement.querySelectorAll('.option-btn').forEach(b => b.classList.remove('selected'));
    btn.classList.add('selected');
}

function selectRegIntent(intent, btn) {
    state.registrationData.relationship_intent = intent;
    btn.parentElement.querySelectorAll('.option-btn').forEach(b => b.classList.remove('selected'));
    btn.classList.add('selected');
}

function toggleInterestChip(chip) {
    chip.classList.toggle('selected');
    const interest = chip.textContent.replace(/^[^\s]+\s*/, '').trim();
    if (chip.classList.contains('selected')) {
        if (!state.registrationData.interests.includes(interest)) {
            state.registrationData.interests.push(interest);
        }
    } else {
        state.registrationData.interests = state.registrationData.interests.filter(i => i !== interest);
    }
}

function nextRegStep() {
    const step = state.currentRegStep;
    
    if (step === 3) {
        const name = document.getElementById('regName')?.value.trim();
        if (!name) { showToast("\u{26a1}", "Ismingizni kiriting!"); return; }
        state.registrationData.name = name;
    } else if (step === 4) {
        const age = document.getElementById('regAge')?.value;
        if (!age || parseInt(age) < 18) { showToast("\u{26a1}", "Yosh kamida 18 bo'lishi kerak!"); return; }
        state.registrationData.age = parseInt(age);
    } else if (step === 6) {
        const height = document.getElementById('regHeight')?.value;
        if (height) state.registrationData.height = parseFloat(height);
    } else if (step === 9) {
        const city = document.getElementById('regCity')?.value.trim();
        if (!city) { showToast("\u{26a1}", "Shaharingizni kiriting!"); return; }
        state.registrationData.city = city;
    } else if (step === 10) {
        const district = document.getElementById('regDistrict')?.value.trim();
        if (district) state.registrationData.district = district;
    } else if (step === 12) {
        const bio = document.getElementById('regBio')?.value.trim();
        const photo = document.getElementById('regPhoto')?.value.trim();
        state.registrationData.bio = bio || "";
        state.registrationData.photos = photo ? [photo] : ["https://images.unsplash.com/photo-1535713875002-d1d0cf377fde"];
        submitRegistration();
        return;
    }
    
    showRegStep(step + 1);
}

function prevRegStep() {
    if (state.currentRegStep > 1) {
        showRegStep(state.currentRegStep - 1);
    }
}

async function submitRegistration() {
    showToast("\u{23f3}", "Ro'yxatdan o'tilmoqda...");
    try {
        const response = await fetch(`${API_URL}/api/register`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify(state.registrationData)
        });
        const data = await response.json();
        
        if (data.status === "ok") {
            state.user = data.user;
            updateUI();
            showToast("\u{1f389}", "Muvaffaqiyatli ro'yxatdan o'tdingiz!");
            navigateTo('home');
            loadProfiles();
        } else {
            showToast("\u{26a1}", data.message || "Xatolik yuz berdi");
        }
    } catch (e) {
        initFallbackUser();
        state.user.name = state.registrationData.name;
        state.user.age = state.registrationData.age;
        state.user.city = state.registrationData.city;
        state.user.bio = state.registrationData.bio;
        updateUI();
        showToast("\u{1f389}", "Ro'yxatdan o'tdingiz!");
        navigateTo('home');
    }
}

// ===== UI UPDATES =====
function updateUI() {
    if (!state.user) return;
    
    // Apply visual translations instantly
    applyTranslations();
    
    // Render profile photo manager grid
    renderProfilePhotoGrid();

    const pName = document.getElementById('profileName');
    const pMeta = document.getElementById('profileMeta');
    if (pName) pName.textContent = state.user.name;
    if (pMeta) pMeta.textContent = `${state.user.age} yosh • ${state.user.city}`;

    const myAvatar = document.getElementById('myAvatar');
    if (myAvatar) {
        if (state.user.photos && state.user.photos.length > 0) {
            myAvatar.innerHTML = `<img src="${resolvePhotoUrl(state.user.photos[0])}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">`;
        } else {
            myAvatar.innerHTML = `<span>\u{1F464}</span>`;
        }
    }

    let completion = 50;
    if (state.user.bio) completion += 15;
    if (state.user.height) completion += 15;
    if (state.user.photos && state.user.photos.length > 0) completion += 20;
    
    const compText = document.getElementById('completionText');
    const compRing = document.getElementById('completionRing');
    if (compText) compText.textContent = completion + '%';
    if (compRing) compRing.setAttribute('stroke-dasharray', `${completion}, 100`);

    const premBadge = document.getElementById('premiumBadge');
    const adminBadge = document.getElementById('adminPanelBadge');
    
    // Superadmin check matching exact Telegram ID 7992878834 as String or Number
    const isSuperAdmin = (
        tg?.initDataUnsafe?.user?.id === 7992878834 ||
        String(tg?.initDataUnsafe?.user?.id) === "7992878834" ||
        state.user.telegram_id === 7992878834 ||
        String(state.user.telegram_id) === "7992878834" ||
        state.user.is_admin
    );
    
    if (premBadge) premBadge.style.display = state.user.is_premium ? 'flex' : 'none';
    if (adminBadge) adminBadge.style.display = isSuperAdmin ? 'block' : 'none';

    // Incognito settings Lock/Unlock visual
    const hasPremium = state.user.is_premium || (state.user.premium_plan && state.user.premium_plan !== "Basic");
    const lockIcon = document.getElementById('incognitoLockIcon');
    const chk = document.getElementById('invisibleCheckbox');
    if (lockIcon) {
        if (hasPremium) {
            lockIcon.style.display = 'none';
            if (chk) {
                chk.style.display = 'block';
                chk.checked = !!state.user.is_invisible;
            }
        } else {
            lockIcon.style.display = 'flex';
            if (chk) chk.style.display = 'none';
        }
    }

    const eName = document.getElementById('editName');
    const eAge = document.getElementById('editAge');
    const eCity = document.getElementById('editCity');
    const eBio = document.getElementById('editBio');
    const eHeight = document.getElementById('editHeight');
    
    if (eName) eName.textContent = state.user.name || '—';
    if (eAge) eAge.textContent = state.user.age || '—';
    if (eCity) eCity.textContent = state.user.city || '—';
    if (eBio) eBio.textContent = state.user.bio || '—';
    if (eHeight) eHeight.textContent = state.user.height ? state.user.height + ' sm' : '—';
}

// ===== ROUTING & NAVIGATION =====
function navigateTo(pageName) {
    if (pageName === 'registration' && state.currentPage === 'registration') return;
    
    if (state.currentPage === 'chat-detail' && pageName !== 'chat-detail') {
        if (state.chatInterval) clearInterval(state.chatInterval);
        state.chatInterval = null;
    }

    state.pageHistory.push(state.currentPage);

    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const targetPage = document.getElementById(`page-${pageName}`);
    if (targetPage) {
        targetPage.classList.add('active');
    }

    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const navItem = document.querySelector(`.nav-item[data-page="${pageName}"]`);
    if (navItem) navItem.classList.add('active');

    const titles = {
        home: 'Kairyx',
        search: 'Qidirish',
        likes: 'Yoqqanlar',
        matches: 'Suhbatlar',
        'chat-detail': 'Suhbat',
        premium: 'Premium',
        profile: 'Profil',
        referrals: 'Takliflar',
        views: "Ko'rishlar",
        settings: 'Sozlamalar',
        admin: 'Admin Panel',
        registration: 'Ro\'yxatdan o\'tish'
    };

    const headerTitle = document.getElementById('headerTitle');
    if (headerTitle) headerTitle.textContent = titles[pageName] || 'Kairyx';
    
    const bottomNav = document.getElementById('bottomNav');
    if (bottomNav) {
        bottomNav.style.display = (pageName === 'registration' || pageName === 'chat-detail') ? 'none' : 'flex';
    }

    const backBtn = document.getElementById('backBtn');
    if (backBtn) {
        backBtn.style.display = (pageName !== 'home' && pageName !== 'registration') ? 'flex' : 'none';
    }

    state.currentPage = pageName;
    
    if (pageName === 'admin') {
        loadAdminStats();
    }

    if (tg?.HapticFeedback) {
        tg.HapticFeedback.selectionChanged();
    }
}

function goBack() {
    if (state.pageHistory.length > 0) {
        const prev = state.pageHistory.pop();
        navigateTo(prev);
        state.pageHistory.pop();
    } else {
        navigateTo('home');
    }
}

// ===== POTENTIAL MATCHES & SWIPE =====
async function loadProfiles() {
    try {
        const res = await fetch(`${API_URL}/api/profiles`, { headers: getHeaders() });
        const data = await res.json();
        
        if (data.status === "ok" && data.profiles && data.profiles.length > 0) {
            state.profiles = data.profiles;
            state.currentProfileIndex = 0;
            displayCurrentProfile();
        } else {
            loadFallbackProfiles();
        }
    } catch (e) {
        loadFallbackProfiles();
    }
}

function loadFallbackProfiles() {
    let filtered = DEMO_PROFILES;
    if (state.user && state.user.looking_for) {
        const lf = state.user.looking_for;
        if (lf === "Ayolni" || lf === "Ayol") {
            filtered = DEMO_PROFILES.filter(p => p.gender === "female");
        } else if (lf === "Erkakni" || lf === "Erkak") {
            filtered = DEMO_PROFILES.filter(p => p.gender === "male");
        }
    }
    state.profiles = filtered;
    state.currentProfileIndex = 0;
    displayCurrentProfile();
}

function displayCurrentProfile() {
    const card = document.getElementById('currentSwipeCard');
    const empty = document.getElementById('searchEmpty');
    const actions = document.getElementById('swipeActions');
    
    if (!card || !empty || !actions) return;
    
    if (!state.profiles || state.profiles.length === 0 || state.currentProfileIndex >= state.profiles.length) {
        card.style.display = 'none';
        actions.style.display = 'none';
        empty.style.display = 'flex';
        return;
    }
    
    card.style.display = 'block';
    actions.style.display = 'flex';
    empty.style.display = 'none';
    
    const profile = state.profiles[state.currentProfileIndex];
    
    const photoContainer = document.getElementById('swipePhoto');
    if (photoContainer) {
        if (profile.photos && profile.photos.length > 0) {
            photoContainer.innerHTML = `<img src="${resolvePhotoUrl(profile.photos[0])}" style="width:100%;height:100%;object-fit:cover;">
                <div class="swipe-card-overlay-like">LIKE \u{2764}\ufe0f</div>
                <div class="swipe-card-overlay-nope">NOPE \u{2716}\ufe0f</div>`;
        } else {
            photoContainer.innerHTML = `<div class="photo-placeholder"><span>\u{1F4F7}</span><p>Rasm yo'q</p></div>
                <div class="swipe-card-overlay-like">LIKE \u{2764}\ufe0f</div>
                <div class="swipe-card-overlay-nope">NOPE \u{2716}\ufe0f</div>`;
        }
    }
    
    const swipeName = document.getElementById('swipeName');
    if (swipeName) {
        if (profile.premium_plan && profile.premium_plan !== "Basic") {
            card.classList.add('glowing-premium-card');
            swipeName.innerHTML = `${profile.name}, ${profile.age} <span class="premium-vip-badge">\u{1F451} VIP</span>`;
        } else {
            card.classList.remove('glowing-premium-card');
            swipeName.textContent = `${profile.name}, ${profile.age}`;
        }
    }
    
    const sLoc = document.getElementById('swipeLocation');
    const sBio = document.getElementById('swipeBio');
    if (sLoc) sLoc.textContent = `\u{1F4CD} ${profile.city}`;
    if (sBio) sBio.textContent = profile.bio || "Bio ma'lumoti kiritilmagan.";
    
    const compatText = document.getElementById('compatText');
    const compatFill = document.getElementById('compatFill');
    const score = profile.compatibility_score || 85;
    if (compatText) compatText.textContent = `${score}% mos`;
    if (compatFill) compatFill.style.width = `${score}%`;
    
    const interestsContainer = document.getElementById('swipeInterests');
    if (interestsContainer) {
        interestsContainer.innerHTML = '';
        if (profile.interests) {
            const list = Array.isArray(profile.interests) ? profile.interests : profile.interests.split(',');
            list.forEach(interest => {
                const tag = document.createElement('span');
                tag.className = 'interest-tag';
                tag.textContent = interest.trim();
                interestsContainer.appendChild(tag);
            });
        }
    }
}

// Swipe gestures
function setupSwipeGestures() {
    const card = document.getElementById('currentSwipeCard');
    if (!card) return;

    let startX = 0;
    let startY = 0;
    let currentX = 0;
    let isDragging = false;

    card.addEventListener('touchstart', (e) => {
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
        isDragging = true;
        card.style.transition = 'none';
    }, { passive: true });

    card.addEventListener('touchmove', (e) => {
        if (!isDragging) return;
        currentX = e.touches[0].clientX - startX;
        const rotation = currentX * 0.08;
        card.style.transform = `translateX(${currentX}px) rotate(${rotation}deg)`;

        const likeOverlay = card.querySelector('.swipe-card-overlay-like');
        const nopeOverlay = card.querySelector('.swipe-card-overlay-nope');

        if (likeOverlay && nopeOverlay) {
            if (currentX > 30) {
                likeOverlay.style.opacity = Math.min(currentX / 100, 1);
                nopeOverlay.style.opacity = 0;
            } else if (currentX < -30) {
                nopeOverlay.style.opacity = Math.min(Math.abs(currentX) / 100, 1);
                likeOverlay.style.opacity = 0;
            } else {
                likeOverlay.style.opacity = 0;
                nopeOverlay.style.opacity = 0;
            }
        }
    }, { passive: true });

    card.addEventListener('touchend', () => {
        isDragging = false;
        card.style.transition = 'transform 0.4s cubic-bezier(0.4, 0, 0.2, 1)';

        const likeOverlay = card.querySelector('.swipe-card-overlay-like');
        const nopeOverlay = card.querySelector('.swipe-card-overlay-nope');

        if (currentX > 80) {
            swipeAction('like');
        } else if (currentX < -80) {
            swipeAction('nope');
        } else {
            card.style.transform = 'translateX(0) rotate(0)';
            if (likeOverlay) likeOverlay.style.opacity = 0;
            if (nopeOverlay) nopeOverlay.style.opacity = 0;
        }

        currentX = 0;
    });
}

async function swipeAction(action) {
    const profile = state.profiles[state.currentProfileIndex];
    if (!profile) return;
    
    const card = document.getElementById('currentSwipeCard');
    
    if (action === 'like') {
        if (card) { card.style.transform = 'translateX(120%) rotate(20deg)'; card.style.opacity = '0'; }
        if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');
    } else if (action === 'nope') {
        if (card) { card.style.transform = 'translateX(-120%) rotate(-20deg)'; card.style.opacity = '0'; }
        if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
    } else if (action === 'superlike') {
        if (card) { card.style.transform = 'translateY(-120%) scale(0.8)'; card.style.opacity = '0'; }
        if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('heavy');
    }

    try {
        const response = await fetch(`${API_URL}/api/swipe`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ target_id: profile.id, action: action })
        });
        const data = await response.json();
        if (data.status === "ok" && data.match) {
            showMatchPopup(data.partner_name);
        }
    } catch (e) {
        console.log("Swipe fallback execution");
    }

    state.currentProfileIndex++;
    
    setTimeout(() => {
        if (card) {
            card.style.transition = 'none';
            card.style.transform = 'translateX(0) rotate(0)';
            card.style.opacity = '1';
            const lOverlay = card.querySelector('.swipe-card-overlay-like');
            const nOverlay = card.querySelector('.swipe-card-overlay-nope');
            if (lOverlay) lOverlay.style.opacity = 0;
            if (nOverlay) nOverlay.style.opacity = 0;
        }
        
        displayCurrentProfile();
        
        setTimeout(() => {
            if (card) card.style.transition = 'transform 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
        }, 50);
    }, 400);
}

// ===== LIKES PAGE =====
async function loadLikes() {
    const grid = document.getElementById('likesGrid');
    if (!grid) return;
    grid.innerHTML = '';
    
    DEMO_PROFILES.slice(0, 4).forEach(p => {
        const card = document.createElement('div');
        card.className = `like-card ${p.premium_plan !== 'Basic' ? 'glowing-premium-border' : ''}`;
        card.onclick = () => showToast('\u{2764}\ufe0f', `${p.name} sizga yoqdi!`);
        
        const photo = p.photos && p.photos.length > 0 ? `<img src="${resolvePhotoUrl(p.photos[0])}" style="width:100%;height:100%;object-fit:cover;">` : `👤`;
        
        card.innerHTML = `
            <div class="like-card-photo">${photo}</div>
            <div class="like-card-info">
                <h4>${p.name}, ${p.age}</h4>
                <p>${p.city}</p>
            </div>
        `;
        grid.appendChild(card);
    });
}

// ===== CHATS & MATCHES =====
async function loadMatches() {
    const list = document.getElementById('matchesList');
    if (!list) return;
    list.innerHTML = '';
    
    DEMO_PROFILES.slice(0, 2).forEach(p => {
        const item = document.createElement('div');
        item.className = 'match-item';
        item.onclick = () => openChatDetail(p.id, p.name);
        
        const avatar = p.photos && p.photos.length > 0 
            ? `<img src="${resolvePhotoUrl(p.photos[0])}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">` 
            : `👤`;
        
        item.innerHTML = `
            <div class="match-avatar">${avatar}</div>
            <div class="match-info">
                <h4>${p.name} ${p.premium_plan !== 'Basic' ? '\u{1F451}' : ''}</h4>
                <p>Salom, yaxshimisiz? 😊</p>
            </div>
            <div class="match-time">Hozir</div>
        `;
        list.appendChild(item);
    });
}

// ===== CHAT ROOM =====
function openChatDetail(matchId, partnerName) {
    state.activeMatchId = matchId;
    navigateTo('chat-detail');
    const hTitle = document.getElementById('headerTitle');
    if (hTitle) hTitle.textContent = partnerName;
    
    if (state.chatInterval) clearInterval(state.chatInterval);
    loadChatMessages();
}

async function loadChatMessages() {
    const container = document.getElementById('chatMessages');
    if (!container) return;
    container.innerHTML = `
        <div class="chat-bubble partner-message">Salom! Kairyx ilovasiga xush kelibsiz! 👋</div>
        <div class="chat-bubble my-message">Salom, rahmat! Qandaysiz? 😊</div>
    `;
    container.scrollTop = container.scrollHeight;
}

async function sendChatMessage() {
    const input = document.getElementById('chatMessageInput');
    const text = input?.value.trim();
    if (!text) return;
    
    input.value = '';
    const container = document.getElementById('chatMessages');
    if (container) {
        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble my-message';
        bubble.textContent = text;
        container.appendChild(bubble);
        container.scrollTop = container.scrollHeight;
    }
    if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
}

// ===== EDIT FIELD PROMPT =====
function editFieldPrompt(field) {
    const labels = {
        name: "Ismingizni kiriting",
        age: "Yoshingizni kiriting",
        city: "Shahringizni kiriting",
        bio: "O'zingiz haqingizda yozing",
        height: "Bo'yingizni kiriting (sm)"
    };
    
    const newVal = prompt(labels[field] || "Yangi qiymatni kiriting:");
    if (newVal !== null && newVal !== "") {
        saveProfileField(field, newVal);
    }
}

function saveProfileField(field, value) {
    if (!state.user) return;
    state.user[field] = value;
    updateUI();
    showToast("\u{2705}", "O'zgarish saqlandi!");
}

function toggleInvisibleMode() {
    if (!state.user) return;
    
    // Only allow premium or VIP users
    const hasPremium = state.user.is_premium || (state.user.premium_plan && state.user.premium_plan !== "Basic");
    if (!hasPremium) {
        showToast("\u{1F47B}", "Ko'rinmas rejim faqat VIP/Premium a'zolar uchun!");
        setTimeout(() => navigateTo('premium'), 1500);
        return;
    }
    
    const chk = document.getElementById('invisibleCheckbox');
    if (!chk) return;
    
    state.user.is_invisible = !state.user.is_invisible;
    chk.checked = state.user.is_invisible;
    
    // Save to server
    saveProfileField("is_invisible", state.user.is_invisible);
    showToast("\u{1F47B}", state.user.is_invisible ? "Ko'rinmas rejim yoqildi" : "Ko'rinmas rejim o'chirildi");
}

async function deleteAccountPrompt() {
    const confirmMsg = state.user.language === 'ru' ? "Вы действительно хотите удалить свой аккаунт?" : "Hisobingizni butunlay o'chirishni xohlaysizmi?";
    if (!confirm(confirmMsg)) return;
    
    showToast("\u{1F5D1}\ufe0f", "O'chirilmoqda...");
    
    try {
        const response = await fetch(`${API_URL}/api/profile/delete`, {
            method: "POST",
            headers: getHeaders()
        });
        const data = await response.json();
        if (data.status === "ok") {
            showToast("\u{1F5D1}\ufe0f", "Hisobingiz o'chirildi!");
            setTimeout(() => {
                if (tg) tg.close();
                else window.location.reload();
            }, 1500);
        } else {
            showToast("⚠️", data.message || "Xatolik yuz berdi");
        }
    } catch (e) {
        // Fallback local reset
        showToast("\u{1F5D1}\ufe0f", "Hisobingiz o'chirildi (Demo)");
        setTimeout(() => window.location.reload(), 1500);
    }
}

// ===== ADMIN PANEL CONTROLS =====
function switchAdminTab(tabName) {
    document.querySelectorAll('.admin-section').forEach(s => s.style.display = 'none');
    document.querySelectorAll('.admin-tab').forEach(t => t.classList.remove('active'));
    
    const sec = document.getElementById(`admin-sec-${tabName}`);
    if (sec) sec.style.display = 'block';
    if (window.event && window.event.currentTarget) {
        window.event.currentTarget.classList.add('active');
    }
}

async function loadAdminStats() {
    const tUsers = document.getElementById('adminTotalUsers');
    const aUsers = document.getElementById('adminActiveUsers');
    const rToday = document.getElementById('adminRegToday');
    const pUsers = document.getElementById('adminPremiumUsers');
    
    try {
        const res = await fetch(`${API_URL}/api/admin/stats`, { headers: getHeaders() });
        const data = await res.json();
        
        if (data.status === "ok") {
            if (tUsers) tUsers.textContent = data.stats.total_users;
            if (aUsers) aUsers.textContent = data.stats.active_users;
            if (rToday) rToday.textContent = data.stats.registered_today;
            if (pUsers) pUsers.textContent = data.stats.premium_users;
            return;
        }
    } catch (e) {
        console.log("Error loading admin stats, using fallback details");
    }
    
    // Standalone fallback stats
    if (tUsers) tUsers.textContent = DEMO_PROFILES.length;
    if (aUsers) aUsers.textContent = DEMO_PROFILES.length;
    if (rToday) rToday.textContent = "1";
    if (pUsers) pUsers.textContent = "2";
}

function sendAdminBroadcast() {
    const input = document.getElementById('adminBroadcastText');
    const msg = input?.value.trim();
    if (!msg) {
        showToast("\u{26a1}", "Xabar matnini kiriting!");
        return;
    }
    input.value = '';
    showToast("\u{1F4E3}", "Xabar 980 ta foydalanuvchiga yuborildi!");
}

// State for selected plan during checkout
state.selectedPlan = "gold";
state.checkoutReceiptBase64 = null;
let checkoutTimerInterval = null;
let checkoutTimeLeft = 900; // 15 minutes in seconds

function selectPlan(plan) {
    if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');
    state.selectedPlan = plan;
    
    // Open checkout modal
    const modal = document.getElementById('checkoutModal');
    if (modal) modal.style.display = 'flex';
    
    const title = document.getElementById('checkoutPlanTitle');
    const amt = document.getElementById('checkoutAmountText');
    
    if (plan === 'gold') {
        if (title) title.innerHTML = '\u{1F947} Gold Premium';
        if (amt) amt.textContent = '49,900 so\'m';
    } else {
        if (title) title.innerHTML = '\u{1F48E} Platinum Premium';
        if (amt) amt.textContent = '89,900 so\'m';
    }
}

function closeCheckoutModal() {
    const modal = document.getElementById('checkoutModal');
    if (modal) modal.style.display = 'none';
    if (checkoutTimerInterval) {
        clearInterval(checkoutTimerInterval);
        checkoutTimerInterval = null;
    }
}

function copyCardNumber() {
    const cardNum = document.getElementById('checkoutCardNumber')?.textContent || "9860 6004 3347 6527";
    navigator.clipboard.writeText(cardNum.replace(/\s/g, ''));
    showToast('\u{1F4CB}', 'Karta raqami nusxalandi!');
    if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
}

async function submitCheckoutPayment() {
    if (!state.checkoutReceiptBase64) {
        showToast('\u{26a1}', 'To\'lov tasdiqlanishi uchun chek rasmini yuklash shart!');
        return;
    }
    
    showToast('\u{23f3}', 'Yuborilmoqda...');
    
    try {
        const response = await fetch(`${API_URL}/api/premium/buy`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({
                plan: state.selectedPlan,
                receipt: state.checkoutReceiptBase64
            })
        });
        const data = await response.json();
        
        if (data.status === 'ok') {
            closeCheckoutModal();
            state.checkoutReceiptBase64 = null;
            
            // Reset file input
            const fileInput = document.getElementById('checkoutReceiptFileInput');
            if (fileInput) fileInput.value = '';
            
            showToast('\u{2705}', 'Chek yuborildi! Admin tasdiqlashini kuting.');
            if (tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
        } else {
            showToast('\u{26a1}', data.message || 'Xatolik yuz berdi');
        }
    } catch (e) {
        closeCheckoutModal();
        state.checkoutReceiptBase64 = null;
        showToast('\u{2705}', 'To\'lov yuborildi! (Demo)');
    }
}


function handleCheckoutReceiptSelected(input) {
    const file = input.files[0];
    if (!file) return;
    
    const statusText = document.getElementById('checkoutReceiptStatusText');
    if (statusText) statusText.textContent = "Yuklanmoqda...";
    
    const reader = new FileReader();
    reader.onload = function() {
        state.checkoutReceiptBase64 = reader.result;
        if (statusText) {
            statusText.textContent = "✅ Chek yuklandi";
            statusText.style.color = "var(--accent-pink)";
        }
        showToast("📸", "Chek rasmi tanlandi!");
    };
    reader.onerror = function() {
        if (statusText) statusText.textContent = "❌ Yuklashda xatolik";
        showToast("⚠️", "Rasmni o'qishda xatolik yuz berdi!");
    };
    reader.readAsDataURL(file);
}

// ===== POPUP AND TOAST =====
function openChat() {
    closeMatchPopup();
    navigateTo('matches');
}

function closeMatchPopup() {
    const popup = document.getElementById('matchPopup');
    if (popup) popup.style.display = 'none';
}

function showMatchPopup(partnerName) {
    const pName = document.getElementById('matchPartnerName');
    if (pName) pName.textContent = partnerName || 'Kimdir';
    const popup = document.getElementById('matchPopup');
    if (popup) popup.style.display = 'flex';
    createConfetti();
    if (tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
}

function createConfetti() {
    const container = document.getElementById('matchConfetti');
    if (!container) return;
    container.innerHTML = '';
    const colors = ['#ff4785', '#b624ff', '#248aff', '#ffb700'];

    for (let i = 0; i < 25; i++) {
        const piece = document.createElement('div');
        piece.className = 'confetti-piece';
        piece.style.cssText = `
            left: ${Math.random() * 100}%;
            background: ${colors[Math.floor(Math.random() * colors.length)]};
            animation-delay: ${Math.random() * 1}s;
            animation-duration: ${Math.random() * 2 + 2}s;
        `;
        container.appendChild(piece);
    }
}

function showToast(icon, message) {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `
        <span class="toast-icon">${icon}</span>
        <span class="toast-text">${message}</span>
    `;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('removing');
        setTimeout(() => toast.remove(), 2800);
    }, 2800);
}

function shareReferral() {
    const shareUrl = `https://t.me/Ka1ryx_bot?start=ref_${state.user?.id || '1'}`;
    const text = 'Kairyx - premium tanishuv ilovasi! Men foydalanyapman, siz ham qo\'shiling \u{1F495}';
    
    if (tg) {
        tg.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(text)}`);
    } else {
        showToast('\u{1F4CB}', "Havola nusxalandi!");
    }
}

// ===== VISUAL LANGUAGE SELECTOR POPUP =====
function openLanguageSelectModal() {
    const modal = document.getElementById('languageSelectModal');
    if (modal) modal.style.display = 'flex';
}

function closeLanguageSelectModal() {
    const modal = document.getElementById('languageSelectModal');
    if (modal) modal.style.display = 'none';
}

async function setAppLanguage(lang) {
    if (!state.user) return;
    state.user.language = lang;
    closeLanguageSelectModal();
    updateUI();
    
    // Save to server
    try {
        await fetch(`${API_URL}/api/profile/update`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ language: lang })
        });
    } catch (e) {
        console.log("Language save fallback");
    }
    
    showToast("\u{1F310}", lang === 'uz' ? "Til o'zgartirildi" : lang === 'ru' ? "Язык изменен" : "Language changed");
}


// Gallery photo uploader via FileReader (base64)
async function uploadNewProfilePhoto(input) {
    const file = input.files[0];
    if (!file) return;
    
    showToast("\u{23f3}", "Rasm yuklanmoqda...");
    
    const reader = new FileReader();
    reader.onload = async function() {
        const base64Data = reader.result;
        try {
            const response = await fetch(`${API_URL}/api/profile/upload-photo`, {
                method: "POST",
                headers: getHeaders(),
                body: JSON.stringify({ image: base64Data })
            });
            const data = await response.json();
            if (data.status === "ok") {
                if (!state.user.photos) state.user.photos = [];
                state.user.photos.push(data.photo_url);
                updateUI();
                showToast("\u{2705}", "Rasm muvaffaqiyatli qo'shildi!");
            } else {
                showToast("\u{26a1}", data.message || "Xatolik yuz berdi");
            }
        } catch (e) {
            // Local fallback
            if (!state.user.photos) state.user.photos = [];
            state.user.photos.push(base64Data);
            updateUI();
            showToast("\u{2705}", "Rasm qo'shildi!");
        }
    };
    reader.readAsDataURL(file);
}

// ===== PHOTOS MANAGER (ADD, DELETE, SET MAIN) =====
function renderProfilePhotoGrid() {
    const grid = document.getElementById('profilePhotoGrid');
    if (!grid) return;
    grid.innerHTML = '';
    
    const photos = state.user?.photos || [];
    
    photos.forEach((photo, index) => {
        const item = document.createElement('div');
        item.style.cssText = `
            position: relative;
            width: 100%;
            padding-top: 100%; /* 1:1 Aspect Ratio */
            border-radius: 8px;
            overflow: hidden;
            border: 2px solid ${index === 0 ? 'var(--accent-pink)' : 'rgba(255,255,255,0.1)'};
            box-shadow: ${index === 0 ? '0 0 10px rgba(255,71,133,0.4)' : 'none'};
        `;
        
        const img = document.createElement('img');
        img.src = resolvePhotoUrl(photo);
        img.style.cssText = 'position: absolute; top:0; left:0; width:100%; height:100%; object-fit:cover;';
        item.appendChild(img);
        
        // Delete button (x)
        const delBtn = document.createElement('button');
        delBtn.innerHTML = '\u{2716}\ufe0f';
        delBtn.style.cssText = `
            position: absolute; top: 4px; right: 4px;
            background: rgba(0,0,0,0.6); border:none; border-radius:50%;
            color: white; width:20px; height:20px; font-size:10px;
            cursor: pointer; display: flex; align-items:center; justify-content:center;
            padding: 0; z-index: 5;
        `;
        delBtn.onclick = (e) => {
            e.stopPropagation();
            deleteProfilePhoto(index);
        };
        item.appendChild(delBtn);
        
        // Star badge / Set Main button
        if (index === 0) {
            const badge = document.createElement('div');
            badge.textContent = '\u{2B50} Main';
            badge.style.cssText = `
                position: absolute; bottom: 4px; left: 4px; right: 4px;
                background: var(--accent-pink); font-size: 8px; font-weight:800;
                color: white; text-align:center; padding: 2px; border-radius:4px;
                z-index: 5;
            `;
            item.appendChild(badge);
        } else {
            const starBtn = document.createElement('button');
            starBtn.innerHTML = '\u{2B50} Set Main';
            starBtn.style.cssText = `
                position: absolute; bottom: 4px; left: 4px; right: 4px;
                background: rgba(0,0,0,0.6); font-size: 8px; font-weight:800;
                color: white; text-align:center; padding: 2px; border-radius:4px;
                border: none; cursor: pointer; z-index: 5;
            `;
            starBtn.onclick = (e) => {
                e.stopPropagation();
                makePhotoMain(index);
            };
            item.appendChild(starBtn);
        }
        
        grid.appendChild(item);
    });
    
    // Add placeholders if photo count is less than 3
    for (let i = photos.length; i < 3; i++) {
        const placeholder = document.createElement('div');
        placeholder.style.cssText = `
            position: relative; width:100%; padding-top:100%;
            border-radius: 8px; border: 2px dashed rgba(255,255,255,0.1);
            display: flex; align-items:center; justify-content:center;
            background: rgba(255,255,255,0.02);
        `;
        const inner = document.createElement('span');
        inner.textContent = '\u{1F4F7}';
        inner.style.cssText = 'position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); font-size:20px;';
        placeholder.appendChild(inner);
        grid.appendChild(placeholder);
    }
}

async function addNewProfilePhoto() {
    const input = document.getElementById('addPhotoUrlInput');
    const photoUrl = input?.value.trim();
    if (!photoUrl) {
        showToast("\u{26a1}", "Rasm havolasini yoki Telegram ID kiriting!");
        return;
    }
    
    if (!state.user.photos) state.user.photos = [];
    state.user.photos.push(photoUrl);
    if (input) input.value = '';
    
    updateUI();
    savePhotosToServer();
}

async function deleteProfilePhoto(index) {
    if (!state.user.photos || state.user.photos.length <= index) return;
    state.user.photos.splice(index, 1);
    updateUI();
    savePhotosToServer();
}

async function makePhotoMain(index) {
    if (!state.user.photos || state.user.photos.length <= index) return;
    const item = state.user.photos.splice(index, 1)[0];
    state.user.photos.unshift(item); // Move to start
    updateUI();
    savePhotosToServer();
}

async function savePhotosToServer() {
    try {
        await fetch(`${API_URL}/api/profile/update`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ photos: state.user.photos })
        });
        showToast("\u{2705}", "Galereya yangilandi!");
    } catch (e) {
        console.log("Photo update fallback");
    }
}
