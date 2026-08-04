"""
轻量级 .env 文件加载器（零外部依赖）
自动从 Skill 根目录的 .env 文件加载环境变量
"""
import os


def load_dotenv(env_path: str = None):
    """
    加载 .env 文件中的环境变量（不覆盖已有变量）

    查找顺序：
    1. 显式指定的 env_path
    2. 当前工作目录的 .env
    3. 脚本所在目录的上一级（Skill 根目录）的 .env
    """
    if env_path and os.path.exists(env_path):
        _parse_env(env_path)
        return

    # 当前目录
    cwd_env = os.path.join(os.getcwd(), ".env")
    if os.path.exists(cwd_env):
        _parse_env(cwd_env)
        return

    # Skill 根目录（scripts/ 的上一级）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_env = os.path.join(os.path.dirname(script_dir), ".env")
    if os.path.exists(root_env):
        _parse_env(root_env)
        return


def _parse_env(filepath: str):
    """解析 .env 文件并设置环境变量"""
    loaded = 0
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # 跳过空行和注释
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # 去除引号
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            # 不覆盖已存在的环境变量
            if key and value and key not in os.environ:
                os.environ[key] = value
                loaded += 1
    if loaded:
        import sys
        print(f"[.env] 已从 {filepath} 加载 {loaded} 个环境变量", file=sys.stderr)
