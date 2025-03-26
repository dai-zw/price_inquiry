import time
import requests
import csv
from datetime import datetime, timedelta
from get_conf import config

# ==================== 数据加载与预处理 ====================
def load_filtered_data(path):
    """读取CSV并处理日期格式"""
    data = []
    with open(path, 'r', encoding=config["encoding"]) as f:
        reader = csv.reader(f)
        headers = [next(reader) for _ in range(3)]  # 保存原始标题行
        for row in reader:
            try:
                date_str = row[7]
                if date_str.isdigit():
                    base_date = datetime(1899, 12, 30)
                    real_date = base_date + timedelta(days=int(date_str))
                else:
                    real_date = datetime.strptime(date_str, "%Y/%m/%d")
                data.append({
                    '凭证号': row[config["voucher"]],
                    '新发地名称': row[config["xfd_row"]].strip(),
                    '新发地规格': row[config["specInfo_row"]].strip(),
                    '登记日期': real_date,
                    'raw_row': row  # 保留原始行数据
                })
            except Exception as e:
                print(f"数据解析错误: {e} | 行内容: {row}")

    return data, headers


# ==================== API查询核心逻辑 ====================
def get_price_data(datas):
    """单个数据的API查询逻辑"""
    if datas['新发地名称'] in config["skipped_names"]:
        return datas['凭证号'], None

    # 旬别日期调整
    target_date = datas["登记日期"]
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
                'prodName': datas['新发地名称'],
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=5
        )
        res.raise_for_status()
        price_data = res.json()
        time.sleep(5)

        if price_data['list']:
            # 遍历所有列表项寻找规格匹配项
            for item in price_data['list']:
                if item["specInfo"] == datas["新发地规格"] or item["specInfo"] == "":
                    # 找到匹配规格，返回对应价格
                    return datas['凭证号'], item['avgPrice']

            # 循环完成仍未找到匹配项
            return datas['凭证号'], "表中新发地规格与查询到的规则字段不匹配"
        else:
            return datas['凭证号'], 0.0

    except Exception as e:
        print(f"API查询失败: {e} | 凭证号: {datas['凭证号']}")
        return datas['凭证号'], None


# ==================== 数据写入逻辑 ====================
def update_csv_with_prices():
    """主处理流程"""
    # 加载数据并保留原始标题
    all_data, headers = load_filtered_data(config["INPUT_PATH"])

    # 创建凭证号到价格的映射
    price_map = {}
    for data in all_data:
        voucher, price = get_price_data(data)
        if price is not None:
            price_map[voucher] = price

        elif price == "表中新发地规格与查询到的规则字段不匹配":
            price_map[voucher] = "表中新发地规格与查询到的规则字段不匹配"

    # 读取原始CSV内容
    with open(config["INPUT_PATH"], 'r', encoding=config["encoding"]) as f:
        reader = csv.reader(f)
        original_rows = list(reader)

    # 更新价格到“询价”列
    try:
        for i in range(3, len(original_rows)):  # 跳过前三行标题
            row = original_rows[i]
            if len(row) > 0:
                voucher = row[config["voucher"]]
                if voucher in price_map:
                    # 确保行有足够的列
                    enough_row = config["priceInquiry_row"] + 1
                    if len(row) < enough_row:
                        row += [''] * (enough_row - len(row))
                    row[config["priceInquiry_row"]] = str(price_map[voucher])

    except Exception as e:
        print(e)

    # 写入更新后的文件
    with open(config["OUTPUT_PATH"], 'w', encoding=config["encoding"], newline='') as f:
        writer = csv.writer(f)
        writer.writerows(original_rows)


if __name__ == "__main__":
    update_csv_with_prices()
    print("价格更新完成！")