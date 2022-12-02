from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sql_app import models, schemas
from sql_app.crud import posts as posts_crud,logs as  logs_crud

def setup_module():
    print("setup_module\n")


def teardown_module():
    print("teardown_module")


def test_select_posts(db: Session,creat_data):
    db = db
    offset = 0
    limit = 50
    condition = schemas.SelectPosts(leasable=True, poster="user")
    result = posts_crud.select_posts(db=db, offset=offset, limit=limit, condition=condition)

    for item in result:
        print(item.__dict__)
    assert result


def test_get_post(db: Session,creat_data):
    db = db
    post_id = 1
    result = posts_crud.get_post(db=db, post_id=post_id)

    print(result.__dict__)
    assert result


def test_count_posts(db: Session,creat_data):
    db = db
    condition = schemas.GetStatistics(area="台北市", upper_rent=5000, from_update="2022-11-01")
    result = posts_crud.count_posts(db=db, condition=condition)

    print(result)
    assert result


def test_create_or_update(db: Session):
    db = db
    # 新增資料
    item = schemas.PostCreateOrUpdate(title="標題名稱", size=5, floor=1 / 12, address="應為新增",
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
    item = schemas.PostCreateOrUpdate(title="new_標題名稱", size=5, floor=2 / 12, address="應為修改",
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
    db = db
    item = schemas.PostCreate(title="測試用標題", size=3, floor=3 / 12, address="台北市大安區",
                      post_update="2022-11-28", rent=10000, url="https://sql.com.tw/",
                      contact="聯絡人欄位", poster="user", leasable=True,
                      crawler_update="2023-12-30 10:10:00")
    result: schemas.Post = posts_crud.create_post(db=db, item=item)
    print(result.__dict__)

    assert result.title == item.title


def test_update_data_by_url(db: Session,creat_data):
    db = db
    item = schemas.PostUpdate(title="更新後標題", contact="更新後聯絡人", url="https://fixture.com.tw/")
    result: schemas.Post = posts_crud.update_data_by_url(db=db, item=item)
    assert result is None

    result = db.query(models.LeaseData).filter(models.LeaseData.url == item.url).first()
    print(result.__dict__)

    assert result.title == item.title
    assert result.poster == item.poster


def test_check_leasable(db: Session,creat_data):
    db = db
    result = posts_crud.check_leasable(db=db)
    assert result is None

    time_now = datetime.now() - timedelta(hours=2)
    result = db.query(models.LeaseData).filter(models.LeaseData.crawler_update <= time_now).first()
    print(result.__dict__)
    assert result.leasable is False


def test_update_data_by_id(db: Session,creat_data):
    db = db
    item = schemas.PostUpdateFromAPI(id=1, title="從API更新標題", poster="從API更新發文者名稱")
    result: schemas.Post = posts_crud.update_data_by_id(db=db, item=item)
    print(result.__dict__)

    assert result.title == item.title
    assert result.poster == item.poster


def test_delete_data(db: Session,creat_data):
    db = db
    item_id = 1
    result = posts_crud.delete_data(db=db, item_id=item_id)
    assert result is None
    result = db.query(models.LeaseData).filter(models.LeaseData.id == item_id).first()
    assert result is None


def test_write_log(db: Session):
    db = db
    log = schemas.WriteLogData(start_time=datetime.now(), end_time=datetime.now(), status="Test", source="pytest",
                               area="台北市", page_num=0, error_message="爬蟲完成", count=10)
    result = logs_crud.write_log(db=db, log=log)
    assert result is None
    result = db.query(models.LogData).filter(models.LogData.source == log.source).first()
    print(result.__dict__)
    assert result.status == log.status
