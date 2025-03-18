import json
import requests
from typing import TypedDict, Dict, List, Tuple, Any
from langgraph.graph import StateGraph

# 定義一個簡單的訊息類別，方便後續存取 content 屬性
class Message:
    def __init__(self, content: str):
        self.content = content

# 定義整個狀態資料結構，包含聊天訊息、查詢參數與結果
class AppState(TypedDict):
    messages: List[Tuple[str, Message]]  # (role, Message)
    params: Dict[str, Any]
    results: List[Any]

# ------------------------------
# 輔助函式：載入設定檔
# ------------------------------
def load_config(filename="config.json"):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

config = load_config()
api_domain = config.get("api_domain")
API_HEADERS = {"Authorization": config.get("api_key")}

VACANCIES_API_URL = f"{api_domain}/api/v3/tools/interview_test/taiwan_hotels/hotel/vacancies"
NEARBY_SEARCH_API_URL = f"{api_domain}/api/v3/tools/external/gcp/places/nearby_search_with_query"

# ------------------------------
# 輔助函式：根據用戶輸入查詢 id
# ------------------------------
def lookup_ids(input_texts: str, category: str) -> List[Any]:
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
# 輔助函式：當用戶輸入 'list' 時顯示所有選項
# ------------------------------
def get_input_with_list_option(prompt: str, category: str, use_field: str = None) -> str:
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
                        display_value = item.get(use_field, key) if use_field else key
                        popular_str = " (熱門)" if item.get("is_popular") else ""
                        if category == "hotel_group_types":
                            print(f" - type: {item['type']}, name: {item['name']}{popular_str}")
                        else:
                            print(f" - {display_value}{popular_str}")
                    print()
                else:
                    print(f"【警告】{category} 沒有選項。")
            except Exception as e:
                print(f"讀取 {category} 選項失敗: {e}")
        else:
            return value

# ------------------------------
# 輔助函式：取得訂房查詢參數（互動式）
# ------------------------------
def get_vacancies_parameters() -> Dict[str, Any]:
    print("【訂房查詢】請提供以下資訊 (所有資訊皆為非必填，若不填則直接跳過):")
    county_input = get_input_with_list_option("請輸入目的地城市名稱 [或輸入 'list' 查看所有選項]: ", "counties")
    county_ids = lookup_ids(county_input, "counties") if county_input else []
    
    district_input = get_input_with_list_option("請輸入目的地鄉鎮區名稱 [或輸入 'list' 查看所有選項]: ", "districts")
    district_ids = lookup_ids(district_input, "districts") if district_input else []
        
    check_in = input("入住日期 (例如 2025-01-01): ").strip() or None
    check_out = input("退房日期 (例如 2025-01-03): ").strip() or None
    
    adults_input = input("成人數: ").strip()
    adults = int(adults_input) if adults_input else None
    
    children_input = input("兒童數: ").strip()
    children = int(children_input) if children_input else None

    hotel_group_types = get_input_with_list_option("旅館類型 (預設 BASIC, 請輸入 type；或輸入 'list' 查看所有選項): ", "hotel_group_types", use_field="type")
    hotel_group_types = hotel_group_types or "BASIC"

    highest_price_input = input("最高預算: ").strip()
    highest_price = int(highest_price_input) if highest_price_input else None
    
    lowest_price_input = input("最低預算: ").strip()
    lowest_price = int(lowest_price_input) if lowest_price_input else None
    
    hotel_facility_input = get_input_with_list_option("請輸入旅館設施名稱 (以逗號分隔，例如: 24小時接待入住,24小時保全) [或輸入 'list' 查看所有選項]: ", "hotel_facilities")
    hotel_facility_ids = lookup_ids(hotel_facility_input, "hotel_facilities") if hotel_facility_input else []
    
    room_facility_input = get_input_with_list_option("請輸入房間設施名稱 (以逗號分隔，例如: 大毛巾,小毛巾) [或輸入 'list' 查看所有選項]: ", "room_type_facilities")
    room_facility_ids = lookup_ids(room_facility_input, "room_type_facilities") if room_facility_input else []
    
    has_breakfast_input = input("是否有早餐? (y/n): ").strip().lower()
    has_breakfast = True if has_breakfast_input == "y" else False if has_breakfast_input == "n" else None
    
    has_lunch_input = input("是否有午餐? (y/n): ").strip().lower()
    has_lunch = True if has_lunch_input == "y" else False if has_lunch_input == "n" else None
    
    has_dinner_input = input("是否有晚餐? (y/n): ").strip().lower()
    has_dinner = True if has_dinner_input == "y" else False if has_dinner_input == "n" else None
    
    params = {"hotel_group_types": hotel_group_types}
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
    def process(self, params: Dict[str, Any]) -> List[Any]:
        try:
            response = requests.get(VACANCIES_API_URL, params=params, headers=API_HEADERS, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print("請求失敗:", e)
            return [{"error_message": "查詢訂房資料時出現問題"}]

class NearbySearchAgent:
    def process(self, params: Dict[str, Any]) -> str:
        try:
            response = requests.post(NEARBY_SEARCH_API_URL, json=params, headers=API_HEADERS, timeout=5)
            response.raise_for_status()
            full_result = response.json()
            filtered = {
                "surroundings_map_images": full_result.get("surroundings_map_images", []),
                "places": []
            }
            for place in full_result.get("places", []):
                filtered_place = {
                    "name": place.get("displayName", {}).get("text", "未知"),
                    "address": place.get("formattedAddress", "未知地址"),
                    "rating": place.get("rating", "無評分"),
                    "opening_hours": place.get("currentOpeningHours", {}).get("weekdayDescriptions", [])
                }
                filtered["places"].append(filtered_place)
            return self.format_result(filtered)
        except requests.RequestException as e:
            print("請求失敗:", e)
            return f"查詢周邊資訊時出現問題: {e}"
    
    def format_result(self, result: Dict[str, Any]) -> str:
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
                output_lines.append(f"   評分: {place.get('rating', 'N/A')}")
                if place.get("opening_hours"):
                    output_lines.append("   營業時間:")
                    for line in place["opening_hours"]:
                        output_lines.append(f"     {line}")
                output_lines.append("")
        else:
            output_lines.append("查無地點資訊。")
        return "\n".join(output_lines)

def process_nearby_search(query: str) -> str:
    agent = NearbySearchAgent()
    nearby_params = {"text_query": query}
    return agent.process(nearby_params)

def display_results(vacancies_result: List[Any]) -> None:
    if not vacancies_result or not isinstance(vacancies_result, list):
        print("查無訂房資訊或資料格式錯誤。")
        prompt_continue(main)
    elif 'error_message' in vacancies_result[0]:
        print(vacancies_result[0]['error_message'])
        prompt_continue(main)

    print("\n=== 訂房查詢結果推薦 ===")
    poi_categories = ["景點", "咖啡廳", "購物中心", "公園", "夜市"]
    for idx, hotel in enumerate(vacancies_result, start=1):
        print(f"\n--------------------\n推薦 {idx}:")
        hotel_name = hotel.get("name", "未知飯店")
        hotel_address = hotel.get("address", "未知地址")
        hotel_intro = hotel.get("intro", "無介紹")
        print(f"飯店名稱: {hotel_name}")
        print(f"地址: {hotel_address}")
        print(f"介紹: {hotel_intro}")
        
        for poi in poi_categories:
            query_text = f"{hotel_name} 附近的{poi}"
            print(f"\n查詢: {query_text}")
            nearby_result = process_nearby_search(query_text)
            print("推薦結果:")
            print(nearby_result)
    print("\n以上是我們為您精心整理的所有查詢與推薦結果，期望這些資訊能為您的旅程帶來啟發與便利，祝您旅途愉快！")

def prompt_continue(main_func):
    cont = input("\n是否重新查詢訂房相關資訊？(y/n): ").strip().lower()
    if cont == "y":
        print("\n重新開始查詢...\n")
        main_func()  # 呼叫傳入的主查詢函數
    else:
        print("感謝使用，再見！")

# ------------------------------
# LangGraph 節點函數
# ------------------------------
def get_params_node(state: AppState) -> AppState:
    # 呼叫互動式參數輸入
    state["params"] = get_vacancies_parameters()
    return state

def process_vacancies_node(state: AppState) -> AppState:
    agent = HotelVacanciesAgent()
    vacancies_result = agent.process(state["params"])
    state["results"] = vacancies_result
    return state

def display_results_node(state: AppState) -> AppState:
    display_results(state["results"])
    # 將回應訊息加入 state["messages"]，以供聊天室介面呈現
    state["messages"] = [("assistant", Message("訂房查詢結果已呈現。"))]
    return state

# ------------------------------
# 建構與執行 StateGraph 工作流
# ------------------------------
def main():
    initial_state: AppState = {"messages": [], "params": {}, "results": []}
    graph_builder = StateGraph(AppState)
    graph_builder.add_node("get_params", get_params_node)
    graph_builder.add_node("vacancies", process_vacancies_node)
    graph_builder.add_node("display", display_results_node)
    
    graph_builder.add_edge("get_params", "vacancies")
    graph_builder.add_edge("vacancies", "display")
    
    graph_builder.set_entry_point("get_params")
    graph_builder.set_finish_point("display")
    
    # 編譯圖
    graph = graph_builder.compile()
    
    # 實現聊天室介面：每次用戶輸入皆建立初始 state 並以 graph.stream 方式執行
    print("=== 訂房查詢流程開始 ===\n")
    state = {"messages": [("user", Message('找空房'))], "params": {}, "results": []}
    for event in graph.stream(state):
        for value in event.values():
            #print("Assistant:", value["messages"][-1].content)
            pass

    prompt_continue(main)

if __name__ == "__main__":
    main()
