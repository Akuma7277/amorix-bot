const tg = window.Telegram?.WebApp;
const API_URL = (window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1"))
    ? window.location.origin
    : "https://amorix-bot-production.up.railway.app";

let base64Photo = "";
let isAdminUser = false;
let currentView = "";

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

    // Handle Admin Header view
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
            const status = data.user_status;
            
            if (status === 'DRAFT') {
                showView('registrationScreen');
            } else if (status === 'PENDING_APPROVAL') {
                showView('pendingScreen');
            } else if (status === 'APPROVED') {
                showView('approvedScreen');
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
        errText.textContent = "Barcha majburiy maydonlarni to'ldiring hamda profil rasmini yuklang.";
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

// Admin Panel Toggle
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
        // 1. Fetch Stats
        const statsRes = await fetch(`${API_URL}/api/admin/stats?${getQueryParams()}`, {
            method: "GET",
            headers: getHeaders()
        });
        if (statsRes.ok) {
            const statsData = await statsRes.json();
            if (statsData.success) {
                document.getElementById('statPending').textContent = statsData.stats.pending;
                document.getElementById('statApproved').textContent = statsData.stats.approved;
                document.getElementById('statTotal').textContent = statsData.stats.total;
            }
        }

        // 2. Fetch Pending Users
        const usersRes = await fetch(`${API_URL}/api/admin/pending?${getQueryParams()}`, {
            method: "GET",
            headers: getHeaders()
        });
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
                            <p style="margin:2px 0 0 0; font-size:11px; color:#ffb700;">ID: ${user.telegram_id}</p>
                        </div>
                    </div>
                    <p style="margin:0; font-size:13px; line-height:1.4; color:rgba(255,255,255,0.8); background:rgba(0,0,0,0.2); padding:8px; border-radius:6px;">${user.bio}</p>
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
        if (res.ok) {
            loadAdminData();
        } else {
            alert("Tasdiqlashda xatolik yuz berdi.");
        }
    } catch (e) {
        alert("Xatolik: " + e.message);
    }
};

window.rejectUser = async function(userId) {
    const reason = prompt("Rad etish sababini kiriting (ixtiyoriy):", "Premium qoidalarga mos kelmadi.");
    if (reason === null) return; // Cancel
    try {
        const res = await fetch(`${API_URL}/api/admin/reject?${getQueryParams()}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify({ user_id: userId, reason: reason })
        });
        if (res.ok) {
            loadAdminData();
        } else {
            alert("Rad etishda xatolik yuz berdi.");
        }
    } catch (e) {
        alert("Xatolik: " + e.message);
    }
};

if (tg) {
    try {
        tg.ready();
        tg.expand();
    } catch(err) {}
}

document.getElementById('btnRetry').addEventListener('click', verifySession);
verifySession();
