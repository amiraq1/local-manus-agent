"""Template Registry - catalog of project templates."""

TEMPLATE_REGISTRY = {
    "html-landing-page": {
        "id": "html-landing-page",
        "name": "HTML Landing Page",
        "description": "Single-page responsive landing page with hero, features, and CTA.",
        "category": "web",
        "recommended_for": ["landing page", "portfolio", "product page"],
        "required_tools": ["write_file", "start_preview"],
        "variables": ["project_name", "description", "primary_color"],
        "files": {
            "index.html": """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{project_name}}</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <header class="hero">
    <h1>{{project_name}}</h1>
    <p>{{description}}</p>
    <a href="#features" class="btn">Learn More</a>
  </header>
  <section id="features" class="features">
    <div class="card"><h3>Fast</h3><p>Built for speed and performance.</p></div>
    <div class="card"><h3>Simple</h3><p>Easy to use and customize.</p></div>
    <div class="card"><h3>Reliable</h3><p>Tested and production-ready.</p></div>
  </section>
  <footer><p>&copy; 2024 {{project_name}}</p></footer>
</body>
</html>""",
            "style.css": """* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: system-ui, sans-serif; color: #1a1a2e; }
.hero { text-align: center; padding: 80px 20px; background: {{primary_color}}; color: white; }
.hero h1 { font-size: 2.5rem; margin-bottom: 16px; }
.hero p { font-size: 1.2rem; opacity: 0.9; margin-bottom: 24px; }
.btn { display: inline-block; padding: 12px 32px; background: white; color: {{primary_color}}; border-radius: 8px; text-decoration: none; font-weight: 600; }
.features { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 24px; padding: 60px 24px; max-width: 900px; margin: 0 auto; }
.card { padding: 24px; border: 1px solid #e0e0e0; border-radius: 12px; }
.card h3 { margin-bottom: 8px; color: {{primary_color}}; }
footer { text-align: center; padding: 24px; color: #666; }""",
        },
    },
    "react-vite-app": {
        "id": "react-vite-app",
        "name": "React + Vite App",
        "description": "Modern React app with Vite, ready for development.",
        "category": "web",
        "recommended_for": ["react app", "SPA", "web app", "dashboard"],
        "required_tools": ["write_file", "run_command"],
        "variables": ["project_name", "description"],
        "files": {
            "index.html": """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{{project_name}}</title></head>
<body><div id="root"></div><script type="module" src="/src/main.jsx"></script></body>
</html>""",
            "src/main.jsx": """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(<React.StrictMode><App /></React.StrictMode>);""",
            "src/App.jsx": """export default function App() {
  return (
    <div className="app">
      <h1>{{project_name}}</h1>
      <p>{{description}}</p>
    </div>
  );
}""",
            "src/index.css": """body { font-family: system-ui; margin: 0; padding: 40px; background: #fafafa; }
.app { max-width: 600px; margin: 0 auto; text-align: center; }
h1 { color: #333; }""",
            "package.json": """{
  "name": "{{project_name}}",
  "private": true,
  "version": "0.1.0",
  "scripts": { "dev": "vite", "build": "vite build" },
  "dependencies": { "react": "^18.3.0", "react-dom": "^18.3.0" },
  "devDependencies": { "@vitejs/plugin-react": "^4.3.0", "vite": "^5.4.0" }
}""",
            "vite.config.js": """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({ plugins: [react()] });""",
        },
    },
    "fastapi-api": {
        "id": "fastapi-api",
        "name": "FastAPI REST API",
        "description": "Python REST API with FastAPI, ready to extend.",
        "category": "backend",
        "recommended_for": ["API", "backend", "REST", "microservice"],
        "required_tools": ["write_file", "run_command"],
        "variables": ["project_name", "description"],
        "files": {
            "main.py": """\"\"\"{{project_name}} - {{description}}\"\"\"
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="{{project_name}}", description="{{description}}")

class Item(BaseModel):
    name: str
    description: str = ""

items: list[Item] = []

@app.get("/")
def root():
    return {"service": "{{project_name}}", "status": "running"}

@app.get("/items")
def list_items():
    return {"items": items}

@app.post("/items")
def create_item(item: Item):
    items.append(item)
    return {"created": item.name}
""",
            "requirements.txt": "fastapi>=0.115.0\nuvicorn>=0.30.0\n",
            "README.md": """# {{project_name}}

{{description}}

## Run

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```
""",
        },
    },
    "python-cli-tool": {
        "id": "python-cli-tool",
        "name": "Python CLI Tool",
        "description": "Command-line tool with argument parsing.",
        "category": "tool",
        "recommended_for": ["CLI", "command line", "script", "tool"],
        "required_tools": ["write_file"],
        "variables": ["project_name", "description"],
        "files": {
            "cli.py": """\"\"\"{{project_name}} - {{description}}\"\"\"
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="{{description}}")
    parser.add_argument("command", choices=["run", "status", "help"], help="Command to execute")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    if args.command == "run":
        print("Running {{project_name}}...")
    elif args.command == "status":
        print("Status: OK")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
""",
            "README.md": "# {{project_name}}\n\n{{description}}\n\n## Usage\n\n```bash\npython cli.py run\npython cli.py status\n```\n",
        },
    },
    "docs-site": {
        "id": "docs-site",
        "name": "Documentation Site",
        "description": "Simple documentation site with navigation.",
        "category": "docs",
        "recommended_for": ["documentation", "docs", "wiki", "guide"],
        "required_tools": ["write_file", "start_preview"],
        "variables": ["project_name", "description"],
        "files": {
            "index.html": """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{{project_name}} Docs</title><link rel="stylesheet" href="style.css"></head>
<body>
<nav><a href="index.html">Home</a> | <a href="getting-started.html">Getting Started</a> | <a href="api.html">API</a></nav>
<main><h1>{{project_name}}</h1><p>{{description}}</p><h2>Quick Start</h2><p>Get started with {{project_name}} in minutes.</p></main>
</body></html>""",
            "getting-started.html": """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Getting Started - {{project_name}}</title><link rel="stylesheet" href="style.css"></head>
<body><nav><a href="index.html">Home</a> | <a href="getting-started.html">Getting Started</a> | <a href="api.html">API</a></nav>
<main><h1>Getting Started</h1><p>Follow these steps to set up {{project_name}}.</p><ol><li>Install dependencies</li><li>Configure settings</li><li>Run the application</li></ol></main>
</body></html>""",
            "api.html": """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>API - {{project_name}}</title><link rel="stylesheet" href="style.css"></head>
<body><nav><a href="index.html">Home</a> | <a href="getting-started.html">Getting Started</a> | <a href="api.html">API</a></nav>
<main><h1>API Reference</h1><p>Complete API documentation for {{project_name}}.</p></main>
</body></html>""",
            "style.css": "body{font-family:system-ui;margin:0;padding:0;color:#333}nav{background:#f5f5f5;padding:12px 24px;border-bottom:1px solid #ddd}nav a{margin-right:16px;color:#0066cc;text-decoration:none}main{max-width:800px;margin:0 auto;padding:40px 24px}h1{color:#1a1a2e}",
        },
    },
    "nextjs-dashboard": {
        "id": "nextjs-dashboard",
        "name": "Next.js Dashboard",
        "description": "Admin dashboard with sidebar navigation.",
        "category": "web",
        "recommended_for": ["dashboard", "admin panel", "management"],
        "required_tools": ["write_file", "run_command"],
        "variables": ["project_name", "description", "primary_color"],
        "files": {
            "app/page.tsx": """export default function Home() {
  return (
    <div style={{padding: '40px'}}>
      <h1>{{project_name}}</h1>
      <p>{{description}}</p>
      <div style={{display:'grid',gridTemplateColumns:'repeat(3,1fr)',gap:'16px',marginTop:'24px'}}>
        <div style={{padding:'20px',border:'1px solid #e0e0e0',borderRadius:'8px'}}><h3>Users</h3><p style={{fontSize:'2rem'}}>1,234</p></div>
        <div style={{padding:'20px',border:'1px solid #e0e0e0',borderRadius:'8px'}}><h3>Revenue</h3><p style={{fontSize:'2rem'}}>$56K</p></div>
        <div style={{padding:'20px',border:'1px solid #e0e0e0',borderRadius:'8px'}}><h3>Orders</h3><p style={{fontSize:'2rem'}}>892</p></div>
      </div>
    </div>
  );
}""",
            "app/layout.tsx": """export default function Layout({ children }: { children: React.ReactNode }) {
  return (<html><body style={{margin:0,fontFamily:'system-ui'}}><div style={{display:'flex'}}><aside style={{width:'200px',background:'#1a1a2e',color:'white',minHeight:'100vh',padding:'20px'}}><h2 style={{fontSize:'1rem'}}>{{project_name}}</h2><nav style={{marginTop:'20px'}}><a href="/" style={{display:'block',color:'#aaa',marginBottom:'8px',textDecoration:'none'}}>Dashboard</a><a href="/users" style={{display:'block',color:'#aaa',marginBottom:'8px',textDecoration:'none'}}>Users</a><a href="/settings" style={{display:'block',color:'#aaa',textDecoration:'none'}}>Settings</a></nav></aside><main style={{flex:1}}>{children}</main></div></body></html>);
}""",
            "package.json": """{\"name\":\"{{project_name}}\",\"private\":true,\"scripts\":{\"dev\":\"next dev\",\"build\":\"next build\"},\"dependencies\":{\"next\":\"^14.2.0\",\"react\":\"^18.3.0\",\"react-dom\":\"^18.3.0\"}}""",
        },
    },
}


def list_templates(category: str = "") -> list[dict]:
    """List available templates."""
    results = []
    for tid, t in TEMPLATE_REGISTRY.items():
        if category and t["category"] != category:
            continue
        results.append({
            "id": t["id"],
            "name": t["name"],
            "description": t["description"],
            "category": t["category"],
            "variables": t["variables"],
            "file_count": len(t["files"]),
        })
    return results


def get_template(template_id: str) -> dict | None:
    """Get a template by ID."""
    return TEMPLATE_REGISTRY.get(template_id)
