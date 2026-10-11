# 笔记提取 · note-extract

从用户提供的小红书图文笔记链接提取原文和全部配图，保存为 Markdown、Word 和图片目录。

## 核心流程

完整分享链接无 Cookie 请求 → 校验并导出正文与全部图片；需要认证时 → 用户自己的浏览器检查登录 → 同一配置 Cookie → 只重试失败笔记。

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

### 无 Cookie 是否可以提取

2026-10-11 实测：一篇笔记的**完整分享链接**无 Cookie 成功取得正文和全部4张图片，MD/Word正文及嵌图顺序检查通过；去掉分享参数的同一链接只返回首页壳页。这说明部分笔记可以无 Cookie 提取，不能保证所有链接都可以。

默认命令直接无 Cookie 请求，无需先登录或读取浏览器。保留完整分享参数；校验目标ID、正文及所有配图，成功即导出。匿名阶段需要认证时输出 `auth_required / AUTH_FALLBACK_REQUIRED`、退出码2，Agent再检查用户浏览器登录后进行认证重试。网络和证书错误不触发登录。流程见 [SKILL.md](skills/note-extract/SKILL.md)。

### 默认无 Cookie 提取

需要 Python 3.10+。在仓库根目录执行：

```bash
python3 -m pip install --target skills/note-extract/.deps \
  -r skills/note-extract/scripts/requirements.txt
python3 skills/note-extract/scripts/extract_note.py \
  --url '完整小红书分享链接' --out './output/笔记提取'
```

### 失败后的登录与 Cookie 回退

收到 `auth_required` 时，先在用户自己的 Chrome 打开该篇完整分享链接并确认登录；未登录则由用户在该页面登录。脚本不会打开浏览器或检查页面账号状态。

登录确认后，只对失败链接执行：

```bash
python3 skills/note-extract/scripts/extract_note.py \
  --authenticated --url '失败笔记的完整分享链接' --out './output/笔记提取'
```

认证阶段默认 Chrome，用 `--profile 'Profile 1'` 指定刚检查的配置，或用 `--browser edge` 等按用户选择。通过脚本指定配置的预检针对macOS的Chrome/Edge/Brave；其他系统读取能力取决于browser-cookie3，不宣称均已实测。

多个笔记重复传 `--url`，已有成功结果保留，只回退失败项。`--authenticated --cookie-stdin` 接受本次通过安全通道取得的Cookie，不额外读取本地浏览器；不要把Cookie写入命令行参数、文件、仓库或日志。`--check-auth`只检查Cookie读取结果，不能代替页面登录检查。退出码0为全部成功，1为一般失败，2为需要认证回退或认证不可用。

`--html 文件 --url 原链接`可复验已有HTML；配图仍通过CDN下载，不证明本次网页抓取或认证成功。无Cookie请求优先用系统curl，忽略个人配置、清空Cookie头并逐跳校验重定向；没有curl时使用Python HTTPS。Python使用系统信任并补充certifi根证书，始终验证证书；TLS错误与需要登录分别判断。

维护者可运行 `python3 -m unittest discover -s tests -v`，验证匿名优先、认证回退、混合批次与请求边界。回退控制测试使用模拟认证，不等同于实际浏览器登录测试。

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
