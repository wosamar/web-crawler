import schedule
import time
from lease_crawler.crawler_main import get_lease_data_591, get_lease_data_housefun
from sql_app.crud import *


def schedule_start():
    db = next(get_db())
    try:
        schedule.every().hour.at(":02").do(get_lease_data_591, region=1, start_page=0, end_page=None)
        schedule.every().hour.at(":02").do(get_lease_data_591, region=3, start_page=0, end_page=None)

        schedule.every().hour.at(":02").do(get_lease_data_housefun, region=1, end_page=None)
        schedule.every().hour.at(":02").do(get_lease_data_housefun, region=3, end_page=None)
        check_leasable(db)
    except Exception as e:
        print(e.__str__())

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    schedule_start()
