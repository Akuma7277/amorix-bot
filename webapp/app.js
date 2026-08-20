const tg = window.Telegram?.WebApp;
const API_URL = (window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1"))
    ? window.location.origin
    : "https://amorix-bot-production.up.railway.app";

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

async function verifySession() {
    document.getElementById('userStatus').textContent = "Checking...";
    document.getElementById('userStatus').style.color = "#ffb700";
    document.getElementById('errorScreen').style.display = 'none';

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
            document.getElementById('userStatus').textContent = data.user_status;
            document.getElementById('userStatus').style.color = "#24ff8a";
            document.getElementById('tgId').textContent = data.user.telegram_id;
            document.getElementById('tgUsername').textContent = data.user.username ? '@' + data.user.username : '—';
        } else {
            throw new Error(data.error?.message || "Auth failed");
        }
    } catch (e) {
        clearTimeout(timeout);
        console.error(e);
        document.getElementById('userStatus').textContent = "ERROR";
        document.getElementById('userStatus').style.color = "#ff4785";
        
        document.getElementById('errorScreen').style.display = 'block';
        if (e.name === 'AbortError') {
            document.getElementById('errorText').textContent = "Ulanish vaqti tugadi (Timeout). Internetni tekshirib qayta urining.";
        } else {
            document.getElementById('errorText').textContent = `Xatolik: ${e.message}`;
        }
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
