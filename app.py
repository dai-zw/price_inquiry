"""
# -*- coding: utf-8 -*-
# @Time     : 2025/3/26 下午8:46
# @Author   : 代志伟
# @File     : app.py
# code is far away from bugs with the god animal protecting
    I love animals. They taste delicious.
              ┏┓      ┏┓
            ┏┛┻━━━━━━━━━━━┛┻┓
            ┃     ☃   ┃
            ┃  ┳━━┛  ┗━━┳ ┃
            ┃     ━┻━   ┃
            ┗━┓      ┏━┛
                ┃      ┗━━━┓
                ┃  神兽保佑    ┣┓
                ┃　永无BUG！   ┏┛
                ┗┓┓┏━━━━┳┓┏┛
                  ┃┫┫  ┃┫┫
                  ┗┻┛  ┗┻┛
"""
from flask import Flask, render_template, request, send_file
import io
import csv
from datetime import datetime, timedelta
import time
import requests

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 获取上传文件
        file = request.files.get('file')
        if not file or file.filename == '':
            return '请选择CSV文件'

        # 解析配置参数
        config = {
            'encoding': request.form.get('encoding', 'gbk'),
            'voucher': int(request.form.get('voucher', 0)),
            'xfd_row': int(request.form.get('xfd_row', 4)),
            'specInfo_row': int(request.form.get('specInfo_row', 5)),
            'priceInquiry_row': int(request.form.get('priceInquiry_row', 13)),
            'date_row': int(request.form.get('date_row', 7)),
            'skipped_names': [name.strip() for name in request.form.get('skipped_names', '#N/A, , 0').split(',')]
        }

        # 读取并处理CSV内容
        try:
            content = file.stream.read().decode(config['encoding'])
        except UnicodeDecodeError:
            return '文件编码错误，请检查编码设置'

        # 处理CSV并生成结果
        output = process_csv(content, config)
        return send_file(
            output,
            as_attachment=True,
            download_name=f'processed_{file.filename}',
            mimetype='text/csv'
        )

    return render_template('index.html')


def process_csv(content, config):
    # 将CSV内容转换为行列表
    csv_reader = csv.reader(io.StringIO(content))
    rows = list(csv_reader)

    # 解析数据行
    data_entries = []
    for row_idx in range(3, len(rows)):
        try:
            row = rows[row_idx]
            date_str = row[config['date_row']]

            # 处理日期格式
            if date_str.isdigit():
                base_date = datetime(1899, 12, 30)
                real_date = base_date + timedelta(days=int(date_str))
            else:
                real_date = datetime.strptime(date_str, "%Y/%m/%d")

            data_entries.append({
                'row_index': row_idx,
                '凭证号': row[config['voucher']],
                '新发地名称': row[config['xfd_row']].strip(),
                '新发地规格': row[config['specInfo_row']].strip(),
                '登记日期': real_date
            })
        except Exception as e:
            print(f"行解析错误: {e}")

    # 查询价格数据
    price_map = {}
    for entry in data_entries:
        voucher, price = get_price_data(entry, config)
        if price is not None:
            price_map[voucher] = price

    # 更新CSV行数据
    for entry in data_entries:
        row = rows[entry['row_index']]
        if len(row) <= config['priceInquiry_row']:
            row += [''] * (config['priceInquiry_row'] - len(row) + 1)
        row[config['priceInquiry_row']] = str(price_map.get(entry['凭证号'], ''))

    # 生成输出文件
    output = io.BytesIO()
    csv_content = ''.join([','.join(row) + '\n' for row in rows])
    output.write(csv_content.encode(config['encoding']))
    output.seek(0)
    return output


def get_price_data(data, config):
    if data['新发地名称'] in config['skipped_names']:
        return data['凭证号'], None

    # 处理日期查询范围
    target_date = data['登记日期']
    day = target_date.day
    adjusted_day = 1 if day <= 10 else 11 if day <= 20 else 21
    adjusted_date = target_date.replace(day=adjusted_day).strftime("%Y/%m/%d")

    try:
        res = requests.post(
            url="http://m.xinfadi.com.cn/getPriceData.html",
            data={
                "limit": 20,
                "current": 1,
                'pubDateStartTime': adjusted_date,
                'pubDateEndTime': adjusted_date,
                'prodName': data['新发地名称'],
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=5
        )
        res.raise_for_status()
        price_data = res.json()
        time.sleep(1)  # 适当降低延时

        if price_data['list']:
            for item in price_data['list']:
                if item["specInfo"] == data["新发地规格"]:
                    return data['凭证号'], item['avgPrice']
            return data['凭证号'], "规格不匹配"
        else:
            return data['凭证号'], "无数据"
    except Exception as e:
        print(f"API请求失败: {e}")
        return data['凭证号'], "请求失败"


if __name__ == '__main__':
    app.run(debug=True)