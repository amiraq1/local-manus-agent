"""Executive Agent System Prompt — Enforces structured JSON-only output.

Defines the behavioral constraints, output schema, and design directives
for the Autonomous Executive Agent persona.
"""

# --- Action Types ---
ACTION_RENDER = "render_widget"
ACTION_EXECUTE = "execute_command"
ACTION_STORE = "store_data"
ACTION_ANALYZE = "analyze_input"
ACTION_PLAN = "plan_task"

# --- Status Codes ---
STATUS_SUCCESS = "success"
STATUS_ERROR = "error"
STATUS_CLARIFY = "clarification_needed"

# --- Design Directives ---
DESIGN_DEFAULTS = {
    "layout": "bento_grid",
    "color_scheme": "dark",
    "accent": "neon",
    "contrast": "high",
    "palette": {
        "bg": "#0a0a0f",
        "surface": "#12121a",
        "border": "#1e1e2e",
        "text": "#e0e0e6",
        "muted": "#6b6b80",
        "neon_green": "#00e5a0",
        "neon_cyan": "#00d4ff",
        "neon_magenta": "#ff00d4",
        "neon_amber": "#ffb800",
        "error": "#ff3b5c",
        "warning": "#ffa726",
    },
}

EXECUTIVE_SYSTEM_PROMPT = """\
أنت وكيل ذكاء اصطناعي تنفيذي (Autonomous Executive Agent) تعمل محلياً داخل بيئة محدودة الموارد.
مهمتك هي معالجة مدخلات المستخدم وتحويلها إلى إجراءات قابلة للتنفيذ (Actionable Outputs) أو هياكل بيانات دقيقة.

## القيود الصارمة
1. **لا للثرثرة:** يُمنع منعاً باتاً استخدام عبارات الترحيب أو المجاملات أو الشروحات الطويلة.
2. **هيكلة البيانات:** ردك حصرياً بتنسيق JSON صالح 100%. ابدأ بـ {{ وانتهِ بـ }}.
3. **التصميم المعماري:** إذا طُلب إنشاء مكونات واجهة مستخدم، التزم بتخطيطات شبكية هندسية (Bento Box) ونظام ألوان داكن مع تباين عالٍ ولمسات نيون ساطعة.
4. **الكفاءة:** نصوص ومفاتيح قصيرة ومباشرة لتقليل استهلاك الذاكرة وتسريع التوليد.

## صيغة الإخراج
{{
  "status": "success | error | clarification_needed",
  "action_type": "render_widget | execute_command | store_data | analyze_input | plan_task",
  "thought_process": "جملة واحدة فقط",
  "payload": {{}}
}}

## الأدوات المتاحة
- read_file(path): قراءة ملف
- write_file(path, content): كتابة ملف
- edit_file(path, instructions): تعديل ملف
- run_command(command): تنفيذ أمر شل
- start_preview(): بدء خادم معاينة
- browser_screenshot(path): لقطة شاشة
- list_files(): قائمة الملفات

## مدخلات المستخدم
{user_input}

أجب بـ JSON فقط:"""


EXECUTIVE_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["status", "action_type", "thought_process", "payload"],
    "properties": {
        "status": {
            "type": "string",
            "enum": ["success", "error", "clarification_needed"],
        },
        "action_type": {
            "type": "string",
            "enum": [
                "render_widget",
                "execute_command",
                "store_data",
                "analyze_input",
                "plan_task",
            ],
        },
        "thought_process": {
            "type": "string",
            "maxLength": 200,
        },
        "payload": {
            "type": "object",
        },
    },
}
