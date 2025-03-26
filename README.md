1、安装依赖：
pip install -r requirements.txt

2、input_csv文件夹中存放需要询价的文本，格式为csv，编码格式utf-8，编码格式可以通过配置文件更改

3、如果csv中：凭证号、新发地名称、询价三个字段行号编号，需要在配置文件中修改

4、当前“新发地名称”字段，可以跳过'#N/A', '', "0"，如有新增，可以在配置文件中修改

5、生产环境使用gunicorn方式启动命令：nohup gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 --access-logfile gunicorn.log app:app > app.log 2>&1 &