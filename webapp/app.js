const API_URL = (window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1"))
    ? window.location.origin
    : "https://amorix-bot-production.up.railway.app";

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
