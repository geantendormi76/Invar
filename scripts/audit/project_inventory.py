import json
import hashlib
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "tmp" / "INVAR_PLATFORM_STATE.json"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""

def analyze_python(path: Path) -> dict:
    result = {"file": str(path.relative_to(ROOT)), "functions": [], "classes": [], "imports": []}
    try:
        code = path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                result["functions"].append(node.name)
            elif isinstance(node, ast.ClassDef):
                result["classes"].append(node.name)
            elif isinstance(node, ast.Import):
                for n in node.names: result["imports"].append(n.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module: result["imports"].append(node.module)
    except Exception as e:
        result["error"] = str(e)
    return result

def scan():
    data = {"root": str(ROOT), "python": [], "javascript": [], "json_assets": [], "directories": []}
    for p in ROOT.rglob("*"):
        if p.is_dir() or ".venv" in p.parts or "__pycache__" in p.parts:
            continue
        rel = str(p.relative_to(ROOT))
        if p.suffix == ".py":
            item = analyze_python(p)
            item["sha256"] = sha256_file(p)
            data["python"].append(item)
        elif p.suffix in [".js", ".vue"]:
            data["javascript"].append({"file": rel, "size": p.stat().st_size, "sha256": sha256_file(p)})
        elif p.suffix == ".json":
            data["json_assets"].append({"file": rel, "size": p.stat().st_size})

    for d in ROOT.rglob("*"):
        if d.is_dir() and ".venv" not in d.parts and "__pycache__" not in d.parts:
            data["directories"].append(str(d.relative_to(ROOT)))
    return data

if __name__ == "__main__":
    print("==================================================")
    print(" 📦 正在生成 Invar 平台资产全量白盒状态清单...")
    print("==================================================")
    result = scan()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"  ├─ 🐍 结构化 Python 模块 : {len(result['python'])} 个")
    print(f"  ├─ 📜 资产前端/脚本文件  : {len(result['javascript'])} 个")
    print(f"  ├─ 📄 JSON 契约文件      : {len(result['json_assets'])} 个")
    print(f"  └─ 📁 工作区法定目录数  : {len(result['directories'])} 个")
    print(f"\n[✓] 资产状态清单已落盘至: {OUTPUT}")
