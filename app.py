import os
import base64
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
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
    <title>AI-Automator - Вход</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, sans-serif; background: #0f0f23; color: #e0e0e0; min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .auth-box { max-width: 400px; width: 100%; padding: 40px; }
        h1 { text-align: center; font-size: 2.2em; margin-bottom: 8px; background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { text-align: center; color: #888; margin-bottom: 30px; }
        .tabs { display: flex; gap: 0; margin-bottom: 20px; border-radius: 8px; overflow: hidden; border: 2px solid #333; }
        .tab { flex: 1; padding: 12px; text-align: center; cursor: pointer; background: transparent; color: #888; transition: all 0.3s; }
        .tab.active { background: linear-gradient(135deg, #667eea, #764ba2); color: white; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; color: #aaa; font-size: 14px; }
        input { width: 100%; padding: 12px; border: 2px solid #333; border-radius: 8px; background: #1a1a2e; color: #e0e0e0; font-size: 16px; }
        input:focus { outline: none; border-color: #667eea; }
        button { width: 100%; padding: 14px; border: none; border-radius: 8px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; font-size: 16px; cursor: pointer; margin-top: 10px; }
        button:hover { opacity: 0.9; }
        .error { color: #e74c3c; text-align: center; margin-bottom: 15px; font-size: 14px; }
        .pricing { margin-top: 30px; padding: 20px; border: 2px solid #333; border-radius: 8px; background: #1a1a2e; }
        .pricing h3 { margin-bottom: 15px; color: #667eea; }
        .plan { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #333; }
        .plan:last-child { border: none; }
        .plan-name { font-weight: bold; }
        .plan-limit { color: #888; }
        .plan-price { color: #764ba2; }
    </style>
</head>
<body>
    <div class="auth-box">
        <h1>AI-Automator</h1>
        <p class="subtitle">Автоматизация бизнес-процессов на базе AI</p>

        <div id="error" class="error" style="display:none;"></div>

        <div class="tabs">
            <div class="tab active" onclick="switchTab('login')">Вход</div>
            <div class="tab" onclick="switchTab('register')">Регистрация</div>
        </div>

        <form id="loginForm" onsubmit="return submitAuth('login')">
            <div class="form-group">
                <label>Email</label>
                <input type="email" id="loginEmail" required placeholder="your@email.com">
            </div>
            <div class="form-group">
                <label>Пароль</label>
                <input type="password" id="loginPass" required placeholder="••••••••">
            </div>
            <button type="submit">Войти</button>
        </form>

        <form id="registerForm" style="display:none;" onsubmit="return submitAuth('register')">
            <div class="form-group">
                <label>Email</label>
                <input type="email" id="regEmail" required placeholder="your@email.com">
            </div>
            <div class="form-group">
                <label>Пароль</label>
                <input type="password" id="regPass" required placeholder="Минимум 6 символов" minlength="6">
            </div>
            <button type="submit">Создать аккаунт</button>
        </form>

        <div class="pricing">
            <h3>Тарифы</h3>
            <div class="plan">
                <span class="plan-name">Free</span>
                <span class="plan-limit">10 запросов/день</span>
                <span class="plan-price">Бесплатно</span>
            </div>
            <div class="plan">
                <span class="plan-name">Starter</span>
                <span class="plan-limit">100 запросов/день</span>
                <span class="plan-price">$9/мес</span>
            </div>
            <div class="plan">
                <span class="plan-name">Pro</span>
                <span class="plan-limit">500 запросов/день</span>
                <span class="plan-price">$29/мес</span>
            </div>
            <div class="plan">
                <span class="plan-name">Enterprise</span>
                <span class="plan-limit">Безлимит</span>
                <span class="plan-price">$99/мес</span>
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
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: type, email, password: pass })
                });
                const data = await res.json();

                if (data.success) {
                    localStorage.setItem('api_key', data.api_key);
                    localStorage.setItem('email', data.email);
                    window.location.href = '/app';
                } else {
                    document.getElementById('error').textContent = data.error;
                    document.getElementById('error').style.display = 'block';
                }
            } catch (e) {
                document.getElementById('error').textContent = 'Ошибка соединения';
                document.getElementById('error').style.display = 'block';
            }
            return false;
        }
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
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, sans-serif; background: #0f0f23; color: #e0e0e0; min-height: 100vh; }
        .topbar { display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; background: #1a1a2e; border-bottom: 1px solid #333; }
        .topbar .user { color: #888; font-size: 14px; }
        .topbar .plan-badge { background: linear-gradient(135deg, #667eea, #764ba2); padding: 4px 12px; border-radius: 12px; font-size: 12px; margin-left: 10px; }
        .topbar .usage { color: #aaa; font-size: 13px; }
        .topbar button { background: transparent; border: 1px solid #555; color: #aaa; padding: 6px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; }
        .topbar button:hover { border-color: #667eea; color: #667eea; }
        .container { max-width: 800px; margin: 0 auto; padding: 30px 20px; }
        h1 { text-align: center; font-size: 2.2em; margin-bottom: 8px; background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { text-align: center; color: #888; margin-bottom: 30px; }
        .tabs { display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }
        .tab { padding: 10px 18px; border: 2px solid #333; border-radius: 8px; cursor: pointer; transition: all 0.3s; background: transparent; color: #e0e0e0; font-size: 13px; }
        .tab:hover { border-color: #667eea; }
        .tab.active { background: linear-gradient(135deg, #667eea, #764ba2); border-color: transparent; color: white; }
        textarea { width: 100%; height: 140px; padding: 14px; border: 2px solid #333; border-radius: 8px; background: #1a1a2e; color: #e0e0e0; font-size: 15px; resize: vertical; margin-bottom: 15px; }
        textarea:focus { outline: none; border-color: #667eea; }
        .btn-row { display: flex; gap: 10px; margin-bottom: 15px; }
        button.main-btn { flex: 1; padding: 14px; border: none; border-radius: 8px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; font-size: 15px; cursor: pointer; }
        button.upload-btn { padding: 14px 20px; border: 2px dashed #555; border-radius: 8px; background: transparent; color: #aaa; cursor: pointer; font-size: 14px; }
        .result { margin-top: 15px; padding: 18px; border: 2px solid #333; border-radius: 8px; background: #1a1a2e; white-space: pre-wrap; line-height: 1.6; font-size: 14px; }
        .loading { text-align: center; color: #667eea; }
        .file-info { color: #667eea; font-size: 13px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="topbar">
        <div>
            <span class="user" id="userEmail"></span>
            <span class="plan-badge" id="planBadge">FREE</span>
        </div>
        <div style="display:flex;align-items:center;gap:15px;">
            <span class="usage" id="usageInfo"></span>
            <button onclick="window.location.replace('/logout')">Выйти</button>
        </div>
    </div>

    <div class="container">
        <h1>AI-Automator</h1>
        <p class="subtitle">Автоматизация бизнес-процессов на базе AI</p>

        <div class="tabs">
            <button class="tab active" onclick="setMode('document', this)">Документы</button>
            <button class="tab" onclick="setMode('support', this)">Поддержка</button>
            <button class="tab" onclick="setMode('report', this)">Отчёты</button>
            <button class="tab" onclick="setMode('summarize', this)">Резюме</button>
            <button class="tab" onclick="setMode('translate', this)">Перевод</button>
            <button class="tab" onclick="setMode('emails', this)">Email</button>
            <button class="tab" onclick="setMode('url', this)">Ссылка URL</button>
        </div>

        <textarea id="input" placeholder="Введите текст для обработки..."></textarea>

        <div class="btn-row">
            <button class="main-btn" onclick="process()">Обработать</button>
            <button class="upload-btn" onclick="document.getElementById('fileInput').click()">Файл</button>
        </div>
        <input type="file" id="fileInput" accept=".txt,.csv,.json,.md,.pdf,.docx,.doc,.xlsx,.xls,.jpg,.jpeg,.png,.webp" style="display:none" onchange="handleFile(event)">
        <div class="file-info" id="fileName" style="display:none;"></div>

        <div id="result" class="result" style="display:none;"></div>
    </div>

    <script>
        const API_KEY = localStorage.getItem('api_key');
        if (!API_KEY) window.location.href = '/';

        let mode = 'document';
        let uploadedFile = null;

        document.getElementById('userEmail').textContent = localStorage.getItem('email') || '';

        async function loadUsage() {
            try {
                const res = await fetch('/api/usage', { headers: { 'X-API-Key': API_KEY } });
                const data = await res.json();
                document.getElementById('planBadge').textContent = (data.plan || 'free').toUpperCase();
                document.getElementById('usageInfo').textContent = data.remaining + ' запросов осталось';
            } catch(e) {}
        }
        loadUsage();

        function setMode(m, el) {
            mode = m;
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            if (el) el.classList.add('active');
            const input = document.getElementById('input');
            const placeholders = {
                document: 'Вставьте текст документа, счёта или договора...',
                support: 'Введите вопрос клиента...',
                report: 'Вставьте данные для отчёта...',
                summarize: 'Вставьте текст для резюмирования...',
                translate: 'Вставьте текст для перевода на английский...',
                emails: 'Вставьте текст для извлечения email-адресов...',
                url: 'Вставьте ссылку для чтения содержимого...'
            };
            input.placeholder = placeholders[m] || '';
        }

        function handleFile(event) {
            const file = event.target.files[0];
            if (!file) return;
            document.getElementById('fileName').textContent = 'Файл: ' + file.name;
            document.getElementById('fileName').style.display = 'block';
            const ext = file.name.split('.').pop().toLowerCase();
            const binaryExts = ['pdf', 'docx', 'xlsx', 'doc', 'xls'];
            const imageTypes = ['jpg', 'jpeg', 'png', 'webp', 'gif'];

            if (imageTypes.includes(ext)) {
                const reader = new FileReader();
                reader.onload = (e) => { uploadedFile = { type: 'image', data: e.target.result, name: file.name }; };
                reader.readAsDataURL(file);
            } else if (binaryExts.includes(ext)) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    uploadedFile = { type: 'binary', data: e.target.result, name: file.name, ext: ext };
                    document.getElementById('input').value = '[Файл: ' + file.name + ']';
                };
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
            const btn = document.querySelector('.main-btn');
            const result = document.getElementById('result');
            btn.disabled = true; btn.textContent = 'Обработка...';
            result.style.display = 'block';
            result.innerHTML = '<span class="loading">AI обрабатывает запрос...</span>';

            try {
                const payload = { text: input, mode: mode };
                if (uploadedFile && uploadedFile.type === 'image') { payload.image = uploadedFile.data; payload.image_name = uploadedFile.name; payload.mode = 'image'; }
                else if (uploadedFile && uploadedFile.type === 'binary') { payload.file_data = uploadedFile.data; payload.file_ext = uploadedFile.ext; payload.file_name = uploadedFile.name; payload.mode = 'file'; }
                if (mode === 'url' && (input.includes('http://') || input.includes('https://'))) payload.mode = 'url';

                const res = await fetch('/api/process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-API-Key': API_KEY },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                result.textContent = data.result || data.error;
                uploadedFile = null;
                loadUsage();
            } catch (e) {
                result.textContent = 'Ошибка: ' + e.message;
            }
            btn.disabled = false; btn.textContent = 'Обработать';
        }

        function logout() {
            localStorage.removeItem('api_key');
            localStorage.removeItem('email');
            window.location.replace('/');
        }
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


@app.route("/api/logout")
def api_logout():
    session.clear()
    return redirect("/")


@app.route("/api/usage")
@login_required
def api_usage():
    user = request.user
    return jsonify({
        "email": user["email"],
        "plan": user["plan"],
        "remaining": user["remaining"],
    })


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

            if file_ext == "pdf":
                text = extract_pdf_text(file_bytes)
            elif file_ext in ("docx", "doc"):
                text = extract_docx_text(file_bytes)
            elif file_ext in ("xlsx", "xls"):
                text = extract_xlsx_text(file_bytes)
            elif file_ext in ("csv",):
                text = extract_csv_text(file_bytes)
            else:
                text = file_bytes.decode("utf-8", errors="replace")

            result = process_document(truncate(text))

        elif mode == "image":
            result = process_image_text(f"[Изображение: {data.get('image_name', 'фото')}]\n\nОпредели содержимое.")
        elif mode == "document":
            result = process_document(text)
        elif mode == "support":
            result = customer_support(text)
        elif mode == "report":
            result = generate_report(text)
        elif mode == "summarize":
            result = summarize(text)
        elif mode == "translate":
            result = translate(text)
        elif mode == "emails":
            result = extract_emails(text)
        elif mode == "url":
            result = summarize_url(text.strip())
        else:
            return jsonify({"error": "Неизвестный режим"}), 400

        return jsonify({"result": result})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Ошибка: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
