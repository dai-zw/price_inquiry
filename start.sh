#!/bin/bash
source /path/to/your/venv/bin/activate  # 替换为你的虚拟环境路径
exec gunicorn -w 4 -b 0.0.0.0:5000 --access-logfile - "app:app"