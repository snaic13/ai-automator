import os
import base64
from flask import Flask, request, jsonify, render_template_string
from automator import (
    process_document, customer_support, generate_report,
    summarize, translate, extract_emails, fetch_url, summarize_url,
    process_image_text, extract_pdf_text, extract_docx_text,
    extract_xlsx_text, extract_csv_text, truncate
)

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI-Automator</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, sans-serif; background: #0f0f23; color: #e0e0e0; min-height: 100vh; }
        .container { max-width: 800px; margin: 0 auto; padding: 40px 20px; }
        h1 { text-align: center; font-size: 2.5em; margin-bottom: 10px; background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { text-align: center; color: #888; margin-bottom: 40px; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        .tab { padding: 12px 24px; border: 2px solid #333; border-radius: 8px; cursor: pointer; transition: all 0.3s; background: transparent; color: #e0e0e0; font-size: 14px; }
        .tab:hover { border-color: #667eea; }
        .tab.active { background: linear-gradient(135deg, #667eea, #764ba2); border-color: transparent; color: white; }
        .input-area { margin-bottom: 20px; }
        textarea { width: 100%; height: 150px; padding: 16px; border: 2px solid #333; border-radius: 8px; background: #1a1a2e; color: #e0e0e0; font-size: 16px; resize: vertical; }
        textarea:focus { outline: none; border-color: #667eea; }
        button { width: 100%; padding: 16px; border: none; border-radius: 8px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; font-size: 16px; cursor: pointer; transition: transform 0.2s; }
        button:hover { transform: translateY(-2px); }
        button:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .result { margin-top: 20px; padding: 20px; border: 2px solid #333; border-radius: 8px; background: #1a1a2e; white-space: pre-wrap; line-height: 1.6; }
        .loading { text-align: center; color: #667eea; }
    </style>
</head>
<body>
    <div class="container">
        <h1>AI-Automator</h1>
        <p class="subtitle">Автоматизация бизнес-процессов на базе AI</p>

        <div class="tabs">
            <button class="tab active" onclick="setMode('document')">Документы</button>
            <button class="tab" onclick="setMode('support')">Поддержка</button>
            <button class="tab" onclick="setMode('report')">Отчёты</button>
            <button class="tab" onclick="setMode('summarize')">Резюме</button>
            <button class="tab" onclick="setMode('translate')">Перевод</button>
            <button class="tab" onclick="setMode('emails')">Email</button>
            <button class="tab" onclick="setMode('url')">Ссылка URL</button>
        </div>

        <div class="input-area">
            <textarea id="input" placeholder="Введите текст для обработки..."></textarea>
        </div>

        <div class="upload-area" id="uploadArea">
            <input type="file" id="fileInput" accept=".txt,.csv,.json,.md,.pdf,.docx,.doc,.xlsx,.xls,.jpg,.jpeg,.png,.webp" style="display:none" onchange="handleFile(event)">
            <button onclick="document.getElementById('fileInput').click()" style="background:transparent;border:2px dashed #555;padding:12px 24px;border-radius:8px;color:#aaa;cursor:pointer;width:100%;margin-bottom:15px;">
                📎 Загрузить файл (текст, фото, документ)
            </button>
            <div id="fileName" style="color:#667eea;margin-bottom:10px;display:none;"></div>
        </div>

        <button id="submitBtn" onclick="process()">Обработать</button>

        <div id="result" class="result" style="display:none;"></div>
    </div>

    <script>
        let mode = 'document';

        let uploadedFile = null;
        let uploadedFileName = '';

        function setMode(m) {
            mode = m;
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            const input = document.getElementById('input');
            if (m === 'document') input.placeholder = 'Вставьте текст документа, счёта или договора...';
            if (m === 'support') input.placeholder = 'Введите вопрос клиента...';
            if (m === 'report') input.placeholder = 'Вставьте данные для отчёта...';
            if (m === 'summarize') input.placeholder = 'Вставьте текст для резюмирования...';
            if (m === 'translate') input.placeholder = 'Вставьте текст для перевода на английский...';
            if (m === 'emails') input.placeholder = 'Вставьте текст для извлечения email-адресов...';
            if (m === 'url') input.placeholder = 'Вставьте ссылку для чтения содержимого...';
        }

        function handleFile(event) {
            const file = event.target.files[0];
            if (!file) return;

            uploadedFileName = file.name;
            document.getElementById('fileName').textContent = 'Файл: ' + file.name;
            document.getElementById('fileName').style.display = 'block';

            const ext = file.name.split('.').pop().toLowerCase();
            const binaryExts = ['pdf', 'docx', 'xlsx', 'doc', 'xls'];
            const imageTypes = ['jpg', 'jpeg', 'png', 'webp', 'gif'];

            if (imageTypes.includes(ext)) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    uploadedFile = { type: 'image', data: e.target.result, name: file.name };
                };
                reader.readAsDataURL(file);
            } else if (binaryExts.includes(ext)) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    uploadedFile = { type: 'binary', data: e.target.result, name: file.name, ext: ext };
                    document.getElementById('input').value = '[Файл загружен: ' + file.name + ']';
                };
                reader.readAsDataURL(file);
            } else {
                const reader = new FileReader();
                reader.onload = (e) => {
                    document.getElementById('input').value = e.target.result;
                    uploadedFile = null;
                };
                reader.readAsText(file);
            }
        }

        async function process() {
            const input = document.getElementById('input').value;
            if (!input.trim() && !uploadedFile) return;

            const btn = document.getElementById('submitBtn');
            const result = document.getElementById('result');

            btn.disabled = true;
            btn.textContent = 'Обработка...';
            result.style.display = 'block';
            result.innerHTML = '<span class="loading">AI обрабатывает запрос...</span>';

            try {
                const payload = { text: input, mode: mode };

                if (uploadedFile && uploadedFile.type === 'image') {
                    payload.image = uploadedFile.data;
                    payload.image_name = uploadedFile.name;
                    payload.mode = 'image';
                } else if (uploadedFile && uploadedFile.type === 'binary') {
                    payload.file_data = uploadedFile.data;
                    payload.file_ext = uploadedFile.ext;
                    payload.file_name = uploadedFile.name;
                    payload.mode = 'file';
                }

                if (mode === 'url' && (input.includes('http://') || input.includes('https://'))) {
                    payload.mode = 'url';
                }

                const res = await fetch('/api/process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                result.textContent = data.result || data.error;
                uploadedFile = null;
            } catch (e) {
                result.textContent = 'Ошибка: ' + e.message;
            }

            btn.disabled = false;
            btn.textContent = 'Обработать';
        }
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/process", methods=["POST"])
def api_process():
    data = request.json
    text = data.get("text", "")
    mode = data.get("mode", "document")

    try:
        if mode == "file":
            file_data = data.get("file_data", "")
            file_ext = data.get("file_ext", "")
            file_name = data.get("file_name", "")
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
            result = process_image_text(f"[Изображение загружено: {data.get('image_name', 'фото')}]\n\nОпредели содержимое изображения и обработай его.")

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
