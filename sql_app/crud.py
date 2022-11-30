from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sql_app.database import *
from sqlalchemy import update, and_
from typing import List
from . import models, schemas


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 取得主頁貼文資料
# def get_posts(db: Session, offset: int, limit: int) -> List[dict]:
#     return db.query(models.LeaseData).order_by(models.LeaseData.post_update).offset(offset).limit(limit).all()


# 取得主頁查詢貼文資料
def select_posts(db: Session, offset: int, limit: int, condition: schemas.SelectPosts = None) -> List[dict]:
    condition = condition.dict(exclude_none=True)
    condition = {k: v for k, v in condition.items() if v != ''}

    return db.query(models.LeaseData).order_by(models.LeaseData.post_update).filter_by(**condition).offset(
        offset).limit(limit).all()


# 取得指定ID詳細資料
def get_post(db: Session, post_id: int):
    return db.query(models.LeaseData).filter(models.LeaseData.id == post_id).first()


# 回傳指定條件下的統計資訊(資料筆數)
def count_posts(db: Session, condition: schemas.GetStatistics) -> int:
    condition = condition.dict(exclude_none=True)  # 排除為None的項目
    query = db.query(models.LeaseData)
    if "area" in condition:
        query = query.filter(models.LeaseData.area == condition["area"])
    if "lower_rent" in condition:
        query = query.filter(condition["lower_rent"] <= models.LeaseData.rent)
    if "upper_rent" in condition:
        query = query.filter(models.LeaseData.rent <= condition["upper_rent"])
    if "from_update" in condition:
        query = query.filter(condition["from_update"] <= models.LeaseData.post_update)
    if "end_update" in condition:
        query = query.filter(models.LeaseData.post_update <= condition["end_update"])
    return query.count()


# 判斷新增或修改
def create_or_update(db: Session, item: schemas.PostCreateOrUpdate):
    result = db.query(models.LeaseData).filter(models.LeaseData.url == item.url).first()
    if result:
        update_data(db=db, item=schemas.PostUpdate(**item.dict()))
    else:
        create_post(db=db, item=schemas.PostCreate(**item.dict()))


# 新增資料
def create_post(db: Session, item: schemas.PostCreate):
    db_item = models.LeaseData(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return schemas.Post(**db_item.__dict__)


# 更新(修改)資料
def update_data(db: Session, item: schemas.PostUpdate):
    try:
        db.execute(update(models.LeaseData).filter(models.LeaseData.url == item.url).values(**item.dict()))
        db.commit()
    except Exception as e:
        print(e.__class__.__name__)
        print(str(e))


# 爬蟲更新租賃狀況
def check_leasable(db: Session):
    time_now = datetime.now() - timedelta(hours=2)
    db.execute(update(models.LeaseData).filter(models.LeaseData.crawler_update <= time_now).values(
        {models.LeaseData.leasable: 0}))
    db.commit()


# API更新資料
def api_update_data(db: Session, item: schemas.APIUpdatePost):
    item = item.dict(exclude_none=True)
    db.execute(update(models.LeaseData).filter(models.LeaseData.id == item['id']).values(**item))
    db.commit()
    return get_post(db=db, post_id=item['id'])


# 刪除資料
def delete_data(db: Session, item_id: int):
    db.query(models.LeaseData).filter(models.LeaseData.id == item_id).delete()
    db.commit()

# 寫log
def write_log(db: Session, log: schemas.WriteLogData):
    db_item = models.LogData(**log.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)


if __name__ == '__main__':
    pass
