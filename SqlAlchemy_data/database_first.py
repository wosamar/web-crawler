from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column
from sqlalchemy import Integer, String, DATE, Boolean, Float, DATETIME
from sqlalchemy.orm import sessionmaker

# 初始化
engine_url = "mysql+pymysql://root:eland1234@10.10.10.55:3306/my_database"
engine = create_engine(engine_url, echo=True)  # echo將執行過程輸出到 terminal
Base = declarative_base()  # Base class


# 資料表結構
class LeaseData(Base):
    __tablename__ = "lease_data"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(30))  # 標題名稱
    size = Column(Float)  # 坪數
    floor = Column(String(10))  # 樓層
    address = Column(String(55))  # 房屋地址
    update = Column(DATE)  # 更新時間
    rent = Column(Integer)  # 每月租金
    url = Column(String(55))  # 文章連結
    contact = Column(String(10))  # 聯絡人
    poster = Column(String(10))  # 發文者
    area = Column(String(3))  # 地區
    leased = Column(Boolean)  # 是否可以被租賃
    source = Column(String(5))  # 資料來源網站or手動新增


class LogData(Base):
    __tablename__ = "log_data"
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DATETIME)
    level = Column(String(8))
    message = Column(String(55))
    course = Column(String(20))  # 產生訊息的功能 爬蟲/API/資料庫原因


# 建立及刪除table
def create_table():
    Base.metadata.create_all(engine)


def drop_table():
    Base.metadata.drop_all(engine)


# 操作實體
def create_session():
    session = sessionmaker(bind=engine)
    session = session()

    return session


# 作為主程式運行時清空資料庫
if __name__ == '__main__':
    drop_table()
    create_table()
