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
from auth import register, login, check_api_key, set_plan, change_password, reset_password, ADMIN_KEY
from payment import PLANS
from payment import robokassa_init_url, robokassa_verify

app = Flask(__name__)
app.secret_key = os.urandom(24)
payment_logs = []

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = session.get("api_key") or request.headers.get("X-API-Key")
        if not api_key:
            return jsonify({"error": "Требуется авторизация"}), 401
        try:
            user = check_api_key(api_key, count=False)
        except Exception as e:
            return jsonify({"error": f"Ошибка базы данных: {str(e)}"}), 500
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
        try:
            user = check_api_key(api_key, count=True)
        except Exception as e:
            return jsonify({"error": f"Ошибка базы данных: {str(e)}"}), 500
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
body{font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif;background:var(--bg);color:var(--ink);-webkit-font-smoothing:antialiased;overflow-x:hidden;min-height:100vh;display:flex;flex-direction:column}

.hero{position:relative;flex:1;overflow:hidden;isolation:isolate;display:flex;flex-direction:column}
.hero__bg{position:absolute;inset:0;background:url('https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920&q=85') center/cover no-repeat;z-index:0}
.hero__mask{position:absolute;inset:0;z-index:1;pointer-events:none}

.hero__content{position:relative;z-index:2;display:flex;flex-direction:column;align-items:center;justify-content:center;flex:1;padding:0 20px;text-align:center}
.hero__title{font-family:'Noto Serif SC','Georgia',serif;font-size:56px;font-weight:600;color:var(--ink);letter-spacing:1px;margin-bottom:16px}
.hero__subtitle{font-family:'Inter',sans-serif;font-size:18px;color:var(--ink-soft);font-weight:300;line-height:1.6;max-width:600px;margin-bottom:40px}

.auth-card{background:rgba(252,250,248,0.92);backdrop-filter:blur(24px);border:1px solid rgba(0,0,0,0.06);border-radius:16px;padding:36px;width:100%;max-width:400px;box-shadow:0 8px 40px rgba(0,0,0,0.08);overflow:hidden}

.tabs{display:flex;margin-bottom:24px;border-radius:10px;overflow:hidden;border:1px solid var(--border)}
.tab{flex:1;padding:10px;text-align:center;cursor:pointer;background:transparent;color:var(--ink-soft);font-size:14px;font-weight:500;transition:all 0.2s}
.tab.active{background:var(--ink);color:#fafafa}

.form-group{margin-bottom:16px;position:relative}
label{display:block;margin-bottom:5px;color:var(--ink-soft);font-size:12px;font-weight:500;text-transform:uppercase;letter-spacing:0.5px}
input{width:100%;padding:12px 14px;border:1px solid var(--border);border-radius:8px;background:transparent;color:var(--ink);font-size:14px;font-family:inherit;transition:border-color 0.2s}
input:focus{outline:none;border-color:var(--ink)}
input::placeholder{color:#aaa}
.pw-toggle{position:absolute;right:12px;top:32px;cursor:pointer;font-size:16px;color:var(--ink-soft);user-select:none}

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
<div class="form-group"><label>Пароль</label><input type="password" id="loginPass" required placeholder="&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;"><span class="pw-toggle" onclick="togglePw('loginPass')">👁</span></div>
<button type="submit" class="submit-btn">Войти</button>
<div style="text-align:center;margin-top:12px"><a href="#" onclick="showResetPw()" style="color:var(--ink-soft);font-size:13px;text-decoration:underline">Забыли пароль?</a></div>
</form>
<form id="registerForm" style="display:none" onsubmit="return submitAuth('register')">
<div class="form-group"><label>Email</label><input type="email" id="regEmail" required placeholder="your@email.com"></div>
<div class="form-group"><label>Пароль</label><input type="password" id="regPass" required placeholder="Минимум 6 символов" minlength="6"><span class="pw-toggle" onclick="togglePw('regPass')">👁</span></div>
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
</div>
</div>
</section>
<div style="text-align:center;padding:12px;font-size:11px;color:#666;background:#fff;border-top:1px solid #eee">ИНН: 526320301575 &middot; Самозанятый Маширов С.Д. &middot; <a href="/legal" style="color:#666;text-decoration:underline">Публичная оферта</a> &middot; <a href="/pricing" style="color:#666;text-decoration:underline">Тарифы</a></div>
<div id="resetModal" style="display:none;position:fixed;inset:0;z-index:200;background:rgba(0,0,0,0.5);align-items:center;justify-content:center" onclick="if(event.target===this)closeResetPw()">
<div style="background:var(--bg);border-radius:16px;padding:32px;max-width:380px;width:90%;box-shadow:0 20px 60px rgba(0,0,0,0.2)">
<h3 style="margin-bottom:16px;font-size:18px">Сброс пароля</h3>
<p style="font-size:13px;color:var(--ink-soft);margin-bottom:16px">Введите email, указанный при регистрации</p>
<div style="margin-bottom:16px"><input type="email" id="resetEmail" placeholder="your@email.com" style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:8px;font-size:14px;background:transparent;color:var(--ink)"></div>
<div id="resetMsg" style="font-size:13px;margin-bottom:12px"></div>
<div style="display:flex;gap:8px"><button onclick="doResetPw()" style="flex:1;padding:10px;background:var(--ink);color:var(--bg);border:none;border-radius:8px;font-size:14px;cursor:pointer;font-family:inherit">Отправить</button><button onclick="closeResetPw()" style="padding:10px 16px;background:transparent;border:1px solid var(--border);border-radius:8px;font-size:14px;cursor:pointer;color:var(--ink);font-family:inherit">Отмена</button></div>
</div>
</div>

<script>
function togglePw(id){const i=document.getElementById(id);i.type=i.type==='password'?'text':'password'}
function switchTab(t){document.querySelectorAll('.tab').forEach(e=>e.classList.remove('active'));event.target.classList.add('active');document.getElementById('loginForm').style.display=t==='login'?'block':'none';document.getElementById('registerForm').style.display=t==='register'?'block':'none';document.getElementById('error').style.display='none'}
async function submitAuth(t){event.preventDefault();const e=document.getElementById(t==='login'?'loginEmail':'regEmail').value,p=document.getElementById(t==='login'?'loginPass':'regPass').value;try{const r=await fetch('/api/auth',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:t,email:e,password:p})});const d=await r.json();if(d.success){localStorage.setItem('api_key',d.api_key);localStorage.setItem('email',d.email);window.location.href='/app'}else{document.getElementById('error').textContent=d.error;document.getElementById('error').style.display='block'}}catch(er){document.getElementById('error').textContent='Ошибка соединения';document.getElementById('error').style.display='block'}return false}
function showResetPw(){document.getElementById('resetModal').style.display='flex'}
function closeResetPw(){document.getElementById('resetModal').style.display='none'}
async function doResetPw(){const e=document.getElementById('resetEmail').value,m=document.getElementById('resetMsg');if(!e){m.textContent='Введите email';m.style.color='#dc2626';return}try{const r=await fetch('/api/reset-password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:e})});const d=await r.json();m.textContent=d.message||d.error;m.style.color=d.success?'#16a34a':'#dc2626'}catch(er){m.textContent='Ошибка соединения';m.style.color='#dc2626'}}

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
<a href="/pricing" style="color:var(--ink-soft);text-decoration:none;font-size:11px;border:1px solid var(--border);padding:3px 10px;border-radius:12px;white-space:nowrap;transition:all 0.2s" onmouseover="this.style.borderColor='var(--ink)';this.style.color='var(--ink)'" onmouseout="this.style.borderColor='var(--border)';this.style.color='var(--ink-soft)'">Тарифы</a>
<button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Сменить тему">☀️</button>
<button class="logout" onclick="document.getElementById('pwModal').style.display='flex'" title="Настройки аккаунта">⚙️</button>
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

<div class="footer">AI-Automator &copy; 2026 &middot; ИНН: 526320301575 &middot; Самозанятый Маширов С.Д. &middot; <a href="/legal" style="color:inherit;text-decoration:underline">Публичная оферта</a></div>
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

function closePwModal(){document.getElementById('pwModal').style.display='none'}
async function changePw(){const o=document.getElementById('oldPw').value,n=document.getElementById('newPw').value,c=document.getElementById('confirmPw').value,m=document.getElementById('pwMsg');if(!o||!n||!c){m.textContent='Заполните все поля';m.style.color='#dc2626';return}if(n!==c){m.textContent='Пароли не совпадают';m.style.color='#dc2626';return}if(n.length<6){m.textContent='Минимум 6 символов';m.style.color='#dc2626';return}try{const r=await fetch('/api/change-password',{method:'POST',headers:{'Content-Type':'application/json','X-API-Key':API_KEY},body:JSON.stringify({old_password:o,new_password:n})});const d=await r.json();if(d.success){m.textContent='Пароль изменён!';m.style.color='#16a34a';document.getElementById('oldPw').value='';document.getElementById('newPw').value='';document.getElementById('confirmPw').value=''}else{m.textContent=d.error||'Ошибка';m.style.color='#dc2626'}}catch(e){m.textContent='Ошибка соединения';m.style.color='#dc2626'}}

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
<div id="pwModal" style="display:none;position:fixed;inset:0;z-index:200;background:rgba(0,0,0,0.5);align-items:center;justify-content:center" onclick="if(event.target===this)closePwModal()">
<div style="background:var(--bg);border-radius:16px;padding:32px;max-width:380px;width:90%;box-shadow:0 20px 60px rgba(0,0,0,0.2)">
<h3 style="margin-bottom:20px;font-size:18px">Смена пароля</h3>
<div style="margin-bottom:12px"><label style="display:block;font-size:12px;color:var(--ink-soft);margin-bottom:4px">Текущий пароль</label><input type="password" id="oldPw" style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:8px;font-size:14px;background:transparent;color:var(--ink)"></div>
<div style="margin-bottom:12px"><label style="display:block;font-size:12px;color:var(--ink-soft);margin-bottom:4px">Новый пароль</label><input type="password" id="newPw" style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:8px;font-size:14px;background:transparent;color:var(--ink)"></div>
<div style="margin-bottom:16px"><label style="display:block;font-size:12px;color:var(--ink-soft);margin-bottom:4px">Повторите пароль</label><input type="password" id="confirmPw" style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:8px;font-size:14px;background:transparent;color:var(--ink)"></div>
<div id="pwMsg" style="font-size:13px;margin-bottom:12px"></div>
<div style="display:flex;gap:8px"><button onclick="changePw()" style="flex:1;padding:10px;background:var(--ink);color:var(--bg);border:none;border-radius:8px;font-size:14px;cursor:pointer;font-family:inherit">Сохранить</button><button onclick="closePwModal()" style="padding:10px 16px;background:transparent;border:1px solid var(--border);border-radius:8px;font-size:14px;cursor:pointer;color:var(--ink);font-family:inherit">Отмена</button></div>
</div>
</div>
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


LEGAL_HTML = r"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Реквизиты и оферта — AI-Automator</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Noto+Serif+SC:wght@400;500;600&display=swap');
:root{--bg:#fcfaf8;--ink:#26251e;--ink-soft:#504f49;--border:#979696;--card:#fff;--card-border:rgba(0,0,0,0.06)}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--ink)}
.container{max-width:800px;margin:0 auto;padding:40px 20px}
h1{font-family:'Noto Serif SC',serif;font-size:28px;margin-bottom:24px}
h2{font-size:18px;margin:28px 0 12px;font-weight:600}
p,li{line-height:1.8;font-size:14px;color:var(--ink-soft);margin-bottom:12px}
table{width:100%;border-collapse:collapse;margin:16px 0}
td{padding:10px 16px;border-bottom:1px solid var(--card-border);font-size:14px}
td:first-child{color:var(--ink-soft);width:220px}
ol,ul{padding-left:20px;margin:8px 0}
li{margin-bottom:8px}
.back{display:inline-block;margin-top:24px;color:var(--ink-soft);text-decoration:none;font-size:14px}
.back:hover{color:var(--ink)}
.highlight{background:rgba(102,126,234,0.08);border:1px solid rgba(102,126,234,0.2);border-radius:8px;padding:16px;margin:16px 0}
</style>
</head>
<body>
<div class="container">
<h1>Публичная оферта и реквизиты</h1>

<h2>1. Исполнитель</h2>
<table>
<tr><td>Статус</td><td>Самозанятый (НПД)</td></tr>
<tr><td>ФИО</td><td>Маширов Сергей Дмитриевич</td></tr>
<tr><td>ИНН</td><td>526320301575</td></tr>
<tr><td>Телефон</td><td>+7 (930) 719-80-05</td></tr>
<tr><td>Email</td><td>serega.mashirov@gmail.com</td></tr>
</table>

<h2>2. Предмет оферты</h2>
<p>Исполнитель предоставляет Пользователю доступ к сервису «AI-Automator» — платформе автоматизации бизнес-процессов на базе искусственного интеллекта, включая обработку документов, чат с AI, генерацию контента и другие функции.</p>
<p>Настоящий документ является публичной офертой в соответствии со ст. 437 ГК РФ.</p>

<h2>3. Тарифы и стоимость</h2>
<table>
<tr><td>Бесплатный</td><td>0 ₽ — 10 запросов в день</td></tr>
<tr><td>Про</td><td>1 490 ₽/мес — 500 запросов в день</td></tr>
<tr><td>Бизнес</td><td>4 990 ₽/мес — безлимит запросов</td></tr>
</table>

<h2>4. Порядок оплаты</h2>
<p>Оплата производится онлайн через платёжную систему Robokassa. Доступные способы оплаты: банковские карты (Visa, MasterCard, МИР), СБП (Система Быстрых Платежей), ЮMoney.</p>
<p>После успешной оплаты доступ к выбранному тарифу предоставляется автоматически и активируется немедленно.</p>

<h2>5. Порядок и условия возврата денежных средств</h2>

<div class="highlight">
<p><strong>Возврат денежных средств осуществляется в соответствии с Законом РФ «О защите прав потребителей» и правилами дистанционной продажи товаров (работ, услуг).</strong></p>
</div>

<h3>5.1. Условия возврата</h3>
<ol>
<li>Пользователь вправе отказаться от оплаченной услуги в течение <strong>14 календарных дней</strong> с момента оплаты (ст. 26.1 Закона «О защите прав потребителей»).</li>
<li>Возврат производится при условии, что услуга не была использована или использована частично.</li>
<li>Если услуга была использована (совершён хотя бы один запрос), возврат осуществляется пропорционально неиспользованному периоду.</li>
<li>Возврат денежных средств осуществляется на тот же платёжный инструмент, которым была произведена оплата.</li>
</ol>

<h3>5.2. Перечень документов для оформления возврата</h3>
<ul>
<li>Заявление на возврат (в свободной форме или по шаблону).</li>
<li>Чек или подтверждение оплаты (скриншот, выписка из банка).</li>
<li>Копия документа, удостоверяющего личность (при необходимости).</li>
</ul>

<h3>5.3. Порядок действий покупателя</h3>
<ol>
<li>Направить заявление на возврат на адрес электронной почты: <strong>serega.mashirov@gmail.com</strong></li>
<li>Указать: ФИО, email, дату и сумму оплаты, причину возврата.</li>
<li>Приложить чек/подтверждение оплаты.</li>
<li>Дождаться ответа от Исполнителя.</li>
</ol>

<h3>5.4. Сроки рассмотрения и выплат</h3>
<ul>
<li>Срок рассмотрения заявления: <strong>не более 3 рабочих дней</strong> с момента получения.</li>
<li>Срок возврата денежных средств: <strong>не более 10 рабочих дней</strong> с момента принятия решения о возврате (ст. 22 Закона «О защите прав потребителей»).</li>
<li>Возврат осуществляется на банковскую карту или электронный кошелёк, указанный Пользователем.</li>
</ul>

<h3>5.5. Основания для отказа в возврате</h3>
<ul>
<li>Обращение после истечения 14 календарных дней с момента оплаты (если услуга была использована).</li>
<li>Отсутствие подтверждения оплаты.</li>
<li>Использование всех оплаченных запросов в рамках тарифа.</li>
</ul>

<h2>6. Персональные данные</h2>
<p>Исполнитель обязуется не передавать персональные данные Пользователя третьим лицам. Обработка данных осуществляется в соответствии с Федеральным законом №152-ФЗ «О персональных данных».</p>

<h2>7. Контакты</h2>
<p>По вопросам оплаты, возврата и технической поддержки обращайтесь:</p>
<ul>
<li>Email: <strong>serega.mashirov@gmail.com</strong></li>
<li>Телефон: <strong>+7 (930) 719-80-05</strong></li>
</ul>

<a href="/pricing" class="back">← Вернуться к тарифам</a>
</div>
</body>
</html>"""

PRICING_HTML = r"""<!DOCTYPE html>
<!-- v2 -->
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Тарифы — AI-Automator</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Noto+Serif+SC:wght@400;500;600&display=swap');
:root{--bg:#fcfaf8;--ink:#26251e;--ink-soft:#504f49;--border:#979696;--card:#fff;--card-border:rgba(0,0,0,0.06)}
[data-theme="dark"]{--bg:#0a0a0f;--ink:#e8e6e3;--ink-soft:#9a9890;--border:#2a2a30;--card:#121218;--card-border:rgba(255,255,255,0.06)}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--ink);min-height:100vh}

.topbar{display:flex;justify-content:space-between;align-items:center;padding:0 32px;height:65px;border-bottom:1px solid var(--card-border)}
.topbar .logo{font-family:'Noto Serif SC',serif;font-size:18px;font-weight:600;color:var(--ink);text-decoration:none}
.topbar .back{color:var(--ink-soft);text-decoration:none;font-size:14px;transition:color 0.2s}
.topbar .back:hover{color:var(--ink)}

.main{max-width:900px;margin:0 auto;padding:40px 20px 60px}
h1{text-align:center;font-family:'Noto Serif SC',serif;font-size:36px;font-weight:600;margin-bottom:8px}
.subtitle{text-align:center;color:var(--ink-soft);font-size:16px;margin-bottom:48px}

.plans{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}
.plan-card{background:var(--card);border:1px solid var(--card-border);border-radius:16px;padding:32px 24px;text-align:center;transition:all 0.3s;position:relative}
.plan-card:hover{transform:translateY(-4px);box-shadow:0 8px 30px rgba(0,0,0,0.08)}
.plan-card.popular{border-color:var(--ink)}
.plan-card.popular::before{content:'ПОПУЛЯРНЫЙ';position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:var(--ink);color:var(--bg);padding:4px 16px;border-radius:20px;font-size:11px;font-weight:700;letter-spacing:0.5px}
.plan-name{font-size:14px;font-weight:600;color:var(--ink-soft);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}
.plan-price{font-size:42px;font-weight:800;color:var(--ink);margin-bottom:4px}
.plan-price span{font-size:16px;font-weight:400;color:var(--ink-soft)}
.plan-period{font-size:13px;color:var(--ink-soft);margin-bottom:24px}
.plan-features{list-style:none;margin-bottom:28px;text-align:left}
.plan-features li{padding:8px 0;font-size:14px;color:var(--ink-soft);border-bottom:1px solid var(--card-border);display:flex;align-items:center;gap:8px}
.plan-features li:last-child{border:none}
.plan-features li::before{content:'✓';color:var(--ink);font-weight:700}
.buy-btn{display:block;width:100%;padding:14px;border:1px solid var(--ink);border-radius:46px;background:transparent;color:var(--ink);font-size:15px;font-weight:500;cursor:pointer;transition:all 0.2s;font-family:inherit}
.buy-btn:hover{background:var(--ink);color:var(--bg)}
.buy-btn.primary{background:var(--ink);color:var(--bg)}
.buy-btn.primary:hover{opacity:0.85}

.custom-section{margin-top:48px;text-align:center}
.custom-section h2{font-size:24px;margin-bottom:8px}
.custom-section .subtitle{color:var(--ink-soft);margin-bottom:32px}
.custom-card{background:var(--card);border:1px solid var(--card-border);border-radius:16px;padding:40px 32px;max-width:480px;margin:0 auto}
.custom-card .slider-row{display:flex;align-items:center;gap:16px;margin-bottom:24px}
.custom-card input[type=range]{flex:1;height:6px;-webkit-appearance:none;background:var(--card-border);border-radius:3px;outline:none}
.custom-card input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:24px;height:24px;border-radius:50%;background:var(--ink);cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,0.2)}
.custom-card .val{font-size:20px;font-weight:700;min-width:80px;text-align:right}
.custom-card .divider{color:var(--ink-soft);margin:16px 0;font-size:13px}
.custom-card .input-row{display:flex;gap:12px;align-items:center;justify-content:center;margin-bottom:24px}
.custom-card .input-row label{font-size:14px;color:var(--ink-soft)}
.custom-card .input-row input[type=number]{width:140px;padding:12px 16px;border:1px solid var(--card-border);border-radius:12px;font-size:18px;font-weight:600;text-align:center;background:var(--bg);color:var(--ink);font-family:inherit}
.custom-card .input-row input[type=number]:focus{outline:none;border-color:var(--ink)}
.custom-card .price-display{font-size:36px;font-weight:800;margin-bottom:8px}
.custom-card .price-display span{font-size:14px;font-weight:400;color:var(--ink-soft)}
.custom-card .per-req{font-size:13px;color:var(--ink-soft);margin-bottom:24px}

.footer{margin-top:60px;padding:30px 0;border-top:1px solid var(--card-border);text-align:center;color:var(--ink-soft);font-size:12px}

@media(max-width:640px){.plans{grid-template-columns:1fr;max-width:360px;margin:0 auto}h1{font-size:28px}.topbar{padding:0 16px}}
</style>
</head>
<body>
<div class="topbar">
<a href="/app" class="logo">AI-Automator</a>
<a href="/app" class="back">← Назад</a>
</div>

<div class="main">
<h1>Выберите тариф</h1>
<p class="subtitle">Оплатите картой, СБП или ЮMoney через Яндекс.Кассу</p>

<div class="plans">
<div class="plan-card">
<div class="plan-name">Бесплатный</div>
<div class="plan-price">0 ₽</div>
<div class="plan-period">навсегда</div>
<ul class="plan-features">
<li>10 запросов в день</li>
<li>Все 16 функций</li>
<li>Загрузка файлов</li>
<li>Чат с AI</li>
</ul>
<button class="buy-btn" onclick="window.location.href='/app'">Текущий план</button>
</div>

<div class="plan-card popular">
<div class="plan-name">Про</div>
<div class="plan-price">1 490 ₽<span>/мес</span></div>
<div class="plan-period">≈ 50 ₽ в день</div>
<ul class="plan-features">
<li>500 запросов в день</li>
<li>Все 16 функций</li>
<li>Приоритетная обработка</li>
<li>Загрузка файлов</li>
<li>Чат с AI без лимитов</li>
</ul>
<button class="buy-btn primary" onclick="buy('pro')">Оплатить 1 490 ₽</button>
</div>

<div class="plan-card">
<div class="plan-name">Бизнес</div>
<div class="plan-price">4 990 ₽<span>/мес</span></div>
<div class="plan-period">≈ 166 ₽ в день</div>
<ul class="plan-features">
<li>Безлимит запросов</li>
<li>Все 16 функций</li>
<li>Приоритетная обработка</li>
<li>API доступ</li>
<li>Персональная поддержка</li>
</ul>
<button class="buy-btn" onclick="buy('business')">Оплатить 4 990 ₽</button>
</div>
</div>

<div class="custom-section">
<h2>Свой тариф</h2>
<p class="subtitle">Выберите количество запросов или введите сумму</p>
<div class="custom-card">
<div class="slider-row">
<input type="range" id="reqSlider" min="10" max="1000" value="100" step="10">
<div class="val" id="reqVal">100</div>
</div>
<div class="divider">— или —</div>
<div class="input-row">
<label>Сумма:</label>
<input type="number" id="sumInput" min="50" max="50000" value="300" step="10">
<label>₽</label>
</div>
<div class="price-display" id="priceDisplay">300 ₽</div>
<div class="per-req" id="perReq">≈ 3 ₽ за запрос</div>
<button class="buy-btn primary" onclick="buyCustom()">Оплатить</button>
</div>
</div>

</div>

<div class="footer">AI-Automator &copy; 2026 &middot; ИНН: 526320301575 &middot; Самозанятый Маширов С.Д. &middot; <a href="/legal" style="color:inherit;text-decoration:underline">Публичная оферта</a></div>

<script>
const PRICE_PER_REQ=5;
const slider=document.getElementById('reqSlider');
const reqVal=document.getElementById('reqVal');
const sumInput=document.getElementById('sumInput');
const priceDisplay=document.getElementById('priceDisplay');
const perReq=document.getElementById('perReq');

slider.addEventListener('input',function(){
const r=parseInt(this.value);
const s=r*PRICE_PER_REQ;
reqVal.textContent=r;
sumInput.value=s;
priceDisplay.textContent=s.toLocaleString('ru-RU')+' ₽';
perReq.textContent='≈ '+PRICE_PER_REQ+' ₽ за запрос';
});

sumInput.addEventListener('input',function(){
const s=Math.max(50,Math.min(50000,parseInt(this.value)||50));
const r=Math.round(s/PRICE_PER_REQ);
slider.value=Math.min(1000,Math.max(10,r));
reqVal.textContent=r;
priceDisplay.textContent=s.toLocaleString('ru-RU')+' ₽';
perReq.textContent='≈ '+PRICE_PER_REQ+' ₽ за запрос';
});

function buy(plan){const email=localStorage.getItem('email');if(!email){alert('Войдите в аккаунт для оплаты');window.location.href='/';return}fetch('/api/payment/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({plan:plan,email:email})}).then(r=>r.json()).then(d=>{if(d.confirmation_url){window.location.href=d.confirmation_url}else{alert(d.error||'Ошибка создания платежа')}}).catch(e=>alert('Ошибка: '+e.message))}

function buyCustom(){
const email=localStorage.getItem('email');
if(!email){alert('Войдите в аккаунт для оплаты');window.location.href='/';return}
const sum=parseInt(sumInput.value);
const reqs=Math.round(sum/PRICE_PER_REQ);
if(sum<50){alert('Минимальная сумма — 50 ₽');return}
fetch('/api/payment/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({plan:'custom',email:email,amount:sum,requests:reqs})}).then(r=>r.json()).then(d=>{if(d.confirmation_url){window.location.href=d.confirmation_url}else{alert(d.error||'Ошибка создания платежа')}}).catch(e=>alert('Ошибка: '+e.message))
}
</script>
</body>
</html>"""


@app.route("/pricing")
def pricing_page():
    return render_template_string(PRICING_HTML)


@app.route("/legal")
def legal_page():
    return render_template_string(LEGAL_HTML)


@app.route("/api/payment/create", methods=["POST"])
def payment_create():
    data = request.json
    plan_id = data.get("plan")
    email = data.get("email", "").strip().lower()

    if not plan_id or not email:
        return jsonify({"error": "Не указан тариф или email"}), 400

    if plan_id == "custom":
        amount = data.get("amount", 0)
        requests = data.get("requests", 0)
        if amount < 50 or requests < 1:
            return jsonify({"error": "Минимальная сумма — 50 ₽"}), 400
        description = f"AI-Automator: {requests} запросов"
        shp_requests = str(requests)
    else:
        plan = PLANS.get(plan_id)
        if not plan:
            return jsonify({"error": "Неизвестный тариф"}), 400
        amount = plan["price"]
        requests = plan["requests_limit"]
        description = f"AI-Automator: {plan['name']}"
        shp_requests = str(requests)

    import time
    inv_id = str(int(time.time()))
    success_url = request.host_url + "payment/success"
    fail_url = request.host_url + "payment/fail"

    print(f"[PAYMENT CREATE] plan={plan_id}, email={email}, amount={amount}, requests={shp_requests}, inv_id={inv_id}")

    url = robokassa_init_url(
        inv_id=inv_id,
        amount=amount,
        description=description,
        email=email,
        success_url=success_url,
        fail_url=fail_url,
        requests=shp_requests,
    )

    if not url:
        return jsonify({"error": "Платёжная система не настроена. Обратитесь к администратору."}), 500

    return jsonify({"confirmation_url": url})


@app.route("/api/payment/result", methods=["POST"])
def payment_result():
    all_params = dict(request.form)
    inv_id = request.form.get("InvId", "")
    out_sum = request.form.get("OutSum", "")
    signature = request.form.get("SignatureValue", "")
    email = request.form.get("Shp_Email", "")
    requests = request.form.get("Shp_Requests", "")
    result = "FAIL" if not robokassa_verify(inv_id, out_sum, signature, email, requests) else "OK"
    from datetime import datetime
    payment_logs.append({"time": datetime.now().isoformat(), "inv_id": inv_id, "out_sum": out_sum, "email": email, "requests": requests, "result": result, "sig": signature, "all_params": all_params})
    if len(payment_logs) > 50:
        payment_logs.pop(0)
    print(f"[PAYMENT CALLBACK] inv_id={inv_id}, email={email}, requests={requests}, result={result}")

    if result == "OK":
        if email:
            if requests:
                set_plan(email, "custom", 30, int(requests), create_if_missing=True)
                print(f"[PAYMENT OK] Set plan for {email}: custom, {requests} requests")
            else:
                plan_id = request.form.get("Shp_plan", "")
                plan = PLANS.get(plan_id)
                if plan:
                    set_plan(email, plan_id, plan["days"], create_if_missing=True)
                    print(f"[PAYMENT OK] Set plan for {email}: {plan_id}")
        return "OK", 200

    print(f"[PAYMENT FAIL] Signature mismatch for inv_id={inv_id}, email={email}")
    return "INVALID SIGNATURE", 400

@app.route("/api/payment/logs")
def payment_logs_view():
    return jsonify(payment_logs[-20:])


@app.route("/payment/success", methods=["GET", "POST"])
def payment_success():
    inv_id = request.args.get("InvId", "")
    out_sum = request.args.get("OutSum", "")
    signature = request.args.get("SignatureValue", "")
    email = request.args.get("Shp_Email", "")
    requests_val = request.args.get("Shp_Requests", "")

    print(f"[PAYMENT SUCCESS PAGE] inv_id={inv_id}, email={email}, requests={requests_val}, sig={signature}")

    if inv_id and out_sum and signature and email:
        if robokassa_verify(inv_id, out_sum, signature, email, requests_val):
            if requests_val:
                set_plan(email, "custom", 30, int(requests_val), create_if_missing=True)
                print(f"[PAYMENT SUCCESS] Set plan for {email}: custom, {requests_val} requests")
            else:
                print(f"[PAYMENT SUCCESS] No requests param for {email}")
        else:
            print(f"[PAYMENT SUCCESS] Signature verification FAILED for {email}")
    else:
        print(f"[PAYMENT SUCCESS] Missing params: inv_id={bool(inv_id)}, out_sum={bool(out_sum)}, sig={bool(signature)}, email={bool(email)}")

    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Оплата прошла</title>
    <style>body{font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;background:#fcfaf8;color:#26251e;text-align:center}
    .box{max-width:400px;padding:40px}.check{font-size:64px;margin-bottom:16px}.btn{display:inline-block;margin-top:20px;padding:12px 32px;background:#26251e;color:#fafafa;text-decoration:none;border-radius:46px;font-size:15px}
    .note{font-size:13px;color:#666;margin-top:16px;padding:12px;background:#f5f5f5;border-radius:8px}</style></head>
    <body><div class="box"><div class="check">✅</div><h1>Оплата прошла!</h1><p>Ваш тариф активирован. Войдите в аккаунт.</p><div class="note">Если вы ранее не регистрировались — пароль по умолчанию: <b>paid123</b><br>Рекомендуется сменить пароль после входа.</div><a href="/app" class="btn">Перейти в приложение</a></div></body></html>"""


@app.route("/payment/fail")
def payment_fail():
    return """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Ошибка оплаты</title>
    <style>body{font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;background:#fcfaf8;color:#26251e;text-align:center}
    .box{max-width:400px;padding:40px}.btn{display:inline-block;margin-top:20px;padding:12px 32px;background:#26251e;color:#fafafa;text-decoration:none;border-radius:46px;font-size:15px}</style></head>
    <body><div class="box"><h1>Ошибка оплаты</h1><p>Попробуйте ещё раз.</p><a href="/pricing" class="btn">Вернуться к тарифам</a></div></body></html>"""



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

@app.route("/api/change-password", methods=["POST"])
@login_required
def api_change_password():
    data = request.json
    old_password = data.get("old_password", "")
    new_password = data.get("new_password", "")
    if not old_password or not new_password:
        return jsonify({"error": "Заполните оба поля"}), 400
    result = change_password(request.user["email"], old_password, new_password)
    return jsonify(result)

@app.route("/api/reset-password", methods=["POST"])
def api_reset_password():
    data = request.json
    email = data.get("email", "").strip().lower()
    if not email:
        return jsonify({"error": "Введите email"}), 400
    result = reset_password(email)
    return jsonify(result)

@app.route("/api/admin/plan", methods=["POST"])
def admin_set_plan():
    data = request.json
    if data.get("admin_key") != ADMIN_KEY: return jsonify({"error": "Неверный ключ"}), 403
    set_plan(data.get("email","").strip().lower(), data.get("plan","enterprise"), data.get("days",3650), data.get("requests",0))
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
