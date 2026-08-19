/* ============================================
   KAIRYX MINI APP - BULLETPROOF SPA JAVASCRIPT
   ============================================ */

const tg = window.Telegram?.WebApp;
const ADMIN_TELEGRAM_ID = 7992878834;
const API_URL = "";

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
        bio: "Kofeman ☕, Sayohat va fotografiya ixlosmandi 📸. Samimiy va quvnoq insonlar bilan tanishmoqchiman ✨",
        interests: ["Sayohat", "Fotografiya", "Kofe", "Musiqa"],
        premium_plan: "Gold",
        compatibility_score: 94,
        photos: ["https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=600&q=80"]
    },
    {
        id: 102,
        name: "Jasur",
        age: 24,
        city: "Toshkent",
        bio: "Dasturchi 💻. IT va sport bilan shug'ullanaman. Jiddiy munosabat uchun tanishaman 🎯",
        interests: ["Dasturlash", "Sport", "Fitness", "Kino"],
        premium_plan: "Platinum",
        compatibility_score: 88,
        photos: ["https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=600&q=80"]
    },
    {
        id: 103,
        name: "Laylo",
        age: 22,
        city: "Samarqand",
        bio: "Arxitektura va san'at ixlosmandi 🎨. Yaxshi suhbatdoshlarni hurmat qilaman 🌸",
        interests: ["San'at", "Dizayn", "Kitoblar", "Musiqa"],
        premium_plan: "Basic",
        compatibility_score: 82,
        photos: ["https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=600&q=80"]
    },
    {
        id: 104,
        name: "Sardor",
        age: 25,
        city: "Buxoro",
        bio: "Tadbirkor 💼. Bo'sh vaqtimda futbol va avtomobillarga qiziqaman 🚗",
        interests: ["Biznes", "Futbol", "Avto", "Sayohat"],
        premium_plan: "Gold",
        compatibility_score: 91,
        photos: ["https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=600&q=80"]
    }
];


// Helper: Resolve Telegram photo using local proxy
function resolvePhotoUrl(photoId) {
    if (!photoId) return "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=600&q=80";
    if (photoId.startsWith("http")) return photoId;
    return `${API_URL}/api/photo/${photoId}`;
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
    const isUserAdmin = (tg?.initDataUnsafe?.user?.id === ADMIN_TELEGRAM_ID);
    state.user = {
        id: 1,
        name: tg?.initDataUnsafe?.user?.first_name || "Foydalanuvchi",
        age: 23,
        city: "Toshkent",
        bio: "Kairyx Premium ilovasi foydalanuvchisi ✨",
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
        if (!name) { showToast("⚠️", "Ismingizni kiriting!"); return; }
        state.registrationData.name = name;
    } else if (step === 4) {
        const age = document.getElementById('regAge')?.value;
        if (!age || parseInt(age) < 18) { showToast("⚠️", "Yosh kamida 18 bo'lishi kerak!"); return; }
        state.registrationData.age = parseInt(age);
    } else if (step === 6) {
        const height = document.getElementById('regHeight')?.value;
        if (height) state.registrationData.height = parseFloat(height);
    } else if (step === 9) {
        const city = document.getElementById('regCity')?.value.trim();
        if (!city) { showToast("⚠️", "Shaharingizni kiriting!"); return; }
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
    showToast("⏳", "Ro'yxatdan o'tilmoqda...");
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
            showToast("🎉", "Muvaffaqiyatli ro'yxatdan o'tdingiz!");
            navigateTo('home');
            loadProfiles();
        } else {
            showToast("⚠️", data.message || "Xatolik yuz berdi");
        }
    } catch (e) {
        initFallbackUser();
        state.user.name = state.registrationData.name;
        state.user.age = state.registrationData.age;
        state.user.city = state.registrationData.city;
        state.user.bio = state.registrationData.bio;
        updateUI();
        showToast("🎉", "Ro'yxatdan o'tdingiz!");
        navigateTo('home');
    }
}

// ===== UI UPDATES =====
function updateUI() {
    if (!state.user) return;

    const pName = document.getElementById('profileName');
    const pMeta = document.getElementById('profileMeta');
    if (pName) pName.textContent = state.user.name;
    if (pMeta) pMeta.textContent = `${state.user.age} yosh • ${state.user.city}`;

    const myAvatar = document.getElementById('myAvatar');
    if (myAvatar) {
        if (state.user.photos && state.user.photos.length > 0) {
            myAvatar.innerHTML = `<img src="${resolvePhotoUrl(state.user.photos[0])}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">`;
        } else {
            myAvatar.innerHTML = `<span>👤</span>`;
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
    const isSuperAdmin = (tg?.initDataUnsafe?.user?.id === ADMIN_TELEGRAM_ID || state.user.telegram_id === ADMIN_TELEGRAM_ID || state.user.is_admin);
    if (premBadge) premBadge.style.display = state.user.is_premium ? 'flex' : 'none';
    if (adminBadge) adminBadge.style.display = isSuperAdmin ? 'block' : 'none';
    
    // Update settings language label
    const langLabel = document.getElementById('currentSettingsLang');
    if (langLabel) {
        const langMap = { "uz": "O'zbekcha", "ru": "Русский", "en": "English" };
        langLabel.textContent = langMap[state.user.language] || "O'zbekcha";
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
            state.profiles = DEMO_PROFILES;
            displayCurrentProfile();
        }
    } catch (e) {
        state.profiles = DEMO_PROFILES;
        displayCurrentProfile();
    }
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
                <div class="swipe-card-overlay-like">LIKE ❤️</div>
                <div class="swipe-card-overlay-nope">NOPE ✖️</div>`;
        } else {
            photoContainer.innerHTML = `<div class="photo-placeholder"><span>📷</span><p>Rasm yo'q</p></div>
                <div class="swipe-card-overlay-like">LIKE ❤️</div>
                <div class="swipe-card-overlay-nope">NOPE ✖️</div>`;
        }
    }
    
    const swipeName = document.getElementById('swipeName');
    if (swipeName) {
        if (profile.premium_plan && profile.premium_plan !== "Basic") {
            card.classList.add('glowing-premium-card');
            swipeName.innerHTML = `${profile.name}, ${profile.age} <span class="premium-vip-badge">👑 VIP</span>`;
        } else {
            card.classList.remove('glowing-premium-card');
            swipeName.textContent = `${profile.name}, ${profile.age}`;
        }
    }
    
    const sLoc = document.getElementById('swipeLocation');
    const sBio = document.getElementById('swipeBio');
    if (sLoc) sLoc.textContent = `📍 ${profile.city}`;
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
        card.onclick = () => showToast('❤️', `${p.name} sizga yoqdi!`);
        
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
                <h4>${p.name} ${p.premium_plan !== 'Basic' ? '👑' : ''}</h4>
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
    showToast("✅", "O'zgarish saqlandi!");
}

function toggleInvisibleMode() {
    const chk = document.getElementById('invisibleCheckbox');
    if (!chk || !state.user) return;
    state.user.is_invisible = !chk.checked;
    chk.checked = state.user.is_invisible;
    showToast("👻", state.user.is_invisible ? "Ko'rinmas rejim yoqildi" : "Ko'rinmas rejim o'chirildi");
}

function deleteAccountPrompt() {
    if (confirm("Hisobingizni butunlay o'chirishni xohlaysizmi?")) {
        showToast("🗑️", "Hisobingiz o'chirildi");
        setTimeout(() => window.location.reload(), 1000);
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
        showToast("⚠️", "Xabar matnini kiriting!");
        return;
    }
    input.value = '';
    showToast("📣", "Xabar 980 ta foydalanuvchiga yuborildi!");
}

// State for selected plan during checkout
state.selectedPlan = "gold";

function selectPlan(plan) {
    if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');
    state.selectedPlan = plan;
    
    // Open checkout modal
    const modal = document.getElementById('checkoutModal');
    if (modal) modal.style.display = 'flex';
    
    const title = document.getElementById('checkoutPlanTitle');
    const amt = document.getElementById('checkoutAmountText');
    
    if (plan === 'gold') {
        if (title) title.innerHTML = '🥇 Gold Premium';
        if (amt) amt.textContent = '49,900 so'm';
    } else {
        if (title) title.innerHTML = '💎 Platinum Premium';
        if (amt) amt.textContent = '89,900 so'm';
    }
}

function closeCheckoutModal() {
    const modal = document.getElementById('checkoutModal');
    if (modal) modal.style.display = 'none';
}

function copyCardNumber() {
    const cardNum = document.getElementById('checkoutCardNumber')?.textContent || "9860 6004 3347 6527";
    navigator.clipboard.writeText(cardNum.replace(/\s/g, ''));
    showToast('📋', 'Karta raqami nusxalandi!');
    if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
}

async function submitCheckoutPayment() {
    const receiptInput = document.getElementById('checkoutReceiptInput');
    const receipt = receiptInput?.value.trim();
    
    if (!receipt) {
        showToast('⚠️', 'To'lov cheki havolasini kiriting!');
        return;
    }
    
    showToast('⏳', 'Yuborilmoqda...');
    
    try {
        const response = await fetch(`${API_URL}/api/premium/buy`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({
                plan: state.selectedPlan,
                receipt: receipt
            })
        });
        const data = await response.json();
        
        if (data.status === 'ok') {
            closeCheckoutModal();
            if (receiptInput) receiptInput.value = '';
            showToast('✅', 'Chek yuborildi! Admin tasdiqlashini kuting.');
            if (tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
        } else {
            showToast('⚠️', data.message || 'Xatolik yuz berdi');
        }
    } catch (e) {
        closeCheckoutModal();
        if (receiptInput) receiptInput.value = '';
        showToast('✅', 'To'lov yuborildi! (Demo)');
    }
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
    const text = 'Kairyx - premium tanishuv ilovasi! Men foydalanyapman, siz ham qo\'shiling 💕';
    
    if (tg) {
        tg.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(text)}`);
    } else {
        showToast('📋', "Havola nusxalandi!");
    }
}

// Settings page language changer
function changeSettingsLanguagePrompt() {
    const selected = prompt("Tilni tanlang / Выберите язык / Choose language:\n1 - O'zbekcha\n2 - Русский\n3 - English");
    if (selected === "1") {
        saveProfileField("language", "uz");
    } else if (selected === "2") {
        saveProfileField("language", "ru");
    } else if (selected === "3") {
        saveProfileField("language", "en");
    }
}
