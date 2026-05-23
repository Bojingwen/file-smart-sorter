<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green?logo=opensourceinitiative&logoColor=white" alt="License">
  <a href="#-演示视频"><img src="https://img.shields.io/badge/-🎬_演示视频-red?style=flat-square" alt="Demo"></a>
  <a href="skill/SKILL.md"><img src="https://img.shields.io/badge/-Skill_定义-blue?style=flat-square" alt="Skill"></a>
</p>

<h1 align="center">File Smart Sorter</h1>

<p align="center">
  <strong>用 AI 和规则引擎，让任意文件夹一键从混乱变得井井有条</strong>
</p>

<p align="center">
  <sub>零配置 · 零依赖 · 全中文 · 安全优先 · 开箱即用</sub>
</p>

<p align="center">
  <a href="#-快速开始">快速开始</a> &nbsp;·&nbsp;
  <a href="#-核心能力">核心能力</a> &nbsp;·&nbsp;
  <a href="#-效果预览">效果预览</a> &nbsp;·&nbsp;
  <a href="#-使用方式">使用方式</a> &nbsp;·&nbsp;
  <a href="#-工作原理">工作原理</a> &nbsp;·&nbsp;
  <a href="#skill-定义">Skill 定义</a>
</p>

---

## 演示视频

<a href="assets/file-smart-sorter-demo.mp4"><p align="center">🎥 点击播放完整演示视频（12MB）</p></a>

---

## 效果预览

### 整理前

```
Desktop/
├── 报告2026Q1_final(2).pdf
├── Screenshot_2025-12-01.png
├── invoice_20260115.pdf
├── com.app.example_v3.2.1.apk
├── main.user.js
├── 视频教程_第3集.mp4
├── 数据导出_2026.json
├── backup_db.sql
├── 张三_简历_最新版.docx
├── ... 还有 163 个文件混在一起 🤯
```

### 整理后

```
Desktop/
├── 文档/
│   ├── 报告/
│   ├── 简历/
│   ├── 发票_收据/
│   └── ...
├── 图片/
│   ├── 截图/
│   └── ...
├── 视频/          ← 30 个文件
├── 安卓应用/       ← 44 个 .apk
├── 程序_安装包/    ← 38 个
├── 压缩包/
├── 代码/
├── 音频/
├── 数据_配置/
├── 电子书/
├── 字体/
└── 磁盘映像/       ✨ 干净了
```

---

## 核心能力

| | |
|:--|:--|
| **规则优先，AI 增强** | 内置 126+ 扩展名 + 文件名模式匹配，覆盖 ~98% 文件无需 AI。剩余 ~2% 才调用 AI 判断。 |
| **适用任何文件夹** | 桌面、下载、文档、项目输出……哪里乱就整理哪里，不做目录假设。 |
| **安全第一** | 默认只预览不操作；敏感路径自动拦截；每次执行生成可回滚的操作日志。 |
| **多 AI 后端** | OpenAI / DeepSeek / Ollama / 任何 OpenAI 兼容接口，自由选择。 |
| **纯 Python 零依赖** | 不需要 `pip install` 任何东西，`python smart_sort.py` 直接跑。 |
| **全中文界面** | 所有输出和提示均为中文，对非技术用户同样友好。 |

### 识别范围一览（17 大类 + 智能子分类）

```
文档 │ 图片 │ 视频 │ 音频 │ 压缩包
程序/安装包 │ 安卓应用 │ 苹果应用 │ 代码 │ 数据/配置
字体 │ 电子书 │ 磁盘映像
──── 智能模式匹配 ────
截图 │ 发票/收据 │ 简历 │ 报告 │ 备份 │ 崩溃日志
```

---

## 使用方式

### 方式一：WorkBuddy Skill 对话触发（推荐）

直接说人话即可：

> 「帮我整理桌面」  
> 「把 Downloads 分分类」  
> 「这个文件夹太乱了，帮我归档一下」

Skill 自动完成：扫描 → 分类 → 可视化预览 → 等你确认 → 执行。

详细定义见 [SKILL.md](skill/SKILL.md)。

### 方式二：命令行调用

```bash
# 1️⃣  扫描预览（dry-run，不会动任何文件）
python skill/scripts/smart_sort.py --scan ~/Desktop

# 2️⃣  启用 AI 处理模糊文件（可选，需 API Key）
python skill/scripts/smart_sort.py --scan ~/Desktop --ai \
    --api-key $OPENAI_API_KEY --model gpt-4o-mini

# 3️⃣  复制模式（保留原文件不动）
python skill/scripts/smart_sort.py --scan ~/Desktop --copy

# 4️⃣  清理文件名随机后缀 + 归档
python skill/scripts/smart_sort.py --scan ~/Downloads --clean-names

# 5️⃣  执行已确认的计划
python skill/scripts/skill/smart_sort.py --execute ~/.file-sorter-plan.json
```

<details>
<summary><b>更多 AI 后端示例（点开查看）</b></summary>

```bash
# DeepSeek
python skill/scripts/smart_sort.py --scan ~/Desktop --ai \
    --api-base https://api.deepseek.com/v1 \
    --model deepseek-chat \
    --api-key $DEEPSEEK_API_KEY

# Ollama 本地部署（完全免费，无需 API Key）
python skill/scripts/smart_sort.py --scan ~/Desktop --ai \
    --api-base http://localhost:11434/v1 \
    --model qwen2.5:7b
```

</details>

---

## 工作原理

```
┌─────────────────────────────────────────────────┐
│                  输入：任意混乱的文件夹              │
└──────────────────────┬──────────────────────────┘
                       ▼
           ┌───────────────────────┐
           │  Step 1  文件扫描      │  排除隐藏项 / 系统文件
           │  提取元数据             │  文件名 · 扩展名 · 大小 · 时间
           └───────────┬───────────┘
                       ▼
     ┌─────────────────────────────────┐
     │  Step 2  规则分类引擎  (~98%)    │  ⚡ 零成本，无网络请求
     │                                 │
     │  · 扩展名精确匹配               │  .pdf→文档  .apk→安卓应用
     │  · 文件名语义匹配               │  Screenshot→截图  invoice→发票
     └──────────────┬──────────────────┘
                    ▼ 未命中
     ┌─────────────────────────────────┐
     │  Step 3  AI 分类  (~2%, 可选)   │  🤖 仅处理模糊文件
     │                                 │  OpenAI / DeepSeek / Ollama
     │  · 构造上下文 Prompt            │  返回分类 + 置信度
     │  · 结构化 JSON 输出             │  低 temperature 保证稳定
     └──────────────┬──────────────────┘
                    ▼
     ┌─────────────────────────────────┐
     │  Step 4  生成整理计划            │  JSON 格式，可复用
     │         [{源, 目标, 分类, 置信}]  │
     └──────────────┬──────────────────┘
                    ▼
     ┌─────────────────────────────────┐
     │  Step 5  TUI 预览 → 用户确认     │  🔒 必须手动确认才执行
     │         → 执行移动/复制          │  📋 同时写入操作日志（可回滚）
     └─────────────────────────────────┘
```

---

## 安全机制

本工具操作的是你的真实文件，安全是最高优先级。

| 安全层 | 具体措施 |
|:------:|----------|
| 默认不操作 | `--scan` 只做 dry-run 预览，绝不自动执行 |
| 显式确认 | 必须用户输入确认后才执行实际文件操作 |
| 路径防护 | 自动拦截 Windows / System32 / AppData 等敏感目录 |
| 操作日志 | 每次执行生成 `.file-sorter-logs/` JSON 日志，包含所有成功操作的源路径，支持手动回滚 |
| 权限感知 | 权限不足的文件自动跳过并记录警告，不中断流程 |
| 大量预警 | 文件数 > 200 时提前提示耗时，建议分批处理 |

---

## 项目结构

```
file-smart-sorter/
├── README.md                        # 你正在看这个
├── LICENSE                          # MIT
├── .gitignore
│
├── skill/                           # ═══ WorkBuddy Skill 核心 ═══
│   ├── SKILL.md                     #   Skill 定义与工作流规范
│   ├── scripts/
│   │   └── smart_sort.py            #   分类引擎 + CLI 入口（~800 行）
│   ├── references/
│   │   └── category_rules.md        #   分类规则详细参考
│   └── assets/
│       └── categories.json          #   可扩展的分类配置
│
└── assets/
    └── file-smart-sorter-demo.mp4   # 产品演示视频
```

**代码亮点：**
- 单脚本架构 — 一个 `.py` 文件包含全部功能，零外部依赖
- 插件化分类 — 通过 `categories.json` 自定义/扩展分类规则
- 双模式设计 — 规则引擎兜底 + AI 增强，有 Key 更强，没 Key 照样跑

---

## 贡献

Issue 和 Pull Request 都欢迎。

1. Fork → 2. 创建分支 (`git checkout -b feature/xxx`) → 3. Commit → 4. Push → 5. PR

---

<p align="center">
  <strong>MIT © 2026 <a href="https://github.com/Bojingwen">Jingwen</a></strong>
</p>

<p align="center">
  如果这个项目帮到了你，欢迎给个 ⭐
</p>
