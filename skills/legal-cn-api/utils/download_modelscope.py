#!/usr/bin/env python3
"""Download Chinese-Laws dataset from ModelScope"""

import os
from modelscope.hub.api import HubApi
from modelscope.hub.file_download import model_file_download

# You can download the dataset dengcao/Chinese-Laws
print("Downloading dataset dengcao/Chinese-Laws from ModelScope...")

model_dir = "data/chinese-laws-2025"
os.makedirs(model_dir, exist_ok=True)

api = HubApi()

# Try to list files
# We'll use snapshot_download
from modelscope.hub.snapshot_download import snapshot_download

try:
    model_dir = snapshot_download('dengcao/Chinese-Laws', cache_dir='data', local_dir=model_dir)
    print(f"Download completed to {model_dir}")
    print("Files:")
    for root, dirs, files in os.walk(model_dir):
        for f in files:
            print(f"  - {os.path.join(root, f)}")
except Exception as e:
    print(f"Error downloading: {e}")
    import traceback
    traceback.print_exc()
