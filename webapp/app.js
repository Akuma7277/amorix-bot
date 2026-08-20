const tg = window.Telegram?.WebApp;
const API_URL = (window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1"))
    ? window.location.origin
    : "https://amorix-bot-production.up.railway.app";

let base64Photo = "";
let isAdminUser = false;
let currentView = "";
let currentUser = null;
let datingProfiles = [];
let currentProfileIndex = 0;
let currentMatchId = null;
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
    const views = ['verifyingScreen', 'registrationScreen', 'pendingScreen', 'approvedScreen', 'rejectedScreen', 'bannedScreen', 'errorScreen', 'adminScreen'];
    views.forEach(v => {
        const el = document.getElementById(v);
        if (el) el.style.display = (v === viewId) ? 'block' : 'none';
    });

    const adminToggle = document.getElementById('adminToggleHeader');
    if (adminToggle) {
        adminToggle.style.display = isAdminUser ? 'block' : 'none';
        const switchBtn = document.getElementById('btnSwitchView');
        if (switchBtn) {
            switchBtn.textContent = (viewId === 'adminScreen') ? "User Rejimiga o'tish" : "Admin Paneli";
        }
    }
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
            } else if (status === 'PENDING_APPROVAL') {
                showView('pendingScreen');
            } else if (status === 'APPROVED') {
                showView('approvedScreen');
                // Fill user profile data
                document.getElementById('myPhoto').src = currentUser.photo;
                document.getElementById('myNameAge').textContent = `${currentUser.name}, ${currentUser.age}`;
                document.getElementById('myCity').textContent = currentUser.city;
                document.getElementById('myBio').textContent = currentUser.bio;
                loadSwipeProfiles();
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
        console.error(e);
        showView('errorScreen');
        if (e.name === 'AbortError') {
            document.getElementById('errorText').textContent = "Ulanish vaqti tugadi (Timeout). Internetni tekshirib qayta urining.";
        } else {
            document.getElementById('errorText').textContent = `Xatolik: ${e.message}`;
        }
    }
}

// Convert chosen photo to base64
document.getElementById('regPhoto').addEventListener('change', function (e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function (evt) {
            base64Photo = evt.target.result;
            document.getElementById('previewImg').src = base64Photo;
            document.getElementById('photoPreview').style.display = 'block';
        };
        reader.readAsDataURL(file);
    }
});

// Form Submit Handler
document.getElementById('btnSubmitReg').addEventListener('click', async () => {
    const name = document.getElementById('regName').value.trim();
    const age = document.getElementById('regAge').value.trim();
    const city = document.getElementById('regCity').value.trim();
    const bio = document.getElementById('regBio').value.trim();
    const terms = document.getElementById('regTerms').checked;
    const errText = document.getElementById('regError');

    errText.style.display = 'none';

    if (!name || !age || !city || !bio || !base64Photo) {
        errText.textContent = "Barcha maydonlarni to'ldiring hamda profil rasmini yuklang.";
        errText.style.display = 'block';
        return;
    }

    if (parseInt(age) < 18) {
        errText.textContent = "Ilovadan foydalanish uchun yoshingiz 18 yoshdan katta bo'lishi shart.";
        errText.style.display = 'block';
        return;
    }

    if (!terms) {
        errText.textContent = "Iltimos, Privacy Policy roziligini belgilang.";
        errText.style.display = 'block';
        return;
    }

    const btn = document.getElementById('btnSubmitReg');
    btn.disabled = true;
    btn.textContent = "Yuborilmoqda...";

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);

    try {
        const response = await fetch(`${API_URL}/api/register?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({
                name: name,
                age: parseInt(age),
                city: city,
                photo: base64Photo,
                bio: bio,
                terms_accepted: terms
            }),
            signal: controller.signal
        });
        clearTimeout(timeout);

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.error?.message || `HTTP ${response.status}`);
        }
        
        const resData = await response.json();
        if (resData.success) {
            showView('pendingScreen');
        } else {
            throw new Error("Tizimda xatolik yuz berdi.");
        }
    } catch (e) {
        clearTimeout(timeout);
        btn.disabled = false;
        btn.textContent = "Arizani yuborish";
        errText.textContent = `Xatolik: ${e.message}`;
        errText.style.display = 'block';
    }
});

// Switch view admin / user
document.getElementById('btnSwitchView').addEventListener('click', () => {
    if (currentView === 'adminScreen') {
        verifySession();
    } else {
        showView('adminScreen');
        loadAdminData();
    }
});

async function loadAdminData() {
    const listContainer = document.getElementById('pendingList');
    listContainer.innerHTML = "<p style='color:rgba(255,255,255,0.6); font-style:italic;'>Arizalar yuklanmoqda...</p>";

    try {
        const statsRes = await fetch(`${API_URL}/api/admin/stats?${getQueryParams()}`, { method: "GET", headers: getHeaders() });
        if (statsRes.ok) {
            const statsData = await statsRes.json();
            if (statsData.success) {
                document.getElementById('statPending').textContent = statsData.stats.pending;
                document.getElementById('statApproved').textContent = statsData.stats.approved;
                document.getElementById('statTotal').textContent = statsData.stats.total;
            }
        }

        const usersRes = await fetch(`${API_URL}/api/admin/pending?${getQueryParams()}`, { method: "GET", headers: getHeaders() });
        if (!usersRes.ok) throw new Error("Arizalarni yuklab bo'lmadi.");
        const usersData = await usersRes.json();

        if (usersData.success) {
            const users = usersData.users;
            if (users.length === 0) {
                listContainer.innerHTML = "<p style='color:#24ff8a; font-weight:bold; text-align:center;'>Ayni damda kutilayotgan arizalar yo'q!</p>";
                return;
            }

            listContainer.innerHTML = "";
            users.forEach(user => {
                const userCard = document.createElement('div');
                userCard.style.cssText = "background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.05); border-radius:12px; padding:15px; display:flex; flex-direction:column; gap:10px;";
                userCard.innerHTML = `
                    <div style="display:flex; gap:15px; align-items:center;">
                        <img src="${user.photo}" style="width:70px; height:70px; object-fit:cover; border-radius:8px; border:1px solid rgba(255,71,133,0.2);">
                        <div>
                            <h4 style="margin:0; color:#ff4785;">${user.name}, ${user.age}</h4>
                            <p style="margin:2px 0 0 0; font-size:12px; color:rgba(255,255,255,0.6);">${user.city}</p>
                        </div>
                    </div>
                    <p style="margin:0; font-size:13px; color:rgba(255,255,255,0.8);">${user.bio}</p>
                    <div style="display:flex; gap:10px;">
                        <button onclick="approveUser(${user.id})" style="flex:1; background:#24ff8a; color:#000; border:none; padding:8px; border-radius:6px; font-weight:bold; cursor:pointer;">Approve</button>
                        <button onclick="rejectUser(${user.id})" style="flex:1; background:#ff4785; color:#fff; border:none; padding:8px; border-radius:6px; font-weight:bold; cursor:pointer;">Reject</button>
                    </div>
                `;
                listContainer.appendChild(userCard);
            });
        }
    } catch(e) {
        listContainer.innerHTML = `<p style='color:#ff4785; font-weight:bold;'>Xatolik: ${e.message}</p>`;
    }
}

window.approveUser = async function(userId) {
    if (!confirm("Ushbu foydalanuvchini tasdiqlaysizmi?")) return;
    try {
        const res = await fetch(`${API_URL}/api/admin/approve?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ user_id: userId })
        });
        if (res.ok) loadAdminData();
    } catch (e) {
        alert(e.message);
    }
};

window.rejectUser = async function(userId) {
    if (!confirm("Rad etasizmi?")) return;
    try {
        const res = await fetch(`${API_URL}/api/admin/reject?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ user_id: userId })
        });
        if (res.ok) loadAdminData();
    } catch (e) {
        alert(e.message);
    }
};

// TAB VIEW SWITCHING FOR APPROVED USERS
function switchTab(tabId) {
    const tabs = ['viewSwipe', 'viewMatches', 'viewProfile'];
    tabs.forEach(t => {
        document.getElementById(t).style.display = (t === tabId) ? 'block' : 'none';
    });

    const buttons = ['btnTabSwipe', 'btnTabMatches', 'btnTabProfile'];
    buttons.forEach(btn => {
        const el = document.getElementById(btn);
        if (el) {
            if (btn === 'btnTab' + tabId.replace('view', '')) {
                el.classList.add('active');
            } else {
                el.classList.remove('active');
            }
        }
    });

    if (tabId === 'viewSwipe') loadSwipeProfiles();
    if (tabId === 'viewMatches') loadMatchesList();
}

document.getElementById('btnTabSwipe').addEventListener('click', () => switchTab('viewSwipe'));
document.getElementById('btnTabMatches').addEventListener('click', () => switchTab('viewMatches'));
document.getElementById('btnTabProfile').addEventListener('click', () => switchTab('viewProfile'));

// SWIPE LIFECYCLE
async function loadSwipeProfiles() {
    const container = document.getElementById('datingCardContainer');
    container.innerHTML = "<p style='color:rgba(255,255,255,0.6); text-align:center; font-style:italic;'>Qidirilmoqda...</p>";

    try {
        const response = await fetch(`${API_URL}/api/profiles?${getQueryParams()}`, {
            method: "GET",
            headers: getHeaders()
        });
        if (!response.ok) throw new Error("Yuklab bo'lmadi.");
        const data = await response.json();

        if (data.success) {
            datingProfiles = data.profiles;
            currentProfileIndex = 0;
            renderCurrentProfileCard();
        }
    } catch (e) {
        container.innerHTML = `<p style='color:#ff4785; text-align:center;'>Xatolik: ${e.message}</p>`;
    }
}

function renderCurrentProfileCard() {
    const container = document.getElementById('datingCardContainer');
    if (datingProfiles.length === 0 || currentProfileIndex >= datingProfiles.length) {
        container.innerHTML = "<div style='padding:50px 20px; text-align:center;'><h3 style='color:#ff4785;'>Ayni damda hech kim yo'q! 🌌</h3><p style='color:rgba(255,255,255,0.6); font-size:13px; line-height:1.4;'>Tez kunda yaqin atrofdagi yangi profillar paydo bo'ladi. Qayta yuklash uchun tanishuv bo'limiga kiring.</p></div>";
        return;
    }

    const p = datingProfiles[currentProfileIndex];
    container.innerHTML = `
        <div class="dating-card">
            <img src="${p.photo}" style="width:100%; height:320px; object-fit:cover; display:block;">
            <div style="position:absolute; bottom:0; left:0; right:0; background:linear-gradient(to top, rgba(5,5,16,1) 30%, rgba(5,5,16,0)); padding:20px; padding-top:40px;">
                <h2 style="margin:0; font-size:22px; color:white;">${p.name}, ${p.age}</h2>
                <p style="margin:5px 0; color:#ff4785; font-size:12px; font-weight:bold;">📍 ${p.city}</p>
                <p style="margin:10px 0 0 0; color:rgba(255,255,255,0.8); font-size:13px; line-height:1.4;">${p.bio}</p>
                
                <div style="display:flex; justify-content:space-between; gap:15px; margin-top:20px;">
                    <button onclick="handleSwipeAction(${p.id}, false)" style="flex:1; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); color:rgba(255,255,255,0.8); padding:10px; border-radius:10px; font-weight:bold; cursor:pointer; font-size:14px;">Pass 👎</button>
                    <button onclick="handleSwipeAction(${p.id}, true)" style="flex:1; background:linear-gradient(135deg, #ff4785, #b624ff); color:white; border:none; padding:10px; border-radius:10px; font-weight:bold; cursor:pointer; font-size:14px;">Like 💖</button>
                </div>
            </div>
        </div>
    `;
}

window.handleSwipeAction = async function(targetId, isLike) {
    try {
        const response = await fetch(`${API_URL}/api/swipe?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ target_id: targetId, is_like: isLike })
        });
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.match) {
                alert("Tabriklaymiz! Sizda moslik bor! 🎉");
            }
            currentProfileIndex++;
            renderCurrentProfileCard();
        }
    } catch(e) {
        console.error(e);
    }
};

// MATCHES & CHAT SYSTEM
async function loadMatchesList() {
    const container = document.getElementById('matchesList');
    container.innerHTML = "<p style='color:rgba(255,255,255,0.6); grid-column: span 2; text-align:center;'>Juftliklar yuklanmoqda...</p>";

    try {
        const response = await fetch(`${API_URL}/api/matches?${getQueryParams()}`, {
            method: "GET",
            headers: getHeaders()
        });
        if (!response.ok) throw new Error("Yuklanmadi.");
        const data = await response.json();

        if (data.success) {
            const matches = data.matches;
            if (matches.length === 0) {
                container.innerHTML = "<p style='color:rgba(255,255,255,0.5); grid-column: span 2; text-align:center; padding-top:30px; font-style:italic;'>Hali juftliklar mavjud emas. Swiping qilib like bosing!</p>";
                return;
            }

            container.innerHTML = "";
            matches.forEach(m => {
                const partnerCard = document.createElement('div');
                partnerCard.style.cssText = "background:rgba(255,255,255,0.02); border:1px solid rgba(255,71,133,0.1); border-radius:12px; padding:10px; text-align:center; cursor:pointer;";
                partnerCard.onclick = () => openChatWindow(m.match_id, m.partner);
                partnerCard.innerHTML = `
                    <img src="${m.partner.photo}" style="width:60px; height:60px; object-fit:cover; border-radius:50%; border:1px solid #ff4785; margin:0 auto 8px auto; display:block;">
                    <h4 style="margin:0; font-size:14px; color:white;">${m.partner.name}</h4>
                    <span style="font-size:11px; color:#ff4785;">Chatni ochish 💬</span>
                `;
                container.appendChild(partnerCard);
            });
        }
    } catch(e) {
        container.innerHTML = `<p style='color:#ff4785; grid-column: span 2; text-align:center;'>Xatolik: ${e.message}</p>`;
    }
}

// Open Chat window
function openChatWindow(matchId, partner) {
    currentMatchId = matchId;
    document.getElementById('chatPartnerPhoto').src = partner.photo;
    document.getElementById('chatPartnerName').textContent = partner.name;
    document.getElementById('chatOverlay').style.display = 'flex';
    document.getElementById('chatMessages').innerHTML = "";
    loadChatMessages();
    
    // Poll for new messages every 3 seconds
    if (chatPollInterval) clearInterval(chatPollInterval);
    chatPollInterval = setInterval(loadChatMessages, 3000);
}

document.getElementById('btnCloseChat').addEventListener('click', () => {
    document.getElementById('chatOverlay').style.display = 'none';
    currentMatchId = null;
    if (chatPollInterval) {
        clearInterval(chatPollInterval);
        chatPollInterval = null;
    }
    loadMatchesList();
});

async function loadChatMessages() {
    if (!currentMatchId) return;
    try {
        const response = await fetch(`${API_URL}/api/chat/messages?match_id=${currentMatchId}&${getQueryParams()}`, {
            method: "GET",
            headers: getHeaders()
        });
        if (!response.ok) return;
        const data = await response.json();

        if (data.success) {
            const msgs = data.messages;
            const container = document.getElementById('chatMessages');
            
            // Check if count changed to prevent redundant redraws
            const oldLength = container.children.length;
            if (msgs.length === oldLength) return;

            container.innerHTML = "";
            msgs.forEach(m => {
                const bubble = document.createElement('div');
                if (m.sender_id === 0) { // System
                    bubble.style.cssText = "align-self:center; background:rgba(255,255,255,0.05); color:rgba(255,255,255,0.6); padding:6px 12px; border-radius:8px; font-size:11px; max-width:90%; text-align:center;";
                } else if (m.sender_id === currentUser.id) { // Me
                    bubble.style.cssText = "align-self:flex-end; background:#ff4785; color:white; padding:8px 12px; border-radius:12px 12px 0 12px; font-size:13px; max-width:70%; word-break:break-word;";
                } else { // Partner
                    bubble.style.cssText = "align-self:flex-start; background:rgba(255,255,255,0.07); color:white; padding:8px 12px; border-radius:12px 12px 12px 0; font-size:13px; max-width:70%; word-break:break-word;";
                }
                bubble.textContent = m.text;
                container.appendChild(bubble);
            });
            container.scrollTop = container.scrollHeight;
        }
    } catch(e) {
        console.error(e);
    }
}

// Send Message
document.getElementById('btnSendChat').addEventListener('click', sendMessage);
document.getElementById('chatInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') sendMessage();
});

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const text = input.value.trim();
    if (!text || !currentMatchId) return;

    input.value = "";

    try {
        const response = await fetch(`${API_URL}/api/chat/send?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ match_id: currentMatchId, text: text })
        });
        if (response.ok) {
            loadChatMessages();
        }
    } catch(e) {
        console.error(e);
    }
}

if (tg) {
    try {
        tg.ready();
        tg.expand();
    } catch(err) {}
}

document.getElementById('btnRetry').addEventListener('click', verifySession);
verifySession();
