"""
法律文书生成工具 - 用户信息管理
首次使用录入，后续自动读取。
"""
import json
import os

DEFAULT_FILENAME = "user_config.json"

def get_config_path(skill_dir=None):
    if skill_dir:
        return os.path.join(skill_dir, DEFAULT_FILENAME)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), DEFAULT_FILENAME)

def load_config(config_path=None):
    if config_path is None:
        config_path = get_config_path()
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    return None

def save_config(config, config_path=None):
    if config_path is None:
        config_path = get_config_path()
    os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    return config_path

def validate_config(config):
    required = ["name", "law_firm", "license_number", "phone"]
    missing = [k for k in required if k not in config or not config[k]]
    return missing

if __name__ == "__main__":
    cfg = load_config()
    if cfg:
        print("当前配置信息：")
        for k, v in cfg.items():
            print(f"  {k}: {v}")
    else:
        print("未找到配置信息，请首次使用时录入。")
