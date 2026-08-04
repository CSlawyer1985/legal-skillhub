#!/usr/bin/env python3
"""
APK静态分析脚本
功能：解包APK，提取权限声明、识别第三方SDK、提取内嵌隐私政策、应用基本信息
输出：结构化JSON报告

用法：
    python apk_analyzer.py --apk /path/to/app.apk --output /path/to/report.json
    python apk_analyzer.py --apk /path/to/app.apk  # 输出到stdout

依赖：
    - Python标准库（zipfile, xml.etree, re, json）— 无第三方依赖，开箱即用
    - SDK识别基于classes.dex字节级包名字符串匹配，无需androguard

能力边界（重要）：
    本脚本基于Python标准库的zipfile模块解包APK，采用正则匹配和字节搜索方式
    提取信息。APK内的AndroidManifest.xml为Android二进制XML格式（AXML），
    非纯文本XML，本脚本通过正则匹配字符串池提取权限和包名，而非专业AXML解析。

    已知局限：
    - 权限提取：正则匹配可能遗漏非标格式权限声明
    - SDK识别：仅能识别未混淆的主流SDK包名，混淆过的SDK会漏检
    - 包名/版本号：从二进制XML正则提取，可能不准确
    - 隐私政策：仅搜索assets/res中的文本文件，无法解析编译后资源

    如需更精确的分析，建议搭配以下工具（非脚本依赖，由审查人员自行安装）：
    - androguard（pip install androguard）：专业APK逆向框架，正确解析AXML
    - apktool（需Java）：反编译APK为可读XML
    - jadx（需Java）：dex反编译为Java源码，可查看SDK初始化时序
"""

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

# 第三方SDK包名特征库
SDK_SIGNATURES = {
    "微信OpenSDK": ["com.tencent.mm.opensdk", "com.tencent.mm.sdk"],
    "QQ分享SDK": ["com.tencent.connect", "com.tencent.tauth"],
    "支付宝SDK": ["com.alipay.sdk", "com.alipay.mobile"],
    "友盟统计SDK": ["com.umeng.analytics", "com.umeng.commons", "com.umeng.message"],
    "友盟分享SDK": ["com.umeng.socialize"],
    "极光推送SDK": ["cn.jiguang", "cn.jpush"],
    "极光分享SDK": ["cn.jsharesdk"],
    "个推SDK": ["com.getui", "com.igexin"],
    "百度定位SDK": ["com.baidu.location"],
    "百度地图SDK": ["com.baidu.mapapi", "com.baidu.mapsdk"],
    "百度统计SDK": ["com.baidu.mobstat"],
    "高德地图SDK": ["com.amap.api", "com.autonavi"],
    "科大讯飞SDK": ["com.iflytek", "com.iflymsc"],
    "华为HMS": ["com.huawei.hms", "com.huawei.hianalytics"],
    "小米推送SDK": ["com.xiaomi.mipush", "com.xiaomi.push"],
    "vivo推送SDK": ["com.vivo.push"],
    "OPPO推送SDK": ["com.heytap.mcs", "com.coloros.mcs", "com.meizu.cloud.pushsdk"],
    "魅族推送SDK": ["com.meizu.cloud.pushsdk"],
    "Bugly崩溃监控": ["com.tencent.bugly", "com.tencent.bugly.legu"],
    "阿里云SDK": ["com.aliyun", "com.alibaba.sdk", "com.taobao"],
    "七牛云SDK": ["com.qiniu", "com.qiniu.android"],
    "环信IM SDK": ["com.hyphenate", "com.easemob"],
    "融云IM SDK": ["io.rong.imkit", "io.rong.imlib"],
    "声网Agora SDK": ["io.agora.rtc", "io.agora.rtm"],
    "即构ZEGO SDK": ["im.zego", "com.zego"],
    "涂鸦智能SDK": ["com.tuya.smart", "com.tuya.android"],
    "Google Firebase": ["com.google.firebase"],
    "Google Play Services": ["com.google.android.gms"],
    "Flutter框架": ["io.flutter", "io.flutter.plugins"],
    "React Native框架": ["com.facebook.react", "com.swmansion"],
    "Unity引擎": ["com.unity3d", "com.unity"],
    "网易云信SDK": ["com.netease.nim", "com.netease.nimlib"],
    "ShareSDK分享": ["cn.sharesdk", "com.mob"],
    "穿山甲广告SDK": ["com.bytedance.sdk.openadsdk", "com.bytedance.sdk"],
    "优量汇广告SDK": ["com.qq.e.ads", "com.qq.e.comm"],
    "AdMob广告SDK": ["com.google.android.gms.ads"],
    "SMAATO广告": ["com.smaato.soma"],
    "京东SDK": ["com.jingdong", "com.jd"],
    "拼多多SDK": ["com.xunmeng"],
    "抖音SDK": ["com.bytedance.sdk.social"],
    "快手SDK": ["com.kwad", "com.kuaishou"],
    "微博SDK": ["com.sina.weibo.sdk", "com.sina.weibo"],
    "OneNET": ["com.chinamobile.mcloud"],
    "移动安全认证": ["com.cmic.sso"],
    "DCloud SDK": ["io.dcloud"],
    "Cordova框架": ["org.apache.cordova"],
    "Bugly热更新": ["com.tencent.bugly.beta"],
    "阿里热修复": ["com.taobao.sophix"],
    "微信支付SDK": ["com.tencent.mm.opensdk.constants"],
    "银联支付SDK": ["com.unionpay"],
    "招行支付SDK": ["com.cmbchina"],
}

# 常见敏感权限
SENSITIVE_PERMISSIONS = {
    "android.permission.ACCESS_FINE_LOCATION": "访问精准定位",
    "android.permission.ACCESS_COARSE_LOCATION": "访问粗略位置",
    "android.permission.ACCESS_BACKGROUND_LOCATION": "后台访问位置",
    "android.permission.CAMERA": "使用相机",
    "android.permission.RECORD_AUDIO": "录音",
    "android.permission.READ_CONTACTS": "读取通讯录",
    "android.permission.WRITE_CONTACTS": "编辑通讯录",
    "android.permission.READ_CALENDAR": "读取日历",
    "android.permission.WRITE_CALENDAR": "编辑日历",
    "android.permission.READ_CALL_LOG": "读取通话记录",
    "android.permission.WRITE_CALL_LOG": "编辑通话记录",
    "android.permission.READ_PHONE_STATE": "读取电话状态(IMEI/IMSI)",
    "android.permission.READ_PHONE_NUMBERS": "读取本机电话号码",
    "android.permission.CALL_PHONE": "拨打电话",
    "android.permission.ANSWER_PHONE_CALLS": "接听电话",
    "android.permission.READ_SMS": "读取短信",
    "android.permission.SEND_SMS": "发送短信",
    "android.permission.RECEIVE_SMS": "接收短信",
    "android.permission.READ_EXTERNAL_STORAGE": "读取外置存储",
    "android.permission.WRITE_EXTERNAL_STORAGE": "写入外置存储",
    "android.permission.MANAGE_EXTERNAL_STORAGE": "管理外置存储",
    "android.permission.BODY_SENSORS": "获取身体传感器信息",
    "android.permission.ACTIVITY_RECOGNITION": "活动识别",
    "android.permission.GET_ACCOUNTS": "获取应用账户",
    "android.permission.USE_BIOMETRIC": "使用生物识别",
    "android.permission.USE_FINGERPRINT": "使用指纹",
    "android.permission.SYSTEM_ALERT_WINDOW": "显示系统窗口",
    "android.permission.REQUEST_INSTALL_PACKAGES": "请求安装包",
    "android.permission.ACCESS_NETWORK_STATE": "获取网络状态",
    "android.permission.ACCESS_WIFI_STATE": "获取WiFi状态",
    "android.permission.CHANGE_WIFI_STATE": "改变WiFi状态",
    "android.permission.BLUETOOTH": "蓝牙",
    "android.permission.BLUETOOTH_ADMIN": "蓝牙管理",
    "android.permission.BLUETOOTH_SCAN": "蓝牙扫描",
    "android.permission.BLUETOOTH_CONNECT": "蓝牙连接",
    "android.permission.NFC": "NFC",
    "android.permission.VIBRATE": "振动",
    "android.permission.WAKE_LOCK": "唤醒锁",
    "android.permission.RECEIVE_BOOT_COMPLETED": "开机自启动",
    "android.permission.FOREGROUND_SERVICE": "前台服务",
    "android.permission.INTERNET": "网络访问",
}


def parse_android_manifest(manifest_path):
    """解析AndroidManifest.xml（apktool解码后的可读XML格式）"""
    permissions = []
    app_info = {}
    sdk_info = {}

    try:
        tree = ET.parse(manifest_path)
        root = tree.getroot()

        # 处理命名空间
        ns = {"android": "http://schemas.android.com/apk/res/android"}

        # 提取权限
        for perm in root.iter("uses-permission"):
            name = perm.get("{http://schemas.android.com/apk/res/android}name")
            if name:
                permissions.append(name)

        # 提取自定义权限
        for perm in root.iter("permission"):
            name = perm.get("{http://schemas.android.com/apk/res/android}name")
            if name and name not in permissions:
                permissions.append(name)

        # 提取应用信息
        app_elem = root.find("application")
        if app_elem is not None:
            app_info["app_name"] = app_elem.get("{http://schemas.android.com/apk/res/android}label", "")
            app_info["package_name"] = root.get("package", "")

        # 提取SDK版本信息
        uses_sdk = root.find("uses-sdk")
        if uses_sdk is not None:
            sdk_info["min_sdk_version"] = uses_sdk.get("{http://schemas.android.com/apk/res/android}minSdkVersion", "")
            sdk_info["target_sdk_version"] = uses_sdk.get("{http://schemas.android.com/apk/res/android}targetSdkVersion", "")
            sdk_info["max_sdk_version"] = uses_sdk.get("{http://schemas.android.com/apk/res/android}maxSdkVersion", "")

        # 提取version信息
        version_name = root.get("{http://schemas.android.com/apk/res/android}versionName", "")
        version_code = root.get("{http://schemas.android.com/apk/res/android}versionCode", "")
        app_info["version_name"] = version_name
        app_info["version_code"] = version_code

    except ET.ParseError:
        # 如果是二进制XML（未解码），尝试正则提取
        with open(manifest_path, "rb") as f:
            content = f.read()
            # 从二进制XML中提取权限名
            permissions = re.findall(rb'android\.permission\.[A-Z_]+', content)
            permissions = [p.decode("utf-8", errors="ignore") for p in permissions]

    return permissions, app_info, sdk_info


def extract_permissions_from_binary_apk(apk_path):
    """从未解码的二进制APK中提取权限（使用正则）"""
    permissions = []
    with zipfile.ZipFile(apk_path, "r") as zf:
        try:
            with zf.open("AndroidManifest.xml") as f:
                content = f.read()
                # 二进制XML中权限名以明文字符串形式存在
                perm_pattern = rb"(android\.permission\.[A-Z_]+|[a-z]+\.[a-z]+\.[A-Z_]+_PERMISSION)"
                permissions = list(set(re.findall(perm_pattern, content)))
                permissions = [p.decode("utf-8", errors="ignore") if isinstance(p, bytes) else p for p in permissions]
        except KeyError:
            pass
    return permissions


def identify_sdks(apk_path):
    """识别APK中包含的第三方SDK"""
    identified_sdks = []
    with zipfile.ZipFile(apk_path, "r") as zf:
        all_names = zf.namelist()
        # 搜索dex文件和lib中的包名特征
        dex_content = b""
        for name in all_names:
            if name.endswith(".dex"):
                try:
                    with zf.open(name) as f:
                        dex_content += f.read()
                except Exception:
                    pass

        # 在dex内容中搜索SDK包名特征
        for sdk_name, signatures in SDK_SIGNATURES.items():
            found = False
            for sig in signatures:
                sig_bytes = sig.encode("utf-8")
                if sig_bytes in dex_content:
                    found = True
                    break
            if found:
                identified_sdks.append(sdk_name)

        # 也检查lib目录下的.so文件名
        lib_files = [n for n in all_names if n.startswith("lib/") and n.endswith(".so")]
        so_names = [os.path.basename(n).replace("lib", "").replace(".so", "") for n in lib_files]

        # 基于so文件名补充识别
        so_to_sdk = {
            "jpush": "极光推送SDK",
            "jcore": "极光核心",
            "jsharesdk": "极光分享SDK",
            "lbs": "百度定位SDK",
            "BaiduMapSDK": "百度地图SDK",
            "amapv": "高德地图SDK",
            "AMap": "高德地图SDK",
            "umeng": "友盟SDK",
            "BUGLY": "Bugly崩溃监控",
            "weibosdkcore": "微博SDK",
            "tuSDK": "涂鸦智能SDK",
            "tuya": "涂鸦智能SDK",
            "zegofilter": "即构ZEGO SDK",
            "agora-rtc": "声网Agora SDK",
        }
        for so_name in so_names:
            for key, sdk_name in so_to_sdk.items():
                if key.lower() in so_name.lower() and sdk_name not in identified_sdks:
                    identified_sdks.append(sdk_name)

    return identified_sdks


def search_privacy_policy(apk_path):
    """搜索APK内嵌的隐私政策文本和链接"""
    policy_texts = []
    policy_links = []

    with zipfile.ZipFile(apk_path, "r") as zf:
        all_names = zf.namelist()

        # 搜索资源文件中的隐私政策文本
        for name in all_names:
            if name.startswith("assets/") or name.startswith("res/raw/") or name.startswith("res/"):
                if name.endswith((".txt", ".html", ".htm", ".json", ".xml")):
                    try:
                        with zf.open(name) as f:
                            content = f.read()
                            try:
                                text = content.decode("utf-8", errors="ignore")
                            except Exception:
                                continue

                            # 搜索隐私政策关键词
                            if any(kw in text for kw in ["隐私政策", "隐私权政策", "个人信息保护政策", "privacy policy", "PrivacyPolicy"]):
                                policy_texts.append({
                                    "file": name,
                                    "snippet": text[:500]  # 前500字符
                                })

                            # 搜索隐私政策URL链接
                            links = re.findall(r'https?://[^\s"\'<>]+(?:privacy|policy|yinsi|yinshi|gerenxinxi)[^\s"\'<>]*', text, re.IGNORECASE)
                            for link in links:
                                if link not in policy_links:
                                    policy_links.append(link)
                    except Exception:
                        continue

    return policy_texts, policy_links


def check_enhanced_tools():
    """检测是否安装了增强分析工具，返回可用工具列表"""
    available = []

    # 检测androguard
    try:
        import androguard  # noqa: F401
        available.append("androguard")
    except ImportError:
        pass

    # 检测aapt2
    if shutil.which("aapt2"):
        available.append("aapt2")

    # 检测apktool
    if shutil.which("apktool"):
        available.append("apktool")

    # 检测jadx
    if shutil.which("jadx"):
        available.append("jadx")

    return available


def print_capability_notice(enhanced_tools):
    """启动时打印能力边界告知"""

    print("=" * 64, file=sys.stderr)
    print("  APK静态分析 — 能力边界告知", file=sys.stderr)
    print("=" * 64, file=sys.stderr)
    print(file=sys.stderr)
    print("  本脚本基于Python标准库，零第三方依赖，开箱即用。", file=sys.stderr)
    print("  采用正则匹配+字节搜索方式提取信息，已知以下局限：", file=sys.stderr)
    print(file=sys.stderr)
    print("  - 权限提取：正则匹配二进制XML字符串池，非标格式可能遗漏", file=sys.stderr)
    print("  - SDK识别：仅识别未混淆的主流SDK包名，混淆SDK会漏检", file=sys.stderr)
    print("  - 包名/版本号：从二进制XML正则提取，可能不准确", file=sys.stderr)
    print("  - 隐私政策：仅搜索assets/res文本文件，无法解析编译后资源", file=sys.stderr)
    print(file=sys.stderr)

    if enhanced_tools:
        print(f"  检测到已安装增强工具: {', '.join(enhanced_tools)}", file=sys.stderr)
        print(file=sys.stderr)
        if "androguard" in enhanced_tools:
            print("  [androguard] 可用于精确解析AXML、反编译DEX提取完整类名", file=sys.stderr)
            print("               建议在脚本输出后用androguard交叉验证权限和SDK清单", file=sys.stderr)
        if "aapt2" in enhanced_tools:
            print("  [aapt2] 可用于精确提取targetSdkVersion和权限列表", file=sys.stderr)
            print("          命令: aapt2 dump permissions app.apk", file=sys.stderr)
        if "apktool" in enhanced_tools:
            print("  [apktool] 可用于反编译APK为可读XML，辅助人工审查", file=sys.stderr)
        if "jadx" in enhanced_tools:
            print("  [jadx] 可用于反编译dex为Java源码，查看SDK初始化时序", file=sys.stderr)
            print("         建议用jadx查看Application.onCreate()确认同意前是否初始化SDK", file=sys.stderr)
    else:
        print("  未检测到增强工具。如需更精确的分析，建议安装以下任一工具：", file=sys.stderr)
        print("    - androguard: pip install androguard", file=sys.stderr)
        print("    - apktool:    https://ibotpeaches.github.io/Apktool/", file=sys.stderr)
        print("    - jadx:       https://github.com/skylot/jadx", file=sys.stderr)
    print(file=sys.stderr)
    print("=" * 64, file=sys.stderr)
    print(file=sys.stderr)


def analyze_apk(apk_path):
    """分析APK文件，返回结构化报告"""
    if not os.path.exists(apk_path):
        return {"error": f"APK文件不存在: {apk_path}"}

    report = {
        "apk_path": apk_path,
        "analysis_type": "static",
        "file_size": os.path.getsize(apk_path),
    }

    try:
        with zipfile.ZipFile(apk_path, "r") as zf:
            report["file_count"] = len(zf.namelist())
            report["contains_manifest"] = "AndroidManifest.xml" in zf.namelist()
    except zipfile.BadZipFile:
        return {"error": "文件不是有效的APK(ZIP)格式"}

    # 1. 提取权限
    permissions = extract_permissions_from_binary_apk(apk_path)
    report["permissions"] = {
        "total_count": len(permissions),
        "all_permissions": sorted(permissions),
        "sensitive_permissions": [
            {"name": p, "description": SENSITIVE_PERMISSIONS.get(p, "未知权限")}
            for p in permissions if p in SENSITIVE_PERMISSIONS
        ],
        "sensitive_count": len([p for p in permissions if p in SENSITIVE_PERMISSIONS]),
    }

    # 2. 识别SDK
    identified_sdks = identify_sdks(apk_path)
    report["sdks"] = {
        "total_count": len(identified_sdks),
        "identified_sdks": identified_sdks,
    }

    # 3. 搜索隐私政策
    policy_texts, policy_links = search_privacy_policy(apk_path)
    report["privacy_policy"] = {
        "embedded_texts": policy_texts,
        "found_links": policy_links,
    }

    # 4. 提取应用基本信息（从二进制XML中）
    with zipfile.ZipFile(apk_path, "r") as zf:
        try:
            with zf.open("AndroidManifest.xml") as f:
                content = f.read()
                # 尝试从二进制XML提取包名
                # 包名通常在manifest标签的package属性中
                package_match = re.search(rb'[\x00-\xff]{0,50}([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+)', content)
                if package_match:
                    pkg = package_match.group(1).decode("utf-8", errors="ignore")
                    # 验证是否像包名
                    if re.match(r'^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$', pkg):
                        report["app_info"] = {"package_name": pkg}
        except KeyError:
            pass

    # 5. targetSdkVersion检查（合规关注点）
    # 从二进制XML中较难提取，标记为需手动确认
    report["compliance_warnings"] = []
    report["compliance_warnings"].append({
        "warning": "targetSdkVersion需手动确认（使用aapt2 dump badging检查），<23可能导致捆绑授权违规",
        "check_method": "aapt2 dump badging app.apk | grep targetSdkVersion"
    })

    # 6. 权限一致性核验提示
    sensitive_perms = report["permissions"]["sensitive_permissions"]
    if sensitive_perms:
        report["compliance_warnings"].append({
            "warning": f"发现{len(sensitive_perms)}个敏感权限，须与隐私政策声明逐一核对",
            "sensitive_permissions": [p["name"] for p in sensitive_perms],
            "check_action": "将这些权限与业务部门提供的权限使用清单及隐私政策声明的权限逐项比对（一致性核验）"
        })

    # 7. SDK一致性核验提示
    if identified_sdks:
        report["compliance_warnings"].append({
            "warning": f"识别到{len(identified_sdks)}个第三方SDK，须与隐私政策SDK清单核对",
            "identified_sdks": identified_sdks,
            "check_action": "将这些SDK与业务部门提供的SDK清单及隐私政策SDK声明逐项比对（一致性核验），找出未声明的SDK"
        })

    return report


def main():
    parser = argparse.ArgumentParser(description="APK静态分析工具 - APP合规检查")
    parser.add_argument("--apk", required=True, help="APK文件路径")
    parser.add_argument("--output", "-o", help="输出JSON报告文件路径（不指定则输出到stdout）")
    parser.add_argument("--format", choices=["json", "summary"], default="json", help="输出格式")

    args = parser.parse_args()

    # 启动时检测增强工具并打印能力边界告知
    enhanced_tools = check_enhanced_tools()
    print_capability_notice(enhanced_tools)

    print(f"正在分析APK: {args.apk}", file=sys.stderr)
    report = analyze_apk(args.apk)

    # 将增强工具检测结果写入报告
    report["analyzer_capabilities"] = {
        "enhanced_tools_detected": enhanced_tools,
        "base_engine": "python-stdlib (zipfile + regex)",
        "limitations": [
            "权限提取：正则匹配二进制XML字符串池，非标格式可能遗漏",
            "SDK识别：仅识别未混淆的主流SDK包名，混淆SDK会漏检",
            "包名/版本号：从二进制XML正则提取，可能不准确",
            "隐私政策：仅搜索assets/res文本文件，无法解析编译后资源"
        ],
        "recommendation": "如检测到androguard/aapt2/apktool/jadx，建议用其交叉验证本脚本输出" if enhanced_tools else "建议安装androguard或apktool以获得更精确的分析结果"
    }

    if "error" in report:
        print(f"❌ 分析失败: {report['error']}", file=sys.stderr)
        sys.exit(1)

    if args.format == "summary":
        # 输出摘要
        print("\n" + "=" * 60)
        print("APK静态分析报告摘要")
        print("=" * 60)
        print(f"文件大小: {report.get('file_size', 0) / 1024 / 1024:.2f} MB")
        print(f"文件数量: {report.get('file_count', 0)}")
        print(f"\n权限总数: {report['permissions']['total_count']}")
        print(f"敏感权限: {report['permissions']['sensitive_count']}个")
        for p in report["permissions"]["sensitive_permissions"]:
            print(f"  - {p['name']} ({p['description']})")
        print(f"\n识别到的SDK: {report['sdks']['total_count']}个")
        for sdk in report["sdks"]["identified_sdks"]:
            print(f"  - {sdk}")
        if report["privacy_policy"]["found_links"]:
            print(f"\n内嵌隐私政策链接:")
            for link in report["privacy_policy"]["found_links"]:
                print(f"  - {link}")
        print(f"\n合规警告:")
        for w in report["compliance_warnings"]:
            print(f"  ⚠️ {w['warning']}")
        print("\n" + "=" * 60)
    else:
        output = json.dumps(report, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"✅ 报告已保存到: {args.output}", file=sys.stderr)
        else:
            print(output)


if __name__ == "__main__":
    main()
