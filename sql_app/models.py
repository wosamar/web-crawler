from sqlalchemy.dialects.mysql import TEXT
from .database import Base
from sqlalchemy import Column, Integer, String, DATE, Boolean, Float, DATETIME


# 資料表結構
class LeaseData(Base):
    __tablename__ = "lease_data"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255))  # 標題名稱
    size = Column(Float)  # 坪數
    floor = Column(String(20))  # 樓層
    address = Column(String(55))  # 房屋地址
    post_update = Column(DATE)  # 更新時間
    rent = Column(Integer)  # 每月租金
    url = Column(String(255))  # 文章連結
    contact = Column(String(10))  # 聯絡人
    poster = Column(String(30))  # 發文者
    area = Column(String(5))  # 地區
    leasable = Column(Boolean)  # 是否可以被租賃
    source = Column(String(5))  # 資料來源網站or手動新增
    crawler_update = Column(DATETIME)  # 最後一次爬到的時間



class LogData(Base):
    __tablename__ = "log_data"
    id = Column(Integer, primary_key=True, autoincrement=True)
    start_time = Column(DATETIME)
    end_time = Column(DATETIME)
    status = Column(String(55))
    source = Column(String(10))
    area = Column(String(5))
    page_num = Column(Integer)  # 第幾頁
    count = Column(Integer)  # 本頁爬到筆數
    error_message = Column(TEXT)  #失敗訊息