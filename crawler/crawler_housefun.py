from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as BS
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
import re
from crawler import set_driver as sd
from sql_app.crud import posts as posts_crud, logs as logs_crud
from sql_app import schemas as item_schemas

def button_click(driver):
    button = driver.find_elements(By.CSS_SELECTOR, "li.has-arrow")[-1].find_element(By.CSS_SELECTOR, "a")
    driver.execute_script("(arguments[0].click());", button)
    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "article.DataList"))
    )


def parse_page(page_source):
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

        yield item_schemas.PostCreateOrUpdate(title=title, size=size, floor=floor, address=address,
                                              post_update=post_update, rent=rent, url=url,
                                              contact=contact,
                                              poster=poster, leasable=leasable,
                                              crawler_update=is_now)


# 爬好房網
def get_lease_data(region: int, end_page: int = None):
    source: str = "好房網"

    # 判斷地區
    if region == 1:  # 台北市
        area = "台北市"
        reg_text = "%E5%8F%B0%E5%8C%97%E5%B8%82"
    elif region == 3:  # 新北市
        area = "新北市"
        reg_text = "%E6%96%B0%E5%8C%97%E5%B8%82"
    else:
        print('區域參數輸入錯誤')
        return
    url_hf = "https://rent.housefun.com.tw/region/{}".format(reg_text)

    driver = sd.set_driver(url=url_hf, source="housefun")
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
                button_click(driver)
            items = parse_page(page_source=driver.page_source)
            for item in items:
                item.area = area
                item.source = source
                posts_crud.create_or_update(db=sd.db, item=item)  # 寫入資料庫
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
            logs_crud.write_log(db=sd.db,
                                log=item_schemas.WriteLogData(start_time=log_start, end_time=log_end, status=log_status,
                                                              source=source,
                                                              area=area, page_num=page_num, error_message=error_message,
                                                              count=item_count))

if __name__ == '__main__':
    get_lease_data(region=1, end_page=3)
    posts_crud.check_leasable(sd.db)