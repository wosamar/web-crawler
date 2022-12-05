import schedule
import time
from crawler import crawler_591,crawler_housefun
from sql_app.crud.posts import check_leasable
from sql_app.db_utils import get_db


def schedule_start(start_time):
    db = next(get_db())
    schedule.every().hour.at(f":{start_time}").do(crawler_591.get_lease_data, region=1, start_page=0, end_page=None)
    schedule.every().hour.at(f":{start_time}").do(crawler_591.get_lease_data, region=3, start_page=0, end_page=None)

    schedule.every().hour.at(f":{start_time}").do(crawler_housefun.get_lease_data, region=1, end_page=None)
    schedule.every().hour.at(f":{start_time}").do(crawler_housefun.get_lease_data, region=3, end_page=None)
    check_leasable(db)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    schedule_start(00)
