#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
律师工作台 · 桌面入口生成器（骨架模板）

作用：在桌面生成一个「双击即开」的 .app —— 不弹终端窗口。
      双击后它自己判断服务在不在跑：在跑就打开网页，不在跑就先拉起来再打开。
      图标自动跟工作台页面同一套配色（品牌蓝）。

用法：
    1. 改下面【要改的三处】
    2. python3 桌面入口.py
    3. 自己 open 一次验证（脚本最后会打印验证命令）

依赖：Pillow（pip3 install pillow）；sips / iconutil / osacompile 是 macOS 自带。

author: 小台 (DeskCraft) · 陆凌燕（北京德恒（无锡）律师事务所）
"""

import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

# ───────────────────────── 要改的三处 ─────────────────────────

APP_NAME = "律师工作台"                      # ① 桌面图标的显示名
PORT = 8765                                  # ② 工作台服务端口
LABEL = "com.example.lawyerdesk"             # ③ 开机自启的 launchd 标签（没有就留空串）

# 图标配色：直接抄工作台页面 :root 里的品牌色，图标才和界面是一套
BRAND = (24, 95, 165)        # 主品牌色
BRAND2 = (12, 68, 124)       # 品牌深色（渐变终点）
BRAND_LIGHT = (46, 127, 208)  # 品牌亮色（渐变起点）
LINE_GREY = (185, 203, 224)  # 内容占位线

# ────────────────────────────────────────────────────────────

SIZE = 1024
SS = 2  # 超采样倍数：先画 2 倍大再缩回，边缘才不锯齿
S = SIZE * SS
HERE = Path(__file__).resolve().parent
DESKTOP = Path.home() / "Desktop"
APP = DESKTOP / f"{APP_NAME}.app"


def _p(v: float) -> int:
    """按超采样倍数换算坐标"""
    return int(round(v * SS))


def make_icon_png(out: Path) -> Path:
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))

    # ① 底：圆角方块 + 竖向渐变（圆角半径取边长的 22% 左右，贴近 macOS 观感）
    grad = Image.new("RGB", (1, S))
    for y in range(S):
        t = y / (S - 1)
        grad.putpixel(
            (0, y),
            tuple(int(round(BRAND_LIGHT[i] + (BRAND2[i] - BRAND_LIGHT[i]) * t)) for i in range(3)),
        )
    grad = grad.resize((S, S))
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=_p(228), fill=255)
    img.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(img)

    # ② 主体：白卡片（示意"一张排期表"）
    d.rounded_rectangle([_p(232), _p(293), _p(792), _p(731)], radius=_p(58), fill=(255, 255, 255, 255))

    # ③ 顶部三枚小圆点
    for cx in (372, 512, 652):
        d.ellipse([_p(cx - 22), _p(373), _p(cx + 22), _p(417)], fill=BRAND + (255,))

    # ④ 三条条目线：前两条灰，第三条品牌色（示意"今天这条"）
    d.rounded_rectangle([_p(300), _p(463), _p(724), _p(495)], radius=_p(16), fill=LINE_GREY + (255,))
    d.rounded_rectangle([_p(300), _p(541), _p(724), _p(573)], radius=_p(16), fill=LINE_GREY + (255,))
    d.rounded_rectangle([_p(300), _p(619), _p(596), _p(651)], radius=_p(16), fill=BRAND + (255,))

    img = img.resize((SIZE, SIZE), Image.LANCZOS)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    return out


def make_icns(png: Path, out: Path) -> Path:
    """sips 缩尺寸 → iconutil 打包"""
    iconset = Path("/tmp/_deskentry.iconset")
    if iconset.exists():
        shutil.rmtree(iconset)
    iconset.mkdir(parents=True)
    pairs = [
        (16, "icon_16x16.png"), (32, "icon_16x16@2x.png"),
        (32, "icon_32x32.png"), (64, "icon_32x32@2x.png"),
        (128, "icon_128x128.png"), (256, "icon_128x128@2x.png"),
        (256, "icon_256x256.png"), (512, "icon_256x256@2x.png"),
        (512, "icon_512x512.png"), (1024, "icon_512x512@2x.png"),
    ]
    for size, name in pairs:
        subprocess.run(["sips", "-z", str(size), str(size), str(png), "--out", str(iconset / name)],
                       check=True, capture_output=True)
    subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(out)], check=True, capture_output=True)
    shutil.rmtree(iconset, ignore_errors=True)
    return out


# 双击后的三步：探测 → 拉起来 → 打开
APPLESCRIPT = '''on run
	set base to "http://127.0.0.1:{port}/"
	set probe to base & "api/state"
	set alive to false

	-- ① 服务在跑吗？
	try
		do shell script "/usr/bin/curl -s -o /dev/null --noproxy '*' --max-time 1 " & quoted form of probe
		set alive to true
	end try

	-- ② 不在跑 → 先试 kickstart：服务还在 launchd 托管里时，这一条就够了
	set kicked to false
	if not alive and "{label}" is not "" then
		try
			do shell script "/bin/launchctl kickstart -k gui/$(/usr/bin/id -u)/{label}"
			set kicked to true
		end try

		-- ③ kickstart 失败 = 服务被停掉并从托管里摘出去了 → 重新载入
		--    ⚠️ 两条只走一条：bootstrap 本身就会启动最新代码，若再 kickstart
		--    会把刚起来的进程杀掉重启，白白多等一次冷启动
		if not kicked then
			try
				do shell script "/bin/launchctl bootstrap gui/$(/usr/bin/id -u) " & quoted form of (POSIX path of (path to home folder) & "Library/LaunchAgents/{label}.plist")
			end try
		end if

		repeat 24 times
			delay 0.5
			try
				do shell script "/usr/bin/curl -s -o /dev/null --noproxy '*' --max-time 1 " & quoted form of probe
				set alive to true
				exit repeat
			end try
		end repeat
	end if

	-- ③ 还不行 → 直接 load 兜底
	if not alive and "{label}" is not "" then
		try
			do shell script "/bin/launchctl load -w " & quoted form of (POSIX path of (path to home folder) & "Library/LaunchAgents/{label}.plist")
		end try
		repeat 24 times
			delay 0.5
			try
				do shell script "/usr/bin/curl -s -o /dev/null --noproxy '*' --max-time 1 " & quoted form of probe
				set alive to true
				exit repeat
			end try
		end repeat
	end if

	-- ④ 用默认浏览器打开
	try
		open location base
	on error
		do shell script "/usr/bin/open " & quoted form of base
	end try
end run
'''


def build_app(icns: Path) -> Path:
    if APP.exists():
        shutil.rmtree(APP)
    src = Path("/tmp/_deskentry.applescript")
    src.write_text(APPLESCRIPT.format(port=PORT, label=LABEL), encoding="utf-8")
    subprocess.run(["osacompile", "-o", str(APP), str(src)], check=True, capture_output=True)

    shutil.copy2(icns, APP / "Contents/Resources/applet.icns")

    info = APP / "Contents/Info.plist"
    for k, v in [
        ("CFBundleName", APP_NAME),
        ("CFBundleDisplayName", APP_NAME),
        ("CFBundleIdentifier", (LABEL + ".launcher") if LABEL else "com.example.deskentry.launcher"),
        ("CFBundleShortVersionString", "1.0"),
        ("CFBundleVersion", "1"),
        ("CFBundleIconFile", "applet"),
        ("LSApplicationCategoryType", "public.app-category.productivity"),
    ]:
        # 先试 Set（键已存在），失败再 Add（键不存在）—— 顺序不能反
        subprocess.run(["/usr/libexec/PlistBuddy", "-c", f"Set :{k} {v}", str(info)], capture_output=True)
        subprocess.run(["/usr/libexec/PlistBuddy", "-c", f"Add :{k} string {v}", str(info)], capture_output=True)

    # ⚠️ 改完 plist 必须重新签名，否则双击报"应用已损坏"
    subprocess.run(["codesign", "--force", "--deep", "--sign", "-", str(APP)], capture_output=True)
    subprocess.run(["touch", str(APP)])
    return APP


def main() -> int:
    png = make_icon_png(Path("/tmp/_deskentry.png"))
    print(f"✅ 图标源图：{png}")
    icns = make_icns(png, Path("/tmp/_deskentry.icns"))
    app = build_app(icns)
    print(f"✅ 桌面入口：{app}")
    print()
    print("下一步：自己双击验证一次（光看文件生成了不算数）")
    print(f"    open \"{app}\"")
    print(f"    xattr -l \"{app}\"      # 只看到 macl / provenance 就是正常的")
    return 0


if __name__ == "__main__":
    sys.exit(main())
