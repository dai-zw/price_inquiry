import yaml
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
# 计算配置文件的路径
config_file_path = os.path.join(current_dir, '..', 'conf.yaml')

with open('conf.yaml', 'r', encoding='utf-8') as ymlfile:
    config = yaml.safe_load(ymlfile)