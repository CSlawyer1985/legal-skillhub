#!/usr/bin/env python3
"""
Zero-One-Two-Three 知识库密码锁 🔐 (工业增强版 v6.0)
对知识笔记进行智能加密：公开试读 + 核心加密 + 自动备份
特性：
  1. 支持整数/小数百分比参数（如 30 或 0.3）
  2. 密码强度验证（≥8 位，含大小写字母和数字）
  3. 加密前自动备份原文件
  4. 区分"密码错误"与"文件损坏"错误
  5. 统一元信息格式标签

用法：
  加密：python3 knowledge_lock.py lock   <文件路径> <密码> [--preview 30] [--no-backup]
  解密：python3 knowledge_lock.py unlock <文件路径> <密码>
  查看：python3 knowledge_lock.py peek   <文件路径>
"""

# ==========================================
# 🛡️ Windows 编码兼容性修复
# ==========================================
import sys
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
# ==========================================

import os
import re
import json
import time
import shutil
import base64
import hashlib
from datetime import datetime

try:
    from cryptography.fernet import Fernet
except ImportError:
    print("\n⚠️ 环境缺失：需要安装 cryptography 库")
    print("## ⚙️ 安装指南")
    print("pip install 'cryptography>=42.0.8,<43'")
    print("# 如需升级：pip install --upgrade cryptography")
    sys.exit(1)


def derive_key(password: str) -> bytes:
    """从用户密码派生 Fernet 兼容的 32 字节密钥"""
    digest = hashlib.sha256(password.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest)


def check_password_strength(password: str) -> tuple:
    """
    检查密码强度
    返回 (bool, str): (是否通过，提示信息)
    """
    if len(password) < 8:
        return False, "❌ 密码长度至少 8 位（当前 {} 位）".format(len(password))
    if not re.search(r'[A-Z]', password):
        return False, "❌ 密码需包含至少一个大写字母"
    if not re.search(r'[a-z]', password):
        return False, "❌ 密码需包含至少一个小写字母"
    if not re.search(r'\d', password):
        return False, "❌ 密码需包含至少一个数字"
    return True, "✅ 密码强度验证通过"


def parse_preview_ratio(value: str) -> float:
    """
    解析 preview 参数，支持整数（如 30）和小数（如 0.3）
    返回 0.05~0.95 之间的浮点数
    """
    try:
        val = float(value)
        if val > 1:
            ratio = val / 100.0  # 整数转小数（30 → 0.3）
        else:
            ratio = val           # 已是小数（0.3）
        return max(0.05, min(0.95, ratio))  # 限制在 5%~95%
    except ValueError:
        return 0.3  # 默认值


def split_content_for_preview(content: str, preview_ratio: float = 0.3) -> tuple:
    """智能分割内容：公开试读区 + 核心加密区"""
    h2_pattern = r'\n## '
    matches = list(re.finditer(h2_pattern, content))
    
    if len(matches) >= 2:
        split_pos = matches[1].start()
        preview = content[:split_pos].strip()
        core = content[split_pos:].strip()
        
        if len(preview) < 200:
            split_pos = int(len(content) * preview_ratio)
            preview = content[:split_pos].strip()
            core = content[split_pos:].strip()
        
        return preview, core
    
    split_pos = int(len(content) * preview_ratio)
    return content[:split_pos].strip(), content[split_pos:].strip()


def backup_file(filepath: str) -> str:
    """创建带时间戳的备份文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base, ext = os.path.splitext(filepath)
    backup_path = f"{base}.backup_{timestamp}{ext}"
    shutil.copy2(filepath, backup_path)
    return backup_path


def lock_file(filepath: str, password: str, preview_ratio: float = 0.3, do_backup: bool = True):
    """智能加密文件"""
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在：{filepath}")
        sys.exit(1)

    # 密码强度验证
    passed, msg = check_password_strength(password)
    print(msg)
    if not passed:
        print("\n💡 建议：使用密码管理器生成强密码（如 Bitwarden/1Password）")
        sys.exit(1)

    # 自动备份
    if do_backup:
        backup_path = backup_file(filepath)
        print(f"💾 已备份原文件：{backup_path}")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    preview_content, core_content = split_content_for_preview(content, preview_ratio)

    key = derive_key(password)
    fernet = Fernet(key)
    encrypted_core = fernet.encrypt(core_content.encode('utf-8'))

    # 统一使用"元信息:"格式（带冒号）
    meta = {
        "tool": "Zero-One-Two-Three Knowledge Lock",
        "version": "6.0 (Industrial)",
        "locked_at": datetime.now().isoformat(),
        "source_file": os.path.basename(filepath),
        "preview_ratio": preview_ratio,
        "content_hash": hashlib.sha256(content.encode('utf-8')).hexdigest()[:16],
        "preview_hash": hashlib.sha256(preview_content.encode('utf-8')).hexdigest()[:16],
        "core_hash": hashlib.sha256(core_content.encode('utf-8')).hexdigest()[:16]
    }

    locked_path = filepath + '.locked'
    try:
        with open(locked_path, 'w', encoding='utf-8') as f:
            f.write(preview_content)
            f.write("\n\n---\n\n")
            f.write("<!-- 🔐 ZERO-ONE-TWO-THREE LOCK: 以下为加密核心内容 -->\n")
            f.write(f"<!-- 元信息: {json.dumps(meta, ensure_ascii=False)} -->\n")
            f.write("<!-- 密文: -->\n")
            f.write(encrypted_core.decode('utf-8'))
            f.write("\n")
    except IOError as e:
        print(f"❌ 写入加密文件失败：{e}")
        sys.exit(1)

    print(f"🔐 智能加密成功！")
    print(f"   加密文件：{locked_path}")
    print(f"   👀 公开试读：{len(preview_content)} 字符")
    print(f"   🔒 核心加密：{len(core_content)} 字符")

def unlock_file(filepath: str, password: str):
    """解密文件，区分密码错误与文件损坏"""
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在：{filepath}")
        sys.exit(1)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except IOError as e:
        print(f"❌ 读取文件失败：{e}")
        sys.exit(1)

    if "<!-- 🔐 ZERO-ONE-TWO-THREE LOCK:" not in content:
        print("❌ 不是有效的 Zero-One-Two-Three 加密文件")
        sys.exit(1)

    lock_section_marker = "\n\n---\n\n<!-- 🔐 ZERO-ONE-TWO-THREE LOCK:"
    lock_pos = content.find(lock_section_marker)
    
    if lock_pos == -1:
        print("❌ 无法定位加密区标记")
        sys.exit(1)

    preview_content = content[:lock_pos].strip()
    encrypted_part = content[lock_pos + len("\n\n---\n"):].strip()

    meta_line = None
    encrypted_content = None

    for line in encrypted_part.split('\n'):
        if line.startswith("<!-- 元信息:"):
            try:
                meta_json = line.replace("<!-- 元信息:", "").replace("-->", "").strip()
                meta_line = json.loads(meta_json)
            except json.JSONDecodeError:
                print("❌ 元信息格式损坏！文件可能已被篡改或传输过程中损坏。")
                sys.exit(1)
        elif line.startswith("<!-- 密文: -->"):
            encrypted_content = encrypted_part.split("<!-- 密文: -->\n")[1].strip()
            break

    if not encrypted_content:
        print("❌ 无法解析加密文件格式！文件可能已损坏。")
        sys.exit(1)

    key = derive_key(password)
    fernet = Fernet(key)

    try:
        decrypted_core = fernet.decrypt(encrypted_content.encode('utf-8'))
        core_content = decrypted_core.decode('utf-8')
    except Exception:
        print("❌ 解密失败！密码错误。")
        print("💡 提示：请确认密码大小写及特殊字符是否正确。")
        sys.exit(1)

    full_content = preview_content + "\n\n" + core_content

    preview_hash = hashlib.sha256(preview_content.encode('utf-8')).hexdigest()[:16]
    core_hash = hashlib.sha256(core_content.encode('utf-8')).hexdigest()[:16]
    
    if meta_line and preview_hash == meta_line.get("preview_hash") and core_hash == meta_line.get("core_hash"):
        print(f"✅ 指纹验证通过：{meta_line.get('content_hash')}")
    else:
        print("⚠️ 指纹不匹配！文件可能在加密后被篡改或损坏。")

    if filepath.endswith('.locked'):
        unlocked_path = filepath[:-7]
    else:
        unlocked_path = filepath + '.unlocked'

    with open(unlocked_path, 'w', encoding='utf-8') as f:
        f.write(full_content)

    print(f"🔓 解密成功！完整内容已还原")
    print(f"   还原文件：{unlocked_path}")


def peek_file(filepath: str):
    """查看加密文件的元信息"""
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在：{filepath}")
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    for line in content.split('\n'):
        if line.startswith("<!-- 元信息:"):
            try:
                meta_json = line.replace("<!-- 元信息:", "").replace("-->", "").strip()
                meta = json.loads(meta_json)
                print(f"📋 加密文件元信息：")
                print(f"   工具：{meta.get('tool', '?')}")
                print(f"   版本：{meta.get('version', '?')}")
                print(f"   原始文件：{meta.get('source_file', '?')}")
                print(f"   加密时间：{meta.get('locked_at', '?')}")
                print(f"   内容指纹：{meta.get('content_hash', '?')}")
                return
            except json.JSONDecodeError:
                print("❌ 元信息格式损坏！")
                sys.exit(1)

    print("❌ 无法解析元信息")


def main():
    if len(sys.argv) < 2:
        print("🔐 Zero-One-Two-Three 知识库密码锁 v6.0 (Industrial)")
        print("")
        print("用法：")
        print("  加密：python3 knowledge_lock.py lock <文件路径> <密码> [--preview 30] [--no-backup]")
        print("  解密：python3 knowledge_lock.py unlock <文件路径> <密码>")
        print("  查看：python3 knowledge_lock.py peek <文件路径>")
        print("")
        print("## ⚙️ 安装依赖")
        print("pip install 'cryptography>=42.0.8,<43'")
        sys.exit(0)

    action = sys.argv[1]

    if action == "lock":
        if len(sys.argv) < 4:
            print("❌ 加密需要提供密码")
            sys.exit(1)
        filepath = sys.argv[2]
        password = sys.argv[3]
        
        preview_ratio = 0.3
        do_backup = True  # 默认开启备份
        
        if "--preview" in sys.argv:
            idx = sys.argv.index("--preview")
            if idx + 1 < len(sys.argv):
                preview_ratio = parse_preview_ratio(sys.argv[idx+1])
        
        if "--no-backup" in sys.argv:
            do_backup = False
        
        lock_file(filepath, password, preview_ratio, do_backup)

    elif action == "unlock":
        if len(sys.argv) < 4:
            print("❌ 解密需要提供密码")
            sys.exit(1)
        filepath = sys.argv[2]
        password = sys.argv[3]
        unlock_file(filepath, password)

    elif action == "peek":
        if len(sys.argv) < 3:
            print("❌ 请提供文件路径")
            sys.exit(1)
        peek_file(sys.argv[2])

    else:
        print(f"❌ 未知操作：{action}")
        sys.exit(1)


if __name__ == "__main__":
    main()
