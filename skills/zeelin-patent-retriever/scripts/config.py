"""配置加载：支持从 .env 读取 GOOGLE_APPLICATION_CREDENTIALS 等。"""
import os
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
if ENV_PATH.exists():
    try:
        from dotenv import load_dotenv  # type: ignore
    except ImportError:
        # 静默失败，让调用方看到缺少依赖提示
        pass
    else:
        load_dotenv(dotenv_path=ENV_PATH)

# 兼容直接在环境里设置，不做额外校验

def require_env(name: str):
    if not os.getenv(name):
        raise RuntimeError(f"缺少环境变量 {name}，请在 .env 或 shell 中设置")

# BigQuery 客户端需要的最常见变量
for var in ["GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_CLOUD_PROJECT"]:
    if not os.getenv(var):
        # 不强制 raise，留给运行时报错提示
        pass
