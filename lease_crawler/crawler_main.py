from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as BS
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from datetime import datetime, timedelta
import logging
import math
import time
import re
from SqlAlchemy_data.database_CRUD import *

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'}


# 爬591
def get_lease_data_591(region: int):  # 1為台北，3為新北
    # 從地區建立url
    main_url_591 = "https://rent.591.com.tw/?region={}".format(region)

    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get(main_url_591)
    print("591 loading...")
    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "section.vue-list-rent-item"))
    )

    # 取得總頁數
    res = driver.page_source
    soup = BS(res, 'html.parser')
    rows: int = int(soup.select('div.list-container-content > div > section.vue-list-rent-sort > div > div > span')[
                        0].get_text().replace(",", ""))
    print(f'共{rows}筆')
    do_next = math.ceil(rows / 30)  # 除以每頁筆數，無條件進位

    try:
        for page in range(3):  # 放進do_next
            print(f'=====第{page + 1}頁=====')
            res = driver.page_source
            soup = BS(res, 'html.parser')
            urls = soup.select('section[class="vue-list-rent-item"]')
            for i in urls:
                # 判斷租房類型
                i_kind = i.find('ul', class_='item-style').li
                if i_kind.get_text() == "車位":  # 類型為車位不輸出
                    print("此筆資料為車位")
                    print('==========')
                    continue
                else:
                    pass

                # 取得參數
                url: str = i.a['href']
                title: str = i.a.find('div', class_='item-title').get_text().replace("優選好屋", "").strip()

                size: float = 0
                floor: str = ""
                address = i.find('div', class_='item-area').span.get_text()
                update = None  # 日期格式
                rent: int = int(i.find('div', class_='item-price-text').span.get_text().replace(",", ""))
                contact: str = i.find('div', class_='item-msg').get_text().split("/")[0].strip().split(" ")[0]
                poster: str = i.find('div', class_='item-msg').get_text().split("/")[0].strip().split(" ")[1]
                area: str = ""
                leased: bool = True
                source: str = "591租屋"

                # 判斷區域
                re_area = lambda x: "台北市" if x == 1 else "新北市"
                area = re_area(region)

                # 取得坪數
                item_style_text = i_kind.find_next()
                if "坪" in item_style_text.get_text():
                    size = float(item_style_text.get_text().split("坪")[0])
                    floor = item_style_text.find_next().get_text()
                else:
                    size = float(item_style_text.find_next().get_text().split("坪")[0])
                    floor = item_style_text.find_next().find_next().get_text()

                # 取得更新日期
                is_now: datetime = datetime.now()  # 取得現在時間
                updated = i.find('div', class_='item-msg').get_text().split("/")[1]  # 取得更新時間字串
                update_time_num: int = int("".join(re.findall(r'\d+', updated)))  # 取得更新時間數字
                if "天" in updated:
                    update = (is_now - timedelta(days=update_time_num)).strftime("%Y-%m-%d")
                elif "小時" in updated:
                    update = (is_now - timedelta(hours=update_time_num)).strftime("%Y-%m-%d")
                else:
                    update = (is_now - timedelta(minutes=update_time_num)).strftime("%Y-%m-%d")

                # 如果地址要取前面那項的話
                # try:
                #     address = i.find('div', class_='item-area').a.get_text()
                # except AttributeError:
                #     address = i.find('div', class_='item-area').span.get_text()
                #     pass

                # 寫入資料庫
                datas = {
                    "title": title,
                    "size": size,
                    "floor": floor,
                    "address": address,
                    "update": update,
                    "rent": rent,
                    "url": url,
                    "contact": contact,
                    "poster": poster,
                    "area": area,
                    "leased": leased,
                    "source": source,
                }
                create_data(datas)

                print(
                    '標題：{}\n地區：{}\n地址：{}\n坪數：{}坪\n樓層：{}\n租金：{}元\n聯絡人：{}\n發文者：{}\n更新時間：{}\n網址：{}'.format(
                        title, area,
                        address, size,
                        floor, rent, contact,
                        poster, update,
                        url))
                print('==========')
            # 到下一頁
            button = driver.find_element(By.CLASS_NAME, "pageNext")
            button.click()
            WebDriverWait(driver, 10).until(
                expected_conditions.invisibility_of_element((By.CSS_SELECTOR, "div#j-loading"))
            )

    except AttributeError as e:
        print(e.args)
        print('==========')


# 爬好房網
def get_lease_data_housefun(region: int):
    if region == 1:  # 台北市
        reg_text = "%E5%8F%B0%E5%8C%97%E5%B8%82"
    elif region == 3:  # 新北市
        reg_text = "%E6%96%B0%E5%8C%97%E5%B8%82"
    else:
        logging.debug('參數輸入錯誤')
        return
    main_url_hf = "https://rent.housefun.com.tw/region/{}".format(reg_text)

    options = webdriver.ChromeOptions()
    prefs = {'profile.default_content_setting_values': {'notifications': 2}}  # 關通知
    options.add_experimental_option('prefs', prefs)

    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    driver.get(main_url_hf)
    print("housefun loading...")
    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "article.DataList"))
    )
    res = driver.page_source
    soup = BS(res, 'html.parser')
    pages: int = int(soup.select('#PageCount')[0].get_text().split("/")[1])
    print(f'共{pages}頁')  # 每頁為十筆
    try:
        for page in range(5):  # 放進pages
            print(f'=====第{page + 1}頁=====')

            res = driver.page_source
            soup = BS(res, 'html.parser')
            urls = soup.select('article[class="DataList both"]')
            for i in urls:
                # 取得文章網址和標題
                url: str = "https://rent.housefun.com.tw" + i.a['href']
                title: str = i.a['title']

                # 判斷租房類型
                house_type = True
                if "停車" in title:  # 類型為車位不輸出
                    house_type = False
                    # return house_type
                    print("此筆資料為車位")
                    print('==========')
                    continue
                else:
                    pass

                # 取得參數
                size: float = float(i.find('span', class_='infos').find_next().get_text().split(" ")[2])
                floor: str = i.find('span', class_='pattern').get_text().split("：")[1]
                address: str = i.address.get_text()
                update = None  # 日期格式
                rent: int = int(i.select('div.info > ul > li:nth-child(1) > span.infos.num')[0].get_text().split(" ")[
                                    0].replace(",", ""))
                contact: str = i.select('div.info > ul > li:nth-child(3) > span')[0].get_text().split("：")[0]
                poster: str = i.select('div.info > ul > li:nth-child(3) > span')[0].get_text().split("：")[1]
                area: str = ""
                leased: bool = True
                source: str = "好房網"

                # 判斷區域
                re_area = lambda x: "台北市" if x == 1 else "新北市"
                area = re_area(region)

                # 日期
                is_now: datetime = datetime.now()  # 取得現在時間
                updated = i.find('li', class_='InfoList num').span.find_next().get_text()
                update_time_num: int = int("".join(re.findall(r'\d+', updated)))
                if "天" in updated:
                    update = (is_now - timedelta(days=update_time_num)).strftime("%Y-%m-%d")
                elif "小時" in updated:
                    update = (is_now - timedelta(days=update_time_num)).strftime("%Y-%m-%d")
                else:
                    update = (is_now - timedelta(days=update_time_num)).strftime("%Y-%m-%d")

                datas = {
                    "title": title,
                    "size": size,
                    "floor": floor,
                    "address": address,
                    "update": update,
                    "rent": rent,
                    "url": url,
                    "contact": contact,
                    "poster": poster,
                    "area": area,
                    "leased": leased,
                    "source": source,
                }
                create_data(datas)

                print(
                    '標題:{}\n地區：{}\n地址：{}\n坪數：{}坪\n樓層：{}\n租金：{}元\n聯絡人：{}\n發文者：{}\n更新時間：{}\n網址：{}'.format(
                        title, area,
                        address, size,
                        floor, rent, contact,
                        poster, update, url))
                print('==========')

            # 到下一頁
            button = driver.find_elements(By.CSS_SELECTOR, "li.has-arrow")[-1].find_element(By.CSS_SELECTOR, "a")
            driver.execute_script("(arguments[0].click());", button)
            WebDriverWait(driver, 10).until(
                expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "article.DataList"))
            )

    except AttributeError as e:
        print('==========')
        print(e.args)
        print('==========')


#
if __name__ == '__main__':
    get_lease_data_591(3)
    # get_lease_data_housefun(3)
