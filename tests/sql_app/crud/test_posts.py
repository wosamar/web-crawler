from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sql_app import models, schemas
from sql_app.crud import posts as posts_crud


def test_set_post_filters(db: Session, creat_data):
    query = db.query(models.LeaseData)
    query = posts_crud.set_post_filters(query=query, area="台北市")
    result = query.order_by(models.LeaseData.post_update).first()

    assert result


def test_select_posts(db: Session, creat_data):
    offset = 0
    limit = 50
    condition = {}
    condition.update(leasable=True, poster="user")
    result = posts_crud.select_posts(db=db, offset=offset, limit=limit, **condition)

    item = result[0]
    print(item.__dict__)
    assert item.__dict__["title"] == creat_data.title


def test_get_post(db: Session, creat_data):
    result = posts_crud.get_post(db=db, post_id=creat_data.id)

    print(result.__dict__)
    assert result.title == creat_data.title


def test_count_posts(db: Session, creat_data):
    condition = {}
    condition.update(area="台北市", upper_rent=5000, from_update="2022-11-01")
    result = posts_crud.count_posts(db=db, **condition)

    print(f"result:{result}")
    assert result == 1


def test_create_or_update(db: Session):
    # 新增資料
    item = schemas.PostBase(title="標題名稱", size=5, floor="1 / 12", address="應為新增",
                            post_update="2022-11-28", rent=10000, url="https://pytest.com.tw/",
                            contact="聯絡人欄位", poster="user", leasable=True,
                            crawler_update="2023-12-30 10:10:00")
    result = posts_crud.create_or_update(db=db, item=item)
    assert result is None

    result = db.query(models.LeaseData).filter(models.LeaseData.url == item.url).first()
    print(result.__dict__)
    assert result.title == item.title
    assert result.poster == item.poster

    # 修改資料
    item = schemas.PostBase(title="new_標題名稱", size=5, floor="2 / 12", address="應為修改",
                            post_update="2022-11-28", rent=10000, url="https://pytest.com.tw/",
                            contact="聯絡人欄位", poster="user", leasable=True,
                            crawler_update="2023-12-30 10:10:00")
    result = posts_crud.create_or_update(db=db, item=item)
    assert result is None

    result = db.query(models.LeaseData).filter(models.LeaseData.url == item.url).first()
    print(result.__dict__)
    assert result.title == item.title
    assert result.address == item.address


def test_create_post(db: Session):
    item = schemas.PostCreate(title="測試用標題", size=3, floor="3 / 12", address="台北市大安區",
                              post_update="2022-11-28", rent=10000, url="https://sql.com.tw/",
                              contact="聯絡人欄位", poster="user", leasable=True,
                              crawler_update="2023-12-30 10:10:00")
    result: schemas.PostInDatabase = posts_crud.create_post(db=db, item=item)
    print(result.__dict__)

    assert result.title == item.title


def test_update_data_by_url(db: Session, creat_data):
    item = schemas.PostUpdate(title="更新後標題", contact="更新後聯絡人", url="https://fixture.com.tw/")
    result = posts_crud.update_data_by_url(db=db, item=item)

    assert result is None

    result = db.query(models.LeaseData).filter(models.LeaseData.url == item.url).first()
    print(result.__dict__)

    assert result.title == item.title
    assert result.poster == creat_data.poster


def test_check_leasable(db: Session, creat_data):
    result = posts_crud.check_leasable(db=db)
    assert result is None

    time_now = datetime.now() - timedelta(hours=2)
    result = db.query(models.LeaseData).filter(models.LeaseData.crawler_update <= time_now).first()
    print(result.__dict__)
    assert result.leasable is False


def test_update_data_by_id(db: Session, creat_data):
    item = schemas.PostUpdateFromAPI(id=1, title="從API更新標題", poster="從API更新發文者名稱")
    result: schemas.PostInDatabase = posts_crud.update_data_by_id(db=db, item=item)
    print(result.__dict__)

    assert result.title == item.title
    assert result.poster == item.poster


def test_delete_data(db: Session, creat_data):
    item_id = 1
    result = posts_crud.delete_data(db=db, item_id=item_id)
    assert result is None
    result = db.query(models.LeaseData).filter(models.LeaseData.id == item_id).first()
    assert result is None
