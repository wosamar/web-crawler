from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as BS
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
import math
import re
from sql_app.crud import *

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'}
db = next(get_db())


# 檢查是否跳出alert
def call(driver):
    alert = driver.switch_to.alert
    alert.accept()
    driver.get(driver.current_url)
    print("此頁請求超時")
    return driver


# 到下一頁
def button_click_591(driver):
    button = driver.find_element(By.CLASS_NAME, "pageNext")
    driver.execute_script("(arguments[0].click());", button)
    try:
        driver = call(driver)
    except Exception as e:
        pass
    WebDriverWait(driver, 10).until(
        expected_conditions.invisibility_of_element((By.CSS_SELECTOR, "div#j-loading"))
    )


def parse_591_page(page_source):
    soup = BS(page_source, 'html.parser')
    items = soup.select('section[class="vue-list-rent-item"]')# 找到貼文欄位

    for item in items:
        i_kind = item.find('ul', class_='item-style').li  # 判斷租房類型
        if i_kind.get_text() == "車位":  # 類型為車位不輸出
            # print("此筆資料為車位")
            # print('==========')
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

        is_now = datetime.now()  # 取得現在時間
        updated = item.find('div', class_='item-msg').get_text().split("/")[1]  # 取得更新時間字串
        update_time_num: int = int("".join(re.findall(r'\d+', updated)))  # 從字串取得更新時間數字
        if "天" in updated:
            post_update = (is_now - timedelta(days=update_time_num)).strftime("%Y-%m-%d")
        elif "小時" in updated:
            post_update = (is_now - timedelta(hours=update_time_num)).strftime("%Y-%m-%d")
        else:
            post_update = (is_now - timedelta(minutes=update_time_num)).strftime("%Y-%m-%d")

        yield schemas.PostCreateOrUpdate(title=title, size=size, floor=floor, address=address,
                                         post_update=post_update, rent=rent, url=url,
                                         contact=contact,
                                         poster=poster, leasable=leasable,
                                         crawler_update=is_now)

        # print(
        #     '標題：{}\n地區：{}\n地址：{}\n坪數：{}坪\n樓層：{}\n租金：{}元\n聯絡人：{}\n發文者：{}\n更新時間：{}\n網址：{}'.format(
        #         title, area,
        #         address, size,
        #         floor, rent, contact,
        #         poster, post_update,
        #         url))
        # print('==========')


# 爬591
def get_lease_data_591(region: int, start_page: int = 0, end_page: int = None):  # 地區1為台北，3為新北  # pages為要爬頁數，0為全部
    source: str = "591租屋"
    # 判斷區域
    re_area = lambda x: "台北市" if x == 1 else "新北市"
    area = re_area(region)

    # 建立url
    main_url_591 = "https://rent.591.com.tw/?region={}&firstRow={}".format(region, start_page * 30)

    # 下載driver&讀取頁面
    options = webdriver.ChromeOptions().add_argument('--headless')
    driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)
    driver.get(main_url_591)
    print("591 loading...")
    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "section.vue-list-rent-item"))
    )
    res = driver.page_source
    soup = BS(res, 'html.parser')

    rows: int = int(soup.select('div.list-container-content > div > section.vue-list-rent-sort > div > div > span')[
                        0].get_text().replace(",", "")) - start_page  # 取得總筆數 - 開始筆數
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
                button_click_591(driver)
            items = parse_591_page(page_source=driver.page_source)
            for item in items:
                item.area = area
                item.source = source
                create_or_update(db=db, item=item)  # 寫入資料庫
                item_count += 1
        except AttributeError as e:
            log_status = "AttributeError"
            error_message = e.__str__()

        except ValueError as e:
            log_status = "ValueError"
            error_message = e.__str__()

        except RuntimeError as e:
            log_status = "RuntimeError"
            error_message = e.__str__()

        except Exception as e:
            log_status = "ExceptionError"
            error_message = e.__str__()

        finally:
            log_end = datetime.now()
            write_log(db=db,
                      log=schemas.WriteLogData(start_time=log_start, end_time=log_end, status=log_status, source=source,
                                               area=area, page_num=page_num, error_message=error_message,
                                               count=item_count))


def button_click_housefun(driver):
    button = driver.find_elements(By.CSS_SELECTOR, "li.has-arrow")[-1].find_element(By.CSS_SELECTOR, "a")
    driver.execute_script("(arguments[0].click());", button)
    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "article.DataList"))
    )


def parse_housefun(page_source):
    soup = BS(page_source, 'html.parser')
    urls = soup.select('article[class="DataList both"]')
    for i in urls:
        # 取得文章網址和標題
        url: str = "https://rent.housefun.com.tw" + i.a['href']
        title: str = i.a['title']
        # 取得參數
        size: float = float(i.find('span', class_='infos').find_next().get_text().split(" ")[2])
        floor: str = i.find('span', class_='pattern').get_text().split("：")[1]
        address: str = i.address.get_text()
        rent: int = int(i.select('div.info > ul > li:nth-child(1) > span.infos.num')[0].get_text().split(" ")[
                            0].replace(",", ""))
        contact: str = i.select('div.info > ul > li:nth-child(3) > span')[0].get_text().split("：")[0]
        poster: str = i.select('div.info > ul > li:nth-child(3) > span')[0].get_text().split("：")[1]
        leasable: bool = True
        source: str = "好房網"

        # 日期
        is_now = datetime.now()  # 取得現在時間
        updated = i.find('li', class_='InfoList num').span.find_next().get_text()
        update_time_num: int = int("".join(re.findall(r'\d+', updated)))
        if "天" in updated:
            post_update = (is_now - timedelta(days=update_time_num)).strftime("%Y-%m-%d")
        elif "小時" in updated:
            post_update = (is_now - timedelta(days=update_time_num)).strftime("%Y-%m-%d")
        else:
            post_update = (is_now - timedelta(days=update_time_num)).strftime("%Y-%m-%d")

        # print(
        #     '標題:{}\n地區：{}\n地址：{}\n坪數：{}坪\n樓層：{}\n租金：{}元\n聯絡人：{}\n發文者：{}\n更新時間：{}\n網址：{}'.format(
        #         title, area,
        #         address, size,
        #         floor, rent, contact,
        #         poster, post_update, url))
        # print('==========')
        yield schemas.PostCreateOrUpdate(title=title, size=size, floor=floor, address=address,
                                         post_update=post_update, rent=rent, url=url,
                                         contact=contact,
                                         poster=poster, leasable=leasable,
                                         crawler_update=is_now)


# 爬好房網
def get_lease_data_housefun(region: int, first_row: int = 0, end_page: int = None):
    source: str = "好房網"

    # 判斷地區，建立URL
    if region == 1:  # 台北市
        area = "台北市"
        reg_text = "%E5%8F%B0%E5%8C%97%E5%B8%82"
    elif region == 3:  # 新北市
        area = "新北市"
        reg_text = "%E6%96%B0%E5%8C%97%E5%B8%82"
    else:
        print('區域參數輸入錯誤')
        return
    main_url_hf = "https://rent.housefun.com.tw/region/{}".format(reg_text)

    options = webdriver.ChromeOptions().add_argument('--headless')

    driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)
    driver.get(main_url_hf)
    print("housefun loading...")
    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "article.DataList"))
    )
    res = driver.page_source
    soup = BS(res, 'html.parser')
    if end_page is None:
        total_pages: int = int(soup.select('#PageCount')[0].get_text().split("/")[1])
        print(f'共{total_pages}頁')  # 每頁為十筆
    else:
        total_pages = end_page

    for current_page in range(total_pages):  # 放進pages
        page_num = current_page + 1  # 紀錄頁數
        item_count = 0
        log_start = datetime.now()  # 紀錄開始時間
        error_message = "爬蟲完成"
        log_status = "Done"
        try:
            if total_pages > current_page > 0:
                button_click_housefun(driver)
            items = parse_housefun(page_source=driver.page_source)
            for item in items:
                item.area = area
                item.source = source
                create_or_update(db=db, item=item)  # 寫入資料庫
                item_count += 1


        except AttributeError as e:
            log_status = "AttributeError"
            error_message = e.__str__()

        except ValueError as e:
            log_status = "ValueError"
            error_message = e.__str__()

        except RuntimeError as e:
            log_status = "RuntimeError"
            error_message = e.__str__()

        except Exception as e:
            log_status = "ExceptionError"
            error_message = e.__str__()

        finally:
            log_end = datetime.now()
            write_log(db=db,
                      log=schemas.WriteLogData(start_time=log_start, end_time=log_end, status=log_status, source=source,
                                               area=area, page_num=page_num, error_message=error_message,
                                               count=item_count))


if __name__ == '__main__':
    get_lease_data_591(region=1, start_page=0, end_page=None)
    # get_lease_data_housefun(region=3, end_page=None)
    check_leasable(db)
