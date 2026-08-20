(() => {
    const API = "/api";
    const SESSION_KEY = "agencurent_session";

    const messagesEl = document.getElementById("messages");
    const form = document.getElementById("chat-form");
    const input = document.getElementById("chat-input");
    const btnSend = document.getElementById("btn-send");
    const btnCollect = document.getElementById("btn-collect");
    const btnClear = document.getElementById("btn-clear");
    const btnViewChat = document.getElementById("btn-view-chat");
    const btnViewQuotes = document.getElementById("btn-view-quotes");
    const viewChat = document.getElementById("view-chat");
    const viewQuotes = document.getElementById("view-quotes");
    const quotesBody = document.getElementById("quotes-body");
    const healthEl = document.getElementById("health");
    const chips = document.querySelectorAll(".chip");
    const suggestions = document.getElementById("suggestions");

    let quoteMode = "latest";
    let typingEl = null;

    function sessionId() {
        let id = localStorage.getItem(SESSION_KEY);
        if (!id) {
            id = `web-${crypto.randomUUID().slice(0, 8)}`;
            localStorage.setItem(SESSION_KEY, id);
        }
        return id;
    }

    function nowLabel() {
        return new Date().toLocaleTimeString("ru-RU", {
            hour: "2-digit",
            minute: "2-digit",
        });
    }

    function showView(name) {
        const isChat = name === "chat";
        viewChat.classList.toggle("is-active", isChat);
        viewQuotes.classList.toggle("is-active", !isChat);
        viewChat.hidden = !isChat;
        viewQuotes.hidden = isChat;
        btnViewChat.classList.toggle("active", isChat);
        btnViewQuotes.classList.toggle("active", !isChat);
        if (!isChat) {
            loadQuotes();
        }
    }

    function renderMarkdown(text) {
        const raw = window.marked.parse(text, {
            gfm: true,
            breaks: true,
        });
        return window.DOMPurify.sanitize(raw, {
            USE_PROFILES: { html: true },
        });
    }

    function addMessage(role, text) {
        if (role === "system") {
            const wrap = document.createElement("div");
            wrap.className = "msg system";
            wrap.innerHTML = `<div class="bubble">${escapeHtml(text)}</div>`;
            messagesEl.appendChild(wrap);
            messagesEl.scrollTop = messagesEl.scrollHeight;
            return wrap;
        }

        const isUser = role === "user";
        const wrap = document.createElement("div");
        wrap.className = `msg ${isUser ? "user" : "assistant"}`;
        wrap.innerHTML = `
            <div class="avatar ${isUser ? "you" : "agent"}">
                ${isUser ? "Вы" : "AC"}
            </div>
            <div class="msg-body">
                <div class="msg-meta">
                    <span class="msg-name">${isUser ? "Вы" : "AgenCurent"}</span>
                    <span class="msg-time">${nowLabel()}</span>
                </div>
                <div class="bubble ${isUser ? "" : "md"}"></div>
            </div>
        `;
        const bubble = wrap.querySelector(".bubble");
        if (isUser) {
            bubble.textContent = text;
        } else {
            bubble.innerHTML = renderMarkdown(text);
        }
        messagesEl.appendChild(wrap);
        messagesEl.scrollTop = messagesEl.scrollHeight;
        return wrap;
    }

    function showTyping() {
        hideTyping();
        typingEl = document.createElement("div");
        typingEl.className = "msg assistant typing";
        typingEl.innerHTML = `
            <div class="avatar agent">AC</div>
            <div class="msg-body">
                <div class="msg-meta">
                    <span class="msg-name">AgenCurent</span>
                    <span class="msg-time">считает…</span>
                </div>
                <div class="bubble">
                    <span class="dot"></span>
                    <span class="dot"></span>
                    <span class="dot"></span>
                </div>
            </div>
        `;
        messagesEl.appendChild(typingEl);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function hideTyping() {
        if (typingEl) {
            typingEl.remove();
            typingEl = null;
        }
    }

    function escapeHtml(text) {
        return text
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;");
    }

    function formatPrice(value) {
        if (value == null) return "—";
        return `${Number(value).toLocaleString("ru-RU", {
            maximumFractionDigits: 2,
        })} ₽`;
    }

    function autoResize() {
        input.style.height = "auto";
        input.style.height = `${Math.min(input.scrollHeight, 140)}px`;
    }

    async function api(path, options = {}) {
        const res = await fetch(`${API}${path}`, {
            headers: { "Content-Type": "application/json" },
            ...options,
        });
        if (!res.ok) {
            let detail = res.statusText;
            try {
                const body = await res.json();
                detail = body.detail || detail;
            } catch (_) {
                /* ignore */
            }
            throw new Error(detail);
        }
        if (res.status === 204) return null;
        return res.json();
    }

    async function loadHealth() {
        try {
            const data = await api("/health");
            healthEl.textContent = `API ${data.status}`;
        } catch (_) {
            healthEl.textContent = "API offline";
        }
    }

    async function loadQuotes() {
        const latest = quoteMode === "latest";
        quotesBody.innerHTML =
            '<tr><td colspan="6">Загрузка…</td></tr>';
        try {
            const rows = await api(
                `/quotes?latest_only=${latest ? "true" : "false"}`,
            );
            if (!rows.length) {
                quotesBody.innerHTML =
                    '<tr><td colspan="6">Нет данных. Нажмите «Собрать цены».</td></tr>';
                return;
            }
            quotesBody.innerHTML = rows
                .map((row) => {
                    const route = `${row.departure} → ${row.destination}`;
                    const src = row.source || "—";
                    const srcClass =
                        src === "live" ? "live" : "collect";
                    return `
                        <tr>
                            <td>${route}</td>
                            <td>${row.carrier_name}</td>
                            <td class="price">${formatPrice(row.transport_price)}</td>
                            <td>${row.delivery_days ?? "—"}</td>
                            <td><span class="badge ${srcClass}">${src}</span></td>
                            <td>${row.collected_at || "—"}</td>
                        </tr>
                    `;
                })
                .join("");
        } catch (err) {
            quotesBody.innerHTML =
                `<tr><td colspan="6">Ошибка: ${err.message}</td></tr>`;
        }
    }

    async function loadHistory() {
        try {
            const history = await api(
                `/chat/history?session_id=${encodeURIComponent(sessionId())}`,
            );
            messagesEl.innerHTML = "";
            if (!history.length) {
                addMessage(
                    "system",
                    "Напишите маршрут — агент пересчитает LIVE и сравнит с историей цен.",
                );
                return;
            }
            history.forEach((item) => {
                addMessage(item.role, item.content);
            });
        } catch (_) {
            addMessage(
                "system",
                "Напишите маршрут — агент пересчитает LIVE и сравнит с историей цен.",
            );
        }
    }

    async function sendMessage(message) {
        const text = message.trim();
        if (!text) return;

        addMessage("user", text);
        input.value = "";
        autoResize();
        btnSend.disabled = true;
        input.disabled = true;
        showTyping();

        try {
            const data = await api("/chat", {
                method: "POST",
                body: JSON.stringify({
                    message: text,
                    session_id: sessionId(),
                }),
            });
            hideTyping();
            addMessage("assistant", data.reply);
        } catch (err) {
            hideTyping();
            addMessage("system", `Ошибка: ${err.message}`);
        } finally {
            btnSend.disabled = false;
            input.disabled = false;
            input.focus();
        }
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        await sendMessage(input.value);
    });

    input.addEventListener("input", autoResize);
    input.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            form.requestSubmit();
        }
    });

    suggestions.addEventListener("click", (event) => {
        const btn = event.target.closest(".suggest");
        if (!btn) return;
        showView("chat");
        sendMessage(btn.dataset.q);
    });

    btnViewChat.addEventListener("click", () => showView("chat"));
    btnViewQuotes.addEventListener("click", () => showView("quotes"));

    btnCollect.addEventListener("click", async () => {
        btnCollect.disabled = true;
        btnCollect.textContent = "Сбор…";
        try {
            const data = await api("/collect", { method: "POST" });
            showView("chat");
            addMessage(
                "system",
                `Сбор завершён: OK ${data.ok_count}, ошибки ${data.error_count}.`,
            );
        } catch (err) {
            showView("chat");
            addMessage("system", `Сбор не удался: ${err.message}`);
        } finally {
            btnCollect.disabled = false;
            btnCollect.textContent = "Собрать цены";
        }
    });

    btnClear.addEventListener("click", async () => {
        try {
            await api(
                `/chat/history?session_id=${encodeURIComponent(sessionId())}`,
                { method: "DELETE" },
            );
            showView("chat");
            messagesEl.innerHTML = "";
            addMessage("system", "Чат очищен.");
        } catch (err) {
            addMessage("system", `Не удалось очистить: ${err.message}`);
        }
    });

    chips.forEach((chip) => {
        chip.addEventListener("click", () => {
            chips.forEach((c) => c.classList.remove("active"));
            chip.classList.add("active");
            quoteMode = chip.dataset.mode;
            loadQuotes();
        });
    });

    loadHealth();
    loadHistory();
    showView("chat");
})();
