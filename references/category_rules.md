# File Smart Sorter — 分类规则参考

## 分类体系说明

### 一级分类（17 类）

| 分类 | 说明 | 常见扩展名 |
|------|------|-----------|
| 文档 | 文本、办公文档 | .pdf, .docx, .xlsx, .pptx, .csv |
| 图片 | 图像文件 | .jpg, .png, .gif, .webp, .svg |
| 视频 | 视频文件 | .mp4, .mkv, .avi, .mov |
| 音频 | 音乐/音频 | .mp3, .wav, .flac, .aac |
| 压缩包 | 归档文件 | .zip, .rar, .7z, .tar.gz |
| 程序/安装包 | 可执行程序 | .exe, .msi, .dmg |
| 代码 | 源代码 | .py, .js, .ts, .java, .go |
| 数据/配置 | 数据和配置文件 | .json, .yaml, .sql, .db |
| 字体 | 字体文件 | .ttf, .otf, .woff |
| 电子书 | 电子书格式 | .epub, .mobi, .azw3 |
| 磁盘映像 | ISO 等镜像 | .iso, .img |
| 安卓应用 | 安卓安装包 | .apk, .xapk, .apks |
| 苹果应用 | iOS 安装包 | .ipa |

### 子分类

部分一级分类支持子分类，用于创建更细粒度的文件夹结构：

```
文档/
├── 办公文档/
│   ├── 报告/
│   ├── 简历/
│   └── 发票_收据/
├── 电子书/
图片/
├── 截图/
└── 照片/
代码/
├── 前端/
├── 后端/
└── 配置/
```

## 文件名模式匹配

除了扩展名，还支持通过文件名正则模式进行智能匹配：

| 模式 | 匹配示例 | 目标分类 |
|------|---------|---------|
| screenshot / 截屏 / Screen Shot | `Screenshot 2026-05-23.png` | 截图 |
| invoice / 发票 / receipt | `invoice-2026Q2.pdf` | 发票/收据 |
| resume / CV / 简历 | `张三_简历_v2.pdf` | 简历 |
| report / 报告 | `年度报告_2025.docx` | 报告 |
| backup / 备份 | `backup_db.sql` | 备份 |
| *.crash / *.dmp | `app_crash_20260523.dmp` | 崩溃日志 |

## AI 分类指南

### 何时触发 AI 分类？

以下情况的文件会交给 AI 判断：

1. **未知扩展名** — 扩展名不在任何已定义的分类中
2. **语义模糊** — 文件名本身需要理解语义才能判断
3. **特殊命名** — 用户自定义的、非标准的文件命名方式
4. **跨类别** — 文件可能属于多个分类（如 `data-export.pdf`）

### AI 分类的 Prompt 设计原则

- 提供**完整的上下文信息**：文件名、大小、修改时间、同目录其他文件
- 使用**低 temperature**（0.1）确保结果稳定可复现
- 要求返回**结构化 JSON**，便于解析
- 设置**置信度阈值**，低于 0.4 的结果标记为不确定

## 自定义分类

### 方法一：修改 categories.json

直接编辑 `assets/categories.json`，添加或修改分类：

```json
{
  "我的项目": [".myproj", ".custom"],
  "_subcategories": {
    "我的项目": {
      "数据导出": ["export", "dump"],
      "配置备份": ["config", "settings"]
    }
  }
}
```

### 方法二：在对话中指定

用户可以在使用 Skill 时临时指定分类偏好：

> "帮我整理桌面，把所有 .log 文件归到「日志」文件夹"

## API 配置说明

### OpenAI 官方

```bash
export OPENAI_API_KEY="sk-..."
# 默认 base URL: https://api.openai.com/v1
```

### DeepSeek

```bash
export DEEPSEEK_API_KEY="sk-..."
# 使用时: --api-base https://api.deepseek.com/v1 --model deepseek-chat
```

### Ollama（本地）

```bash
# 无需 API Key
--api-base http://localhost:11434/v1 --model qwen2.5:7b
```

### 其他兼容接口

任何支持 `/chat/completions` 接口的 LLM 服务均可使用。

## 安全机制

1. **Dry-run 默认模式** — `--scan` 只预览不操作
2. **敏感路径保护** — 不处理 Windows/System32 等
3. **批量确认** — 每批最多 20 个文件，逐批确认
4. **操作日志** — 自动记录到 `.file-sorter-logs/`
5. **回滚支持** — 日志中包含完整操作记录，可手动回滚
