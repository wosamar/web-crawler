from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import update
from typing import List
from sql_app import models, schemas


# 取得主頁查詢貼文資料
def select_posts(db: Session, offset: int, limit: int, **condition) -> List[dict]:
    condition = {k: v for k, v in condition.items() if v}

    return db.query(models.LeaseData).order_by(models.LeaseData.post_update).filter_by(**condition).offset(
        offset).limit(limit).all()


# 取得指定ID詳細資料
def get_post(db: Session, post_id: int):
    return db.query(models.LeaseData).filter(models.LeaseData.id == post_id).first()


# 回傳指定條件下的統計資訊(資料筆數)
def count_posts(db: Session, area=None, lower_rent=None, upper_rent=None, from_update=None, end_update=None) -> int:
    query = db.query(models.LeaseData)
    if area:
        query = query.filter(models.LeaseData.area == area)
    if lower_rent:
        query = query.filter(lower_rent <= models.LeaseData.rent)
    if upper_rent:
        query = query.filter(models.LeaseData.rent <= upper_rent)
    if from_update:
        query = query.filter(from_update <= models.LeaseData.post_update)
    if end_update:
        query = query.filter(models.LeaseData.post_update <= end_update)
    return query.count()


# 判斷新增或修改
def create_or_update(db: Session, item: schemas.PostBase):
    result = db.query(models.LeaseData).filter(models.LeaseData.url == item.url).first()
    if result:
        update_data_by_url(db=db, item=schemas.PostUpdate(**item.dict()))
    else:
        create_post(db=db, item=schemas.PostCreate(**item.dict()))


def create_post(db: Session, item: schemas.PostCreate | schemas.PostCreateFromAPI):
    db_item = models.LeaseData(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return schemas.PostInDatabase(**db_item.__dict__)


def update_data_by_url(db: Session, item: schemas.PostUpdate):
    item = item.dict(exclude_none=True)
    db.execute(update(models.LeaseData).filter(models.LeaseData.url == item["url"]).values(**item))
    db.commit()


# 從爬蟲時間判斷租賃狀況
def check_leasable(db: Session):
    time_now = datetime.now() - timedelta(hours=2)
    db.execute(update(models.LeaseData).filter(models.LeaseData.crawler_update <= time_now).values(
        {models.LeaseData.leasable: 0}))
    db.commit()


def update_data_by_id(db: Session, item: schemas.PostUpdateFromAPI):
    item = item.dict(exclude_none=True)
    db.execute(update(models.LeaseData).filter(models.LeaseData.id == item['id']).values(**item))
    db.commit()
    return get_post(db=db, post_id=item['id'])


# 刪除資料
def delete_data(db: Session, item_id: int):
    db.query(models.LeaseData).filter(models.LeaseData.id == item_id).delete()
    db.commit()


if __name__ == '__main__':
    pass
