import os
import base64
from flask import Flask, request, jsonify, render_template_string, session, redirect
from functools import wraps
from automator import (
    process_document, customer_support, generate_report,
    summarize, translate, extract_emails, fetch_url, summarize_url,
    process_image_text, extract_pdf_text, extract_docx_text,
    extract_xlsx_text, extract_csv_text, truncate,
    chat, generate_image_idea, business_idea, resume_improve,
    legal_review, math_solve, code_generate, email_compose, social_post
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

AUTH_HTML = r"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI-Automator</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Noto+Serif+SC:wght@400;500;600&display=swap');
:root{--bg:#fcfaf8;--ink:#26251e;--ink-soft:#504f49;--border:#979696;--chip:#f3f0ef;--accent:#667eea;--accent2:#a855f7}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif;background:var(--bg);color:var(--ink);-webkit-font-smoothing:antialiased}

.hero{position:relative;height:100vh;overflow:hidden;isolation:isolate}
.hero__bg{position:absolute;inset:0;background:url('https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920&q=85') center/cover no-repeat;z-index:0}
.hero__mask{position:absolute;inset:0;z-index:1;pointer-events:none}

.hero__content{position:relative;z-index:2;display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;padding:0 20px;text-align:center}
.hero__title{font-family:'Noto Serif SC','Georgia',serif;font-size:56px;font-weight:600;color:var(--ink);letter-spacing:1px;margin-bottom:16px}
.hero__subtitle{font-family:'Inter',sans-serif;font-size:18px;color:var(--ink-soft);font-weight:300;line-height:1.6;max-width:600px;margin-bottom:40px}

.auth-card{background:rgba(252,250,248,0.92);backdrop-filter:blur(24px);border:1px solid rgba(0,0,0,0.06);border-radius:16px;padding:36px;width:100%;max-width:400px;box-shadow:0 8px 40px rgba(0,0,0,0.08);overflow:hidden}

.tabs{display:flex;margin-bottom:24px;border-radius:10px;overflow:hidden;border:1px solid var(--border)}
.tab{flex:1;padding:10px;text-align:center;cursor:pointer;background:transparent;color:var(--ink-soft);font-size:14px;font-weight:500;transition:all 0.2s}
.tab.active{background:var(--ink);color:#fafafa}

.form-group{margin-bottom:16px}
label{display:block;margin-bottom:5px;color:var(--ink-soft);font-size:12px;font-weight:500;text-transform:uppercase;letter-spacing:0.5px}
input{width:100%;padding:12px 14px;border:1px solid var(--border);border-radius:8px;background:transparent;color:var(--ink);font-size:14px;font-family:inherit;transition:border-color 0.2s}
input:focus{outline:none;border-color:var(--ink)}
input::placeholder{color:#aaa}

.submit-btn{width:100%;padding:12px;border:1px solid var(--ink);border-radius:46px;background:var(--ink);color:#fafafa;font-size:15px;font-weight:500;cursor:pointer;transition:all 0.2s;font-family:inherit;letter-spacing:0.2px}
.submit-btn:hover{background:#3a3933;border-color:#3a3933;transform:translateY(-1px)}

.error{color:#dc2626;text-align:center;margin-bottom:12px;font-size:13px}

.features-row{display:flex;gap:10px;margin-top:28px;justify-content:center;flex-wrap:wrap}
.feat{padding:8px 14px;border:1px solid rgba(0,0,0,0.08);border-radius:8px;font-size:11px;color:var(--ink-soft);display:inline-flex;align-items:center;gap:5px;white-space:nowrap}
.feat span{font-size:14px}
</style>
</head>
<body>
<section class="hero" id="hero">
<div class="hero__bg" aria-hidden="true"></div>
<canvas class="hero__mask" id="heroMask" aria-hidden="true"></canvas>
<div class="hero__content">
<h1 class="hero__title">AI-Automator</h1>
<p class="hero__subtitle">Автоматизация бизнес-процессов на базе AI. Обрабатывайте документы, тексты и данные за секунды.</p>

<div class="auth-card">
<div id="error" class="error" style="display:none"></div>
<div class="tabs">
<div class="tab active" onclick="switchTab('login')">Вход</div>
<div class="tab" onclick="switchTab('register')">Регистрация</div>
</div>
<form id="loginForm" onsubmit="return submitAuth('login')">
<div class="form-group"><label>Email</label><input type="email" id="loginEmail" required placeholder="your@email.com"></div>
<div class="form-group"><label>Пароль</label><input type="password" id="loginPass" required placeholder="&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;"></div>
<button type="submit" class="submit-btn">Войти</button>
</form>
<form id="registerForm" style="display:none" onsubmit="return submitAuth('register')">
<div class="form-group"><label>Email</label><input type="email" id="regEmail" required placeholder="your@email.com"></div>
<div class="form-group"><label>Пароль</label><input type="password" id="regPass" required placeholder="Минимум 6 символов" minlength="6"></div>
<button type="submit" class="submit-btn">Создать аккаунт</button>
</form>
<div class="features-row">
<div class="feat"><span>📄</span>Документы</div>
<div class="feat"><span>💬</span>Поддержка</div>
<div class="feat"><span>📊</span>Отчёты</div>
<div class="feat"><span>🌐</span>Перевод</div>
</div>
</div>
</div>
</section>

<script>
function switchTab(t){document.querySelectorAll('.tab').forEach(e=>e.classList.remove('active'));event.target.classList.add('active');document.getElementById('loginForm').style.display=t==='login'?'block':'none';document.getElementById('registerForm').style.display=t==='register'?'block':'none';document.getElementById('error').style.display='none'}
async function submitAuth(t){event.preventDefault();const e=document.getElementById(t==='login'?'loginEmail':'regEmail').value,p=document.getElementById(t==='login'?'loginPass':'regPass').value;try{const r=await fetch('/api/auth',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:t,email:e,password:p})});const d=await r.json();if(d.success){localStorage.setItem('api_key',d.api_key);localStorage.setItem('email',d.email);window.location.href='/app'}else{document.getElementById('error').textContent=d.error;document.getElementById('error').style.display='block'}}catch(er){document.getElementById('error').textContent='Ошибка соединения';document.getElementById('error').style.display='block'}return false}

(function(){
const hero=document.getElementById('hero'),canvas=document.getElementById('heroMask');
if(!hero||!canvas)return;
const canHover=window.matchMedia('(hover:hover)').matches;
if(!canHover){canvas.style.display='none';return}
const ctx=canvas.getContext('2d');
const MASK='252,250,248';
const R_START=8,R_END=128,R_VARY=0.45,LIFETIME=520,STAMP_STEP=12,MAX_STAMPS=160;
const DPR=Math.min(window.devicePixelRatio||1,2);
let w=0,h=0;
function resize(){const r=hero.getBoundingClientRect();w=r.width;h=r.height;canvas.width=Math.round(w*DPR);canvas.height=Math.round(h*DPR);canvas.style.width=w+'px';canvas.style.height=h+'px';ctx.setTransform(DPR,0,0,DPR,0,0);ctx.globalCompositeOperation='source-over';ctx.fillStyle='rgb('+MASK+')';ctx.fillRect(0,0,w,h)}
resize();window.addEventListener('resize',resize);
const stamps=[];let lastX=null,lastY=null;
function addStamp(x,y){if(stamps.length>=MAX_STAMPS)stamps.shift();stamps.push({x,y,born:performance.now(),seed:Math.random()*Math.PI*2,rmax:R_END*(1-R_VARY+Math.random()*R_VARY)})}
function stampAlong(x,y){if(lastX===null){addStamp(x,y)}else{const dx=x-lastX,dy=y-lastY,dist=Math.hypot(dx,dy),steps=Math.max(1,Math.ceil(dist/STAMP_STEP));for(let i=1;i<=steps;i++)addStamp(lastX+(dx*i)/steps,lastY+(dy*i)/steps)}lastX=x;lastY=y}
function carveInk(x,y,r,alpha,seed){const g=ctx.createRadialGradient(x,y,r*0.25,x,y,r);g.addColorStop(0,'rgba(0,0,0,'+0.95*alpha+')');g.addColorStop(0.55,'rgba(0,0,0,'+0.88*alpha+')');g.addColorStop(1,'rgba(0,0,0,0)');ctx.fillStyle=g;ctx.beginPath();const segs=32;for(let i=0;i<=segs;i++){const a=(i/segs)*Math.PI*2,wob=0.78+0.14*Math.sin(a*3+seed)+0.08*Math.sin(a*7+seed*2.1)+0.05*Math.sin(a*13+seed*0.7),rr=r*wob,px=x+Math.cos(a)*rr,py=y+Math.sin(a)*rr;i===0?ctx.moveTo(px,py):ctx.lineTo(px,py)}ctx.closePath();ctx.fill()}
let running=false;
function loop(){const now=performance.now();ctx.globalCompositeOperation='source-over';ctx.fillStyle='rgb('+MASK+')';ctx.fillRect(0,0,w,h);ctx.globalCompositeOperation='destination-out';for(let i=stamps.length-1;i>=0;i--){const t=(now-stamps[i].born)/LIFETIME;if(t>=1){stamps.splice(i,1);continue}const ease=1-Math.pow(1-t,3),r=R_START+(stamps[i].rmax-R_START)*ease,alpha=1-t*t;carveInk(stamps[i].x,stamps[i].y,r,alpha,stamps[i].seed)}if(stamps.length){requestAnimationFrame(loop)}else{running=false}}
function start(){if(!running){running=true;requestAnimationFrame(loop)}}
hero.addEventListener('mouseenter',e=>{const r=hero.getBoundingClientRect();lastX=e.clientX-r.left;lastY=e.clientY-r.top;stampAlong(lastX,lastY);start()});
hero.addEventListener('mousemove',e=>{const r=hero.getBoundingClientRect();stampAlong(e.clientX-r.left,e.clientY-r.top);start()});
hero.addEventListener('mouseleave',()=>{lastX=null;lastY=null});
})();
</script>
</body>
</html>"""

APP_HTML = r"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI-Automator</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Noto+Serif+SC:wght@400;500;600&display=swap');
:root{--bg:#fcfaf8;--ink:#26251e;--ink-soft:#504f49;--border:#979696;--chip:#f3f0ef;--card:#fff;--card-border:rgba(0,0,0,0.06);--mask:'252,250,248';--hero-bg:url('https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=1920&q=85')}
[data-theme="dark"]{--bg:#0a0a0f;--ink:#e8e6e3;--ink-soft:#9a9890;--border:#2a2a30;--chip:#15151a;--card:#121218;--card-border:rgba(255,255,255,0.06);--mask:'10,10,15';--hero-bg:url('https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1920&q=85')}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',-apple-system,sans-serif;background:var(--bg);color:var(--ink);-webkit-font-smoothing:antialiased;transition:background 0.4s,color 0.4s}

.hero{position:relative;height:300px;overflow:hidden;isolation:isolate}
@media(min-width:768px){.hero{height:340px}}
.hero__bg{position:absolute;inset:0;background:var(--hero-bg) center/cover no-repeat;z-index:0;transition:background 0.4s}
.hero__bg::after{content:'';position:absolute;inset:0;background:linear-gradient(to bottom,rgba(0,0,0,0.1) 0%,rgba(0,0,0,0.35) 100%)}
.hero__mask{position:absolute;inset:0;z-index:1;pointer-events:none}
.hero__content{position:relative;z-index:2;display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;text-align:center}
.hero__title{font-family:'Noto Serif SC',serif;font-size:28px;font-weight:600;color:#fff;letter-spacing:0.5px;margin-bottom:6px;text-shadow:0 2px 12px rgba(0,0,0,0.6)}
@media(min-width:768px){.hero__title{font-size:38px;margin-bottom:8px}}
.hero__subtitle{color:rgba(255,255,255,0.85);font-size:13px;font-weight:300;padding:0 20px;text-shadow:0 1px 8px rgba(0,0,0,0.5)}
@media(min-width:768px){.hero__subtitle{font-size:15px}}

.topbar{position:fixed;top:0;left:0;right:0;z-index:100;display:flex;justify-content:space-between;align-items:center;padding:0 12px;height:50px;background:color-mix(in srgb,var(--bg) 85%,transparent);backdrop-filter:blur(20px);border-bottom:1px solid var(--card-border);transition:background 0.4s;overflow:hidden}
@media(min-width:768px){.topbar{padding:0 32px;height:65px}}
.topbar .left{display:flex;align-items:center;gap:6px;min-width:0}
@media(min-width:768px){.topbar .left{gap:16px}}
.topbar .logo{font-family:'Noto Serif SC',serif;font-size:14px;font-weight:600;color:var(--ink);white-space:nowrap}
@media(min-width:768px){.topbar .logo{font-size:18px}}
.topbar .divider{width:1px;height:14px;background:var(--border);flex-shrink:0;display:none}
@media(min-width:768px){.topbar .divider{display:block;height:20px}}
.topbar .user{color:var(--ink-soft);font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:0;display:none}
@media(min-width:600px){.topbar .user{display:inline;max-width:120px}}
@media(min-width:768px){.topbar .user{font-size:13px;max-width:250px}}
.topbar .plan{background:var(--ink);color:var(--bg);padding:2px 8px;border-radius:12px;font-size:9px;font-weight:700;letter-spacing:0.3px;transition:all 0.4s;white-space:nowrap;flex-shrink:0}
@media(min-width:768px){.topbar .plan{padding:3px 12px;font-size:11px;border-radius:20px;letter-spacing:0.5px}}
.topbar .right{display:flex;align-items:center;gap:6px;flex-shrink:0}
@media(min-width:768px){.topbar .right{gap:12px}}
.topbar .usage{color:var(--ink-soft);font-size:10px;white-space:nowrap}
@media(min-width:768px){.topbar .usage{font-size:12px}}
.theme-toggle{width:28px;height:28px;border-radius:50%;border:1px solid var(--border);background:var(--card);color:var(--ink);cursor:pointer;font-size:13px;display:flex;align-items:center;justify-content:center;transition:all 0.3s;flex-shrink:0}
@media(min-width:768px){.theme-toggle{width:36px;height:36px;font-size:16px}}
.theme-toggle:hover{border-color:var(--ink)}
.topbar .logout{background:transparent;border:1px solid var(--border);color:var(--ink-soft);padding:4px 10px;border-radius:46px;cursor:pointer;font-size:10px;font-family:inherit;transition:all 0.2s;white-space:nowrap}
@media(min-width:768px){.topbar .logout{padding:6px 16px;font-size:12px}}
.topbar .logout:hover{border-color:var(--ink);color:var(--ink)}

.main{max-width:860px;margin:0 auto;padding:0 24px 40px}

.tabs{display:flex;gap:6px;margin:24px 0;flex-wrap:wrap;justify-content:center}
.tab{padding:9px 18px;border:1px solid var(--card-border);border-radius:8px;cursor:pointer;background:var(--card);color:var(--ink-soft);font-size:13px;font-weight:500;transition:all 0.2s;font-family:inherit}
.tab:hover{border-color:var(--ink);color:var(--ink)}
.tab.active{background:var(--ink);border-color:var(--ink);color:var(--bg)}

.input-card{background:var(--card);border:1px solid var(--card-border);border-radius:12px;padding:20px;margin-bottom:16px;box-shadow:0 2px 12px rgba(0,0,0,0.03);transition:all 0.4s}
textarea{width:100%;height:150px;padding:14px;border:1px solid var(--card-border);border-radius:8px;background:var(--chip);color:var(--ink);font-size:14px;resize:vertical;font-family:inherit;transition:all 0.4s}
textarea:focus{outline:none;border-color:var(--ink)}
textarea::placeholder{color:var(--ink-soft);opacity:0.5}

.actions{display:flex;gap:10px;margin-top:12px}
.submit-btn{flex:1;padding:12px;border:1px solid var(--ink);border-radius:46px;background:var(--ink);color:var(--bg);font-size:14px;font-weight:500;cursor:pointer;transition:all 0.2s;font-family:inherit}
.submit-btn:hover{opacity:0.85;transform:translateY(-1px)}
.submit-btn:disabled{opacity:0.4;transform:none;cursor:not-allowed}
.upload-btn{padding:12px 20px;border:1px solid var(--border);border-radius:46px;background:transparent;color:var(--ink-soft);cursor:pointer;font-size:13px;font-family:inherit;transition:all 0.2s}
.upload-btn:hover{border-color:var(--ink);color:var(--ink)}

.result-card{background:var(--card);border:1px solid var(--card-border);border-radius:12px;padding:24px;margin-top:16px;display:none;box-shadow:0 2px 12px rgba(0,0,0,0.03);transition:all 0.4s}
.result-card.visible{display:block;animation:fadeIn 0.4s ease}
.result-label{font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--ink-soft);margin-bottom:12px;font-weight:600}
.result-content{white-space:pre-wrap;line-height:1.8;font-size:14px;color:var(--ink)}

.loading{color:var(--ink-soft);padding:20px;text-align:center}
.loading::after{content:'';display:inline-block;width:16px;height:16px;border:2px solid var(--border);border-top-color:var(--ink);border-radius:50%;animation:spin 0.7s linear infinite;margin-left:8px;vertical-align:middle}

.file-info{color:var(--ink-soft);font-size:12px;margin-top:8px;display:none}
.file-info.visible{display:block}

.features{margin-top:30px;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.feature{padding:16px;border:1px solid var(--card-border);border-radius:12px;background:var(--card);text-align:center;cursor:pointer;transition:all 0.2s}
.feature:hover{border-color:var(--ink);transform:translateY(-2px);box-shadow:0 4px 16px rgba(0,0,0,0.06)}
.feature .icon{font-size:24px;margin-bottom:8px}
.feature .name{font-size:12px;color:var(--ink-soft);font-weight:500}
.feature .desc{font-size:11px;color:var(--border);margin-top:4px}

.footer{margin-top:50px;padding:30px 0;border-top:1px solid var(--chip);text-align:center;color:var(--ink-soft);font-size:12px;letter-spacing:0.3px}

@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
@keyframes spin{to{transform:rotate(360deg)}}

@media(max-width:640px){.features{grid-template-columns:repeat(2,1fr)}.hero__title{font-size:28px}.hero{height:260px}.topbar{padding:0 16px}.main{padding:0 16px 30px}}
</style>
</head>
<body>

<div class="topbar">
<div class="left">
<span class="logo">AI-Automator</span>
<div class="divider"></div>
<span class="user" id="userEmail"></span>
<span class="plan" id="planBadge">FREE</span>
</div>
<div class="right">
<span class="usage" id="usageInfo"></span>
<button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Сменить тему">☀️</button>
<button class="logout" onclick="window.location.href='/logout'">Выйти</button>
</div>
</div>

<section class="hero" id="hero">
<div class="hero__bg" aria-hidden="true"></div>
<canvas class="hero__mask" id="heroMask" aria-hidden="true"></canvas>
<div class="hero__content">
<h1 class="hero__title">AI-Automator</h1>
<p class="hero__subtitle">Обрабатывайте документы, тексты и данные с помощью AI за секунды</p>
</div>
</section>

<div class="main">
<div class="tabs">
<button class="tab active" onclick="setMode('chat',this)">💬 Чат</button>
<button class="tab" onclick="setMode('document',this)">📄 Документы</button>
<button class="tab" onclick="setMode('support',this)">🎧 Поддержка</button>
<button class="tab" onclick="setMode('report',this)">📊 Отчёты</button>
<button class="tab" onclick="setMode('summarize',this)">📝 Резюме</button>
<button class="tab" onclick="setMode('translate',this)">🌐 Перевод</button>
<button class="tab" onclick="setMode('code',this)">💻 Код</button>
<button class="tab" onclick="setMode('sql',this)">🗄 SQL</button>
<button class="tab" onclick="setMode('image-idea',this)">🎨 Промпт фото</button>
<button class="tab" onclick="setMode('business',this)">💡 Бизнес</button>
<button class="tab" onclick="setMode('resume',this)">📋 Резюме</button>
<button class="tab" onclick="setMode('legal',this)">⚖️ Юрист</button>
<button class="tab" onclick="setMode('math',this)">🧮 Математика</button>
<button class="tab" onclick="setMode('email',this)">✉️ Письмо</button>
<button class="tab" onclick="setMode('social',this)">📱 Соцсети</button>
<button class="tab" onclick="setMode('seo',this)">🔍 SEO</button>
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
<div class="result-label">Результат</div>
<div class="result-content" id="result"></div>
</div>

<div class="features">
<div class="feature" onclick="setMode('chat',document.querySelector('.tab'))"><div class="icon">💬</div><div class="name">Чат с AI</div><div class="desc">Просто общайтесь</div></div>
<div class="feature" onclick="setMode('document',document.querySelector('.tab'))"><div class="icon">📄</div><div class="name">Документы</div><div class="desc">Счета, договоры</div></div>
<div class="feature" onclick="setMode('image-idea',document.querySelector('.tab'))"><div class="icon">🎨</div><div class="name">Промпт для фото</div><div class="desc">Для Midjourney/DALL-E</div></div>
<div class="feature" onclick="setMode('business',document.querySelector('.tab'))"><div class="icon">💡</div><div class="name">Бизнес-идея</div><div class="desc">Анализ и план</div></div>
<div class="feature" onclick="setMode('resume',document.querySelector('.tab'))"><div class="icon">📋</div><div class="name">Улучшение резюме</div><div class="desc">HR-экспертиза</div></div>
<div class="feature" onclick="setMode('legal',document.querySelector('.tab'))"><div class="icon">⚖️</div><div class="name">Юрист</div><div class="desc">Анализ договоров</div></div>
<div class="feature" onclick="setMode('math',document.querySelector('.tab'))"><div class="icon">🧮</div><div class="name">Математика</div><div class="desc">Пошаговое решение</div></div>
<div class="feature" onclick="setMode('social',document.querySelector('.tab'))"><div class="icon">📱</div><div class="name">Соцсети</div><div class="desc">Посты и контент</div></div>
</div>

<div class="footer">AI-Automator &copy; 2026 &mdash; Автоматизация бизнес-процессов на базе AI</div>
</div>

<script>
const API_KEY=localStorage.getItem('api_key');
if(!API_KEY)window.location.href='/';
let mode='document',uploadedFile=null;
document.getElementById('userEmail').textContent=localStorage.getItem('email')||'';
const PH={chat:'Напишите сообщение...',document:'Вставьте текст документа...',support:'Введите вопрос клиента...',report:'Вставьте данные для отчёта...',summarize:'Вставьте длинный текст для резюмирования...',translate:'Вставьте текст для перевода...',code:'Опишите задачу или вставьте код...',sql:'Опишите задачу для SQL...',seo:'Вставьте текст для SEO-оптимизации...','image-idea':'Опишите какое изображение хотите получить...',business:'Опишите вашу идею или нишу...',resume:'Вставьте текст резюме или опишите опыт...',legal:'Вставьте текст договора или вопрос юристу...',math:'Введите задачу...',email:'Опишите кому и о чём письмо...',social:'Опишите для какой платформы и о чём пост...'};

function toggleTheme(){const d=document.documentElement,cur=d.getAttribute('data-theme'),next=cur==='dark'?'light':'dark';d.setAttribute('data-theme',next);localStorage.setItem('theme',next);document.getElementById('themeBtn').textContent=next==='dark'?'🌙':'☀️'}
const saved=localStorage.getItem('theme');if(saved){document.documentElement.setAttribute('data-theme',saved);document.getElementById('themeBtn').textContent=saved==='dark'?'🌙':'☀️'}

async function loadUsage(){try{const r=await fetch('/api/usage',{headers:{'X-API-Key':API_KEY}});const d=await r.json();if(d.plan){document.getElementById('planBadge').textContent=d.plan.toUpperCase();document.getElementById('usageInfo').textContent=d.remaining+' запросов'}}catch(e){}}
loadUsage();

function setMode(m,el){mode=m;document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));if(el)el.classList.add('active');document.getElementById('input').placeholder=PH[m]||''}
function quick(t){document.getElementById('input').value=t;document.getElementById('input').focus()}

function handleFile(event){const f=event.target.files[0];if(!f)return;document.getElementById('fileName').textContent='📎 '+f.name;document.getElementById('fileName').classList.add('visible');const ext=f.name.split('.').pop().toLowerCase();const bin=['pdf','docx','xlsx','doc','xls'];const img=['jpg','jpeg','png','webp','gif'];if(img.includes(ext)){const r=new FileReader();r.onload=e=>{uploadedFile={type:'image',data:e.target.result,name:f.name}};r.readAsDataURL(f)}else if(bin.includes(ext)){const r=new FileReader();r.onload=e=>{uploadedFile={type:'binary',data:e.target.result,name:f.name,ext:ext};document.getElementById('input').value='[Файл: '+f.name+']'};r.readAsDataURL(f)}else{const r=new FileReader();r.onload=e=>{document.getElementById('input').value=e.target.result;uploadedFile=null};r.readAsText(f)}}

async function process(){const input=document.getElementById('input').value;if(!input.trim()&&!uploadedFile)return;const btn=document.querySelector('.submit-btn');const card=document.getElementById('resultCard');const res=document.getElementById('result');btn.disabled=true;btn.textContent='Обработка...';card.classList.add('visible');res.innerHTML='<span class="loading">AI обрабатывает запрос</span>';try{const p={text:input,mode:mode};if(uploadedFile&&uploadedFile.type==='image'){p.image=uploadedFile.data;p.image_name=uploadedFile.name;p.mode='image'}else if(uploadedFile&&uploadedFile.type==='binary'){p.file_data=uploadedFile.data;p.file_ext=uploadedFile.ext;p.file_name=uploadedFile.name;p.mode='file'}if(mode==='url'&&(input.includes('http://')||input.includes('https://')))p.mode='url';const r=await fetch('/api/process',{method:'POST',headers:{'Content-Type':'application/json','X-API-Key':API_KEY},body:JSON.stringify(p)});const d=await r.json();res.textContent=d.result||d.error;uploadedFile=null;loadUsage()}catch(e){res.textContent='Ошибка: '+e.message}btn.disabled=false;btn.textContent='Обработать'}

(function(){
const hero=document.getElementById('hero'),canvas=document.getElementById('heroMask');
if(!hero||!canvas)return;
const canHover=window.matchMedia('(hover:hover)').matches;
if(!canHover){canvas.style.display='none';return}
const ctx=canvas.getContext('2d');
const R_START=8,R_END=128,R_VARY=0.45,LIFETIME=520,STAMP_STEP=12,MAX_STAMPS=160;
const DPR=Math.min(window.devicePixelRatio||1,2);
let w=0,h=0;
function getMask(){return getComputedStyle(document.documentElement).getPropertyValue('--mask').trim().replace(/'/g,'')}
function resize(){const r=hero.getBoundingClientRect();w=r.width;h=r.height;canvas.width=Math.round(w*DPR);canvas.height=Math.round(h*DPR);canvas.style.width=w+'px';canvas.style.height=h+'px';ctx.setTransform(DPR,0,0,DPR,0,0);ctx.globalCompositeOperation='source-over';ctx.fillStyle='rgb('+getMask()+')';ctx.fillRect(0,0,w,h)}
resize();window.addEventListener('resize',resize);
const stamps=[];let lastX=null,lastY=null;
function addStamp(x,y){if(stamps.length>=MAX_STAMPS)stamps.shift();stamps.push({x,y,born:performance.now(),seed:Math.random()*Math.PI*2,rmax:R_END*(1-R_VARY+Math.random()*R_VARY)})}
function stampAlong(x,y){if(lastX===null){addStamp(x,y)}else{const dx=x-lastX,dy=y-lastY,dist=Math.hypot(dx,dy),steps=Math.max(1,Math.ceil(dist/STAMP_STEP));for(let i=1;i<=steps;i++)addStamp(lastX+(dx*i)/steps,lastY+(dy*i)/steps)}lastX=x;lastY=y}
function carveInk(x,y,r,alpha,seed){const g=ctx.createRadialGradient(x,y,r*0.25,x,y,r);g.addColorStop(0,'rgba(0,0,0,'+0.95*alpha+')');g.addColorStop(0.55,'rgba(0,0,0,'+0.88*alpha+')');g.addColorStop(1,'rgba(0,0,0,0)');ctx.fillStyle=g;ctx.beginPath();const segs=32;for(let i=0;i<=segs;i++){const a=(i/segs)*Math.PI*2,wob=0.78+0.14*Math.sin(a*3+seed)+0.08*Math.sin(a*7+seed*2.1)+0.05*Math.sin(a*13+seed*0.7),rr=r*wob,px=x+Math.cos(a)*rr,py=y+Math.sin(a)*rr;i===0?ctx.moveTo(px,py):ctx.lineTo(px,py)}ctx.closePath();ctx.fill()}
let running=false;
function loop(){const now=performance.now();ctx.globalCompositeOperation='source-over';ctx.fillStyle='rgb('+getMask()+')';ctx.fillRect(0,0,w,h);ctx.globalCompositeOperation='destination-out';for(let i=stamps.length-1;i>=0;i--){const t=(now-stamps[i].born)/LIFETIME;if(t>=1){stamps.splice(i,1);continue}const ease=1-Math.pow(1-t,3),r=R_START+(stamps[i].rmax-R_START)*ease,alpha=1-t*t;carveInk(stamps[i].x,stamps[i].y,r,alpha,stamps[i].seed)}if(stamps.length){requestAnimationFrame(loop)}else{running=false}}
function start(){if(!running){running=true;requestAnimationFrame(loop)}}
hero.addEventListener('mouseenter',e=>{const r=hero.getBoundingClientRect();lastX=e.clientX-r.left;lastY=e.clientY-r.top;stampAlong(lastX,lastY);start()});
hero.addEventListener('mousemove',e=>{const r=hero.getBoundingClientRect();stampAlong(e.clientX-r.left,e.clientY-r.top);start()});
hero.addEventListener('mouseleave',()=>{lastX=null;lastY=null});
})();
</script>
</body>
</html>"""


@app.route("/")
def auth_page():
    return render_template_string(AUTH_HTML)

@app.route("/app")
def app_page():
    if not session.get("api_key"):
        return redirect("/")
    return render_template_string(APP_HTML)

@app.route("/logout")
def logout_page():
    session.clear()
    return '<html><head><script>localStorage.removeItem("api_key");localStorage.removeItem("email");window.location.href="/";</script></head></html>'

@app.route("/api/auth", methods=["POST"])
def api_auth():
    data = request.json
    action = data.get("action")
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    if action == "register": result = register(email, password)
    elif action == "login": result = login(email, password)
    elif action == "logout": session.clear(); return jsonify({"success": True})
    else: return jsonify({"error": "Неизвестное действие"}), 400
    if result["success"]: session["api_key"] = result["api_key"]
    return jsonify(result)

@app.route("/api/usage")
@login_required
def api_usage():
    u = request.user
    return jsonify({"email": u["email"], "plan": u["plan"], "remaining": u["remaining"]})

@app.route("/api/admin/plan", methods=["POST"])
def admin_set_plan():
    data = request.json
    if data.get("admin_key") != ADMIN_KEY: return jsonify({"error": "Неверный ключ"}), 403
    set_plan(data.get("email","").strip().lower(), data.get("plan","enterprise"), data.get("days",3650))
    return jsonify({"success": True})

@app.route("/api/process", methods=["POST"])
@login_required_count
def api_process():
    data = request.json
    text = data.get("text", "")
    mode = data.get("mode", "document")
    try:
        if mode == "file":
            fd = data.get("file_data", "")
            fe = data.get("file_ext", "")
            if fd.startswith("data:"): fd = fd.split(",",1)[1]
            fb = base64.b64decode(fd)
            if fe == "pdf": text = extract_pdf_text(fb)
            elif fe in ("docx","doc"): text = extract_docx_text(fb)
            elif fe in ("xlsx","xls"): text = extract_xlsx_text(fb)
            elif fe == "csv": text = extract_csv_text(fb)
            else: text = fb.decode("utf-8", errors="replace")
            result = process_document(truncate(text))
        elif mode == "image": result = process_image_text(f"[Изображение: {data.get('image_name','фото')}]\n\nОпредели содержимое.")
        elif mode == "document": result = process_document(text)
        elif mode == "support": result = customer_support(text)
        elif mode == "report": result = generate_report(text)
        elif mode == "summarize": result = summarize(text)
        elif mode == "translate": result = translate(text)
        elif mode == "emails": result = extract_emails(text)
        elif mode == "url": result = summarize_url(text.strip())
        elif mode == "code": result = summarize(f"Объясни и улучши этот код:\n\n{text}")
        elif mode == "sql": result = summarize(f"Сгенерируй SQL-запрос по описанию:\n\n{text}")
        elif mode == "seo": result = summarize(f"Сделай SEO-оптимизацию текста, добавь мета-описание и ключевые слова:\n\n{text}")
        elif mode == "caption": result = summarize(f"Напиши engaging подпись для соцсетей:\n\n{text}")
        elif mode == "chat": result = chat(text)
        elif mode == "image-idea": result = generate_image_idea(text)
        elif mode == "business": result = business_idea(text)
        elif mode == "resume": result = resume_improve(text)
        elif mode == "legal": result = legal_review(text)
        elif mode == "math": result = math_solve(text)
        elif mode == "email": result = email_compose(text)
        elif mode == "social": result = social_post(text)
        else: return jsonify({"error": "Неизвестный режим"}), 400
        return jsonify({"result": result})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": f"Ошибка: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
