const tg = window.Telegram?.WebApp;
const API_URL = (window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1"))
    ? window.location.origin
    : "https://amorix-bot-production.up.railway.app";

// Initialize Telegram WebApp
if (tg) {
    try {
        tg.ready();
        tg.expand();
        
        // Show Telegram User details
        const user = tg.initDataUnsafe?.user;
        if (user) {
            document.getElementById('tgId').textContent = user.id;
            document.getElementById('tgName').textContent = user.first_name || '—';
            document.getElementById('tgUsername').textContent = user.username ? '@' + user.username : '—';
        } else {
            document.getElementById('tgUserBox').innerHTML = "<p style='color:#ff4785;'>No Telegram User Data (Open inside Telegram!)</p>";
        }
    } catch (e) {
        console.error("Telegram WebApp Error:", e);
    }
} else {
    document.getElementById('tgUserBox').innerHTML = "<p style='color:#ff4785;'>Telegram WebApp SDK not found.</p>";
}

document.getElementById('btnTest').addEventListener('click', async () => {
    const resText = document.getElementById('apiResponse');
    resText.textContent = "Loading...";
    resText.style.color = "#ffb700";

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);

    try {
        const response = await fetch(`${API_URL}/api/test`, {
            method: "GET",
            headers: { "Content-Type": "application/json" },
            signal: controller.signal
        });
        clearTimeout(timeout);

        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        
        resText.textContent = `Success: ${data.message}`;
        resText.style.color = "#24ff8a";
    } catch (e) {
        clearTimeout(timeout);
        console.error(e);
        if (e.name === 'AbortError') {
            resText.textContent = "Error: Connection Timeout (10s)";
        } else {
            resText.textContent = `Error: ${e.message}`;
        }
        resText.style.color = "#ff4785";
    }
});
