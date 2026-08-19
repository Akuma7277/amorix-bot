/* ============================================
   AMORIX MINI APP - APPLICATION LOGIC
   ============================================ */

// Telegram WebApp SDK
const tg = window.Telegram?.WebApp;

// App State
const state = {
    currentPage: 'home',
    pageHistory: [],
    user: null,
    profiles: [],
    currentProfileIndex: 0,
    likes: [],
    matches: [],
    touchStartX: 0,
    touchStartY: 0,
    isDragging: false,
};

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    // Initialize Telegram WebApp
    if (tg) {
        tg.expand();
        tg.enableClosingConfirmation();
        tg.setHeaderColor('#0a0a1a');
        tg.setBackgroundColor('#0a0a1a');

        // Theme params
        const theme = tg.themeParams;
        if (theme) {
            document.documentElement.style.setProperty('--tg-bg', theme.bg_color || '#0a0a1a');
        }
    }

    // Create background particles
    createParticles();

    // Simulate loading
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Hide loading, show app
    document.getElementById('loadingScreen').classList.add('hidden');
    document.getElementById('appContainer').style.display = 'flex';

    // Load user data
    loadUserData();

    // Setup swipe gestures
    setupSwipeGestures();
}

// ===== PARTICLES =====
function createParticles() {
    const container = document.getElementById('bgParticles');
    const colors = ['rgba(255,107,157,0.3)', 'rgba(196,77,255,0.3)', 'rgba(77,157,255,0.3)', 'rgba(255,215,0,0.2)'];

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

// ===== USER DATA =====
function loadUserData() {
    // In a real app, this would call the API with Telegram initData
    // For now, use demo data or Telegram user info
    const userData = tg?.initDataUnsafe?.user;

    if (userData) {
        state.user = {
            name: userData.first_name || 'Foydalanuvchi',
            age: '',
            city: '',
            bio: '',
            premium: false,
            completion: 65,
        };
    } else {
        // Demo mode
        state.user = {
            name: 'Foydalanuvchi',
            age: '',
            city: 'Toshkent',
            bio: '',
            premium: false,
            completion: 65,
        };
    }

    updateUI();
}

function updateUI() {
    if (!state.user) return;

    // Profile card
    document.getElementById('profileName').textContent = state.user.name;
    document.getElementById('profileMeta').textContent = [state.user.age, state.user.city].filter(Boolean).join(' • ') || "Profilni to'ldiring";

    // Completion ring
    const completion = state.user.completion || 0;
    document.getElementById('completionText').textContent = completion + '%';
    document.getElementById('completionRing').setAttribute('stroke-dasharray', `${completion}, 100`);

    // Premium badge
    if (state.user.premium) {
        document.getElementById('premiumBadge').style.display = 'flex';
    }

    // Edit fields
    document.getElementById('editName').textContent = state.user.name || '—';
    document.getElementById('editAge').textContent = state.user.age || '—';
    document.getElementById('editCity').textContent = state.user.city || '—';
    document.getElementById('editBio').textContent = state.user.bio || '—';
}

// ===== NAVIGATION =====
function navigateTo(pageName) {
    if (pageName === state.currentPage) return;

    // Save history
    state.pageHistory.push(state.currentPage);

    // Update pages
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const targetPage = document.getElementById(`page-${pageName}`);
    if (targetPage) {
        targetPage.classList.add('active');
    }

    // Update nav
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const navItem = document.querySelector(`.nav-item[data-page="${pageName}"]`);
    if (navItem) navItem.classList.add('active');

    // Update header
    const titles = {
        home: 'Amorix',
        search: 'Qidirish',
        likes: 'Layklar',
        matches: 'Suhbatlar',
        premium: 'Premium',
        profile: 'Profil',
        referrals: 'Takliflar',
        views: "Ko'rishlar",
        settings: 'Sozlamalar',
    };

    document.getElementById('headerTitle').textContent = titles[pageName] || 'Amorix';

    // Show/hide back button
    const backBtn = document.getElementById('backBtn');
    if (pageName !== 'home') {
        backBtn.style.display = 'flex';
    } else {
        backBtn.style.display = 'none';
    }

    state.currentPage = pageName;

    // Haptic feedback
    if (tg?.HapticFeedback) {
        tg.HapticFeedback.selectionChanged();
    }
}

function goBack() {
    const prevPage = state.pageHistory.pop() || 'home';
    state.currentPage = null; // Reset to allow navigation
    navigateTo(prevPage);
    state.pageHistory.pop(); // Remove duplicate
}

// ===== SWIPE GESTURES =====
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
        const rotation = currentX * 0.1;
        card.style.transform = `translateX(${currentX}px) rotate(${rotation}deg)`;

        // Show overlays
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

// ===== ACTIONS =====
function swipeAction(action) {
    const card = document.getElementById('currentSwipeCard');

    if (action === 'like') {
        card.style.transform = 'translateX(120%) rotate(20deg)';
        card.style.opacity = '0';
        showToast('❤️', 'Layk yuborildi!');
        if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');
    } else if (action === 'nope') {
        card.style.transform = 'translateX(-120%) rotate(-20deg)';
        card.style.opacity = '0';
        if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
    } else if (action === 'superlike') {
        card.style.transform = 'translateY(-120%) scale(0.8)';
        card.style.opacity = '0';
        showToast('⭐', 'Super Like yuborildi!');
        if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('heavy');
    }

    // Send action to bot
    sendAction(`swipe_${action}`);

    // Reset card after animation
    setTimeout(() => {
        card.style.transition = 'none';
        card.style.transform = 'translateX(0) rotate(0)';
        card.style.opacity = '1';

        // Reset overlays
        card.querySelector('.swipe-card-overlay-like').style.opacity = 0;
        card.querySelector('.swipe-card-overlay-nope').style.opacity = 0;

        setTimeout(() => {
            card.style.transition = 'transform 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
        }, 50);
    }, 400);
}

function selectPlan(plan) {
    if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');
    sendAction(`premium_plan_${plan}`);
    showToast('👑', `${plan.charAt(0).toUpperCase() + plan.slice(1)} rejasi tanlandi! Botga qayting.`);
}

function shareReferral() {
    if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
    const userId = tg?.initDataUnsafe?.user?.id || '0';
    const shareUrl = `https://t.me/amorix_bot?start=ref_${userId}`;

    if (tg) {
        tg.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent('Amorix - sevgi topish ilovasi! Men allaqachon foydalanaman 💕')}`);
    }
    showToast('📤', "Havola ulashishga tayyor!");
}

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

// ===== CONFETTI =====
function createConfetti() {
    const container = document.getElementById('matchConfetti');
    container.innerHTML = '';
    const colors = ['#ff6b9d', '#c44dff', '#4d9dff', '#ffd700', '#4dff9d', '#ff6b6b'];

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

// ===== SEND ACTION TO BOT =====
function sendAction(action) {
    if (tg) {
        tg.sendData(JSON.stringify({ action: action, timestamp: Date.now() }));
    } else {
        console.log('Action:', action);
    }
}

// ===== TOAST NOTIFICATIONS =====
function showToast(icon, message) {
    const container = document.getElementById('toastContainer');
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

// ===== LOAD PROFILES (demo) =====
function loadProfiles() {
    showToast('🔍', "Anketalar qidirilmoqda...");
    // In production, this calls the API
}
