from SqlAlchemy_data.database_first import *
from sqlalchemy import update
from typing import List

# 初始化
engine_url = "mysql+pymysql://root:eland1234@10.10.10.55:3306/my_database"
engine = create_engine(engine_url)  # echo將執行過程輸出到 terminal
Base = declarative_base()  # Base class

session = create_session()

# 取得資料回傳網頁
def get_posts_data(offset: int, limit: int, condition: dict) -> List[dict]:  # 如果有條件回傳查詢，沒有條件回傳全部資料
    clean_condition = {}  # 取得有值的key
    for con_key, con_value in condition.items():
        if con_value:
            clean_condition.setdefault(con_key,con_value)

    if condition:
        results = session.query(LeaseData).order_by(LeaseData.update).filter_by(**clean_condition).offset(offset).limit(
            limit).all()
    else:
        results = session.query(LeaseData).order_by(LeaseData.update).offset(offset).limit(limit).all()
    return [result.__dict__ for result in results]

# 回傳指定條件下的統計資訊
def count_posts_data(condition:dict) -> int:
    clean_condition = {}  # 取得有值的key
    for con_key, con_value in condition.items():
        if con_value:
            clean_condition.setdefault(con_key,con_value)

    if condition:
        count_result = session.query(LeaseData).order_by(LeaseData.update).filter_by(**clean_condition).count()
    else:
        count_result = session.query(LeaseData).order_by(LeaseData.update).count()
    return count_result


# 新增
def create_data(condition: dict):
    result = session.query(LeaseData).filter_by(url=condition["url"]).first()  # 比對是否有相同url
    if result:
        update_data(condition)
    else:
        try:
            session.add(LeaseData(**condition))
            session.commit()
        except Exception as e:
            print(e.__class__.__name__)
            print(str(e))
        finally:
            session.close()


# 查詢
def select_lease_data(condition: dict) -> dict:
    try:
        result = session.query(LeaseData).filter_by(**condition).first()  # 從任何資料查id
        return result

    except Exception as e:
        print(e.__class__.__name__)
        print(str(e))
        return False
    finally:
        session.close()


# 修改
def update_data(condition: dict):  # 修改時傳入整筆資料？
    try:
        session.execute(update(LeaseData).filter_by(url=condition["url"]).values(**condition))
        # session.query(LeaseData).filter_by(url=condition["url"]).update(**condition)
        session.commit()
    except Exception as e:
        print(e.__class__.__name__)
        print(str(e))
    finally:
        session.close()


# 刪除
def delete_data(item_id: int):
    try:
        session.query(LeaseData).filter_by(id=item_id).delete()
        session.commit()
    except Exception as e:
        print(e.__class__.__name__)
        print(str(e))
    finally:
        session.close()


# 從API查詢 #檢查項目
# 塞進JSON pydantic


if __name__ == '__main__':
    # drop_table()
    # create_table()
    # delete_data("https://rent.591.com.tw/rent-detail-13570951.html")
    get_posts_data(0)
