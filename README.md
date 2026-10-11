# 笔记提取 · note-extract

从用户提供的小红书图文笔记链接提取原文和全部配图，保存为 Markdown、Word 和图片目录。

## 核心流程

用户自己的 Chrome 打开链接 → 检查页面登录态 → 读取同一配置的小红书 Cookie → HTTP 提取正文和配图 → 导出及检查。

保留正文换行、表情、话题和图片顺序。Word 内嵌图片，Markdown 使用可迁移的相对路径。只归档指定笔记，不改写、不生成图片、不发布内容；Cookie 仅在内存使用。

## 在 Codex 中安装

可以直接告诉 Codex：

> 安装这个 skill：https://github.com/chasssswen/note-extract/tree/main/skills/note-extract

或使用本机已安装的 skill-installer：

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo chasssswen/note-extract --path skills/note-extract --method git
```

私有仓库需要使用有访问权限的 GitHub 账号和已有 Git 凭据。安装目标已有同名 skill 时，安装器会停止，先处理旧目录。安装后在下一轮对话调用 `$note-extract`，例如：

> 用笔记提取 skill，提取这个小红书链接，保存原文、全部配图、MD 和 Word。

## Python 依赖与命令

需要 Python 3.10+。在仓库根目录执行：

```bash
python3 -m pip install --target skills/note-extract/.deps \
  -r skills/note-extract/scripts/requirements.txt
python3 skills/note-extract/scripts/extract_note.py \
  --url '完整小红书分享链接' --out './output/笔记提取'
```

运行脚本前必须先在用户自己的 Chrome 中打开笔记并检查登录状态；脚本不会代做这两个步骤。默认 Chrome，可用 `--profile 'Profile 1'` 指定对应配置，或用 `--browser edge` 等选择浏览器。通过脚本指定配置的预检针对 macOS 的 Chrome/Edge/Brave；其他系统的读取能力取决于 browser-cookie3，不宣称均已实测。

多个笔记重复传 `--url`。`--cookie-stdin` 接受本次通过安全通道取得的 Cookie，不要把 Cookie 写入命令行参数、文件、仓库或日志。`--check-auth` 只检查 Cookie 读取结果，不能代替页面登录检查。

`--html 文件 --url 原链接` 可复验已保存的 HTML；配图仍会通过 CDN 下载，这个模式不证明登录或网页抓取成功。

## 交付目录

```text
output/笔记提取/标题_笔记ID/
├── 笔记.md
├── 笔记.docx
├── note.json
└── images/
    ├── 01.png、02.png……
    └── original/
```

脚本检查正文、图片解码、MD 引用、Word 嵌图数量和顺序。交付前还需渲染 Word 检查中文、表情和分页；没有渲染工具时明确记录视觉检查未完成。

当前完整支持图文笔记；视频笔记不作为完整提取成功交付。系统拒绝读取 Cookie、验证码或风控时说明真实原因并停止该篇。

## 仓库文件

- [SKILL.md](skills/note-extract/SKILL.md)：执行规则。
- [extract_note.py](skills/note-extract/scripts/extract_note.py)：协议提取与导出。
- [requirements.txt](skills/note-extract/scripts/requirements.txt)：第三方依赖。
- [protocol.md](skills/note-extract/references/protocol.md)：解析、登录及 Word 渲染细节。

仓库不包含登录信息、浏览器数据、真实笔记原稿、输出文件或本机运行时。页面结构和浏览器加密方式可能变化，成功与否以当次完整性检查为准。
