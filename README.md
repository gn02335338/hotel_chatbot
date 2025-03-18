# Hotel Search Chatbot

## 概述

此專案是一個基於 Python 的酒店查詢與推薦系統，利用 LangGraph 框架建立互動式工作流，讓使用者能夠根據多種條件查詢台灣旅館的空房資訊，並依據查詢結果推薦附近的景點、餐廳、購物中心、公園與夜市等周邊資訊。系統會使用預先處理好的資料索引 (taiwan_hotels_data_indexed.json) 來協助將用戶輸入的文字轉換為相對應的 id，並以 API 請求取得實時資料。

## 主要功能

- **互動式訂房查詢**  
  使用者依提示輸入入住日期、退房日期、成人/兒童數、價格、目的地城市與鄉鎮區、旅館設施、房間設施等資訊（皆為非必填，若不填則跳過），同時支援輸入 `list` 來列出所有選項。  
- **飯店類型查詢**  
  透過提示用戶輸入旅館類型（支援列出所有選項並標註熱門項目），預設值為 `BASIC`。  
- **空房查詢 API 呼叫**  
  根據用戶提供的參數呼叫空房查詢 API，取得符合條件的旅館列表，若查無資料則回傳錯誤訊息。  
- **周邊資訊推薦**  
  根據查詢結果中的每家飯店，系統會使用飯店名稱與預設的周邊類別（如「景點」、「咖啡廳」、「購物中心」、「公園」、「夜市」）組合查詢字串，透過 POST 請求調用周邊查詢 API，並整理回傳結果（僅保留飯店名稱、地址、評分、營業時間以及地圖圖片）。
- **互動式流程控制**  
  利用 LangGraph 將流程分成「取得查詢參數」、「查詢空房資料」與「顯示查詢結果」等節點，並在每次查詢後詢問用戶是否重新查詢或結束對話。

## 文件結構

- **langgraph_hotel_search_chatbot.py**  
  主程式，包含 LangGraph 工作流定義、各功能模組（查詢參數收集、API Agent 實作、結果展示）與互動式重複查詢提示。
- **prepare_hotel_data.py**  
  資料前置程式，用於處理並建立包含替代關鍵字的索引檔案 (taiwan_hotels_data_indexed.json)。  
- **taiwan_hotels_data_indexed.json**  
  由 prepare_hotel_data.py 產生的 JSON 索引檔，內容包含各分類（如 counties、districts、hotel_group_types 等）的對應資料，並支援「臺北市」與「台北市」等替代關鍵字。
- **config.json**  
  設定檔，包含 API 網域 (api_domain) 與 API 金鑰 (api_key)，供主程式讀取使用。
- **hotel_search_chatbot.py**  
  未使用LangGraph之主程式，功能與主程式相同

## 系統需求

- Python 3.x
- 第三方套件：
  - requests (`pip install requests`)
  - langgraph (`pip install langgraph`)

## 安裝與配置

1. **建立虛擬環境（可選）**  
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux / macOS
   venv\Scripts\activate      # Windows
   ```

2. **安裝相依套件**  
   ```bash
   pip install requests langgraph
   ```

3. **建立設定檔 config.json**  
   在專案根目錄下建立 config.json

4. **資料準備**  
   執行 prepare_hotel_data.py，產生 taiwan_hotels_data_indexed.json。該檔案會將原始資料轉換成以搜尋關鍵字為索引的格式，支援「臺北市」/「台北市」等替代字串。

## 使用說明

1. **執行主程式**  
   在終端機中執行：
   ```bash
   python langgraph_hotel_search_chatbot.py
   ```
2. **互動式查詢流程**  
   - 程式會先要求您輸入訂房查詢參數（例如：入住日期、退房日期、成人/兒童數、價格、目的地城市與鄉鎮區、旅館設施、房間設施、旅館類型等）。  
   - 當輸入參數時，若輸入 `list` 則會列出該分類所有可選項（並標註熱門項目），讓您參考。  
   - 查詢完成後，系統會依照查詢結果推薦每家飯店的周邊資訊，依序查詢「景點」、「咖啡廳」、「購物中心」、「公園」與「夜市」資訊，並整齊格式化顯示結果與地圖圖片。  
   - 最後，系統會詢問您是否重新查詢訂房相關資訊，若選擇是，則會重新啟動查詢流程。

## 如何運作

- **API 呼叫**  
  根據用戶輸入的查詢參數，程式會透過 GET 請求調用訂房空房查詢 API；而針對周邊資訊推薦則使用 POST 請求調用附近查詢 API，並將回傳的 JSON 數據進行過濾與格式化。

- **互動流程控制**  
  系統利用 LangGraph 定義多個節點（如 `get_params_node`、`process_vacancies_node`、`display_results_node`）組成工作流，讓查詢流程呈現連貫且可重複執行。

- **資料索引**  
  使用 taiwan_hotels_data_indexed.json 提供索引功能，讓用戶可以以「臺北市,新北市」等文字輸入，程式自動比對並回傳對應的 id 列表，供 API 查詢參數使用。
