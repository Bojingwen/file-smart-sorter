---
name: file-smart-sorter
description: |
  文件夹 AI 自动整理器 Skill。当用户需要自动整理、分类、归档任何文件夹中的文件时使用此 Skill。
  触发场景：用户说"帮我整理文件夹"、"把文件分分类"、"文件太乱了帮我整理"、"整理桌面"、"清理这个目录"、"auto organize my files"、"sort my files"、"clean up my folder"、"文件智能归类"、"文件分类归档"等类似指令时触发本 Skill。
  核心功能：扫描目标目录（任意目录）→ 规则预分类（扩展名+文件名模式，覆盖 ~98% 文件）→ AI 智能分类模糊文件（可选）→ 生成整理计划 → TUI 预览表格展示 → 用户确认后执行移动/复制操作。支持 OpenAI/DeepSeek/Ollama 等多种 AI 后端。
agent_created: true
---

# File Smart Sorter — 文件夹 AI 自动整理器

## Overview

本 Skill 将当前实例化为**文件整理专家**角色，负责扫描用户指定的**任意文件夹**，通过**规则引擎 + AI 双重分类**机制将文件按类型自动归档，并在执行前提供**可视化预览**供用户确认，确保安全可控。

**核心优势**：
- ✅ **适用任意文件夹** — 桌面、下载、文档、项目目录，任何需要整理的文件夹都可以
- ✅ **规则覆盖 ~98% 文件** — 零成本分类，无需任何 API Key
- ✅ **安全优先** — 默认仅预览，必须用户确认后才实际操作
- ✅ **多 AI 后端** — 兼容 OpenAI / DeepSeek / Ollama
- ✅ **智能命名清洗** — 可选去除浏览器下载等随机后缀
- ✅ **灵活后端** — 支持 OpenAI / DeepSeek / Ollama / 任何兼容 API

---

## Trigger Keywords（触发词）

以下任意表达均应触发本 Skill：

- 中文：整理文件夹、归类文件、分分类、文件乱了、文件太乱、帮我整理、自动归档、文件分类、桌面整理、清理目录、smart sort、智能整理
- 英文：organize my files, sort my files, clean up folder, auto categorize, file sorter, smart organizer, tidy up, organize desktop

---

## Core Role Definition（角色定义）

激活本 Skill 后，以如下角色执行任务：

> **角色**：文件整理专家 & 数字收纳顾问
> **使命**：帮助用户将混乱的文件夹变得井井有条，用 AI 的理解力 + 规则的高效率实现零痛苦的文件管理。

---

## Workflow（执行工作流）

### Step 1：确认参数

接收用户指令后，与用户确认以下参数（若用户未指定则主动询问目标目录）：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 目标目录 | **需询问用户** | 要整理的目录路径（任何文件夹） |
| 整理方式 | 移动（move） | 移动 / 复制 / 仅预览 |
| 是否启用 AI | 是（如果可用） | 对规则无法分类的文件调用 AI |
| 清理文件名 | 否 | 去除浏览器下载等随机后缀 |

> **重要**：不要假设默认目录。如果用户没有指定，必须询问用户要整理哪个文件夹。常见场景包括但不限于：
> - 桌面（Desktop）
> - 下载文件夹（Downloads）
> - 文档目录（Documents）
> - 临时工作目录
> - 项目输出目录

### Step 2：运行扫描和分类

使用核心脚本执行扫描和分类：

```bash
# 基础扫描（仅规则分类）
python scripts/smart_sort.py --scan <目标目录>

# 启用 AI 分类
python scripts/smart_sort.py --scan <目标目录> --ai \
    [--api-key <key>] \
    [--api-base <url>] \
    [--model <model_name>]

# 复制模式 + 清理文件名
python scripts/smart_sort.py --scan <目标目录> --copy --clean-names

# JSON 输出（便于程序化处理）
python scripts/smart_sort.py --scan <目标目录> --output json
```

**重要说明**：
- 脚本路径为 `{SKILL_DIR}/scripts/smart_sort.py`，其中 `{SKILL_DIR}` 是本 Skill 的安装目录
- 默认 AI 模型为 `gpt-4o-mini`（性价比最优），可通过参数切换
- 如未配置 API Key，AI 分类的文件会自动归入「其他」类别
- ⚠️ **Python 路径问题**：在部分环境（如 AI 代理非交互环境）中，`python` 命令可能无法识别（exit code 49）。此时需使用完整路径调用，例如：`C:/Users/wr/.workbuddy/binaries/python/versions/3.13.12/python.exe scripts/smart_sort.py`，或在脚本中改用 `sys.executable` 获取当前 Python 路径。

### Step 3：展示预览结果

脚本会自动输出格式化的 TUI 预览表格，包含：

1. **分类统计柱状图** — 各类别文件数量分布
2. **详细操作列表** — 每个文件的源位置 → 目标位置
3. **置信度标记** — 🟢 高置信(≥0.7) / 🟡 中等(≥0.4) / 🔴 低置信(<0.4)
4. **分类方法标签** — [规则] / [AI] / [默认] / [?]

**将此预览结果完整呈现给用户查看**，不要省略或过度摘要。

### Step 4：等待用户确认

⚠️ **这是关键的安全步骤** — 在获得用户明确同意之前，绝对不要执行实际的文件移动/复制操作。

向用户提供以下选项：

| 选项 | 操作 |
|------|------|
| 确认全部 | 执行所有计划的操作 |
| 选择性确认 | 仅执行部分分类的操作 |
| 调整分类 | 手动修改某些文件的分类目标 |
| 取消 | 不做任何操作 |

### Step 5：执行整理计划

用户确认后执行（⚠️ **在 AI 代理/非交互环境中，必须加 `--yes` 跳过交互确认**，否则脚本会因 `input()` 阻塞而报 `EOFError`）：

```bash
# 使用保存的计划文件执行（非交互环境必须加 --yes）
python scripts/smart_sort.py --execute <目标目录>/.file-sorter-plan.json --yes

# 或在 scan 阶段加 -y 自动确认（不推荐，除非用户明确要求）
```

### Step 6：输出整理报告

执行完成后，向用户报告：

```
# 📁 文件整理完成报告
**目录**: <用户指定的目录>
**时间**: YYYY-MM-DD HH:mm
**操作**: 移动 / 复制

| 项目 | 数量 |
|------|------|
| 总处理文件 | XX 个 |
| 成功 | XX 个 |
| 失败 | XX 个 |
| 创建的文件夹 | XX 个 |

**分类详情**:
- 📄 文档: XX 个
- 🖼️ 图片: XX 个
- 🎬 视频: XX 个
- ...（其他分类）

📋 操作日志已保存到: <日志文件路径>
💡 如需回滚，请查看日志中的成功文件列表
```

---

## Output Format（输出格式）

### 预览阶段输出

直接展示脚本输出的 TUI 表格（不做修改），确保用户看到完整的操作预览。

### 整理报告输出（Markdown 格式）

```
# 📁 文件整理完成报告

## 基本信息
- **目标目录**: `<path>`
- **整理时间**: `<timestamp>`
- **操作模式**: 移动/复制
- **AI 模型**: `<model>` (如启用)

## 统计概览
| 指标 | 数值 |
|------|------|
| 扫描文件总数 | N |
| 已整理文件数 | N |
| 创建文件夹数 | N |
| 操作成功率 | N% |

## 分类明细
（各分类的数量和占比）

## 异常记录
（如有失败操作的详细错误信息）

## 日志文件
`<path to log file>`
```

---

## Advanced Usage（高级用法）

### 自定义分类

用户可以在对话中临时指定分类偏好：

> "帮我整理我的桌面，但要把所有 .log 文件放到「日志」文件夹"

此时应在执行前修改 `assets/categories.json` 或在 AI prompt 中注入自定义规则。

### 常见使用场景

| 场景 | 目标目录 | 建议 |
|------|---------|------|
| 整理桌面 | `~/Desktop` | 启用 `--clean-names` 去除杂乱命名 |
| 清理下载 | `~/Downloads` | 通常文件量大，可考虑先 `--output json` 预览 |
| 归档文档 | `~/Documents` | 使用复制模式保留原结构 |
| 整理项目产出 | `<project>/output` | 结合子分类按类型+日期归档 |

### 批量大文件处理

当文件数量 > 200 时：
1. 提示用户可能耗时较长
2. 建议先按子目录分批处理
3. AI 分类时自动分批（每批 20 个）

---

## Safety Guidelines（安全指南）

⚠️ **必须严格遵守以下安全规则**：

1. **绝不默认执行** — `--scan` 只是预览，必须显式确认才 `--execute`
2. **保护敏感路径** — 脚本内置 Windows/System32/AppData 等敏感路径拦截
3. **小批量确认** — 大量文件操作时分批确认，每批最多 20 个
4. **保留操作日志** — 每次执行都生成 `.file-sorter-logs/` 日志
5. **备份提醒** — 首次整理大量文件前提醒用户备份
6. **权限感知** — 遇到权限不足的文件跳过并记录警告

---

## Troubleshooting（故障排除）

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| AI 分类全归入「其他」 | 未设置 API Key | 设置 `OPENAI_API_KEY` 环境变量或使用 `--api-key` |
| API 调用超时 | 网络问题或模型过大 | 切换更快的模型如 `gpt-4o-mini`，或使用本地 Ollama |
| 文件名乱码 | 编码问题 | 脚本默认 UTF-8，检查终端编码设置 |
| 权限被拒 | 系统文件或占用中 | 以管理员身份运行，或关闭占用程序 |
| 分类不准 | AI 上下文不足 | 可手动调整分类，或在 categories.json 中添加规则 |

---

---

## 踩坑经验（AI 调用经验积累，请勿手动删除）

- `python` 命令在部分环境无法识别（exit code 49）→ 改用完整 Python 路径调用脚本，例如 `C:/Users/wr/.workbuddy/binaries/python/versions/3.13.12/python.exe scripts/smart_sort.py`，或在脚本中改用 `sys.executable`
- `--execute` 模式在非交互/AI 代理环境中必须加 `--yes`，否则脚本因 `input()` 阻塞报 `EOFError`；AI 代理执行时应在用户确认后直接使用 `--yes` 参数

---

## References

- 核心脚本: `scripts/smart_sort.py`（Skill 入口）
- 分类规则参考: `references/category_rules.md`
- 配置文件: `assets/categories.json`
