#2

import json
import requests

# ------------------------------
# API Domain 與 Endpoint 配置
# ------------------------------
api_domain = "https://k6oayrgulgb5sasvwj3tsy7l7u0tikfd.lambda-url.ap-northeast-1.on.aws"

VACANCIES_API_URL = f"{api_domain}/api/v3/tools/interview_test/taiwan_hotels/hotel/vacancies"
NEARBY_SEARCH_API_URL = f"{api_domain}/api/v3/tools/external/gcp/places/nearby_search_with_query"


# ------------------------------
# 外部專用 API Key 設定
# ------------------------------
API_HEADERS = {
    "Authorization": "DhDkXZkGXaYBZhkk1Z9m9BuZDJGy"
}

# ------------------------------
# 輔助函式：根據用戶輸入（以逗號分隔）查詢對應的 id 列表
# ------------------------------
def lookup_ids(input_texts: str, category: str) -> list:
    """
    讀取 taiwan_hotels_data_indexed.json，對於指定的 category，
    若用戶輸入的文字為某個 key 的子字串，則回傳該項目的 id。
    """
    try:
        with open("taiwan_hotels_data_indexed.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        category_data = data.get(category, {})
        result_ids = []
        for text in input_texts.split(","):
            query = text.strip()
            if query:
                for key, item in category_data.items():
                    if query in key:
                        result_ids.append(item["id"])
        if not result_ids:
            print(f"【警告】在 {category} 中找不到與 '{input_texts}' 匹配的項目。")
        return result_ids
    except Exception as e:
        print("讀取 taiwan_hotels_data_indexed.json 失敗:", e)
        return []

# ------------------------------
# 輔助函式：當用戶輸入 'list' 時列出指定分類所有選項
# ------------------------------
def get_input_with_list_option(prompt: str, category: str, use_field: str = None) -> str:
    """
    當用戶輸入 'list' 時，讀取 taiwan_hotels_data_indexed.json 中該分類的所有選項，
    並列印出來，支持輸入替代字（例如臺北市與台北市均顯示）。
    """
    while True:
        value = input(prompt).strip()
        if value.lower() == "list":
            try:
                with open("taiwan_hotels_data_indexed.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                category_data = data.get(category, {})
                if category_data:
                    print(f"\n【{category} 選項】:")
                    for key, item in category_data.items():
                        if use_field and use_field in item:
                            display_value = item[use_field]
                        else:
                            display_value = key
                        popular_str = " (熱門)" if item.get("is_popular") else ""
                        if category == "hotel_group_types":
                            # 針對館型，顯示 type 與 name
                            print(f" - type: {item['type']}, name: {item['name']}{popular_str}")
                        else:
                            print(f" - {display_value}{popular_str}")
                    print()  # 空行間隔
                else:
                    print(f"【警告】{category} 沒有選項。")
            except Exception as e:
                print(f"讀取 {category} 選項失敗: {e}")
            # 列出選項後，再次提示用戶輸入
        else:
            return value

# ------------------------------
# 查詢訂房所需參數
# ------------------------------
def get_vacancies_parameters() -> dict:
    print("【訂房查詢】請提供以下資訊 (所有資訊皆為非必填，若不填則直接跳過):")

    county_input = get_input_with_list_option(
        "請輸入目的地城市名稱 [或輸入 'list' 查看所有選項]: ", 
        "counties"
    )
    county_ids = lookup_ids(county_input, "counties") if county_input else []
    
    district_input = get_input_with_list_option(
        "請輸入目的地鄉鎮區名稱 [或輸入 'list' 查看所有選項]: ", 
        "districts"
    )
    district_ids = lookup_ids(district_input, "districts") if district_input else []
        
    check_in = input("入住日期 (例如 2025-01-01): ").strip() or None
    check_out = input("退房日期 (例如 2025-01-03): ").strip() or None
    
    adults_input = input("成人數: ").strip()
    adults = int(adults_input) if adults_input else None
    
    children_input = input("兒童數: ").strip()
    children = int(children_input) if children_input else None

    hotel_group_types = get_input_with_list_option(
        "旅館類型 (預設 BASIC, 請輸入 type；或輸入 'list' 查看所有選項): ", 
        "hotel_group_types", use_field="type"
    )
    hotel_group_types = hotel_group_types or "BASIC"

    highest_price_input = input("最高預算: ").strip()
    highest_price = int(highest_price_input) if highest_price_input else None
    
    lowest_price_input = input("最低預算: ").strip()
    lowest_price = int(lowest_price_input) if lowest_price_input else None
    
    hotel_facility_input = get_input_with_list_option(
        "請輸入旅館設施名稱 (以逗號分隔，例如: 24小時接待入住,24小時保全) [或輸入 'list' 查看所有選項]: ", 
        "hotel_facilities"
    )
    hotel_facility_ids = lookup_ids(hotel_facility_input, "hotel_facilities") if hotel_facility_input else []
    
    room_facility_input = get_input_with_list_option(
        "請輸入房間設施名稱 (以逗號分隔，例如: 大毛巾,小毛巾) [或輸入 'list' 查看所有選項]: ", 
        "room_type_facilities"
    )
    room_facility_ids = lookup_ids(room_facility_input, "room_type_facilities") if room_facility_input else []
    
    has_breakfast_input = input("是否有早餐? (y/n): ").strip().lower()
    has_breakfast = True if has_breakfast_input == "y" else False if has_breakfast_input == "n" else None
    
    has_lunch_input = input("是否有午餐? (y/n): ").strip().lower()
    has_lunch = True if has_lunch_input == "y" else False if has_lunch_input == "n" else None
    
    has_dinner_input = input("是否有晚餐? (y/n): ").strip().lower()
    has_dinner = True if has_dinner_input == "y" else False if has_dinner_input == "n" else None
    
    params = {
        "hotel_group_types": hotel_group_types,
    }
    if check_in:
        params["check_in"] = check_in
    if check_out:
        params["check_out"] = check_out
    if adults is not None:
        params["adults"] = adults
    if children is not None:
        params["children"] = children
    if lowest_price is not None:
        params["lowest_price"] = lowest_price
    if highest_price is not None:
        params["highest_price"] = highest_price
    if county_ids:
        params["county_ids"] = county_ids
    if district_ids:
        params["district_ids"] = district_ids
    if hotel_facility_ids:
        params["hotel_facility_ids"] = hotel_facility_ids
    if room_facility_ids:
        params["room_facility_ids"] = room_facility_ids
    if has_breakfast is not None:
        params["has_breakfast"] = has_breakfast
    if has_lunch is not None:
        params["has_lunch"] = has_lunch
    if has_dinner is not None:
        params["has_dinner"] = has_dinner
        
    return params

# ------------------------------
# Agent 定義
# ------------------------------
class HotelVacanciesAgent:
    def process(self, params):
        #print("\n調用訂房查詢 API，參數:")
        #print(json.dumps(params, ensure_ascii=False, indent=2))
        try:
            response = requests.get(VACANCIES_API_URL, params=params, headers=API_HEADERS, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print("請求失敗:", e)
            return {"error": "查詢訂房資料時出現問題"}

class NearbySearchAgent:
    def process(self, params):
        #print("\n調用周邊查詢 API (POST)，參數:")
        #print(json.dumps(params, ensure_ascii=False, indent=2))
        try:
            # 使用 POST 請求，傳送 JSON 內容
            response = requests.post(NEARBY_SEARCH_API_URL, json=params, headers=API_HEADERS, timeout=5)
            response.raise_for_status()
            full_result = response.json()
            # 過濾回傳資訊，只保留重要欄位
            filtered = {
                "surroundings_map_images": full_result.get("surroundings_map_images", []),
                "places": []
            }
            for place in full_result.get("places", []):
                filtered_place = {
                    "name": place.get("displayName", {}).get("text", "未知"),
                    "address": place.get("formattedAddress", "未知地址"),
                    #"location": place.get("location", {}),
                    "rating": place.get("rating", "無評分"),
                    "opening_hours": place.get("currentOpeningHours", {}).get("weekdayDescriptions", [])
                }
                filtered["places"].append(filtered_place)
            return self.format_result(filtered)
        except requests.RequestException as e:
            print("請求失敗:", e)
            return f"查詢周邊資訊時出現問題: {e}"
    
    def format_result(self, result: dict) -> str:
        """將回傳結果整理為易讀的文字格式"""
        output_lines = []
        images = result.get("surroundings_map_images", [])
        if images:
            output_lines.append("地圖圖片:")
            for img in images:
                output_lines.append(f"  {img}")
            output_lines.append("")
        places = result.get("places", [])
        if places:
            output_lines.append("推薦的地點：")
            for idx, place in enumerate(places, start=1):
                output_lines.append(f"{idx}. 名稱: {place['name']}")
                output_lines.append(f"   地址: {place['address']}")
                loc = place.get("location", {})
                if loc:
                    output_lines.append(f"   位置: {loc.get('latitude', 'N/A')}, {loc.get('longitude', 'N/A')}")
                output_lines.append(f"   評分: {place.get('rating', 'N/A')}")
                if place.get("opening_hours"):
                    output_lines.append("   營業時間:")
                    for line in place["opening_hours"]:
                        output_lines.append(f"     {line}")
                output_lines.append("")
        else:
            output_lines.append("查無地點資訊。")
        return "\n".join(output_lines)


def prompt_continue(main_func):
    cont = input("\n是否重新查詢訂房相關資訊？(y/n): ").strip().lower()
    if cont == "y":
        print("\n重新開始查詢...\n")
        main_func()  # 呼叫傳入的主查詢函數
    else:
        print("感謝使用，再見！")

# ------------------------------
# 主程式
# ------------------------------
def main():
    print("=== 訂房查詢流程開始 ===\n")
    vacancies_params = get_vacancies_parameters()
    vacancies_agent = HotelVacanciesAgent()
    vacancies_result = vacancies_agent.process(vacancies_params)
    
    # 假設 vacancies_result 為列表，若不是則直接退出
    if not vacancies_result or not isinstance(vacancies_result, list):
        print("查無訂房資訊或資料格式錯誤。")
        prompt_continue(main)
        #return
    elif 'error_message' in vacancies_result[0]:
        print(vacancies_result[0]['error_message'])
        prompt_continue(main)
        
    #print(vacancies_result)
    print("\n=== 訂房查詢結果推薦 ===")
    for idx, hotel in enumerate(vacancies_result, start=1):
        print(f"\n--------------------\n推薦 {idx}:")
        hotel_name = hotel.get("name", "未知飯店")
        hotel_address = hotel.get("address", "未知地址")
        hotel_intro = hotel.get("intro", "無介紹")
        print(f"飯店名稱: {hotel_name}")
        print(f"地址: {hotel_address}")
        print(f"介紹: {hotel_intro}")
        
        # 周邊推薦：依據飯店名稱查詢「附近的景點」、「附近的餐廳」、「附近的商店」
        nearby_agent = NearbySearchAgent()
        poi_categories = ["景點", "咖啡廳", "購物中心", "公園", "夜市"]
        for poi in poi_categories:
            query = f"{hotel_name} 附近的{poi}"
            print(f"\n查詢: {query}")
            nearby_params = {"text_query": query}
            nearby_result = nearby_agent.process(nearby_params)
            print("推薦結果:")
            #print(json.dumps(nearby_result, indent=2, ensure_ascii=False))
            print(nearby_result)
    print("以上是我們為您精心整理的所有查詢與推薦結果，期望這些資訊能為您的旅程帶來啟發與便利，祝您旅途愉快！")
    prompt_continue(main)
    # cont = input("\n是否重新查詢訂房相關資訊？(y/n): ").strip().lower()
    # if cont == "y":
    #     print("\n重新開始查詢...\n")
    #     main()
    # else:
    #     print("感謝使用，再見！")

if __name__ == "__main__":
    main()
