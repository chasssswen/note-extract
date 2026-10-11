# 协议与维护

## 默认匿名优先，认证按阶段回退

默认命令只对完整分享链接做无Cookie GET，解析目标笔记并下载全部配图。不读取浏览器Cookie，不先要求用户登录。

无目标正文、内容不完整、HTTP 401/403时，脚本输出 `auth_required`、原因及 `AUTH_FALLBACK_REQUIRED`，退出码2。Agent随后打开用户自己的浏览器，检查实际登录状态，已登录后使用 `--authenticated` 对失败项重试。认证重试不重复匿名请求；浏览器登录检查由Agent完成，脚本不能证明页面已登录。

`--authenticated`才读取指定浏览器/配置Cookie；`--cookie-stdin`使用当前输入，不额外探测本地浏览器。`--check-auth`是独立认证诊断模式，不在默认路径执行。认证读取只针对xiaohongshu.com，不使用读取全部浏览器的load()。

系统拒绝读取、数据库占用或解密失败与页面登录状态分别判断。保留已完成结果，不改变系统权限、不关闭浏览器、不绕过系统拒绝。Cookie只在内存中使用，不保存、不打印。新输入优先于旧Cookie。

## 请求与解析

保留xsec_token等原始分享参数，不伪造或计算隐藏签名。短链在匿名阶段无Cookie跟随站内HTTPS重定向。认证CookieJar按域名和路径发送，重定向不转发手工Cookie标头；CDN配图始终不带Cookie。

保留用户请求的目标ID，即便最终返回首页/登录壳页也不能误取其他笔记。目标noteDetailMap优先，JSON-LD Article备选。部分状态对象含new Map([])，仅JSON解码目标noteDetailMap，不执行网页JS。发布时间优先note.time；JSON-LD datePublished可能是加载时间。

HTTP 200不是成功：目标正文、图片列表、下载解码与MD/Word内容校验都必须成立。视频、不存在的笔记、输出错误等不进入登录回退。图片链接失效可刷新原笔记一次，仍按原ID和同一认证状态核对，不无限重试。

## TLS与依赖

匿名网页及CDN请求优先使用系统curl，`-q`忽略个人配置，显式清空Cookie头，不使用cookie文件；逐跳校验HTTPS和站点白名单，不把Cookie带到重定向。无curl时使用Python HTTPS；认证网页请求使用Python CookieJar。不同HTTP客户端可能返回不同页面，是否成功仍以目标内容校验为准。

Python使用系统信任并补充certifi根证书；不关闭TLS验证，不改全局证书配置。TLS_CERTIFICATE_ERROR、NETWORK_ERROR等按网络问题处理，不读取Cookie或要求登录。依赖只装到技能.deps。

## Word与交付

脚本将正文与按顺序转换的PNG内嵌Word，检查数量、顺序和文件完整性。逐页视觉检查使用现有Word渲染工具；没有工具就记录未检查，不能将结构验收等同于视觉验收。

中文字体空白时，在任务QA目录使用独立fontconfig，加入实际存在的系统、用户及渲染器字体目录，并只对本次渲染进程设置FONTCONFIG_FILE。不修改系统或运行时文件。保留Emoji回退，逐页看真实PNG。

## 已有验证与适用范围

2026-10-11：完整分享链接无Cookie取得正文771字符、4张配图；全部配图下载、MD引用与Word嵌图顺序校验通过。同笔记去掉分享参数后返回HTTP 200首页壳页。这个单篇结果不保证所有笔记均可匿名访问。

历史上手工Cookie提取成功不能当作Chrome自动读取成功。回退控制的自动化测试使用模拟认证；只有实际检查浏览器并使用当前账号成功提取，才记录本轮真实认证运行。
