const tg = window.Telegram?.WebApp;
const API_URL = (window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1"))
    ? window.location.origin
    : "https://amorix-bot-production.up.railway.app";

const AVAILABLE_INTERESTS = [
    "🎮 Gaming", "🎵 Music", "🏋️ Fitness", "✈️ Travel", 
    "📚 Books", "🎬 Movies", "⚽ Sport", "💻 Technology", 
    "🍳 Cooking", "🎨 Art", "📸 Photography", "☕ Coffee"
];

let currentUser = null;
let isAdminUser = false;
let currentView = "";
let base64Photo = "";
let selectedRegInterests = [];
let selectedEditInterests = [];

let discoverProfiles = [];
let currentDiscoverIndex = 0;
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
    const views = ['verifyingScreen', 'registrationScreen', 'pendingScreen', 'approvedScreen', 'rejectedScreen', 'bannedScreen', 'errorScreen'];
    views.forEach(v => {
        const el = document.getElementById(v);
        if (el) el.style.display = (v === viewId) ? 'block' : 'none';
    });

    const adminBtn = document.getElementById('btnHeaderAdmin');
    if (adminBtn) adminBtn.style.display = isAdminUser ? 'block' : 'none';
}

async function verifySession() {
    showView('verifyingScreen');
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 12000);

    try {
        const response = await fetch(`${API_URL}/api/session?${getQueryParams()}`, {
            method: "GET",
            headers: getHeaders(),
            signal: controller.signal
        });
        clearTimeout(timeout);

        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();

        if (data.success) {
            isAdminUser = !!data.is_admin;
            currentUser = data.user;
            const status = data.user_status;

            if (status === 'DRAFT') {
                showView('registrationScreen');
                initRegInterests();
            } else if (status === 'PENDING_APPROVAL') {
                showView('pendingScreen');
            } else if (status === 'APPROVED') {
                showView('approvedScreen');
                populateMyProfile();
                switchTab('viewDiscover');
            } else if (status === 'REJECTED') {
                showView('rejectedScreen');
            } else if (status === 'BANNED') {
                showView('bannedScreen');
            }
        } else {
            throw new Error(data.error?.message || "Auth failed");
        }
    } catch (e) {
        clearTimeout(timeout);
        showView('errorScreen');
        document.getElementById('errorText').textContent = `Xatolik: ${e.message}`;
    }
}

// ----------------- REGISTRATION WIZARD -----------------
function initRegInterests() {
    const container = document.getElementById('regInterestsContainer');
    container.innerHTML = "";
    AVAILABLE_INTERESTS.forEach(intTag => {
        const span = document.createElement('span');
        span.className = "tag-badge tag-selectable";
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

document.getElementById('regName').addEventListener('input', (e) => {
    document.getElementById('nameCounter').textContent = `${e.target.value.length}/30`;
});
document.getElementById('regBio').addEventListener('input', (e) => {
    document.getElementById('bioCounter').textContent = `${e.target.value.length}/200`;
});

document.getElementById('regPhotoInput').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        if (file.size > 5 * 1024 * 1024) {
            alert("Rasm hajmi 5MB dan oshmasligi kerak!");
            return;
        }
        const reader = new FileReader();
        reader.onload = function(evt) {
            base64Photo = evt.target.result;
            document.getElementById('regPhotoPreview').src = base64Photo;
            document.getElementById('regPhotoPreview').style.display = 'block';
            document.getElementById('photoPlaceholderText').style.display = 'none';
        };
        reader.readAsDataURL(file);
    }
});

function nextRegStep(currStep) {
    if (currStep === 1) {
        const age = parseInt(document.getElementById('regAge').value);
        if (!age || age < 18) {
            alert("Kairyx-dan foydalanish uchun yoshingiz 18 yoki undan katta bo'lishi shart!");
            return;
        }
    } else if (currStep === 2) {
        const name = document.getElementById('regName').value.trim();
        const city = document.getElementById('regCity').value.trim();
        if (!name || !city) {
            alert("Ism va shaharingizni to'ldiring!");
            return;
        }
    } else if (currStep === 3) {
        if (!base64Photo) {
            alert("Iltimos, profilingiz uchun rasm yuklang!");
            return;
        }
    } else if (currStep === 4) {
        const bio = document.getElementById('regBio').value.trim();
        if (!bio) {
            alert("O'zingiz haqingizda qisqacha ma'lumot yozing!");
            return;
        }
        // Prepare summary
        document.getElementById('summaryPhoto').src = base64Photo;
        document.getElementById('summaryNameAge').textContent = `${document.getElementById('regName').value.trim()}, ${document.getElementById('regAge').value}`;
        document.getElementById('summaryCity').textContent = document.getElementById('regCity').value.trim();
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
    const titles = [
        "Qadam 1: Yoshni tasdiqlash",
        "Qadam 2: Shaxsiy ma'lumotlar",
        "Qadam 3: Profil surati",
        "Qadam 4: Bio va Qiziqishlar",
        "Qadam 5: Anketani tasdiqlash"
    ];
    document.getElementById('wizardStepTitle').textContent = titles[step - 1];
    document.getElementById('wizardStepCount').textContent = `${step} / 5`;
    document.getElementById('wizardProgressBar').style.width = `${step * 20}%`;
}

async function submitRegistration() {
    const terms = document.getElementById('regTerms').checked;
    const errText = document.getElementById('regError');
    errText.style.display = 'none';

    if (!terms) {
        errText.textContent = "Foydalanish qoidalariga rozilik belgilanishi shart.";
        errText.style.display = 'block';
        return;
    }

    const btn = document.getElementById('btnSubmitReg');
    btn.disabled = true;
    btn.textContent = "Yuborilmoqda...";

    try {
        const res = await fetch(`${API_URL}/api/register?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({
                name: document.getElementById('regName').value.trim(),
                age: parseInt(document.getElementById('regAge').value),
                city: document.getElementById('regCity').value.trim(),
                photo: base64Photo,
                bio: document.getElementById('regBio').value.trim(),
                interests: selectedRegInterests,
                terms_accepted: true
            })
        });
        const data = await res.json();
        if (data.success) {
            showView('pendingScreen');
        } else {
            throw new Error(data.error?.message || "Xatolik yuz berdi");
        }
    } catch (e) {
        btn.disabled = false;
        btn.textContent = "Arizani yuborish 🚀";
        errText.textContent = e.message;
        errText.style.display = 'block';
    }
}

// ----------------- TAB NAVIGATION -----------------
function switchTab(tabId) {
    const tabs = ['viewDiscover', 'viewMatches', 'viewChats', 'viewProfile', 'viewAdmin'];
    tabs.forEach(t => {
        const el = document.getElementById(t);
        if (el) el.style.display = (t === tabId) ? 'block' : 'none';
    });

    const navBtns = {
        'viewDiscover': 'btnNavDiscover',
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
    if (tabId === 'viewMatches') loadMatchesList();
    if (tabId === 'viewChats') loadChatsList();
    if (tabId === 'viewProfile') populateMyProfile();
    if (tabId === 'viewAdmin') loadAdminData();
}

document.getElementById('btnHeaderAdmin').addEventListener('click', () => switchTab('viewAdmin'));
document.getElementById('btnHeaderSettings').addEventListener('click', () => switchTab('viewProfile'));

// ----------------- DISCOVERY & SWIPE -----------------
async function loadDiscoverProfiles() {
    const container = document.getElementById('cardStackContainer');
    container.innerHTML = "<p style='color: var(--text-muted); text-align: center; padding-top: 150px; font-style: italic;'>Qidirilmoqda...</p>";

    const minAge = document.getElementById('filterMinAge').value;
    const maxAge = document.getElementById('filterMaxAge').value;
    const city = document.getElementById('filterCity').value;

    const q = new URLSearchParams(getQueryParams());
    if (minAge) q.append("min_age", minAge);
    if (maxAge) q.append("max_age", maxAge);
    if (city) q.append("city", city);

    try {
        const res = await fetch(`${API_URL}/api/profiles?${q.toString()}`, { method: "GET", headers: getHeaders() });
        const data = await res.json();
        if (data.success) {
            discoverProfiles = data.profiles;
            currentDiscoverIndex = 0;
            renderDiscoverCard();
        }
    } catch (e) {
        container.innerHTML = `<p style='color: var(--primary); text-align: center; padding-top: 150px;'>Xatolik: ${e.message}</p>`;
    }
}

function renderDiscoverCard() {
    const container = document.getElementById('cardStackContainer');
    if (!discoverProfiles || discoverProfiles.length === 0 || currentDiscoverIndex >= discoverProfiles.length) {
        container.innerHTML = `
            <div class="glass-panel" style="padding: 40px 20px; text-align: center; margin-top: 50px;">
                <div style="font-size: 40px; margin-bottom: 10px;">💫</div>
                <h3 style="color: var(--primary); margin-top: 0;">Hozircha anketalar tugadi</h3>
                <p style="color: var(--text-muted); font-size: 13px; line-height: 1.5;">Yangi a'zolar qo'shilgach bu yerda ko'rinadi. Filtrlarni o'zgartirib qayta qidirishingiz mumkin.</p>
                <button onclick="loadDiscoverProfiles()" style="background: var(--primary-gradient); color: #fff; border: none; padding: 10px 20px; border-radius: var(--radius-sm); font-weight: bold; cursor: pointer; margin-top: 10px;">🔄 Qayta yuklash</button>
            </div>
        `;
        return;
    }

    const p = discoverProfiles[currentDiscoverIndex];
    activeTargetUser = p;

    container.innerHTML = `
        <div class="dating-card">
            <div class="card-image-wrap" onclick="openProfileDetailModal(${p.id})">
                <img src="${p.photo}">
                <div class="card-overlay-info">
                    <h2 style="margin: 0; font-size: 24px; color: #fff;">${p.name}, ${p.age}</h2>
                    <p style="margin: 4px 0 8px 0; color: var(--primary); font-size: 13px; font-weight: bold;">📍 ${p.city}</p>
                    <p style="margin: 0; color: var(--text-sub); font-size: 13px; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">${p.bio}</p>
                </div>
            </div>
            <div style="padding: 12px 20px 16px 20px; background: #121226; display: flex; justify-content: space-between; align-items: center;">
                <button class="btn-action-circle btn-pass" onclick="handleSwipe(${p.id}, false)">👎</button>
                <button class="btn-action-circle btn-info" onclick="openProfileDetailModal(${p.id})">ℹ️</button>
                <button class="btn-action-circle btn-like" onclick="handleSwipe(${p.id}, true)">💖</button>
            </div>
        </div>
    `;
}

async function handleSwipe(targetId, isLike) {
    if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');

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
        console.error(e);
    }

    currentDiscoverIndex++;
    renderDiscoverCard();
}

function showMatchModal(partner, matchId) {
    document.getElementById('matchPartnerName').textContent = partner.name;
    document.getElementById('matchPartnerAvatar').src = partner.photo;
    document.getElementById('matchMyAvatar').src = currentUser?.photo || "";
    document.getElementById('btnMatchChat').onclick = () => {
        closeMatchModal();
        openChatWindow(matchId, partner);
    };
    document.getElementById('matchModal').style.display = 'flex';
}

function closeMatchModal() {
    document.getElementById('matchModal').style.display = 'none';
}

// ----------------- FILTERS MODAL -----------------
function openFilterModal() { document.getElementById('filterModal').style.display = 'flex'; }
function closeFilterModal() { document.getElementById('filterModal').style.display = 'none'; }
function applyFilters() {
    closeFilterModal();
    loadDiscoverProfiles();
}
function resetFilters() {
    document.getElementById('filterMinAge').value = "";
    document.getElementById('filterMaxAge').value = "";
    document.getElementById('filterCity').value = "";
    closeFilterModal();
    loadDiscoverProfiles();
}

// ----------------- PROFILE DETAIL MODAL -----------------
function openProfileDetailModal(userId) {
    const user = discoverProfiles.find(u => u.id === userId) || activeTargetUser;
    if (!user) return;

    document.getElementById('detailPhoto').src = user.photo;
    document.getElementById('detailNameAge').textContent = `${user.name}, ${user.age}`;
    document.getElementById('detailCity').textContent = `📍 ${user.city}`;
    document.getElementById('detailBio').textContent = user.bio;

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

// ----------------- BLOCK & REPORT -----------------
async function blockUser(targetId) {
    if (!confirm("Ushbu foydalanuvchini bloklamoqchimisiz? U boshqa profilingizni ko'ra olmaydi.")) return;
    try {
        const res = await fetch(`${API_URL}/api/user/block?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ target_id: targetId })
        });
        const data = await res.json();
        if (data.success) {
            alert("Foydalanuvchi bloklandi.");
            closeProfileDetailModal();
            loadDiscoverProfiles();
            loadMatchesList();
        }
    } catch (e) { alert(e.message); }
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
        const data = await res.json();
        if (data.success) {
            alert("Shikoyatingiz moderatorlarga yuborildi. Rahmat!");
            closeReportModal();
            closeProfileDetailModal();
        }
    } catch (e) { alert(e.message); }
}

// ----------------- MATCHES & CHAT -----------------
async function loadMatchesList() {
    const container = document.getElementById('matchesList');
    container.innerHTML = "<p style='color: var(--text-muted); grid-column: span 2; text-align: center;'>Yuklanmoqda...</p>";

    try {
        const res = await fetch(`${API_URL}/api/matches?${getQueryParams()}`, { method: "GET", headers: getHeaders() });
        const data = await res.json();
        if (data.success) {
            const matches = data.matches;
            if (matches.length === 0) {
                container.innerHTML = "<p style='color: var(--text-muted); grid-column: span 2; text-align: center; padding: 40px 0;'>Hozircha juftliklar yo'q. Discover bo'limida Like bosing!</p>";
                return;
            }
            container.innerHTML = "";
            matches.forEach(m => {
                const card = document.createElement('div');
                card.className = "glass-panel";
                card.style.cssText = "padding: 12px; text-align: center; cursor: pointer;";
                card.onclick = () => openChatWindow(m.match_id, m.partner);
                card.innerHTML = `
                    <img src="${m.partner.photo}" style="width: 70px; height: 70px; object-fit: cover; border-radius: 50%; border: 2px solid var(--primary); margin: 0 auto 8px auto; display: block;">
                    <h4 style="margin: 0; font-size: 14px; color: #fff;">${m.partner.name}</h4>
                    <span style="font-size: 11px; color: var(--primary); margin-top: 4px; display: inline-block;">💬 Suhbat</span>
                `;
                container.appendChild(card);
            });
        }
    } catch (e) {
        container.innerHTML = `<p style='color: var(--primary); grid-column: span 2; text-align: center;'>Xatolik: ${e.message}</p>`;
    }
}

async function loadChatsList() {
    const container = document.getElementById('chatsList');
    container.innerHTML = "<p style='color: var(--text-muted); text-align: center;'>Suhbatlar yuklanmoqda...</p>";

    try {
        const res = await fetch(`${API_URL}/api/matches?${getQueryParams()}`, { method: "GET", headers: getHeaders() });
        const data = await res.json();
        if (data.success) {
            const matches = data.matches;
            if (matches.length === 0) {
                container.innerHTML = "<p style='color: var(--text-muted); text-align: center; padding: 40px 0;'>Suhbatlar mavjud emas.</p>";
                return;
            }
            container.innerHTML = "";
            matches.forEach(m => {
                const item = document.createElement('div');
                item.className = "glass-panel";
                item.style.cssText = "padding: 12px 16px; display: flex; align-items: center; gap: 12px; cursor: pointer;";
                item.onclick = () => openChatWindow(m.match_id, m.partner);
                const lastTxt = m.last_message ? m.last_message.text : "Yangi juftlik! Suhbatni boshlang.";
                item.innerHTML = `
                    <img src="${m.partner.photo}" style="width: 48px; height: 48px; object-fit: cover; border-radius: 50%; border: 1px solid var(--primary);">
                    <div style="flex: 1; min-width: 0;">
                        <div style="display: flex; justify-content: space-between;">
                            <h4 style="margin: 0; font-size: 15px; color: #fff;">${m.partner.name}</h4>
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
    document.getElementById('chatPartnerPhoto').src = partner.photo;
    document.getElementById('chatPartnerName').textContent = partner.name;
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
            const msgs = data.messages;
            const container = document.getElementById('chatMessages');
            if (msgs.length === container.children.length) return;

            container.innerHTML = "";
            msgs.forEach(m => {
                const bubble = document.createElement('div');
                const timeStr = new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                if (m.sender_id === 0) {
                    bubble.style.cssText = "align-self: center; background: rgba(255,255,255,0.05); color: var(--text-muted); padding: 6px 14px; border-radius: var(--radius-full); font-size: 11px;";
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

document.getElementById('chatInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendChatMessage();
});

function openChatOptionsMenu() {
    if (!activeTargetUser) return;
    const action = confirm("Foydalanuvchi ustidan shikoyat qilish yoki bloklashni xohlaysizmi?");
    if (action) {
        openReportModal(activeTargetUser.id);
    }
}

// ----------------- PROFILE & SETTINGS -----------------
function populateMyProfile() {
    if (!currentUser) return;
    document.getElementById('myPhoto').src = currentUser.photo || "";
    document.getElementById('myNameAge').textContent = `${currentUser.name}, ${currentUser.age}`;
    document.getElementById('myCity').textContent = `📍 ${currentUser.city}`;
    document.getElementById('myBio').textContent = currentUser.bio || "Mavjud emas";

    const pct = currentUser.completion_percentage || 100;
    document.getElementById('myCompletionPct').textContent = `${pct}%`;
    document.getElementById('myCompletionBar').style.width = `${pct}%`;

    const intContainer = document.getElementById('myInterestsList');
    intContainer.innerHTML = "";
    (currentUser.interests || []).forEach(tag => {
        const b = document.createElement('span');
        b.className = "tag-badge";
        b.textContent = tag;
        intContainer.appendChild(b);
    });
}

function openEditProfileModal() {
    if (!currentUser) return;
    document.getElementById('editName').value = currentUser.name;
    document.getElementById('editCity').value = currentUser.city;
    document.getElementById('editBio').value = currentUser.bio;

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

async function saveProfileEdit() {
    const name = document.getElementById('editName').value.trim();
    const city = document.getElementById('editCity').value.trim();
    const bio = document.getElementById('editBio').value.trim();

    try {
        const res = await fetch(`${API_URL}/api/profile/update?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ name, city, bio, interests: selectedEditInterests })
        });
        const data = await res.json();
        if (data.success) {
            currentUser = data.user;
            populateMyProfile();
            closeEditProfileModal();
        }
    } catch (e) { alert(e.message); }
}

async function openBlockedUsersModal() {
    const container = document.getElementById('blockedUsersList');
    container.innerHTML = "<p style='color: var(--text-muted);'>Yuklanmoqda...</p>";
    document.getElementById('blockedUsersModal').style.display = 'flex';

    try {
        const res = await fetch(`${API_URL}/api/user/blocked?${getQueryParams()}`, { method: "GET", headers: getHeaders() });
        const data = await res.json();
        if (data.success) {
            const users = data.blocked_users;
            if (users.length === 0) {
                container.innerHTML = "<p style='color: var(--text-muted); font-size: 13px;'>Bloklangan foydalanuvchilar yo'q.</p>";
                return;
            }
            container.innerHTML = "";
            users.forEach(u => {
                const item = document.createElement('div');
                item.style.cssText = "display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--border-subtle);";
                item.innerHTML = `
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <img src="${u.photo}" style="width: 36px; height: 36px; object-fit: cover; border-radius: 50%;">
                        <span style="font-size: 14px; font-weight: bold;">${u.name}</span>
                    </div>
                    <button onclick="unblockUser(${u.id})" style="background: rgba(255,255,255,0.06); border: 1px solid var(--border-subtle); color: #fff; padding: 5px 10px; border-radius: var(--radius-sm); font-size: 11px; cursor: pointer;">Blokdan ochish</button>
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
    if (!confirm("DIQQAT: Hisobingizni o'chirmoqchimisiz? Bu amal profilingizni to'xtatadi.")) return;
    try {
        const res = await fetch(`${API_URL}/api/account/delete?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders()
        });
        const data = await res.json();
        if (data.success) {
            alert("Hisobingiz o'chirildi.");
            verifySession();
        }
    } catch (e) { alert(e.message); }
}

function openRulesModal() { document.getElementById('rulesModal').style.display = 'flex'; }
function closeRulesModal() { document.getElementById('rulesModal').style.display = 'none'; }

// ----------------- ADMIN DASHBOARD -----------------
let currentAdminTab = "pending";

function switchAdminTab(tab) {
    currentAdminTab = tab;
    document.getElementById('admSecPending').style.display = (tab === 'pending') ? 'block' : 'none';
    document.getElementById('admSecReports').style.display = (tab === 'reports') ? 'block' : 'none';
    document.getElementById('admSecUsers').style.display = (tab === 'users') ? 'block' : 'none';

    document.getElementById('btnAdmTabPending').style.background = (tab === 'pending') ? "var(--primary-gradient)" : "rgba(255,255,255,0.06)";
    document.getElementById('btnAdmTabReports').style.background = (tab === 'reports') ? "var(--primary-gradient)" : "rgba(255,255,255,0.06)";
    document.getElementById('btnAdmTabUsers').style.background = (tab === 'users') ? "var(--primary-gradient)" : "rgba(255,255,255,0.06)";

    if (tab === 'pending') loadAdminPending();
    if (tab === 'reports') loadAdminReports();
    if (tab === 'users') loadAdminUsers();
}

async function loadAdminData() {
    try {
        const res = await fetch(`${API_URL}/api/admin/stats?${getQueryParams()}`, { method: "GET", headers: getHeaders() });
        const data = await res.json();
        if (data.success) {
            document.getElementById('admStatPending').textContent = data.stats.pending;
            document.getElementById('admStatApproved').textContent = data.stats.approved;
            document.getElementById('admStatTotal').textContent = data.stats.total;
        }
    } catch (e) {}
    switchAdminTab(currentAdminTab);
}

async function loadAdminPending() {
    const container = document.getElementById('admPendingList');
    container.innerHTML = "<p style='color: var(--text-muted);'>Arizalar yuklanmoqda...</p>";

    try {
        const res = await fetch(`${API_URL}/api/admin/pending?${getQueryParams()}`, { method: "GET", headers: getHeaders() });
        const data = await res.json();
        if (data.success) {
            const users = data.users;
            if (users.length === 0) {
                container.innerHTML = "<p style='color: var(--accent-green); font-weight: bold; text-align: center;'>Kutilayotgan arizalar yo'q!</p>";
                return;
            }
            container.innerHTML = "";
            users.forEach(u => {
                const card = document.createElement('div');
                card.className = "glass-panel";
                card.style.padding = "14px";
                card.innerHTML = `
                    <div style="display: flex; gap: 12px; align-items: center; margin-bottom: 8px;">
                        <img src="${u.photo}" style="width: 60px; height: 60px; object-fit: cover; border-radius: var(--radius-sm);">
                        <div>
                            <h4 style="margin: 0; color: var(--primary);">${u.name}, ${u.age}</h4>
                            <p style="margin: 2px 0 0 0; font-size: 12px; color: var(--text-muted);">${u.city}</p>
                        </div>
                    </div>
                    <p style="margin: 0 0 10px 0; font-size: 13px; color: var(--text-sub);">${u.bio}</p>
                    <div style="display: flex; gap: 8px;">
                        <button onclick="adminApproveUser(${u.id})" style="flex: 1; background: var(--accent-green); color: #000; border: none; padding: 8px; border-radius: var(--radius-sm); font-weight: bold; cursor: pointer;">Tasdiqlash ✅</button>
                        <button onclick="adminRejectUser(${u.id})" style="flex: 1; background: var(--primary); color: #fff; border: none; padding: 8px; border-radius: var(--radius-sm); font-weight: bold; cursor: pointer;">Rad etish ❌</button>
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
    try {
        const res = await fetch(`${API_URL}/api/admin/reject?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ user_id: id })
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
            const reports = data.reports;
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
                        <span style="color: var(--primary); font-weight: bold; font-size: 13px;">${r.reason}</span>
                        <span style="font-size: 11px; color: var(--text-muted);">${r.status}</span>
                    </div>
                    <p style="margin: 0 0 8px 0; font-size: 13px; color: var(--text-sub);">${r.description || 'Izohsiz'}</p>
                    <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 10px;">
                        Shikoyat qilingan: <b>${r.reported ? r.reported.name : 'Noma`lum'}</b> (ID: ${r.reported ? r.reported.id : '?'})
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <button onclick="adminResolveReport(${r.id}, 'RESOLVE')" style="flex: 1; background: rgba(255,255,255,0.06); border: 1px solid var(--border-subtle); color: #fff; padding: 7px; border-radius: var(--radius-sm); font-size: 11px; cursor: pointer;">Yopish</button>
                        <button onclick="adminResolveReport(${r.id}, 'BAN_USER')" style="flex: 1; background: #ff4747; color: #fff; border: none; padding: 7px; border-radius: var(--radius-sm); font-size: 11px; font-weight: bold; cursor: pointer;">Bloklash ⛔</button>
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

let searchTimer = null;
function debounceUserSearch() {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(loadAdminUsers, 400);
}

async function loadAdminUsers() {
    const container = document.getElementById('admUsersList');
    const q = document.getElementById('admUserSearch').value;
    container.innerHTML = "<p style='color: var(--text-muted);'>Foydalanuvchilar qidirilmoqda...</p>";

    try {
        const res = await fetch(`${API_URL}/api/admin/users?q=${encodeURIComponent(q)}&${getQueryParams()}`, { method: "GET", headers: getHeaders() });
        const data = await res.json();
        if (data.success) {
            const users = data.users;
            if (users.length === 0) {
                container.innerHTML = "<p style='color: var(--text-muted); text-align: center;'>Foydalanuvchi topilmadi.</p>";
                return;
            }
            container.innerHTML = "";
            users.forEach(u => {
                const item = document.createElement('div');
                item.className = "glass-panel";
                item.style.cssText = "padding: 10px; display: flex; justify-content: space-between; align-items: center;";
                const isBanned = u.status === 'BANNED';
                item.innerHTML = `
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <img src="${u.photo || ''}" style="width: 40px; height: 40px; object-fit: cover; border-radius: 50%;">
                        <div>
                            <h4 style="margin: 0; font-size: 14px;">${u.name || 'Draft'}, ${u.age || '?'}</h4>
                            <span style="font-size: 11px; color: ${isBanned ? '#ff4747' : 'var(--accent-green)'};">${u.status}</span>
                        </div>
                    </div>
                    <button onclick="adminToggleBan(${u.id}, ${!isBanned})" style="background: ${isBanned ? 'var(--accent-green)' : '#ff4747'}; color: #000; border: none; padding: 6px 12px; border-radius: var(--radius-sm); font-size: 11px; font-weight: bold; cursor: pointer;">
                        ${isBanned ? 'Faollashtirish' : 'Bloklash'}
                    </button>
                `;
                container.appendChild(item);
            });
        }
    } catch (e) { container.innerHTML = e.message; }
}

async function adminToggleBan(userId, isBan) {
    try {
        const res = await fetch(`${API_URL}/api/admin/user/ban?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ user_id: userId, is_ban: isBan })
        });
        if (res.ok) loadAdminUsers();
    } catch (e) { alert(e.message); }
}

// ----------------- STARTUP -----------------
if (tg) {
    try {
        tg.ready();
        tg.expand();
    } catch (err) {}
}

verifySession();
