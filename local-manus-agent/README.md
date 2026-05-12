# Local Manus Agent v0.10.0

[![CI](https://github.com/amiraq1/local-manus-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/amiraq1/local-manus-agent/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/amiraq1/local-manus-agent)](https://github.com/amiraq1/local-manus-agent/releases)

وكيل ذكاء اصطناعي محلي يعمل بدون الاعتماد على API خارجي. يقوم بتحليل المهام، وضع خطط تنفيذ، إنشاء ملفات مع عرض diff، مراجعة الكود، إصلاح الأخطاء، تنفيذ الأوامر في Docker sandbox معزول، واختبار النتائج بمتصفح آلي.

## المميزات

- 🧠 وكيل ذكي: Plan → Act → Observe → Review → Fix → Final
- 🐳 **Docker Sandbox**: تنفيذ أوامر في بيئة معزولة وآمنة
- 📝 File Diff: عرض التغييرات قبل/بعد مع تمييز الأسطر
- 🔍 Code Review: مراجعة جودة الكود واكتشاف الأخطاء
- 🔧 Auto Fix: إصلاح تلقائي للأخطاء البسيطة
- 🌐 Browser Automation: فتح صفحات، screenshots، تحقق بصري
- 🔒 نظام أمان: Safe Mode و Autonomous Mode
- 🛡️ نظام موافقة: الأوامر والتغييرات تحتاج موافقة في Safe Mode
- 💾 SQLite: حفظ كامل للمحادثات والمهام والتغييرات

## التثبيت والتشغيل

```bash
# 1. Ollama
ollama pull qwen2.5-coder:7b && ollama serve

# 2. Backend
cd backend
pip install -r requirements.txt
playwright install chromium
uvicorn app.main:app --reload --port 8000

# 3. Frontend
cd frontend
npm install
npm run dev

# 4. Docker Sandbox (اختياري)
docker build -f backend/sandbox.Dockerfile -t local-manus-sandbox:latest backend

# افتح: http://localhost:3000
```

## Quick Start for Termux (Android)

```bash
pkg update && pkg install python nodejs git
git clone https://github.com/amiraq1/local-manus-agent
cd local-manus-agent
chmod +x setup-termux.sh start-termux.sh
./setup-termux.sh
./start-termux.sh
# افتح: http://127.0.0.1:3000
```

للـ LLM، استخدم Ollama على كمبيوتر:
```bash
export OLLAMA_BASE_URL=http://<pc-ip>:11434
```
```

## Docker Sandbox

### الهدف

بدل تنفيذ `run_command` مباشرة على جهازك، يتم تنفيذ الأوامر داخل Docker container معزول.

### بناء صورة Sandbox

```bash
docker build -f backend/sandbox.Dockerfile -t local-manus-sandbox:latest backend
```

### ما يحتويه الـ Sandbox

- Python 3
- Node.js 20 + npm
- Git, curl, jq, tree
- مستخدم غير root (UID 1000)
- مجلد `/workspace` فقط

### حدود الأمان

| الحد | القيمة |
|------|--------|
| Memory | 512MB (لا swap) |
| CPU | 1 core |
| PIDs | 256 max |
| Network | معطلة افتراضيًا |
| Capabilities | ALL dropped |
| Privileges | no-new-privileges |
| User | non-root (1000:1000) |
| Timeout | 30 ثانية لكل أمر |
| Docker socket | **ممنوع نهائيًا** |

### الفرق بين Local و Sandbox

| الميزة | Local | Sandbox |
|--------|-------|---------|
| العزل | لا عزل | container معزول |
| الأمان | safety.py فقط | safety.py + Docker isolation |
| الشبكة | متاحة | معطلة افتراضيًا |
| الملفات | وصول كامل | workspace فقط |
| المتطلبات | لا شيء | Docker مثبت |

### تفعيل/تعطيل

```python
# config.py
SANDBOX_ENABLED = True   # تفعيل
SANDBOX_ENABLED = False  # تعطيل (يعود للتنفيذ المحلي)
```

### تفعيل الشبكة

```python
SANDBOX_NETWORK_ENABLED = True  # السماح بالشبكة داخل sandbox
```

### بدون Docker

إذا لم يكن Docker مثبتًا:
- الأوامر تفشل مع رسالة واضحة
- يمكن تعطيل Sandbox بـ `SANDBOX_ENABLED=False`
- نظام الأمان (safety.py) يعمل دائمًا بغض النظر

## API Endpoints

### Sandbox
| Method | Endpoint | الوصف |
|--------|----------|-------|
| GET | `/api/sandbox/status` | حالة Sandbox الشاملة |
| POST | `/api/sandbox/reset` | إيقاف وحذف كل containers |
| GET | `/api/sandbox/tasks/{id}/status` | حالة container لمهمة |

### File Changes
| Method | Endpoint | الوصف |
|--------|----------|-------|
| GET | `/api/changes` | كل التغييرات |
| GET | `/api/tasks/{id}/changes` | تغييرات مهمة |
| POST | `/api/changes/{id}/accept` | قبول تغيير |
| POST | `/api/changes/{id}/reject` | رفض تغيير |

### Code Review
| Method | Endpoint | الوصف |
|--------|----------|-------|
| POST | `/api/review` | مراجعة ملف |
| POST | `/api/lint` | فحص syntax |
| POST | `/api/autofix` | إصلاح تلقائي |

### Browser
| Method | Endpoint | الوصف |
|--------|----------|-------|
| POST | `/api/browser/open` | فتح URL |
| POST | `/api/browser/screenshot` | screenshot |
| GET | `/api/browser/sessions` | الجلسات |

### أخرى
| Method | Endpoint | الوصف |
|--------|----------|-------|
| GET | `/api/health` | صحة الخادم |
| GET/POST | `/api/mode` | الوضع |
| GET | `/api/tasks` | المهام |
| WS | `/ws/agent` | WebSocket |

## قاعدة البيانات

| الجدول | الوصف |
|--------|-------|
| `tasks` | المهام |
| `messages` | الرسائل |
| `plan_steps` | خطوات الخطة |
| `tool_logs` | سجل الأدوات |
| `created_files` | الملفات المُنشأة |
| `pending_approvals` | موافقات الأوامر |
| `browser_logs` | سجل المتصفح |
| `file_changes` | تغييرات الملفات مع diff |

## الإعدادات (config.py)

```python
LLM_PROVIDER = "ollama"
EXECUTION_MODE = "safe"
BROWSER_ALLOW_EXTERNAL_URLS = False
SANDBOX_ENABLED = True
SANDBOX_IMAGE = "local-manus-sandbox:latest"
SANDBOX_MEMORY_LIMIT = "512m"
SANDBOX_CPU_LIMIT = 1
SANDBOX_COMMAND_TIMEOUT = 30
SANDBOX_NETWORK_ENABLED = False
```

## ملاحظة حول Preview

Preview server يعمل محليًا (ليس داخل sandbox) لأن:
- يحتاج port مفتوح للمتصفح
- الملفات موجودة في workspace المشترك
- Docker networking يضيف تعقيدًا غير ضروري للمعاينة

الأوامر الخطيرة فقط هي التي تُنفّذ في sandbox.

## خارطة التطوير

- [x] قاعدة بيانات SQLite
- [x] تاريخ المهام
- [x] نظام موافقة الأوامر
- [x] Safe / Autonomous Mode
- [x] Browser Automation
- [x] File Diff System
- [x] Code Review + Auto Fix
- [x] **Docker Sandbox**
- [ ] تكامل LiteRT-LM
- [ ] محرر كود مدمج
- [ ] دعم Git
- [ ] تصدير مشاريع كـ ZIP

## الترخيص

MIT
