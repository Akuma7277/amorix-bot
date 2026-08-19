/* ============================================
   AMORIX MINI APP - FUNCTIONAL JAVASCRIPT
   ============================================ */

const tg = window.Telegram?.WebApp;
const API_URL = ""; // Relative path to API endpoints since they are hosted on the same server

const state = {
    currentPage: 'home',
    pageHistory: [],
    user: null, // Logged in user profile
    profiles: [], // Potential matches
    currentProfileIndex: 0,
    activeMatchId: null, // Current active chat match ID
    chatInterval: null,
    registrationData: {
        name: "",
        age: 18,
        height: 175,
        gender: "Erkak",
        looking_for: "Ayolni",
        relationship_intent: "serious",
        city: "",
        bio: "",
        photos: []
    },
    currentRegStep: 1,
};

// Headers with Telegram Authorization data
function getHeaders() {
    const headers = {
        "Content-Type": "application/json"
    };
    if (tg && tg.initData) {
        headers["X-TG-Init-Data"] = tg.initData;
        headers["Authorization"] = "Bearer " + tg.initData;
    } else {
        // Dev mock initData header
        headers["X-TG-Init-Data"] = "mock_admin";
        headers["Authorization"] = "Bearer mock_admin";
    }
    return headers;
}

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    if (tg) {
        tg.expand();
        tg.enableClosingConfirmation();
        tg.setHeaderColor('#0a0a1a');
        tg.setBackgroundColor('#0a0a1a');
    }

    createParticles();
    
    // Validate user & Check registration status
    try {
        const response = await fetch(`${API_URL}/api/init`, {
            method: "GET",
            headers: getHeaders()
        });
        const data = await response.json();
        
        // Hide loading
        document.getElementById('loadingScreen').classList.add('hidden');
        document.getElementById('appContainer').style.display = 'flex';
        
        if (data.registered === false) {
            // User needs to register
            state.registrationData.name = data.name || "";
            navigateTo('registration');
        } else if (data.registered === true) {
            state.user = data.user;
            updateUI();
            navigateTo('home');
            
            // Background pre-loads
            loadProfiles();
            loadLikes();
            loadMatches();
        } else {
            showToast("⚠️", "Ulanishda xatolik yuz berdi");
        }
    } catch (e) {
        console.error(e);
        document.getElementById('loadingScreen').classList.add('hidden');
        document.getElementById('appContainer').style.display = 'flex';
        showToast("⚠️", "API serverga ulanib bo'lmadi");
    }
    
    setupSwipeGestures();
}

// ===== BACKGROUND PARTICLES =====
function createParticles() {
    const container = document.getElementById('bgParticles');
    if (!container) return;
    const colors = ['rgba(255,107,157,0.3)', 'rgba(196,77,255,0.3)', 'rgba(77,157,255,0.3)'];

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

// ===== REGISTRATION FLOW =====
function showRegStep(step) {
    document.querySelectorAll('.reg-step').forEach(s => s.style.display = 'none');
    document.querySelector(`.reg-step[data-step="${step}"]`).style.display = 'block';
    
    document.getElementById('btnRegPrev').style.display = step > 1 ? 'block' : 'none';
    document.getElementById('btnRegNext').textContent = step === 3 ? "Tugatish" : "Keyingisi";
    
    state.currentRegStep = step;
}

function nextRegStep() {
    if (state.currentRegStep === 1) {
        const name = document.getElementById('regName').value.trim();
        const age = document.getElementById('regAge').value;
        const height = document.getElementById('regHeight').value;
        
        if (!name || !age) {
            showToast("⚠️", "Ism va yoshni kiriting!");
            return;
        }
        state.registrationData.name = name;
        state.registrationData.age = parseInt(age);
        state.registrationData.height = height ? parseFloat(height) : null;
        
        showRegStep(2);
    } else if (state.currentRegStep === 2) {
        state.registrationData.gender = document.getElementById('regGender').value;
        state.registrationData.looking_for = document.getElementById('regLookingFor').value;
        state.registrationData.relationship_intent = document.getElementById('regIntent').value;
        
        showRegStep(3);
    } else if (state.currentRegStep === 3) {
        const city = document.getElementById('regCity').value.trim();
        const bio = document.getElementById('regBio').value.trim();
        const photo = document.getElementById('regPhoto').value.trim();
        
        if (!city) {
            showToast("⚠️", "Shaharni kiriting!");
            return;
        }
        state.registrationData.city = city;
        state.registrationData.bio = bio;
        state.registrationData.photos = photo ? [photo] : ["https://images.unsplash.com/photo-1535713875002-d1d0cf377fde"]; // Fallback avatar
        
        submitRegistration();
    }
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
        showToast("⚠️", "API xatoligi");
    }
}

// ===== UI UPDATES =====
function updateUI() {
    if (!state.user) return;

    // Set name & meta
    document.getElementById('profileName').textContent = state.user.name;
    document.getElementById('profileMeta').textContent = `${state.user.age} yosh • ${state.user.city}`;

    // Avatar
    const myAvatar = document.getElementById('myAvatar');
    if (state.user.photos && state.user.photos.length > 0) {
        myAvatar.innerHTML = `<img src="${state.user.photos[0]}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">`;
    } else {
        myAvatar.innerHTML = `<span>👤</span>`;
    }

    // Completion percentage calculation
    let completion = 50;
    if (state.user.bio) completion += 15;
    if (state.user.height) completion += 15;
    if (state.user.photos && state.user.photos.length > 0) completion += 20;
    
    document.getElementById('completionText').textContent = completion + '%';
    document.getElementById('completionRing').setAttribute('stroke-dasharray', `${completion}, 100`);

    // Premium status & Admin status
    if (state.user.is_premium) {
        document.getElementById('premiumBadge').style.display = 'flex';
    } else {
        document.getElementById('premiumBadge').style.display = 'none';
    }

    if (state.user.is_admin) {
        document.getElementById('adminPanelBadge').style.display = 'block';
    } else {
        document.getElementById('adminPanelBadge').style.display = 'none';
    }

    // Fill edit fields
    document.getElementById('editName').textContent = state.user.name || '—';
    document.getElementById('editAge').textContent = state.user.age || '—';
    document.getElementById('editCity').textContent = state.user.city || '—';
    document.getElementById('editBio').textContent = state.user.bio || '—';
    document.getElementById('editHeight').textContent = state.user.height ? state.user.height + ' sm' : '—';
    
    const invisibleCheckbox = document.getElementById('invisibleCheckbox');
    if (invisibleCheckbox) {
        invisibleCheckbox.checked = !!state.user.is_invisible;
    }
}

// ===== ROUTING & NAVIGATION =====
function navigateTo(pageName) {
    if (pageName === 'registration' && state.currentPage === 'registration') return;
    
    // Clear chat intervals if leaving chat
    if (state.currentPage === 'chat-detail' && pageName !== 'chat-detail') {
        clearInterval(state.chatInterval);
        state.chatInterval = null;
    }

    state.pageHistory.push(state.currentPage);

    // Toggle pages
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const targetPage = document.getElementById(`page-${pageName}`);
    if (targetPage) {
        targetPage.classList.add('active');
    }

    // Toggle nav active
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const navItem = document.querySelector(`.nav-item[data-page="${pageName}"]`);
    if (navItem) navItem.classList.add('active');

    // Headers
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
        registration: 'Ro'yxatdan o'tish'
    };

    document.getElementById('headerTitle').textContent = titles[pageName] || 'Kairyx';
    
    // Hide nav bar if on registration or chat pages
    const bottomNav = document.getElementById('bottomNav');
    if (pageName === 'registration' || pageName === 'chat-detail') {
        bottomNav.style.display = 'none';
    } else {
        bottomNav.style.display = 'flex';
    }

    // Show/hide back button
    const backBtn = document.getElementById('backBtn');
    if (pageName !== 'home' && pageName !== 'registration') {
        backBtn.style.display = 'flex';
    } else {
        backBtn.style.display = 'none';
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
        state.pageHistory.pop(); // Remove duplicate pushed by navigateTo
    } else {
        navigateTo('home');
    }
}

// ===== POTENTIAL MATCHES & SWIPE =====
async function loadProfiles() {
    try {
        const res = await fetch(`${API_URL}/api/profiles`, {
            headers: getHeaders()
        });
        const data = await res.json();
        
        if (data.status === "ok") {
            state.profiles = data.profiles;
            state.currentProfileIndex = 0;
            displayCurrentProfile();
        }
    } catch (e) {
        console.error(e);
    }
}

function displayCurrentProfile() {
    const card = document.getElementById('currentSwipeCard');
    const empty = document.getElementById('searchEmpty');
    const actions = document.getElementById('swipeActions');
    
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
    
    // Photo
    const photoContainer = document.getElementById('swipePhoto');
    if (profile.photos && profile.photos.length > 0) {
        photoContainer.innerHTML = `<img src="${profile.photos[0]}" style="width:100%;height:100%;object-fit:cover;">
            <div class="swipe-card-overlay-like">LIKE ❤️</div>
            <div class="swipe-card-overlay-nope">NOPE ✖️</div>`;
    } else {
        photoContainer.innerHTML = `<div class="photo-placeholder"><span>📷</span><p>Rasm yo'q</p></div>
            <div class="swipe-card-overlay-like">LIKE ❤️</div>
            <div class="swipe-card-overlay-nope">NOPE ✖️</div>`;
    }
    
    // Premium styling - Gold/Platinum user gets golden outline
    if (profile.premium_plan && profile.premium_plan !== "Basic") {
        card.classList.add('glowing-premium-card');
        document.getElementById('swipeName').innerHTML = `${profile.name}, ${profile.age} <span class="premium-vip-badge">👑 VIP</span>`;
    } else {
        card.classList.remove('glowing-premium-card');
        document.getElementById('swipeName').textContent = `${profile.name}, ${profile.age}`;
    }
    
    document.getElementById('swipeLocation').textContent = `📍 ${profile.city}`;
    document.getElementById('swipeBio').textContent = profile.bio || "Bio ma'lumoti kiritilmagan.";
    
    // Compatibility score
    const compatText = document.getElementById('compatText');
    const compatFill = document.getElementById('compatFill');
    const score = profile.compatibility_score || 65;
    compatText.textContent = `${score}% mos`;
    compatFill.style.width = `${score}%`;
    
    // Interests
    const interestsContainer = document.getElementById('swipeInterests');
    interestsContainer.innerHTML = '';
    if (profile.interests && profile.interests.length > 0) {
        profile.interests.forEach(interest => {
            const tag = document.createElement('span');
            tag.className = 'interest-tag';
            tag.textContent = interest.trim();
            interestsContainer.appendChild(tag);
        });
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
            likeOverlay.style.opacity = 0;
            nopeOverlay.style.opacity = 0;
        }

        currentX = 0;
    });
}

async function swipeAction(action) {
    const profile = state.profiles[state.currentProfileIndex];
    if (!profile) return;
    
    const card = document.getElementById('currentSwipeCard');
    
    // Animation effects
    if (action === 'like') {
        card.style.transform = 'translateX(120%) rotate(20deg)';
        card.style.opacity = '0';
        if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');
    } else if (action === 'nope') {
        card.style.transform = 'translateX(-120%) rotate(-20deg)';
        card.style.opacity = '0';
        if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
    } else if (action === 'superlike') {
        card.style.transform = 'translateY(-120%) scale(0.8)';
        card.style.opacity = '0';
        if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('heavy');
    }

    try {
        const response = await fetch(`${API_URL}/api/swipe`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({
                target_id: profile.id,
                action: action
            })
        });
        const data = await response.json();
        
        if (data.status === "ok" && data.match) {
            showMatchPopup(data.partner_name);
        }
    } catch (e) {
        console.error(e);
    }

    state.currentProfileIndex++;
    
    setTimeout(() => {
        card.style.transition = 'none';
        card.style.transform = 'translateX(0) rotate(0)';
        card.style.opacity = '1';
        
        card.querySelector('.swipe-card-overlay-like').style.opacity = 0;
        card.querySelector('.swipe-card-overlay-nope').style.opacity = 0;
        
        displayCurrentProfile();
        
        setTimeout(() => {
            card.style.transition = 'transform 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
        }, 50);
    }, 400);
}

// ===== LIKES PAGE =====
async function loadLikes() {
    // Demo likes loader
    const grid = document.getElementById('likesGrid');
    if (!grid) return;
    
    try {
        // Fetch users who liked me or similar
        const res = await fetch(`${API_URL}/api/profiles`, { headers: getHeaders() });
        const data = await res.json();
        
        if (data.status === "ok" && data.profiles.length > 0) {
            grid.innerHTML = '';
            // Just take some random profiles for Demo Yoqqanlar
            data.profiles.slice(0, 6).forEach(p => {
                const card = document.createElement('div');
                card.className = `like-card ${p.premium_plan !== 'Basic' ? 'glowing-premium-border' : ''}`;
                card.onclick = () => showToast('❤️', `${p.name} sizga yoqdi!`);
                
                const photo = p.photos && p.photos.length > 0 ? `<img src="${p.photos[0]}" style="width:100%;height:100%;object-fit:cover;">` : `👤`;
                
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
    } catch (e) {
        console.error(e);
    }
}

// ===== CHATS & MATCHES =====
async function loadMatches() {
    const list = document.getElementById('matchesList');
    if (!list) return;
    
    try {
        const res = await fetch(`${API_URL}/api/matches`, {
            headers: getHeaders()
        });
        const data = await res.json();
        
        if (data.status === "ok") {
            if (data.matches.length === 0) {
                list.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">💬</div>
                        <h3>Suhbatlar mavjud emas</h3>
                        <p>Swipe orqali yangi juftliklar toping!</p>
                    </div>
                `;
                return;
            }
            
            list.innerHTML = '';
            data.matches.forEach(m => {
                const item = document.createElement('div');
                item.className = 'match-item';
                item.onclick = () => openChatDetail(m.id, m.partner.name);
                
                const avatar = m.partner.photos && m.partner.photos.length > 0 
                    ? `<img src="${m.partner.photos[0]}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">` 
                    : `👤`;
                
                item.innerHTML = `
                    <div class="match-avatar">${avatar}</div>
                    <div class="match-info">
                        <h4>${m.partner.name} ${m.partner.premium_plan !== 'Basic' ? '👑' : ''}</h4>
                        <p>${m.last_message || 'Suhbatni boshlang...'}</p>
                    </div>
                    <div class="match-time">Hozir</div>
                `;
                list.appendChild(item);
            });
        }
    } catch (e) {
        console.error(e);
    }
}

// ===== CHAT ROOM =====
function openChatDetail(matchId, partnerName) {
    state.activeMatchId = matchId;
    navigateTo('chat-detail');
    document.getElementById('headerTitle').textContent = partnerName;
    
    // Clear old interval
    if (state.chatInterval) clearInterval(state.chatInterval);
    
    loadChatMessages();
    
    // Auto refresh chat messages every 3 seconds
    state.chatInterval = setInterval(loadChatMessages, 3000);
}

async function loadChatMessages() {
    if (state.currentPage !== 'chat-detail' || !state.activeMatchId) {
        clearInterval(state.chatInterval);
        return;
    }
    
    try {
        const res = await fetch(`${API_URL}/api/chat/messages?match_id=${state.activeMatchId}`, {
            headers: getHeaders()
        });
        const data = await res.json();
        
        if (data.status === "ok") {
            const container = document.getElementById('chatMessages');
            container.innerHTML = '';
            
            if (data.messages.length === 0) {
                container.innerHTML = `<p class="chat-empty">Juftingizga salom deb yozing! 👋</p>`;
                return;
            }
            
            data.messages.forEach(msg => {
                const bubble = document.createElement('div');
                bubble.className = `chat-bubble ${msg.is_my_message ? 'my-message' : 'partner-message'}`;
                bubble.textContent = msg.text;
                container.appendChild(bubble);
            });
            
            // Scroll to bottom
            container.scrollTop = container.scrollHeight;
        }
    } catch (e) {
        console.error(e);
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chatMessageInput');
    const text = input.value.trim();
    if (!text || !state.activeMatchId) return;
    
    input.value = '';
    
    try {
        const response = await fetch(`${API_URL}/api/chat/send`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({
                match_id: state.activeMatchId,
                text: text
            })
        });
        const data = await response.json();
        
        if (data.status === "ok") {
            loadChatMessages();
            if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
        }
    } catch (e) {
        showToast("⚠️", "Xabar yuborib bo'lmadi");
    }
}

// ===== EDIT FIELD PROMPT =====
function editFieldPrompt(field) {
    if (tg) {
        const labels = {
            name: "Ismingizni kiriting",
            age: "Yoshingizni kiriting",
            city: "Shahringizni kiriting",
            bio: "O'zingiz haqingizda yozing",
            height: "Bo'yingizni kiriting (sm)"
        };
        
        tg.showPopup({
            title: labels[field] || "Profilni tahrirlash",
            message: "Ushbu maydonni o'zgartirishni xohlaysizmi?",
            buttons: [
                {id: 'yes', type: 'default', text: 'Ha'},
                {id: 'no', type: 'cancel', text: 'Yo\'q'}
            ]
        }, (buttonId) => {
            if (buttonId === 'yes') {
                // To keep it simple, we ask via Telegram input
                // In full implementation, we'd open a dialog.
                // Let's use simple prompt
                const newVal = prompt(labels[field]);
                if (newVal !== null && newVal !== "") {
                    saveProfileField(field, newVal);
                }
            }
        });
    } else {
        const newVal = prompt(`Yangi qiymatni kiriting:`);
        if (newVal !== null && newVal !== "") {
            saveProfileField(field, newVal);
        }
    }
}

async function saveProfileField(field, value) {
    const updateData = {};
    updateData[field] = value;
    
    try {
        const res = await fetch(`${API_URL}/api/profile/update`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify(updateData)
        });
        const data = await res.json();
        if (data.status === "ok") {
            state.user = data.user;
            updateUI();
            showToast("✅", "O'zgarishlar saqlandi!");
        }
    } catch (e) {
        showToast("⚠️", "Saqlab bo'lmadi");
    }
}

// Settings toggle invisible mode
async function toggleInvisibleMode() {
    const chk = document.getElementById('invisibleCheckbox');
    if (!chk) return;
    const nextVal = !chk.checked;
    
    try {
        const res = await fetch(`${API_URL}/api/profile/update`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ is_invisible: nextVal })
        });
        const data = await res.json();
        if (data.status === "ok") {
            state.user = data.user;
            chk.checked = nextVal;
            showToast("👻", nextVal ? "Profil ko'rinmas qilindi" : "Profil faollashtirildi");
        }
    } catch (e) {
        showToast("⚠️", "Xatolik yuz berdi");
    }
}

function deleteAccountPrompt() {
    const confirmDelete = confirm("Hisobingizni butunlay o'chirishni xohlaysizmi? Bu amalni ortga qaytarib bo'lmaydi.");
    if (confirmDelete) {
        // Send delete action to api
        deleteAccount();
    }
}

async function deleteAccount() {
    try {
        const res = await fetch(`${API_URL}/api/admin/user/action`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({
                user_id: state.user.id,
                action: "delete"
            })
        });
        const data = await res.json();
        if (data.status === "ok") {
            showToast("🗑️", "Profil o'chirildi");
            // Refresh
            window.location.reload();
        }
    } catch (e) {
        showToast("⚠️", "O'chirishda xatolik");
    }
}

// ===== REFERRAL SYSTEM =====
async function loadReferrals() {
    try {
        const res = await fetch(`${API_URL}/api/referrals`, { headers: getHeaders() });
        const data = await res.json();
        if (data.status === "ok") {
            document.getElementById('refCount').textContent = data.count;
            document.getElementById('refBonus').textContent = data.bonus_points;
        }
    } catch (e) {
        console.error(e);
    }
}

// ===== ADMIN PANEL CONTROLS =====
let currentAdminTab = 'broadcast';

function switchAdminTab(tabName) {
    document.querySelectorAll('.admin-section').forEach(s => s.style.display = 'none');
    document.querySelectorAll('.admin-tab').forEach(t => t.classList.remove('active'));
    
    document.getElementById(`admin-sec-${tabName}`).style.display = 'block';
    event.currentTarget.classList.add('active');
    
    currentAdminTab = tabName;
    
    if (tabName === 'payments') {
        loadAdminPayments();
    }
}

async function loadAdminStats() {
    try {
        const res = await fetch(`${API_URL}/api/admin/stats`, { headers: getHeaders() });
        const data = await res.json();
        
        if (data.status === "ok") {
            document.getElementById('adminTotalUsers').textContent = data.stats.total_users;
            document.getElementById('adminActiveUsers').textContent = data.stats.active_users;
            document.getElementById('adminRegToday').textContent = data.stats.registered_today;
            document.getElementById('adminPremiumUsers').textContent = data.stats.premium_users;
        }
    } catch (e) {
        console.error(e);
    }
}

async function sendAdminBroadcast() {
    const textInput = document.getElementById('adminBroadcastText');
    const msg = textInput.value.trim();
    if (!msg) {
        showToast("⚠️", "Xabar matnini kiriting!");
        return;
    }
    
    showToast("⏳", "Broadcast yuborilmoqda...");
    try {
        const res = await fetch(`${API_URL}/api/admin/broadcast`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ message: msg })
        });
        const data = await res.json();
        if (data.status === "ok") {
            textInput.value = '';
            showToast("📣", data.message);
        } else {
            showToast("⚠️", data.message || "Xatolik yuz berdi");
        }
    } catch (e) {
        showToast("⚠️", "API xatoligi");
    }
}

async function loadAdminPayments() {
    const list = document.getElementById('adminPaymentsList');
    if (!list) return;
    
    list.innerHTML = `<p class="admin-loading">To'lovlar yuklanmoqda...</p>`;
    
    try {
        const res = await fetch(`${API_URL}/api/admin/payments`, { headers: getHeaders() });
        const data = await res.json();
        
        if (data.status === "ok") {
            if (data.payments.length === 0) {
                list.innerHTML = `<p class="admin-empty">Kutilayotgan to'lovlar yo'q</p>`;
                return;
            }
            
            list.innerHTML = '';
            data.payments.forEach(p => {
                const card = document.createElement('div');
                card.className = 'admin-pay-card glass-card';
                card.innerHTML = `
                    <div class="admin-pay-info">
                        <h4>${p.user ? p.user.name : "Noma'lum"} (ID: ${p.user ? p.user.id : "—"})</h4>
                        <p>Tarif: <b>${p.description}</b></p>
                        <p>Sana: ${p.created_at.substring(0, 16).replace('T', ' ')}</p>
                        <p>Summa: <b>${p.amount.toLocaleString()} so'm</b></p>
                    </div>
                    <div class="admin-pay-actions">
                        <button class="btn-primary btn-sm" onclick="handlePaymentAction(${p.id}, 'approve')">Tasdiqlash</button>
                        <button class="btn-secondary btn-sm" onclick="handlePaymentAction(${p.id}, 'reject')">Rad etish</button>
                    </div>
                `;
                list.appendChild(card);
            });
        }
    } catch (e) {
        list.innerHTML = `<p class="admin-error">Yuklashda xatolik</p>`;
    }
}

async function handlePaymentAction(paymentId, action) {
    try {
        const res = await fetch(`${API_URL}/api/admin/payment/action`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({
                payment_id: paymentId,
                action: action
            })
        });
        const data = await res.json();
        if (data.status === "ok") {
            showToast("💳", `To'lov ${action === 'approve' ? 'tasdiqlandi' : 'rad etildi'}`);
            loadAdminPayments();
            loadAdminStats();
        }
    } catch (e) {
        showToast("⚠️", "Amal bajarilmadi");
    }
}

async function searchAdminUsers() {
    const query = document.getElementById('adminUserSearchInput').value.trim();
    const list = document.getElementById('adminUsersList');
    if (!list) return;
    
    list.innerHTML = `<p class="admin-loading">Qidirilmoqda...</p>`;
    
    try {
        const res = await fetch(`${API_URL}/api/admin/users?search=${encodeURIComponent(query)}`, {
            headers: getHeaders()
        });
        const data = await res.json();
        
        if (data.status === "ok") {
            if (data.users.length === 0) {
                list.innerHTML = `<p class="admin-empty">Hech kim topilmadi</p>`;
                return;
            }
            
            list.innerHTML = '';
            data.users.forEach(u => {
                const card = document.createElement('div');
                card.className = 'admin-user-card glass-card';
                card.innerHTML = `
                    <div class="admin-user-info">
                        <h4>${u.name}, ${u.age} yosh</h4>
                        <p>ID: ${u.id} | Telegram ID: <code>${u.telegram_id}</code></p>
                        <p>Shahar: ${u.city} | Holat: <b>${u.status}</b></p>
                    </div>
                    <div class="admin-user-actions">
                        ${u.status !== 'Bloklangan' 
                            ? `<button class="btn-secondary btn-sm" onclick="handleUserAdminAction(${u.id}, 'ban')">Bloklash</button>` 
                            : `<button class="btn-primary btn-sm" onclick="handleUserAdminAction(${u.id}, 'unban')">Blokdan yechish</button>`
                        }
                        <button class="btn-secondary btn-sm settings-danger" onclick="handleUserAdminAction(${u.id}, 'delete')">O'chirish</button>
                    </div>
                `;
                list.appendChild(card);
            });
        }
    } catch (e) {
        list.innerHTML = `<p class="admin-error">Qidiruvda xatolik</p>`;
    }
}

async function handleUserAdminAction(userId, action) {
    if (action === 'delete') {
        if (!confirm("Ushbu foydalanuvchini butunlay o'chirmoqchimisiz?")) return;
    }
    
    try {
        const res = await fetch(`${API_URL}/api/admin/user/action`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({
                user_id: userId,
                action: action
            })
        });
        const data = await res.json();
        if (data.status === "ok") {
            showToast("👤", `Amal bajarildi: ${action}`);
            searchAdminUsers();
            loadAdminStats();
        }
    } catch (e) {
        showToast("⚠️", "Xatolik yuz berdi");
    }
}

// ===== POPUP AND TOAST =====
function openChat() {
    closeMatchPopup();
    navigateTo('matches');
}

function closeMatchPopup() {
    document.getElementById('matchPopup').style.display = 'none';
}

function showMatchPopup(partnerName) {
    document.getElementById('matchPartnerName').textContent = partnerName || 'Kimdir';
    document.getElementById('matchPopup').style.display = 'flex';
    createConfetti();
    if (tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
}

function createConfetti() {
    const container = document.getElementById('matchConfetti');
    if (!container) return;
    container.innerHTML = '';
    const colors = ['#ff6b9d', '#c44dff', '#4d9dff', '#ffd700'];

    for (let i = 0; i < 30; i++) {
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
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function shareReferral() {
    const shareUrl = `https://t.me/kairyx_bot?start=ref_${state.user?.id || '0'}`;
    const text = 'Kairyx - sevgi topish ilovasi! Men foydalanyapman, siz ham qo\'shiling 💕';
    
    if (tg) {
        tg.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(text)}`);
    } else {
        navigator.clipboard.writeText(shareUrl);
        showToast('📋', "Taklif havolasi buferga nusxalandi!");
    }
}
