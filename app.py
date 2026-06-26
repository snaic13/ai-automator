import os
import base64
from flask import Flask, request, jsonify, render_template_string, session, redirect
from functools import wraps
from automator import (
    process_document, customer_support, generate_report,
    summarize, translate, extract_emails, fetch_url, summarize_url,
    process_image_text, extract_pdf_text, extract_docx_text,
    extract_xlsx_text, extract_csv_text, truncate
)
from auth import register, login, check_api_key, set_plan, ADMIN_KEY

app = Flask(__name__)
app.secret_key = os.urandom(24)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = session.get("api_key") or request.headers.get("X-API-Key")
        if not api_key:
            return jsonify({"error": "Требуется авторизация"}), 401
        user = check_api_key(api_key, count=False)
        if not user["valid"]:
            return jsonify({"error": user["error"]}), 403
        request.user = user
        return f(*args, **kwargs)
    return decorated


def login_required_count(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = session.get("api_key") or request.headers.get("X-API-Key")
        if not api_key:
            return jsonify({"error": "Требуется авторизация"}), 401
        user = check_api_key(api_key, count=True)
        if not user["valid"]:
            return jsonify({"error": user["error"]}), 403
        request.user = user
        return f(*args, **kwargs)
    return decorated


AUTH_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI-Automator</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #050510; color: #e0e0e0; min-height: 100vh; overflow: hidden; }

        #cloud-canvas { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 0; }

        .auth-wrapper { position: relative; z-index: 10; display: flex; align-items: center; justify-content: center; min-height: 100vh; }

        .auth-box { max-width: 420px; width: 100%; padding: 40px; background: rgba(15, 15, 35, 0.85); backdrop-filter: blur(20px); border: 1px solid rgba(102, 126, 234, 0.2); border-radius: 20px; }

        .logo { text-align: center; margin-bottom: 30px; }
        .logo h1 { font-size: 2.4em; font-weight: 800; background: linear-gradient(135deg, #667eea 0%, #a855f7 50%, #ec4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -1px; }
        .logo p { color: #666; font-size: 14px; margin-top: 8px; }

        .tabs { display: flex; gap: 0; margin-bottom: 25px; border-radius: 12px; overflow: hidden; border: 1px solid rgba(102, 126, 234, 0.3); }
        .tab { flex: 1; padding: 12px; text-align: center; cursor: pointer; background: transparent; color: #666; transition: all 0.3s; font-weight: 500; }
        .tab.active { background: linear-gradient(135deg, #667eea, #a855f7); color: white; }

        .form-group { margin-bottom: 18px; }
        label { display: block; margin-bottom: 6px; color: #888; font-size: 13px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
        input { width: 100%; padding: 14px 16px; border: 1px solid rgba(102, 126, 234, 0.2); border-radius: 12px; background: rgba(255,255,255,0.03); color: #e0e0e0; font-size: 15px; transition: all 0.3s; }
        input:focus { outline: none; border-color: #667eea; box-shadow: 0 0 20px rgba(102, 126, 234, 0.15); }
        input::placeholder { color: #444; }

        .submit-btn { width: 100%; padding: 14px; border: none; border-radius: 12px; background: linear-gradient(135deg, #667eea, #a855f7); color: white; font-size: 16px; font-weight: 600; cursor: pointer; transition: all 0.3s; letter-spacing: 0.3px; }
        .submit-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(102, 126, 234, 0.4); }

        .error { color: #ef4444; text-align: center; margin-bottom: 15px; font-size: 13px; }

        .features { margin-top: 35px; display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .feature { padding: 12px; border: 1px solid rgba(102, 126, 234, 0.15); border-radius: 10px; background: rgba(102, 126, 234, 0.05); text-align: center; }
        .feature .icon { font-size: 20px; margin-bottom: 4px; }
        .feature .name { font-size: 12px; color: #888; }
    </style>
</head>
<body>
    <canvas id="cloud-canvas"></canvas>

    <div class="auth-wrapper">
        <div class="auth-box">
            <div class="logo">
                <h1>AI-Automator</h1>
                <p>Автоматизация бизнес-процессов на базе AI</p>
            </div>

            <div id="error" class="error" style="display:none;"></div>

            <div class="tabs">
                <div class="tab active" onclick="switchTab('login')">Вход</div>
                <div class="tab" onclick="switchTab('register')">Регистрация</div>
            </div>

            <form id="loginForm" onsubmit="return submitAuth('login')">
                <div class="form-group"><label>Email</label><input type="email" id="loginEmail" required placeholder="your@email.com"></div>
                <div class="form-group"><label>Пароль</label><input type="password" id="loginPass" required placeholder="&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;"></div>
                <button type="submit" class="submit-btn">Войти</button>
            </form>

            <form id="registerForm" style="display:none;" onsubmit="return submitAuth('register')">
                <div class="form-group"><label>Email</label><input type="email" id="regEmail" required placeholder="your@email.com"></div>
                <div class="form-group"><label>Пароль</label><input type="password" id="regPass" required placeholder="Минимум 6 символов" minlength="6"></div>
                <button type="submit" class="submit-btn">Создать аккаунт</button>
            </form>

            <div class="features">
                <div class="feature"><div class="icon">📄</div><div class="name">Документы</div></div>
                <div class="feature"><div class="icon">💬</div><div class="name">Поддержка</div></div>
                <div class="feature"><div class="icon">📊</div><div class="name">Отчёты</div></div>
                <div class="feature"><div class="icon">🌐</div><div class="name">Перевод</div></div>
                <div class="feature"><div class="icon">📧</div><div class="name">Email</div></div>
                <div class="feature"><div class="icon">🔗</div><div class="name">URL</div></div>
            </div>
        </div>
    </div>

    <script>
        function switchTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('loginForm').style.display = tab === 'login' ? 'block' : 'none';
            document.getElementById('registerForm').style.display = tab === 'register' ? 'block' : 'none';
            document.getElementById('error').style.display = 'none';
        }
        async function submitAuth(type) {
            event.preventDefault();
            const email = document.getElementById(type === 'login' ? 'loginEmail' : 'regEmail').value;
            const pass = document.getElementById(type === 'login' ? 'loginPass' : 'regPass').value;
            try {
                const res = await fetch('/api/auth', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: type, email, password: pass })
                });
                const data = await res.json();
                if (data.success) { localStorage.setItem('api_key', data.api_key); localStorage.setItem('email', data.email); window.location.href = '/app'; }
                else { document.getElementById('error').textContent = data.error; document.getElementById('error').style.display = 'block'; }
            } catch (e) { document.getElementById('error').textContent = 'Ошибка соединения'; document.getElementById('error').style.display = 'block'; }
            return false;
        }

        const canvas = document.getElementById('cloud-canvas');
        const ctx = canvas.getContext('2d');
        let W, H, clouds = [], mouse = { x: -1000, y: -1000 };

        function resize() { W = canvas.width = window.innerWidth; H = canvas.height = window.innerHeight; }
        window.addEventListener('resize', resize); resize();

        class Cloud {
            constructor() { this.reset(); }
            reset() {
                this.x = Math.random() * W;
                this.y = Math.random() * H;
                this.r = 60 + Math.random() * 120;
                this.opacity = 0.15 + Math.random() * 0.25;
                this.vx = (Math.random() - 0.5) * 0.3;
                this.vy = (Math.random() - 0.5) * 0.15;
                this.baseOpacity = this.opacity;
            }
            update() {
                const dx = mouse.x - this.x;
                const dy = mouse.y - this.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 200) {
                    this.opacity = this.baseOpacity * (dist / 200);
                    this.x += dx * 0.02;
                    this.y += dy * 0.02;
                } else {
                    this.opacity += (this.baseOpacity - this.opacity) * 0.05;
                }
                this.x += this.vx; this.y += this.vy;
                if (this.x < -200) this.x = W + 200;
                if (this.x > W + 200) this.x = -200;
                if (this.y < -200) this.y = H + 200;
                if (this.y > H + 200) this.y = -200;
            }
            draw() {
                const g = ctx.createRadialGradient(this.x, this.y, 0, this.x, this.y, this.r);
                g.addColorStop(0, `rgba(102, 126, 234, ${this.opacity})`);
                g.addColorStop(0.5, `rgba(168, 85, 247, ${this.opacity * 0.5})`);
                g.addColorStop(1, 'rgba(0,0,0,0)');
                ctx.fillStyle = g;
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
                ctx.fill();
            }
        }

        for (let i = 0; i < 25; i++) clouds.push(new Cloud());

        const bgImage = new Image();
        bgImage.src = 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1920&q=80';
        let bgReady = false;
        bgImage.onload = () => bgReady = true;

        function drawBgGlow() {
            if (!bgReady) return;
            const g = ctx.createRadialGradient(mouse.x, mouse.y, 0, mouse.x, mouse.y, 250);
            g.addColorStop(0, 'rgba(255,255,255,0.08)');
            g.addColorStop(1, 'rgba(0,0,0,0)');
            ctx.fillStyle = g;
            ctx.beginPath();
            ctx.arc(mouse.x, mouse.y, 250, 0, Math.PI * 2);
            ctx.fill();

            ctx.save();
            ctx.globalCompositeOperation = 'destination-in';
            const g2 = ctx.createRadialGradient(mouse.x, mouse.y, 0, mouse.x, mouse.y, 200);
            g2.addColorStop(0, 'rgba(255,255,255,0.5)');
            g2.addColorStop(1, 'rgba(255,255,255,0)');
            ctx.fillStyle = g2;
            ctx.beginPath();
            ctx.arc(mouse.x, mouse.y, 200, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
        }

        function animate() {
            ctx.fillStyle = '#050510';
            ctx.fillRect(0, 0, W, H);

            clouds.forEach(c => { c.update(); c.draw(); });

            ctx.save();
            ctx.globalAlpha = 0.3;
            if (bgReady) ctx.drawImage(bgImage, 0, 0, W, H);
            ctx.restore();

            drawBgGlow();
            requestAnimationFrame(animate);
        }

        document.addEventListener('mousemove', e => { mouse.x = e.clientX; mouse.y = e.clientY; });
        animate();
    </script>
</body>
</html>
"""

APP_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI-Automator</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #050510; color: #e0e0e0; min-height: 100vh; overflow-x: hidden; }

        #cloud-canvas { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 0; }

        .topbar { position: fixed; top: 0; left: 0; right: 0; z-index: 100; display: flex; justify-content: space-between; align-items: center; padding: 14px 24px; background: rgba(5, 5, 16, 0.8); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(102, 126, 234, 0.1); }
        .topbar .user-info { display: flex; align-items: center; gap: 12px; }
        .topbar .user { color: #888; font-size: 13px; }
        .topbar .plan-badge { background: linear-gradient(135deg, #667eea, #a855f7); padding: 4px 14px; border-radius: 20px; font-size: 11px; font-weight: 600; letter-spacing: 0.5px; }
        .topbar .usage { color: #666; font-size: 12px; }
        .topbar button { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: #888; padding: 7px 18px; border-radius: 8px; cursor: pointer; font-size: 12px; transition: all 0.3s; }
        .topbar button:hover { border-color: #667eea; color: #667eea; }

        .main-content { position: relative; z-index: 10; max-width: 860px; margin: 0 auto; padding: 80px 20px 40px; }

        .hero { text-align: center; margin-bottom: 35px; }
        .hero h1 { font-size: 2.8em; font-weight: 800; background: linear-gradient(135deg, #667eea 0%, #a855f7 50%, #ec4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -1px; margin-bottom: 10px; }
        .hero p { color: #555; font-size: 16px; font-weight: 300; }

        .tabs { display: flex; gap: 6px; margin-bottom: 24px; flex-wrap: wrap; justify-content: center; }
        .tab { padding: 10px 20px; border: 1px solid rgba(102, 126, 234, 0.2); border-radius: 10px; cursor: pointer; transition: all 0.3s; background: rgba(102, 126, 234, 0.05); color: #888; font-size: 13px; font-weight: 500; }
        .tab:hover { border-color: #667eea; color: #667eea; background: rgba(102, 126, 234, 0.1); }
        .tab.active { background: linear-gradient(135deg, #667eea, #a855f7); border-color: transparent; color: white; }

        .input-card { background: rgba(15, 15, 35, 0.8); backdrop-filter: blur(20px); border: 1px solid rgba(102, 126, 234, 0.15); border-radius: 16px; padding: 20px; margin-bottom: 16px; }
        textarea { width: 100%; height: 160px; padding: 16px; border: 1px solid rgba(102, 126, 234, 0.15); border-radius: 12px; background: rgba(255,255,255,0.02); color: #e0e0e0; font-size: 15px; resize: vertical; font-family: 'Inter', sans-serif; transition: all 0.3s; }
        textarea:focus { outline: none; border-color: #667eea; box-shadow: 0 0 30px rgba(102, 126, 234, 0.1); }
        textarea::placeholder { color: #333; }

        .actions { display: flex; gap: 10px; margin-top: 14px; }
        .submit-btn { flex: 1; padding: 14px; border: none; border-radius: 12px; background: linear-gradient(135deg, #667eea, #a855f7); color: white; font-size: 15px; font-weight: 600; cursor: pointer; transition: all 0.3s; }
        .submit-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(102, 126, 234, 0.4); }
        .submit-btn:disabled { opacity: 0.5; transform: none; cursor: not-allowed; }
        .upload-btn { padding: 14px 22px; border: 1px dashed rgba(102, 126, 234, 0.3); border-radius: 12px; background: transparent; color: #666; cursor: pointer; font-size: 13px; transition: all 0.3s; }
        .upload-btn:hover { border-color: #667eea; color: #667eea; }

        .result-card { background: rgba(15, 15, 35, 0.8); backdrop-filter: blur(20px); border: 1px solid rgba(102, 126, 234, 0.15); border-radius: 16px; padding: 24px; margin-top: 16px; display: none; }
        .result-card.visible { display: block; animation: fadeIn 0.4s ease; }
        .result-card .label { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #667eea; margin-bottom: 12px; font-weight: 600; }
        .result-card .content { white-space: pre-wrap; line-height: 1.8; font-size: 14px; color: #ccc; }

        .loading { text-align: center; color: #667eea; padding: 20px; }
        .loading::after { content: ''; display: inline-block; width: 20px; height: 20px; border: 2px solid #667eea; border-top-color: transparent; border-radius: 50%; animation: spin 0.8s linear infinite; margin-left: 10px; vertical-align: middle; }

        .file-info { color: #667eea; font-size: 12px; margin-top: 8px; display: none; }
        .file-info.visible { display: block; }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes spin { to { transform: rotate(360deg); } }

        .tips { margin-top: 30px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
        .tip { padding: 14px; border: 1px solid rgba(102, 126, 234, 0.1); border-radius: 12px; background: rgba(102, 126, 234, 0.03); text-align: center; cursor: pointer; transition: all 0.3s; }
        .tip:hover { border-color: #667eea; transform: translateY(-2px); }
        .tip .icon { font-size: 22px; margin-bottom: 6px; }
        .tip .text { font-size: 11px; color: #666; line-height: 1.4; }
    </style>
</head>
<body>
    <canvas id="cloud-canvas"></canvas>

    <div class="topbar">
        <div class="user-info">
            <span class="user" id="userEmail"></span>
            <span class="plan-badge" id="planBadge">FREE</span>
        </div>
        <div style="display:flex;align-items:center;gap:15px;">
            <span class="usage" id="usageInfo"></span>
            <button onclick="window.location.href='/logout'">Выйти</button>
        </div>
    </div>

    <div class="main-content">
        <div class="hero">
            <h1>AI-Automator</h1>
            <p>Обрабатывайте документы, тексты и данные с помощью AI за секунды</p>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="setMode('document', this)">📄 Документы</button>
            <button class="tab" onclick="setMode('support', this)">💬 Поддержка</button>
            <button class="tab" onclick="setMode('report', this)">📊 Отчёты</button>
            <button class="tab" onclick="setMode('summarize', this)">📝 Резюме</button>
            <button class="tab" onclick="setMode('translate', this)">🌐 Перевод</button>
            <button class="tab" onclick="setMode('emails', this)">📧 Email</button>
            <button class="tab" onclick="setMode('url', this)">🔗 Ссылка URL</button>
            <button class="tab" onclick="setMode('code', this)">💻 Код</button>
            <button class="tab" onclick="setMode('sql', this)">🗄 SQL</button>
            <button class="tab" onclick="setMode('seo', this)">🔍 SEO</button>
            <button class="tab" onclick="setMode('caption', this)">📱 Подпись</button>
        </div>

        <div class="input-card">
            <textarea id="input" placeholder="Введите текст для обработки..."></textarea>
            <div class="actions">
                <button class="submit-btn" onclick="process()">Обработать</button>
                <button class="upload-btn" onclick="document.getElementById('fileInput').click()">📎 Файл</button>
            </div>
            <input type="file" id="fileInput" accept=".txt,.csv,.json,.md,.pdf,.docx,.doc,.xlsx,.xls,.jpg,.jpeg,.png,.webp" style="display:none" onchange="handleFile(event)">
            <div class="file-info" id="fileName"></div>
        </div>

        <div class="result-card" id="resultCard">
            <div class="label">Результат</div>
            <div class="content" id="result"></div>
        </div>

        <div class="tips">
            <div class="tip" onclick="quickExample('Обработай документ и извлеки ключевую информацию: Счёт №45 от 25.06.2026, ООО Ромашка, сумма 150000 руб.')"><div class="icon">📄</div><div class="text">Пример: обработка счёта</div></div>
            <div class="tip" onclick="quickExample('Сгенерируй отчёт по продажам: Январь 100k, Февраль 120k, Март 95k, Апрель 140k')"><div class="icon">📊</div><div class="text">Пример: отчёт по продажам</div></div>
            <div class="tip" onclick="quickExample('Переведи на английский: Автоматизация бизнес-процессов с помощью искусственного интеллекта')"><div class="icon">🌐</div><div class="text">Пример: перевод текста</div></div>
        </div>
    </div>

    <script>
        const API_KEY = localStorage.getItem('api_key');
        if (!API_KEY) window.location.href = '/';
        let mode = 'document';
        let uploadedFile = null;

        document.getElementById('userEmail').textContent = localStorage.getItem('email') || '';

        const placeholders = {
            document: 'Вставьте текст документа, счёта или договора...',
            support: 'Введите вопрос клиента...',
            report: 'Вставьте данные для отчёта...',
            summarize: 'Вставьте длинный текст для резюмирования...',
            translate: 'Вставьте текст для перевода на английский...',
            emails: 'Вставьте текст для извлечения email-адресов...',
            url: 'Вставьте ссылку для чтения содержимого...',
            code: 'Вставьте код для рефакторинга или объяснения...',
            sql: 'Опишите задачу для генерации SQL-запроса...',
            seo: 'Вставьте текст для SEO-оптимизации...',
            caption: 'Опишите фото/видео для создания подписи...'
        };

        async function loadUsage() {
            try {
                const res = await fetch('/api/usage', { headers: { 'X-API-Key': API_KEY } });
                const data = await res.json();
                if (data.plan) {
                    document.getElementById('planBadge').textContent = data.plan.toUpperCase();
                    document.getElementById('usageInfo').textContent = data.remaining + ' запросов';
                }
            } catch(e) {}
        }
        loadUsage();

        function setMode(m, el) {
            mode = m;
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            if (el) el.classList.add('active');
            document.getElementById('input').placeholder = placeholders[m] || '';
        }

        function quickExample(text) {
            document.getElementById('input').value = text;
            document.getElementById('input').focus();
        }

        function handleFile(event) {
            const file = event.target.files[0];
            if (!file) return;
            document.getElementById('fileName').textContent = '📎 ' + file.name;
            document.getElementById('fileName').classList.add('visible');
            const ext = file.name.split('.').pop().toLowerCase();
            const binaryExts = ['pdf', 'docx', 'xlsx', 'doc', 'xls'];
            const imageTypes = ['jpg', 'jpeg', 'png', 'webp', 'gif'];
            if (imageTypes.includes(ext)) {
                const reader = new FileReader();
                reader.onload = (e) => { uploadedFile = { type: 'image', data: e.target.result, name: file.name }; };
                reader.readAsDataURL(file);
            } else if (binaryExts.includes(ext)) {
                const reader = new FileReader();
                reader.onload = (e) => { uploadedFile = { type: 'binary', data: e.target.result, name: file.name, ext: ext }; document.getElementById('input').value = '[Файл: ' + file.name + ']'; };
                reader.readAsDataURL(file);
            } else {
                const reader = new FileReader();
                reader.onload = (e) => { document.getElementById('input').value = e.target.result; uploadedFile = null; };
                reader.readAsText(file);
            }
        }

        async function process() {
            const input = document.getElementById('input').value;
            if (!input.trim() && !uploadedFile) return;
            const btn = document.querySelector('.submit-btn');
            const card = document.getElementById('resultCard');
            const result = document.getElementById('result');
            btn.disabled = true; btn.textContent = 'Обработка...';
            card.classList.add('visible');
            result.innerHTML = '<span class="loading">AI обрабатывает запрос</span>';
            try {
                const payload = { text: input, mode: mode };
                if (uploadedFile && uploadedFile.type === 'image') { payload.image = uploadedFile.data; payload.image_name = uploadedFile.name; payload.mode = 'image'; }
                else if (uploadedFile && uploadedFile.type === 'binary') { payload.file_data = uploadedFile.data; payload.file_ext = uploadedFile.ext; payload.file_name = uploadedFile.name; payload.mode = 'file'; }
                if (mode === 'url' && (input.includes('http://') || input.includes('https://'))) payload.mode = 'url';
                const res = await fetch('/api/process', {
                    method: 'POST', headers: { 'Content-Type': 'application/json', 'X-API-Key': API_KEY },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                result.textContent = data.result || data.error;
                uploadedFile = null;
                loadUsage();
            } catch (e) { result.textContent = 'Ошибка: ' + e.message; }
            btn.disabled = false; btn.textContent = 'Обработать';
        }

        const canvas = document.getElementById('cloud-canvas');
        const ctx = canvas.getContext('2d');
        let W, H, clouds = [], mouse = { x: -1000, y: -1000 };
        function resize() { W = canvas.width = window.innerWidth; H = canvas.height = window.innerHeight; }
        window.addEventListener('resize', resize); resize();

        class Cloud {
            constructor() { this.reset(); }
            reset() { this.x = Math.random() * W; this.y = Math.random() * H; this.r = 60 + Math.random() * 120; this.opacity = 0.1 + Math.random() * 0.2; this.vx = (Math.random() - 0.5) * 0.3; this.vy = (Math.random() - 0.5) * 0.15; this.baseOpacity = this.opacity; }
            update() {
                const dx = mouse.x - this.x, dy = mouse.y - this.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 250) { this.opacity = this.baseOpacity * (dist / 250); this.x += dx * 0.015; this.y += dy * 0.015; }
                else { this.opacity += (this.baseOpacity - this.opacity) * 0.05; }
                this.x += this.vx; this.y += this.vy;
                if (this.x < -200) this.x = W + 200; if (this.x > W + 200) this.x = -200;
                if (this.y < -200) this.y = H + 200; if (this.y > H + 200) this.y = -200;
            }
            draw() {
                const g = ctx.createRadialGradient(this.x, this.y, 0, this.x, this.y, this.r);
                g.addColorStop(0, `rgba(102, 126, 234, ${this.opacity})`);
                g.addColorStop(0.5, `rgba(168, 85, 247, ${this.opacity * 0.5})`);
                g.addColorStop(1, 'rgba(0,0,0,0)');
                ctx.fillStyle = g; ctx.beginPath(); ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2); ctx.fill();
            }
        }
        for (let i = 0; i < 20; i++) clouds.push(new Cloud());

        const bgImage = new Image();
        bgImage.src = 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1920&q=80';
        let bgReady = false; bgImage.onload = () => bgReady = true;

        function animate() {
            ctx.fillStyle = '#050510'; ctx.fillRect(0, 0, W, H);
            clouds.forEach(c => { c.update(); c.draw(); });
            if (bgReady) {
                ctx.save(); ctx.globalAlpha = 0.15; ctx.drawImage(bgImage, 0, 0, W, H); ctx.restore();
                ctx.save(); ctx.globalCompositeOperation = 'destination-in';
                const g = ctx.createRadialGradient(mouse.x, mouse.y, 0, mouse.x, mouse.y, 220);
                g.addColorStop(0, 'rgba(255,255,255,0.6)'); g.addColorStop(1, 'rgba(255,255,255,0)');
                ctx.fillStyle = g; ctx.beginPath(); ctx.arc(mouse.x, mouse.y, 220, 0, Math.PI * 2); ctx.fill();
                ctx.restore();
            }
            requestAnimationFrame(animate);
        }
        document.addEventListener('mousemove', e => { mouse.x = e.clientX; mouse.y = e.clientY; });
        animate();
    </script>
</body>
</html>
"""


@app.route("/")
def auth_page():
    return render_template_string(AUTH_HTML)


@app.route("/app")
def app_page():
    api_key = session.get("api_key")
    if not api_key:
        return redirect("/")
    return render_template_string(APP_HTML)


@app.route("/logout")
def logout_page():
    session.clear()
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><script>
    localStorage.removeItem('api_key');
    localStorage.removeItem('email');
    window.location.href = '/';
    </script></head><body></body></html>"""


@app.route("/api/auth", methods=["POST"])
def api_auth():
    data = request.json
    action = data.get("action")
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if action == "register":
        result = register(email, password)
    elif action == "login":
        result = login(email, password)
    elif action == "logout":
        session.clear()
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Неизвестное действие"}), 400

    if result["success"]:
        session["api_key"] = result["api_key"]

    return jsonify(result)


@app.route("/api/usage")
@login_required
def api_usage():
    user = request.user
    return jsonify({"email": user["email"], "plan": user["plan"], "remaining": user["remaining"]})


@app.route("/api/admin/plan", methods=["POST"])
def admin_set_plan():
    data = request.json
    if data.get("admin_key") != ADMIN_KEY:
        return jsonify({"error": "Неверный ключ"}), 403
    email = data.get("email", "").strip().lower()
    plan = data.get("plan", "enterprise")
    days = data.get("days", 3650)
    set_plan(email, plan, days)
    return jsonify({"success": True, "email": email, "plan": plan})


@app.route("/api/process", methods=["POST"])
@login_required_count
def api_process():
    data = request.json
    text = data.get("text", "")
    mode = data.get("mode", "document")

    try:
        if mode == "file":
            file_data = data.get("file_data", "")
            file_ext = data.get("file_ext", "")
            if file_data.startswith("data:"):
                file_data = file_data.split(",", 1)[1]
            file_bytes = base64.b64decode(file_data)
            if file_ext == "pdf": text = extract_pdf_text(file_bytes)
            elif file_ext in ("docx", "doc"): text = extract_docx_text(file_bytes)
            elif file_ext in ("xlsx", "xls"): text = extract_xlsx_text(file_bytes)
            elif file_ext in ("csv",): text = extract_csv_text(file_bytes)
            else: text = file_bytes.decode("utf-8", errors="replace")
            result = process_document(truncate(text))
        elif mode == "image":
            result = process_image_text(f"[Изображение: {data.get('image_name', 'фото')}]\n\nОпредели содержимое.")
        elif mode == "document": result = process_document(text)
        elif mode == "support": result = customer_support(text)
        elif mode == "report": result = generate_report(text)
        elif mode == "summarize": result = summarize(text)
        elif mode == "translate": result = translate(text)
        elif mode == "emails": result = extract_emails(text)
        elif mode == "url": result = summarize_url(text.strip())
        elif mode == "code": result = summarize(f"Объясни и улучши этот код:\n\n{text}")
        elif mode == "sql": result = summarize(f"Сгенерируй SQL-запрос по описанию:\n\n{text}")
        elif mode == "seo": result = summarize(f"Сделай SEO-оптимизацию текста, добавь ключевые слова, мета-описание:\n\n{text}")
        elif mode == "caption": result = summarize(f"Напиши engaging подпись для соцсетей по описанию:\n\n{text}")
        else: return jsonify({"error": "Неизвестный режим"}), 400
        return jsonify({"result": result})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": f"Ошибка: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
