from database_first import create_session
from database_first import LeaseData
import datetime

session = create_session()

# 插入單筆資料
datas = {
    "name": "hey",
    "time": datetime.datetime.now(),
    "old": "13"
}

def create_data(data):
    try:
        session.add(LeaseData(**data))
        session.commit()
    except Exception as e:
        print(e.__class__.__name__)
        print(str(e))
    finally:
        session.close()

create_data(datas)


# 插入多筆資料
# datas_2 = [
#     Test(name="nick", time=datetime.datetime.now()),
#     Test(name="honey", time=datetime.datetime.now())
# ]
#
# try:
#     session.add_all(datas_2)
#     session.commit()
# except Exception as e:
#     print(e.__class__.__name__)
#     print(str(e))
# finally:
#     session.close()
#
# # 修改資料
# datas_3 = {"name": "andy"}
#
# try:
#     session.query(Test).filter_by(id=1).update(datas_3)
#     session.commit()
# except Exception as e:
#     print(e.__class__.__name__)
#     print(str(e))
# finally:
#     session.close()
#
# # 刪除資料
# try:
#     session.query(Test).filter_by(id=1).delete()
#     session.commit()
# except Exception as e:
#     print(e.__class__.__name__)
#     print(str(e))
# finally:
#     session.close()
