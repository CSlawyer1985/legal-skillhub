# APK静态分析指南

本文件说明如何对Android APK安装包进行静态分析，提取权限声明、识别第三方SDK、提取内嵌隐私政策等技术事实，用于合规检查的"技术取证"和"一致性核验"环节。

## 一、分析原理

APK文件本质上是一个ZIP压缩包，包含编译后的代码和资源文件。静态分析通过解包APK，提取以下关键信息：

| 提取目标 | 文件位置 | 用途 |
|----------|----------|------|
| AndroidManifest.xml | APK根目录 | 权限声明、组件声明、应用基本信息 |
| classes.dex | APK根目录 | 编译后的代码（用于SDK包名识别） |
| res/ | APK内目录 | 资源文件（隐私政策文本、界面布局） |
| assets/ | APK内目录 | 原始资源文件 |
| lib/ | APK内目录 | 原生库（.so文件，可辅助SDK识别） |
| META-INF/ | APK根目录 | 签名信息 |

**重要限制：** 静态分析只能回答"声明了什么、内嵌了什么、疑似接入了什么"，不等同于运行时实际调用行为。运行时真实行为需动态测试确认。

## 二、自动化分析工具

### 使用内置脚本

```bash
python scripts/apk_analyzer.py --apk /path/to/app.apk --output /path/to/report.json
```

脚本功能：
- 解包APK（使用Python zipfile）
- 解析AndroidManifest.xml（使用正则+XML解析）
- 提取全部声明权限
- 识别第三方SDK（基于包名特征库匹配）
- 搜索内嵌隐私政策文本和链接
- 提取应用基本信息（包名、版本号、targetSdkVersion等）
- 输出结构化JSON报告

### 依赖

本脚本仅使用Python标准库（zipfile, xml.etree, re, json），无任何第三方依赖，开箱即用。

### 能力边界与增强工具（重要）

**脚本启动时自动打印能力边界告知**，并检测是否安装了以下增强工具：

| 工具 | 安装方式 | 增强能力 |
|------|----------|----------|
| androguard | `pip install androguard` | 精确解析AXML二进制XML、反编译DEX提取完整类名 |
| aapt2 | Android SDK自带 | 精确提取targetSdkVersion和权限列表 |
| apktool | https://ibotpeaches.github.io/Apktool/ | 反编译APK为可读XML |
| jadx | https://github.com/skylot/jadx | dex反编译为Java源码，可查看SDK初始化时序 |

**已知局限（零依赖模式）**：

| 分析项 | 实现方式 | 局限 |
|--------|----------|------|
| 权限提取 | 正则匹配二进制XML字符串池 | 非标格式权限声明可能遗漏 |
| SDK识别 | classes.dex字节级包名搜索 | 仅识别未混淆的主流SDK，混淆包名会漏检 |
| 包名/版本号 | 从二进制XML正则提取 | 可能不准确 |
| 隐私政策 | 搜索assets/res文本文件 | 无法解析编译后资源 |

SDK识别基于classes.dex字节级包名字符串匹配——dex文件中的字符串以MUTF-8编码存储，简单的字节搜索可覆盖大多数主流SDK。如遇重度混淆的APK导致包名匹配遗漏，审查人员可手动使用上述增强工具辅助分析。分析结果JSON中的`analyzer_capabilities`字段会记录检测到的增强工具和已知局限。

## 三、手动分析方法

### 3.1 解包APK

```bash
# 方法1：使用unzip直接解包
unzip app.apk -d app_unpacked/

# 方法2：使用apktool（保留XML可读性）
apktool d app.apk -o app_decoded/
```

### 3.2 查看权限声明

**使用apktool解码后：**
```bash
cat app_decoded/AndroidManifest.xml
```

**使用aapt2：**
```bash
aapt2 dump permissions app.apk
```

**需提取的权限类型：**

| 权限类别 | 示例 | 合规关注点 |
|----------|------|-----------|
| 敏感权限 | CAMERA, ACCESS_FINE_LOCATION, READ_CONTACTS | 须在隐私政策逐一声明 |
| 普通权限 | INTERNET, ACCESS_NETWORK_STATE | 一般无须单独声明 |
| 自定义权限 | 应用自定义的权限 | 须评估必要性 |

**常见敏感权限清单：**

```
android.permission.ACCESS_FINE_LOCATION          # 精准定位
android.permission.ACCESS_COARSE_LOCATION         # 粗略定位
android.permission.ACCESS_BACKGROUND_LOCATION     # 后台定位
android.permission.CAMERA                          # 相机
android.permission.RECORD_AUDIO                   # 录音
android.permission.READ_CONTACTS                  # 读取通讯录
android.permission.WRITE_CONTACTS                 # 编辑通讯录
android.permission.READ_CALENDAR                  # 读取日历
android.permission.WRITE_CALENDAR                 # 编辑日历
android.permission.READ_CALL_LOG                  # 读取通话记录
android.permission.WRITE_CALL_LOG                 # 编辑通话记录
android.permission.READ_PHONE_STATE               # 电话状态(IMEI/IMSI)
android.permission.READ_PHONE_NUMBERS             # 读取本机号码
android.permission.READ_SMS                        # 读取短信
android.permission.SEND_SMS                        # 发送短信
android.permission.RECEIVE_SMS                     # 接收短信
android.permission.READ_EXTERNAL_STORAGE           # 读取存储
android.permission.WRITE_EXTERNAL_STORAGE          # 写入存储
android.permission.BODY_SENSORS                    # 身体传感器
android.permission.ACTIVITY_RECOGNITION            # 活动识别
android.permission.GET_ACCOUNTS                    # 获取账户
android.permission.USE_BIOMETRIC                   # 生物识别
```

### 3.3 识别第三方SDK

**方法1：基于包名特征库匹配**

在解包后的代码中搜索已知SDK的包名特征：

```bash
# 搜索dex文件中的包名
# 使用dexdump或baksmali
d2j-dex2jar app.apk -o app.jar
jar tf app.jar | grep -E "com\.(tencent|baidu|alibaba|umeng|jiguang|getui|iflytek|tuyasmart|huawei\.hms|google)" | sort -u
```

**方法2：使用androguard**

```python
from androguard.core.apk import APK

apk = APK("app.apk")
# 获取所有类名
for dex in apk.get_all_dex():
    # 分析类名，匹配SDK特征
    pass
```

**常见SDK包名特征库：**

| SDK名称 | 包名特征 | 公司 |
|---------|----------|------|
| 微信OpenSDK | com.tencent.mm.opensdk | 腾讯 |
| QQ分享SDK | com.tencent.connect | 腾讯 |
| 支付宝SDK | com.alipay | 蚂蚁集团 |
| 友盟统计 | com.umeng | 友盟 |
| 极光推送 | cn.jiguang | 和讯华谷 |
| 个推 | com.getui / com.igexin | 个推 |
| 百度定位 | com.baidu.location | 百度 |
| 百度地图 | com.baidu.mapapi | 百度 |
| 高德地图 | com.amap.api | 高德 |
| 科大讯飞 | com.iflytek | 科大讯飞 |
| 华为HMS | com.huawei.hms | 华为 |
| 小米推送 | com.xiaomi.mipush | 小米 |
| vivo推送 | com.vivo.push | vivo |
| OPPO推送 | com.heytap / com.coloros.mcs | OPPO |
| Bugly | com.tencent.bugly | 腾讯 |
| 阿里云 | com.aliyun / com.alibaba.sdk | 阿里云 |
| 七牛云 | com.qiniu | 七牛 |
| 环信IM | com.hyphenate | 环信 |
| 融云IM | io.rong | 融云 |
| 声网Agora | io.agora | 声网 |
| 即构ZEGO | im.zego | 即构 |
| 涂鸦智能 | com.tuya.smart | 涂鸦 |
| Google Firebase | com.google.firebase | Google |
| Google Play Services | com.google.android.gms | Google |
| Flutter框架 | io.flutter | Google |
| React Native框架 | com.facebook.react | Meta |
| Unity引擎 | com.unity3d | Unity |
| Bugly Crash | com.tencent.bugly | 腾讯 |
| 网易云信 | com.netease.nim | 网易 |
| mobtech分享 | com.mob | mobtech |
| ShareSDK | cn.sharesdk | mobtech |
| SMAATO广告 | com.smaato.soma | Smaato |
| 穿山甲广告 | com.bytedance.sdk | 字节跳动 |
| 优量汇广告 | com.qq.e.ads | 腾讯 |
| AdMob广告 | com.google.android.gms.ads | Google |

### 3.4 搜索内嵌隐私政策

```bash
# 在解包后的资源文件中搜索隐私政策文本
grep -r "隐私政策\|隐私权政策\|个人信息保护政策\|privacy policy\|privacy_policy" app_unpacked/res/ app_unpacked/assets/

# 搜索隐私政策URL链接
grep -rEo "https?://[^ \"']+(privacy|policy|yinsi|yinshi)[^ \"']*" app_unpacked/
```

### 3.5 检查targetSdkVersion

```bash
# targetSdkVersion < 23 时，安装时一次性申请全部权限（捆绑），属于违规
aapt2 dump badging app.apk | grep targetSdkVersion
```

**合规要求：** targetSdkVersion应≥23，以支持运行时动态权限申请，避免捆绑授权。

## 四、分析结果应用

### 4.1 权限一致性核验

将APK提取的权限清单与业务部门提供的"权限使用清单"及隐私政策声明的权限比对：

| 比对项 | 判定 |
|--------|------|
| APK声明但清单/政策未列 | ❌ 未声明权限，需补充声明或删除 |
| 清单/政策声明但APK未声明 | ⚠️ 冗余声明，建议清理 |
| 完全一致 | ✅ 合规 |

### 4.2 SDK一致性核验

将APK识别的SDK与业务部门提供的"SDK清单"及隐私政策SDK清单比对：

| 比对项 | 判定 |
|--------|------|
| APK有但清单/政策未列 | ❌ 未声明SDK，须补充声明 |
| 清单/政策有但APK无 | ⚠️ 可能已移除，建议核实 |
| 完全一致 | ✅ 合规 |

### 4.3 隐私政策版本验证

比对APK内嵌的隐私政策文本/链接与业务部门提供的最新版隐私政策：
- 内嵌版本是否为最新
- 链接是否有效
- 内容是否一致

## 五、分析局限性

静态分析无法确认的事项（需动态测试）：
1. **运行时实际调用了什么API** —— 代码中声明了不代表运行时调用了
2. **何时触发收集** —— 触发条件需动态验证
3. **上传了什么数据** —— 网络传输内容需抓包分析
4. **收集频率** —— 实际调用频次需动态监控
5. **后台行为** —— 后台运行时的实际行为

在合规报告中，静态分析发现的问题应标注为"疑似"或"声明层面"，动态行为问题须标注为"需动态测试确认"。

## 六、iOS（IPA）分析说明

本技能以Android APK分析为主。iOS IPA分析能力有限：

- IPA文件为ZIP格式，可解包查看Info.plist中的权限声明（NSUsageDescription）
- 但IPA包含的是编译后的Mach-O二进制，无法像APK那样直接分析代码
- SDK识别可基于Info.plist中的框架声明和embedded.mobileprovision
- 建议iOS合规审查以文本审查为主，技术核验辅助

**iOS关键权限声明（Info.plist）：**

| Key | 权限 |
|-----|------|
| NSCameraUsageDescription | 相机 |
| NSPhotoLibraryUsageDescription | 相册 |
| NSLocationWhenInUseUsageDescription | 定位（使用时） |
| NSLocationAlwaysUsageDescription | 定位（始终） |
| NSMicrophoneUsageDescription | 麦克风 |
| NSContactsUsageDescription | 通讯录 |
| NSCalendarsUsageDescription | 日历 |
| NSHealthShareUsageDescription | 健康数据读取 |
| NSFaceIDUsageDescription | Face ID |
| NSTrackingUsageDescription | 广告标识符追踪 |
