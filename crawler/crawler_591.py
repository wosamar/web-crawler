from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
import math
import re
from crawler import driver_handler
from sql_app.crud import posts as posts_crud, logs as logs_crud
from sql_app import schemas as item_schemas


# 檢查是否跳出alert
def call(driver):
    alert = driver.switch_to.alert
    alert.accept()
    driver.get(driver.current_url)
    print("此頁請求超時")
    return driver


# 到下一頁
def button_click(driver):
    button = driver.find_element(By.CLASS_NAME, "pageNext")
    driver.execute_script("(arguments[0].click());", button)
    try:
        driver = call(driver)
    except Exception as e:
        pass
    WebDriverWait(driver, 10).until(
        expected_conditions.invisibility_of_element((By.CSS_SELECTOR, "div#j-loading"))
    )


def parse_page(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')
    items = soup.select('section[class="vue-list-rent-item"]')  # 找到貼文欄位

    for item in items:
        i_kind = item.find('ul', class_='item-style').li  # 判斷租房類型
        if i_kind.get_text() == "車位":  # 類型為車位不輸出
            continue
        else:
            pass

        # 取得參數
        url: str = item.a['href']
        title: str = item.a.select_one('div.item-title').get_text().replace("優選好屋", "").strip()
        address = item.select_one('div.item-area').span.get_text()
        rent: int = int(item.select_one('div.item-price-text').span.get_text().replace(",", ""))
        contact: str = item.select_one('div.item-msg').get_text().split("/")[0].strip().split(" ")[0]
        poster: str = item.select_one('div.item-msg').get_text().split("/")[0].strip().split(" ")[1]
        leasable: bool = True

        # 取得坪數和樓層
        item_style_text = i_kind.find_next()
        if "坪" in item_style_text.get_text():
            size = float(item_style_text.get_text().split("坪")[0])
            floor = item_style_text.find_next().get_text()
        else:
            size = float(item_style_text.find_next().get_text().split("坪")[0])
            floor = item_style_text.find_next().find_next().get_text()

        is_now = datetime.now()
        updated = item.find('div', class_='item-msg').get_text().split("/")[1]  # 取得更新時間字串
        update_time_num: int = int("".join(re.findall(r'\d+', updated)))  # 從字串取得更新時間數字
        if "天" in updated:
            post_update = (is_now - timedelta(days=update_time_num)).strftime("%Y-%m-%d")
        elif "小時" in updated:
            post_update = (is_now - timedelta(hours=update_time_num)).strftime("%Y-%m-%d")
        else:
            post_update = (is_now - timedelta(minutes=update_time_num)).strftime("%Y-%m-%d")

        yield item_schemas.PostBase(title=title, size=size, floor=floor, address=address,
                                    post_update=post_update, rent=rent, url=url,
                                    contact=contact,
                                    poster=poster, leasable=leasable,
                                    crawler_update=is_now)


# 爬591
def get_lease_data(region: int, start_page: int = 0, end_page: int = None):  # 地區1為台北，3為新北  # pages為要爬頁數，0為全部
    source: str = "591租屋"
    area_dict = {1: "台北市", 3: "新北市"}
    area = area_dict[region]
    url_591 = "https://rent.591.com.tw/?region={}&firstRow={}".format(region, start_page * 30)

    driver = driver_handler.set_driver(url=url_591, source="591")
    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "section.vue-list-rent-item"))
    )
    res = driver.page_source
    soup = BeautifulSoup(res, 'html.parser')

    rows: int = int(soup.select('div.list-container-content > div > section.vue-list-rent-sort > div > div > span')[
                        0].get_text().replace(",", "")) - start_page * 30  # 取得總筆數 - 開始筆數
    if end_page is None:
        total_pages = math.ceil(rows / 30)  # 除以每頁30筆，無條件進位
        print(f'共{rows}筆')
    else:
        total_pages = end_page

    for current_page in range(total_pages):
        log_start = datetime.now()  # 紀錄開始時間
        page_num = current_page + 1  # 紀錄頁數
        error_message = "爬蟲完成"
        log_status = "Done"
        item_count = 0
        try:
            if total_pages > current_page > 0:
                button_click(driver)
            items = parse_page(page_source=driver.page_source)
            for item in items:
                item.area = area
                item.source = source
                posts_crud.create_or_update(db=driver_handler.db, item=item)  # 寫入資料庫
                item_count += 1
        except Exception as e:
            log_status = e.__class__.__name__
            error_message = e.__str__()

        finally:
            log_end = datetime.now()
            logs_crud.write_log(db=driver_handler.db,
                                log=item_schemas.WriteLogData(start_time=log_start, end_time=log_end, status=log_status,
                                                              source=source,
                                                              area=area, page_num=page_num, error_message=error_message,
                                                              count=item_count))


if __name__ == '__main__':
    get_lease_data(region=1, start_page=0, end_page=3)
    posts_crud.check_leasable(driver_handler.db)
