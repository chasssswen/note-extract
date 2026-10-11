# 协议与维护

## 无 Cookie 验证

2026-10-11 使用 curl 进行无 Cookie 请求，忽略个人 curl 配置、显式清空 Cookie 请求头并保持 TLS 证书验证。完整分享链接成功返回目标笔记，正文771字、配图4张，全部配图无 Cookie 下载成功，MD引用与Word嵌图顺序校验通过。去掉分享参数的同一笔记链接返回 HTTP 200 首页壳页，没有目标正文。未在此次协议验证中执行 Word 逐页视觉检查。

这是单篇验证结果。是否可匿名提取取决于当次完整链接和站点响应，不将“全部笔记不用Cookie”作为普遍结论。当前普通认证模式仍使用用户自己的浏览器检查登录并读取同一配置的Cookie；用户明确选择无Cookie模式时按入口相应分支执行。

Python 默认请求若因本机 CA 配置产生 `CERTIFICATE_VERIFY_FAILED`，先区分证书配置与网站登录限制。可使用正常验证TLS的其他HTTP工具完成验证，不禁用证书验证。

## 普通认证模式

入口顺序是用户自己的 Chrome 打开笔记 → 检查该页面登录态 → 已登录后读取同一配置的 Cookie → HTTP 提取。浏览器步骤由当前浏览器工具完成，`extract_note.py` 不负责打开页面；`--check-auth` 只验证 Cookie 读取结果。Codex 内置浏览器、临时配置与用户 Chrome 是不同会话，不能互相代替登录证据。

页面请求是用户完整笔记 URL 的 GET；不存在必须额外调用的签名接口。保留 xsec_token，不伪造或计算隐藏签名。短链用无 Cookie 的 HTTPS GET 跟随站内重定向，得到笔记地址后再带 Cookie。

可通过已连接浏览器公开支持的 Cookie/请求头接口读取当前站点 Cookie，或采用 [browser-cookie3 官方实现](https://github.com/borisbabic/browser_cookie3) 读取已经检查过的同一 Chrome 配置。后者只调用指定浏览器与小红书域名过滤，不调用读取所有浏览器的 load()。其跨系统解密能力受浏览器版本和系统权限限制；出现 Permission denied / Operation not permitted，应报告系统拒绝读取，不尝试其他工具绕过。macOS Keychain 如有授权弹窗，留给用户处理。页面已登录但 Cookie 读取失败时保留两项实际结论，不把它写成用户未登录或未授权提取。

输出只保留目标笔记，不保存整个 `__INITIAL_STATE__`，避免夹带当前账号、推荐流或评论。CookieJar 正常遵守 Cookie 的域名和路径；重定向不转发手工 Cookie 标头。

部分已登录页面的其他状态对象含 `new Map([])`，整个 INITIAL_STATE 不能直接 JSON.parse。脚本只对目标 `noteDetailMap` 使用 JSON raw_decode，避免因无关状态语法而退化到丢失换行的 JSON-LD description。

Word 渲染：本机捆绑 LibreOffice 的默认字体配置可能遗漏系统中文字体，表现为中文空白而英文可见。使用任务 QA 目录内的独立 fontconfig 配置，以 `FONTCONFIG_FILE` 仅传给本次渲染进程；加入实际存在的 `~/Library/Fonts`、`/System/Library/Fonts` 和捆绑 LibreOffice 的字体目录，并将字体缓存放 QA 目录。不要改系统或运行时文件。正文用 Arial Unicode MS，保留系统 Emoji 回退；清除默认 Title 样式的段落边框。仍须逐页看最终 PNG，不能仅靠文本提取宣称排版通过。

历史验证中，无 Cookie 的 HTTP 200 页面可能只是首页壳页；只以目标笔记对象和正文图片的完整性判定成功。页面已登录但系统拒绝读取 Cookie 时，明确分别记录这两个状态。用户提供 Cookie 的成功提取不能当作 Chrome 自动读取已验证成功。
