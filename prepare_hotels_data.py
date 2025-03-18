# 準備資料供查詢
import requests
import json
import os

def load_config(filename="config.json"):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

config = load_config()

# ------------------------------
# 定義各 API 的 URL、描述與參數
# ------------------------------
api_domain = config.get("api_domain")

API_HEADERS = {
    "Authorization": config.get("api_key")
}

api_endpoints = {
    "counties": {
        "url": f"{api_domain}/api/v3/tools/interview_test/taiwan_hotels/counties",
        "description": "取得台灣旅館縣市列表"
    },
    "districts": {
        "url": f"{api_domain}/api/v3/tools/interview_test/taiwan_hotels/districts",
        "description": "取得台灣旅館鄉鎮區列表"
    },
    "hotel_group_types": {
        "url": f"{api_domain}/api/v3/tools/interview_test/taiwan_hotels/hotel_group/types",
        "description": "取得台灣旅館館型列表"
    },
    "hotel_facilities": {
        "url": f"{api_domain}/api/v3/tools/interview_test/taiwan_hotels/hotel/facilities",
        "description": "取得台灣旅館設施列表"
    },
    "room_type_facilities": {
        "url": f"{api_domain}/api/v3/tools/interview_test/taiwan_hotels/hotel/room_type/facilities",
        "description": "取得台灣旅館房間設施列表"
    },
    "room_type_bed_types": {
        "url": f"{api_domain}/api/v3/tools/interview_test/taiwan_hotels/hotel/room_type/bed_types",
        "description": "取得台灣旅館房間床型列表"
    }
}

def query_api(api_name, api_info):
    print(f"查詢 {api_name} - {api_info['description']}")
    try:
        response = requests.get(api_info["url"], API_HEADERS=API_HEADERS, params=api_info.get("params", {}))
        if response.status_code == 200:
            return response.json()
        else:
            print(f"HTTP {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print("Error:", e)
        return None

def query_all_endpoints():
    collected_data = {}
    for api_name, api_info in api_endpoints.items():
        data = query_api(api_name, api_info)
        collected_data[api_name] = data
    return collected_data

# ------------------------------
# Part 2: JSON 轉換功能
# ------------------------------

def generate_alternative_keys(name: str) -> set:
    """
    根據輸入的名稱產生替代的搜尋 key。
    例如，如果名稱包含「臺」，則產生將「臺」替換成「台」的版本；
    如果名稱包含「台」但不含「臺」，則產生將「台」替換成「臺」的版本。
    """
    alternatives = set()
    if "臺" in name:
        alt = name.replace("臺", "台")
        if alt != name:
            alternatives.add(alt)
    if "台" in name and "臺" not in name:
        alt = name.replace("台", "臺")
        if alt != name:
            alternatives.add(alt)
    return alternatives

def convert_json_index(input_file: str, output_file: str):
    """
    讀取原始 JSON 檔案，將每個類別的列表轉換成以項目名稱作 key 的字典，
    並根據替代規則新增額外的 key。
    """
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        new_data = {}
        for category, items in data.items():
            new_data[category] = {}
            # 預期 items 為列表
            for item in items:
                if not isinstance(item, dict):
                    print(f"警告：在 {category} 中遇到非字典資料: {item}，將跳過此項。")
                    continue
                key = item.get("name")
                if key:
                    new_data[category][key] = item
                    alt_keys = generate_alternative_keys(key)
                    for alt in alt_keys:
                        if alt not in new_data[category]:
                            new_data[category][alt] = item
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
        print(f"轉換完成，已存檔至 {output_file}")
    except Exception as e:
        print("轉換失敗:", e)

# ------------------------------
# 主函式：查詢 API 並產生索引 JSON
# ------------------------------
def main():
    # 查詢所有 API，並存入 taiwan_hotels_data.json
    collected_data = query_all_endpoints()
    filename = "taiwan_hotels_data.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(collected_data, f, ensure_ascii=False, indent=4)
    print(f"\n資料已存入 {filename}")
    
    # 載入並印出查詢到的資料（選填）
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
        print("\n載入資料：")
        print(json.dumps(loaded_data, ensure_ascii=False, indent=4))
    
    # 轉換 JSON 為索引版本
    output_filename = "taiwan_hotels_data_indexed.json"
    convert_json_index(filename, output_filename)

if __name__ == "__main__":
    main()
