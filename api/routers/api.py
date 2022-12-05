from datetime import date, timedelta, datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from definition import AreaName
from sql_app.crud import posts as posts_crud
from sql_app import schemas
from sql_app.db_utils import get_db

router = APIRouter(prefix="/api", tags=["api"])


# 預設回傳最新的50筆，並且能夠提供分頁（limit, offset），提供發文者、更新日期、地區、是否可以被租賃等參數進行查詢
@router.get("/posts", response_model=list[schemas.PostInResponse])
async def read_posts_api(offset: int = 0, limit: int = 50, find_poster: str = None,
                         find_area: AreaName = None, find_lease: bool = True, find_update: str = None,
                         db: Session = Depends(get_db)):
    condition = {}
    condition.update(poster=find_poster, area=find_area, post_update=find_update, leasable=find_lease)
    if offset >= 0 and limit > 0:
        results = posts_crud.select_posts(db, offset=offset, limit=limit, **condition)
        if results:
            return results
        else:
            raise HTTPException(status_code=404, detail="找不到資料")
    else:
        raise HTTPException(status_code=401, detail="參數輸入錯誤")


# 回傳指定條件下的統計資訊，包含文章總數，並提供更新日期、地區等參數進行過濾
@router.get("/statistics", response_model=int)
async def statistics_api(select_area: AreaName = None, lower_rent: int = 0, upper_rent: int = None,
                         from_update: date = Query(default=date.today() - timedelta(days=3),
                                                   title="開始時間"),
                         end_update: date = Query(default=date.today(), title="結束時間"),
                         db: Session = Depends(get_db)):
    condition = {}
    condition.update(area=select_area, lower_rent=lower_rent,
                     upper_rent=upper_rent,
                     from_update=from_update, end_update=end_update)
    records = posts_crud.count_posts(db=db, **condition)
    return records


# 建立資料
@router.post("/posts", response_model=schemas.PostInDatabase)
async def add_post_api(post: schemas.APICreatePost, db: Session = Depends(get_db)):
    item = schemas.PostCreateFromAPI(**post.dict())
    item.post_update = datetime.now().strftime("%Y-%m-%d")
    item.leasable = True
    item.source = "手動新增"
    db_post: schemas.PostCreateFromAPI = posts_crud.create_post(db=db, item=item)
    return db_post


# 修改資料
@router.put("/posts/{post_id}", response_model=schemas.PostInDatabase)
async def update_item_api(post_data: schemas.PostUpdate, post_id: int, db: Session = Depends(get_db)):
    post = posts_crud.get_post(db=db, post_id=post_id)
    source = post.source
    if source == "手動新增":
        update_post_data: schemas.PostUpdateFromAPI = schemas.PostUpdateFromAPI(**post_data.dict())
        update_post_data.id = post_id
        item = posts_crud.update_data_by_id(db=db, item=update_post_data)
        return item
    else:
        raise HTTPException(status_code=401, detail="無權限進行更改")


# 詳細資料
@router.get("/posts/{post_id}", response_model=schemas.PostInDatabase)
async def read_post_detail_api(post_id: int, db: Session = Depends(get_db)):
    item_data = posts_crud.get_post(db=db, post_id=post_id)
    if not item_data:
        raise HTTPException(status_code=404,detail="id錯誤，找不到此筆資料")
    return item_data


# 刪除
@router.delete("/posts/{post_id}", response_model=int)
async def delete_post_api(post_id: int, db: Session = Depends(get_db)):
    post_data = posts_crud.get_post(db=db, post_id=post_id)
    if post_data:
        if post_data.source == "手動新增":
            posts_crud.delete_data(db=db, item_id=post_id)
            return post_id
        else:
            raise HTTPException(status_code=401, detail="無權限進行刪除")
    else:
        raise HTTPException(status_code=404, detail="找不到此筆資料")
