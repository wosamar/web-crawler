import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from sql_app.crud import posts
from sql_app.database import Base
from sql_app.schemas import PostCreate


@pytest.fixture(name="db", scope="function")
def db() -> Session:
    # 建立 engine
    engine_url = "sqlite://"
    engine = create_engine(engine_url)

    # 建立資料表
    Base.metadata.create_all(engine)

    #  yield 出 Session
    with sessionmaker(bind=engine)() as session:
        yield session

    # 刪除資料表
    Base.metadata.drop_all(engine)


@pytest.fixture(name="creat_data")
def creat_data(db: Session):
    db = db
    item = PostCreate(title="首筆資料", size=1, floor=2 / 2, address="create by fixture", post_update="2022-11-28",
                      rent=100, url="https://fixture.com.tw/", contact="聯絡人欄位", poster="user", leasable=True,
                      area="台北市", source="python", crawler_update="2022-11-30 10:10:00")
    posts.create_post(db=db, item=item)
