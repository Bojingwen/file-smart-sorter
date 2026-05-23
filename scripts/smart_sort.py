#!/usr/bin/env python3
"""
File Smart Sorter — AI-Powered File Organizer (Core Engine)
扫描目录 → 规则预分类 → AI 智能分类 → 生成整理计划 → 预览/执行
支持任意文件夹，不限于下载目录。

Usage:
  python smart_sort.py --scan <dir>              # 扫描并分类（dry-run）
  python smart_sort.py --scan <dir> --ai          # 启用 AI 分类模糊文件
  python smart_sort.py --execute <plan.json>      # 执行整理计划
  python smart_sort.py --scan <dir> --output json # JSON 格式输出
"""

import argparse
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

# ============================================================
# Configuration
# ============================================================

SCRIPT_DIR = Path(__file__).parent.resolve()
ASSETS_DIR = SCRIPT_DIR.parent / "assets"
CATEGORIES_FILE = ASSETS_DIR / "categories.json"

# Default categories mapping (extension -> category)
DEFAULT_CATEGORIES = {
    "文档": [".pdf", ".docx", ".doc", ".txt", ".md", ".rtf", ".odt",
             ".xlsx", ".xls", ".csv", ".pptx", ".ppt", ".ods", "odp"],
    "图片": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp",
             ".ico", ".tiff", ".tif", ".heic", ".heif", ".avif", ".psd"],
    "视频": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm",
             ".m4v", ".3gp"],
    "音频": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma",
             ".opus"],
    "压缩包": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
               ".tar.gz", ".tar.bz2", ".tar.xz"],
    "程序/安装包": [".exe", ".msi", ".app", ".dmg", ".pkg", ".deb", ".rpm"],
    "安卓应用": [".apk", ".xapk", ".apks", ".aab", ".apkm"],
    "苹果应用": [".ipa"],
    "代码": [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp",
             ".h", ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt",
             ".scala", ".r", ".lua", ".sh", ".bat", ".ps1"],
    "数据/配置": [".json", ".xml", ".yaml", ".yml", ".toml", ".ini",
                  ".cfg", ".conf", ".env", ".sql", ".db", ".sqlite",
                  ".parquet", ".m3u", ".m3u8", ".winmd"],
    "字体": [".ttf", ".otf", ".woff", ".woff2", ".eot"],
    "电子书": [".epub", ".mobi", ".azw3", ".azw", ".fb2"],
    "磁盘映像": [".iso", ".img", ".vhd", ".vmdk"],
}

# Filename pattern rules (regex -> category)
FILENAME_PATTERNS = [
    (re.compile(r"(?i)screenshot|截屏|截图|屏幕截图|Screen Shot|"
                 r"Screen Capture|屏幕快照"), "截图"),
    (re.compile(r"(?i)invoice|发票|收据|receipt|bill"), "发票/收据"),
    (re.compile(r"(?i)resume|简历|CV|curriculum vitae|个人简历"), "简历"),
    (re.compile(r"(?i)report|报告|report_\d{4}|_report"), "报告"),
    (re.compile(r"(?i)backup|备份|bak|dump"), "备份"),
    (re.compile(r"(?i)\d{4}-\d{2}-\d{2}.*\.crash$|\.dmp$|core\.\d+"
                 r"|crash|崩溃|异常转储"), "崩溃日志"),
]

# Browser download suffixes to strip (random alphanumeric strings)
BROWSER_SUFFIX_PATTERN = re.compile(r"\s*\([a-zA-Z0-9]{6,}\)\.")
BROWSER_PREFIX_PATTERN = re.compile(r"^[a-zA-Z0-9]{8,12}[-_]?")

# Sensitive paths that should never be processed
SENSITIVE_PATHS = [
    "Windows", "Program Files", "Program Files (x86)",
    "System32", "AppData", "$Recycle.Bin", "System Volume Information",
]

# ============================================================
# File Scanner
# ============================================================

def scan_directory(directory: str) -> list[dict]:
    """Scan target directory and return file metadata list."""
    dir_path = Path(directory).resolve()

    if not dir_path.exists():
        print(f"[ERROR] 目录不存在: {directory}")
        sys.exit(1)

    if not dir_path.is_dir():
        print(f"[ERROR] 路径不是目录: {directory}")
        sys.exit(1)

    # Safety check
    for sensitive in SENSITIVE_PATHS:
        if sensitive in str(dir_path):
            print(f"[ERROR] 安全限制: 不处理系统敏感目录 ({sensitive})")
            sys.exit(1)

    files = []
    hidden_count = 0
    dir_count = 0

    try:
        for item in dir_path.iterdir():
            # Skip hidden files/folders
            if item.name.startswith("."):
                hidden_count += 1
                continue
            # Skip directories (only process files)
            if item.is_dir():
                dir_count += 1
                continue
            if item.is_file():
                stat = item.stat()
                files.append({
                    "name": item.name,
                    "path": str(item),
                    "extension": item.suffix.lower(),
                    "size_bytes": stat.st_size,
                    "size_human": _human_size(stat.st_size),
                    "modified": datetime.fromtimestamp(
                        stat.st_mtime
                    ).strftime("%Y-%m-%d %H:%M"),
                    "modified_timestamp": stat.st_mtime,
                })
    except PermissionError as e:
        print(f"[WARN] 权限不足，跳过部分文件: {e}")

    print(f"[SCAN] 扫描完成: {len(files)} 个文件, "
          f"{dir_count} 个文件夹, {hidden_count} 个隐藏项")
    return sorted(files, key=lambda x: x["modified_timestamp"], reverse=True)


def _human_size(size: int) -> str:
    """Convert bytes to human-readable size."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


# ============================================================
# Rule-Based Classifier
# ============================================================

def load_categories() -> dict:
    """Load custom categories from assets, fallback to defaults."""
    if CATEGORIES_FILE.exists():
        try:
            return json.loads(CATEGORIES_FILE.read_text("utf-8"))
        except (json.JSONDecodeError, IOError):
            pass
    return DEFAULT_CATEGORIES


def classify_by_rules(files: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Classify files using extension + filename pattern rules.
    Returns (rule_classified, need_ai_classification).
    """
    categories = load_categories()
    # Build reverse map: ext -> category
    ext_to_category = {}
    for cat, exts in categories.items():
        # Skip metadata keys
        if cat.startswith("_"):
            continue
        for ext in exts:
            ext_to_category[ext] = cat

    rule_classified = []
    need_ai = []

    for f in files:
        ext = f["extension"]
        name = f["name"]

        # 1. Try filename patterns first
        matched_pattern = False
        for pattern, cat in FILENAME_PATTERNS:
            if pattern.search(name):
                f["category"] = cat
                f["method"] = "pattern"
                f["confidence"] = 0.85
                rule_classified.append(f)
                matched_pattern = True
                break

        if matched_pattern:
            continue

        # 2. Try extension match
        if ext in ext_to_category:
            f["category"] = ext_to_category[ext]
            f["method"] = "extension"
            f["confidence"] = 0.95
            rule_classified.append(f)
            continue

        # 3. No rule matched — needs AI
        f["category"] = None
        f["method"] = None
        f["confidence"] = 0.0
        need_ai.append(f)

    print(f"[RULE] 规则分类: {len(rule_classified)} 个文件已分类, "
          f"{len(need_ai)} 个待 AI 判断")
    return rule_classified, need_ai


# ============================================================
# AI Classifier (OpenAI-Compatible API)
# ============================================================

def classify_with_ai(
    files: list[dict],
    api_key: str | None = None,
    api_base: str = "https://api.openai.com/v1",
    model: str = "gpt-4o-mini",
    batch_size: int = 20,
) -> list[dict]:
    """
    Classify ambiguous files using an OpenAI-compatible API.
    Supports: OpenAI, DeepSeek, Ollama, any compatible endpoint.
    """
    if not files:
        return []

    # Check for API key from env or param
    key = api_key or os.environ.get("OPENAI_API_KEY") or \
          os.environ.get("DEEPSEEK_API_KEY") or ""
    if not key:
        # If Ollama (local), no key needed
        if "localhost" in api_base or "127.0.0.1" in api_base:
            key = "ollama"
        else:
            print("[AI] 未设置 API Key。跳过 AI 分类，"
                  "这些文件将归入「其他」。")
            print("[AI] 提示: 设置环境变量 OPENAI_API_KEY 或 "
                  "使用参数 --api-key")
            for f in files:
                f["category"] = "其他"
                f["method"] = "fallback"
                f["confidence"] = 0.3
            return files

    categories = load_categories()
    category_list = list(categories.keys()) + ["其他"]

    classified = []
    total = len(files)

    # Process in batches
    for i in range(0, total, batch_size):
        batch = files[i : i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size

        # Build prompt with all files in batch
        file_descriptions = "\n".join(
            f"- {j+1}. {f['name']} "
            f"(扩展名:{f['extension']}, 大小:{f['size_human']}, "
            f"修改时间:{f['modified']})"
            for j, f in enumerate(batch)
        )

        system_prompt = (
            "你是一个文件分类专家。根据文件名、扩展名、大小和修改时间,"
            "将每个文件归入最合适的分类。\n\n"
            f"可用分类: {', '.join(category_list)}\n\n"
            '请以纯 JSON 数组格式返回，不要添加任何其他文字:\n'
            '[{"index": 文件序号, "category": "分类名", '
            '"subcategory": "子分类(可选)", '
            '"confidence": 0.0-1.0, '
            '"reasoning": "简短理由"}]\n\n'
            "规则:\n"
            "- 根据文件名语义判断内容类型\n"
            "- 如果文件名包含中文，优先理解中文含义\n"
            "- confidence > 0.7 表示高置信度\n"
            "- 无法确定时归入「其他」"
        )

        user_prompt = (
            f"请分类以下 {len(batch)} 个文件:\n\n{file_descriptions}\n\n"
            "返回 JSON 数组:"
        )

        result = _call_ai_api(system_prompt, user_prompt,
                              key, api_base, model)

        if result:
            try:
                ai_results = json.loads(result)
                for ai_r in ai_results:
                    idx = ai_r.get("index", 1) - 1
                    if 0 <= idx < len(batch):
                        batch[idx]["category"] = ai_r.get(
                            "category", "其他"
                        )
                        batch[idx]["subcategory"] = ai_r.get(
                            "subcategory", ""
                        )
                        batch[idx]["confidence"] = ai_r.get(
                            "confidence", 0.5
                        )
                        batch[idx]["method"] = "ai"
                        batch[idx]["ai_reasoning"] = ai_r.get(
                            "reasoning", ""
                        )
                        classified.append(batch[idx])
                        # If some weren't in AI response, add as fallback
                    for j, f in enumerate(batch):
                        if f not in classified:
                            f["category"] = "其他"
                            f["method"] = "ai_fallback"
                            f["confidence"] = 0.2
                            classified.append(f)
            except json.JSONDecodeError:
                print(f"[AI WARN] Batch {batch_num}/{total_batches}: "
                      "JSON 解析失败，使用默认分类")
                for f in batch:
                    f["category"] = "其他"
                    f["method"] = "ai_error"
                    f["confidence"] = 0.1
                    classified.append(f)
        else:
            # API failed entirely
            print(f"[AI ERROR] Batch {batch_num}/{total_batches}: "
                  "API 调用失败")
            for f in batch:
                f["category"] = "其他"
                f["method"] = "error"
                f["confidence"] = 0.0
                classified.append(f)

        print(f"[AI] Batch {batch_num}/{total_batches} 完成 "
              f"({min(i+batch_size, total)}/{total})")

    print(f"[AI] AI 分类完成: {len(classified)} 个文件已处理")
    return classified


def _call_ai_api(
    system_prompt: str,
    user_prompt: str,
    api_key: str,
    api_base: str,
    model: str,
) -> str | None:
    """Make an OpenAI-compatible chat completion API call."""
    url = f"{api_base.rstrip('/')}/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 2048,
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if api_key != "ollama":
        headers["Authorization"] = f"Bearer {api_key}"

    req = Request(url, data=payload, headers=headers, method="POST")

    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data.get("choices", [{}])[0].get(
                "message", {}
            ).get("content", "")
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("`")[1].split("```")[0]
            return content.strip()
    except URLError as e:
        print(f"[API ERROR] 连接失败: {e.reason}")
        return None
    except Exception as e:
        print(f"[API ERROR] {type(e).__name__}: {e}")
        return None


# ============================================================
# Plan Generator
# ============================================================

def generate_plan(
    all_files: list[dict],
    source_dir: str,
    organize_mode: str = "move",  # move | copy
) -> dict:
    """Generate organization plan with target paths."""
    plan = {
        "created_at": datetime.now().isoformat(),
        "source_dir": source_dir,
        "mode": organize_mode,
        "summary": {},
        "operations": [],
    }

    category_stats = {}

    for f in all_files:
        cat = f.get("category", "其他")
        subcat = f.get("subcategory", "")
        source_path = Path(f["path"])

        # Determine target folder name
        if subcat:
            target_folder = f"{cat}/{subcat}"
        else:
            target_folder = cat

        target_path = Path(source_dir) / target_folder / source_path.name

        # Stats
        category_stats[cat] = category_stats.get(cat, 0) + 1

        operation = {
            "source": f["path"],
            "target": str(target_path),
            "category": cat,
            "subcat": subcat,
            "method": f.get("method", "unknown"),
            "confidence": f.get("confidence", 0),
            "size": f.get("size_human", "?"),
            "operation_type": organize_mode,
        }
        plan["operations"].append(operation)

    plan["summary"] = {
        "total_files": len(all_files),
        "categories": category_stats,
        "target_folders": len(category_stats),
    }

    return plan


# ============================================================
# TUI Preview
# ============================================================

def display_preview(plan: dict) -> None:
    """Display a pretty preview table of the organization plan."""
    summary = plan["summary"]
    ops = plan["operations"]

    print("\n" + "=" * 72)
    print(f"  📁 File Smart Sorter — 整理计划预览")
    print("=" * 72)
    print(f"  源目录:   {plan['source_dir']}")
    print(f"  整理模式: {'移动' if plan['mode']=='move' else '复制'}")
    print(f"  文件总数: {summary['total_files']}")
    print(f"  目标文件夹: {summary['target_folders']} 个")
    print("-" * 72)

    # Category summary
    print("\n  📊 分类统计:")
    print("  " + "-" * 40)
    for cat, count in sorted(
        summary["categories"].items(), key=lambda x: -x[1]
    ):
        bar_len = min(count, 30)
        bar = "█" * bar_len
        print(f"    {cat:<14} │ {count:>4} 个 {bar}")
    print()

    # Operations detail (grouped by category)
    current_cat = None
    print("  📋 详细操作列表:")
    print("  " + "-" * 68)

    for op in ops:
        if op["category"] != current_cat:
            current_cat = op["category"]
            print(f"\n  [{current_cat}]")

        src_name = Path(op["source"]).name
        # Truncate long filenames
        if len(src_name) > 45:
            src_name = src_name[:42] + "..."

        conf_display = "🟢" if op["confidence"] >= 0.7 else \
                       ("🟡" if op["confidence"] >= 0.4 else "🔴")
        method_tag = {"extension": "[规则]",
                      "pattern": "[规则]",
                      "ai": "[AI]",
                      "fallback": "[默认]",
                      "error": "[错误]"}.get(op["method"], "[?]")

        target_rel = str(Path(op["target"]).relative_to(
            Path(plan["source_dir"])
        ))
        print(f"    {conf_display} {method_tag} {src_name:<46}")
        print(f"       → {target_rel}")

    print("\n" + "=" * 72)
    print(f"  💡 以上为预览。确认执行请使用 --execute <plan.json>")
    print("=" * 72 + "\n")


# ============================================================
# Executor
# ============================================================

def execute_plan(plan: dict, dry_run: bool = False) -> dict:
    """Execute the organization plan."""
    ops = plan["operations"]
    results = {
        "success": [],
        "failed": [],
        "skipped": [],
        "log_file": "",
    }

    mode_str = "移动" if plan["mode"] == "move" else "复制"

    if dry_run:
        print(f"\n[DRY-RUN] 模拟执行 ({mode_str}) — 不会实际操作文件")
        for op in ops:
            print(f"  [SIMULATE] {Path(op['source']).name} → "
                  f"{op['category']}/")
        results["log"] = f"Dry-run simulation at {datetime.now()}"
        return results

    # Create log entry
    log_dir = Path(plan["source_dir"]) / ".file-sorter-logs"
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"sort_log_{timestamp}.json"
    results["log_file"] = str(log_file)

    print(f"\n[EXECUTE] 开始{mode_str} {len(ops)} 个文件...")
    success_count = 0
    fail_count = 0

    for i, op in enumerate(ops, 1):
        src = Path(op["source"])
        tgt = Path(op["target"])

        # Ensure target directory exists
        tgt.parent.mkdir(parents=True, exist_ok=True)

        try:
            if plan["mode"] == "move":
                shutil.move(str(src), str(tgt))
            else:
                shutil.copy2(str(src), str(tgt))

            success_count += 1
            results["success"].append(op)
            print(f"  [{i}/{len(ops)}] ✅ {src.name} → "
                  f"{tgt.parent.relative_to(Path(plan['source_dir']))}/")
        except Exception as e:
            fail_count += 1
            op["error"] = str(e)
            results["failed"].append(op)
            print(f"  [{i}/{len(ops)}] ❌ {src.name} 失败: {e}")

        # Small delay between operations
        time.sleep(0.01)

    # Write log
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "plan_summary": plan["summary"],
        "results": {
            "total": len(ops),
            "success": success_count,
            "failed": fail_count,
            "success_files": [o["source"] for o in results["success"]],
            "failed_files": [
                {"file": o["source"], "error": o.get("error", "")}
                for o in results["failed"]
            ],
        },
    }
    log_file.write_text(json.dumps(log_data, ensure_ascii=False, indent=2),
                         encoding="utf-8")

    print(f"\n[COMPLETE] 完成! 成功: {success_count}, 失败: {fail_count}")
    print(f"[LOG] 操作日志: {log_file}")
    print(f"[UNDO] 如需回滚，查看日志中的成功文件列表")

    return results


# ============================================================
# Download Name Cleaner
# ============================================================

def clean_download_name(filename: str) -> str:
    """Remove random suffixes from filenames (e.g., browser download suffixes)."""
    cleaned = filename

    # Strip trailing random suffix like "(1a2b3c4)." before extension
    match = BROWSER_SUFFIX_PATTERN.search(cleaned)
    if match:
        cleaned = cleaned[:match.start()] + "."

    # Strip leading random prefix like "a1b2c3d4e5f6-"
    match = BROWSER_PREFIX_PATTERN.match(cleaned)
    if match:
        # Only strip if the remaining part looks like a real filename
        rest = cleaned[match.end():]
        if rest and (rest[0].isalpha() or rest[0] in "._"):
            cleaned = rest

    # Clean up double spaces/dots
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = re.sub(r"\.+", ".", cleaned)

    return cleaned


# ============================================================
# Output Formatters
# ============================================================

def output_json(all_files: list[dict], plan: dict) -> str:
    """Output full classification results as JSON."""
    output = {
        "files": all_files,
        "plan": plan,
        "generated_at": datetime.now().isoformat(),
    }
    return json.dumps(output, ensure_ascii=False, indent=2)


def output_simple_table(files: list[dict]) -> str:
    """Simple text table for quick overview."""
    lines = []
    lines.append(f"{'文件名':<35} {'分类':<10} {'方式':<10} {'置信度'}")
    lines.append("-" * 70)

    for f in files:
        name = f["name"][:33] + ".." if len(f["name"]) > 35 else f["name"]
        cat = f.get("category") or "?"
        method = f.get("method") or "?"
        conf = f"{f.get('confidence', 0):.0%}"

        lines.append(f"{name:<35} {cat:<10} {method:<10} {conf}")

    return "\n".join(lines)


# ============================================================
# Main Entry Point
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="File Smart Sorter — AI 文件智能整理器（支持任意文件夹）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --scan ~/Desktop               # 整理桌面
  %(prog)s --scan ~/Downloads --ai         # 整理下载文件夹 + AI 分类
  %(prog)s --scan ~/Documents --copy       # 整理文档目录（复制模式）
  %(prog)s --execute plan.json             # 执行整理计划
  %(prog)s --scan ~/Desktop --clean-names  # 清理文件名随机后缀
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scan", type=str,
                       help="扫描目标目录")
    group.add_argument("--execute", type=str,
                       help="执行已有的整理计划 JSON 文件")

    parser.add_argument("--ai", action="store_true",
                        help="启用 AI 分类（需要 API Key）")
    parser.add_argument("--api-key", type=str, default=None,
                        help="API Key（或设置 OPENAI_API_KEY 环境变量）")
    parser.add_argument("--api-base", type=str,
                        default=os.environ.get(
                            "OPENAI_BASE_URL",
                            "https://api.openai.com/v1",
                        ),
                        help="API 基础 URL（支持 Ollama: http://localhost:11434/v1）")
    parser.add_argument("--model", type=str, default="gpt-4o-mini",
                        help="使用的模型名称（默认: gpt-4o-mini）")
    parser.add_argument("--copy", action="store_true",
                        help="使用复制而非移动（默认移动）")
    parser.add_argument("--clean-names", action="store_true",
                        help="清理文件名中的随机后缀（如浏览器下载添加的）")
    parser.add_argument("--output", choices=["table", "json"],
                        default="table", help="输出格式（默认: table）")
    parser.add_argument("--output-file", type=str, default=None,
                        help="保存结果到文件")
    parser.add_argument("--yes", "-y", action="store_true",
                        help="跳过确认直接执行（慎用）")

    args = parser.parse_args()

    if args.scan:
        # === SCAN MODE ===
        target_dir = os.path.expanduser(os.path.expandvars(args.scan))

        print(f"\n{'='*50}")
        print("  🔍 File Smart Sorter")
        print(f"{'='*50}")
        print(f"  目标: {target_dir}")
        print(f"  模式: {'AI+规则' if args.ai else '仅规则'}")
        print(f"  操作: {'复制' if args.copy else '移动'}")
        print(f"{'='*50}\n")

        # Step 1: Scan
        files = scan_directory(target_dir)
        if not files:
            print("[INFO] 目录为空，无需整理。")
            return

        # Optional: Clean download names
        if args.clean_names:
            cleaned_count = 0
            for f in files:
                new_name = clean_download_name(f["name"])
                if new_name != f["name"]:
                    print(f"  [CLEAN] {f['name'][:50]} → {new_name[:50]}")
                    f["original_name"] = f["name"]
                    f["name"] = new_name
                    cleaned_count += 1
            print(f"[CLEAN] 清理了 {cleaned_count} 个文件名\n")

        # Step 2: Rule classification
        rule_files, ai_files = classify_by_rules(files)

        # Step 3: AI classification (optional)
        if args.ai and ai_files:
            ai_result = classify_with_ai(
                ai_files,
                api_key=args.api_key,
                api_base=args.api_base,
                model=args.model,
            )
            all_files = rule_files + ai_result
        else:
            # Assign default for unclassified
            for f in ai_files:
                f["category"] = "其他"
                f["method"] = "unclassified"
                f["confidence"] = 0.1
            all_files = rule_files + ai_files

        # Step 4: Generate plan
        plan = generate_plan(
            all_files, target_dir,
            organize_mode="copy" if args.copy else "move",
        )

        # Step 5: Output
        if args.output == "json":
            result = output_json(all_files, plan)
            if args.output_file:
                Path(args.output_file).write_text(result, encoding="utf-8")
                print(f"[OUTPUT] JSON 已保存到: {args.output_file}")
            else:
                print(result)
        else:
            display_preview(plan)

        # Save plan for later execution
        plan_file = Path(target_dir) / ".file-sorter-plan.json"
        plan_file.write_text(
            json.dumps(plan, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[PLAN] 整理计划已保存到: {plan_file}")

        # Auto-execute if confirmed
        if args.yes:
            print("\n[CONFIRM] 自动执行模式，立即运行...")
            execute_plan(plan)

    elif args.execute:
        # === EXECUTE MODE ===
        plan_path = Path(args.execute)
        if not plan_path.exists():
            print(f"[ERROR] 计划文件不存在: {args.execute}")
            sys.exit(1)

        plan = json.loads(plan_path.read_text("utf-8"))
        print(f"\n[LOAD] 加载整理计划: {args.execute}")
        print(f"  文件数: {plan['summary']['total_files']}")
        print(f"  模式: {plan['mode']}")

        confirm = args.yes or input(
            "\n⚠️  即将执行文件操作，是否继续？(y/N): "
        ).strip().lower() == "y"

        if confirm:
            execute_plan(plan)
        else:
            print("[CANCELLED] 已取消操作。")


if __name__ == "__main__":
    main()
