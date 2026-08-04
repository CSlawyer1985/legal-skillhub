"""包入口模块，支持通过 python -m scripts 方式运行系统。

当用户执行 python -m scripts 时，Python 会自动查找并执行本模块，
进而调用 main.py 中的 main() 函数启动归档系统。
"""

from .main import main

main()
