const tg = window.Telegram?.WebApp;
const API_URL = (window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1"))
    ? window.location.origin
    : "https://amorix-bot-production.up.railway.app";

let base64Photo = "";

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

function showView(viewId) {
    const views = ['verifyingScreen', 'registrationScreen', 'pendingScreen', 'approvedScreen', 'rejectedScreen', 'bannedScreen', 'errorScreen'];
    views.forEach(v => {
        const el = document.getElementById(v);
        if (el) el.style.display = (v === viewId) ? 'block' : 'none';
    });
}

async function verifySession() {
    showView('verifyingScreen');

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 12000);

    try {
        const queryParams = new URLSearchParams();
        if (tg && tg.initData) {
            queryParams.append("initData", tg.initData);
        } else {
            queryParams.append("initData", "mock_user");
        }

        const response = await fetch(`${API_URL}/api/session?${queryParams.toString()}`, {
            method: "GET",
            headers: getHeaders(),
            signal: controller.signal
        });
        clearTimeout(timeout);

        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();

        if (data.success) {
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

    // Submit button lock to prevent multiple clicks
    const btn = document.getElementById('btnSubmitReg');
    btn.disabled = true;
    btn.textContent = "Yuborilmoqda...";

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);

    try {
        const response = await fetch(`${API_URL}/api/register`, {
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

if (tg) {
    try {
        tg.ready();
        tg.expand();
    } catch(err) {}
}

document.getElementById('btnRetry').addEventListener('click', verifySession);
verifySession();
