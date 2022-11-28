from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sql_app.crud import *
from sql_app import schemas
import uvicorn

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# 產生上下頁連結
def page_up_down(offset, limit, results):
    message = ""
    if results:
        next_page = f"/api/posts/template?offset={offset + limit}&limit{limit}"
    else:
        next_page = ""
        message = "沒有資料囉"
    if offset >= limit:
        last_page = f"/api/posts/template?offset={offset - limit}&limit{limit}"
    else:
        last_page = f"/api/posts/template?offset={offset}&limit{limit}"
    return {"next_page": next_page, "last_page": last_page, "message": message}


# 預設回傳最新的50筆，並且能夠提供分頁（limit, offset），提供發文者、更新日期、地區、是否可以被租賃等參數進行查詢
@app.get("/posts", response_class=HTMLResponse)
async def select_posts_page(request: Request, offset: int = 0, limit: int = 50, find_poster: str = None,
                            find_area: schemas.AreaName = None, find_lease: bool = None, find_update: str = None,
                            db: Session = Depends(get_db)):
    results = select_posts(db, offset=offset, limit=limit,
                           condition=schemas.SelectPosts(poster=find_poster, area=find_area, post_update=find_update,
                                                         leasable=find_lease))
    to_page = page_up_down(offset, limit, results)
    return templates.TemplateResponse("item.html", {"request": request, "posts_data": results, "to_page": to_page})


@app.get("/api/posts", response_model=list[schemas.Post])
async def select_posts_api(offset: int = 0, limit: int = 50, find_poster: str = None,
                           find_area: schemas.AreaName = None, find_lease: bool = None, find_update: str = None,
                           db: Session = Depends(get_db)):
    results = select_posts(db, offset=offset, limit=limit,
                           condition=schemas.SelectPosts(poster=find_poster, area=find_area, post_update=find_update,
                                                         leasable=find_lease))
    return results


# 回傳指定條件下的統計資訊，包含文章總數，並提供更新日期、地區等參數進行過濾
@app.get("/api/statistics", response_model=int)
async def read_item_api(area: schemas.AreaName = None, lower_rent: int = 0, upper_rent: int = None,
                        from_update: datetime = None, end_update: datetime = None, db: Session = Depends(get_db)):
    records = count_posts(db=db,
                          condition=schemas.GetStatistics(area=area, lower_rent=lower_rent, upper_rent=upper_rent,
                                                          from_update=from_update, end_update=end_update))
    return records


# 手動建立一筆租屋資料
@app.post("/posts/", response_class=HTMLResponse)
async def add_post_form(request: Request, post: schemas.APICreatePost, db: Session = Depends(get_db)):
    item = schemas.PostCreate(**post.dict())
    item.post_update = datetime.now().strftime("%Y-%m-%d")
    item.leasable = True
    item.source = "手動新增"
    db_post: schemas.PostCreate = create_post(db=db, item=item)
    return templates.TemplateResponse("detail.html", {"request": request, "post": db_post})


@app.post("/api/posts/", response_model=schemas.Post)
async def add_post_api(post: schemas.APICreatePost, db: Session = Depends(get_db)):
    item = schemas.PostCreate(**post.dict())
    item.post_update = datetime.now().strftime("%Y-%m-%d")
    item.leasable = True
    item.source = "手動新增"
    db_post: schemas.PostCreate = create_post(db=db, item=item)
    return db_post


# 手動修改一筆租屋資料(僅能修改租賃狀況)
@app.put("/posts/{post_id}", response_class=HTMLResponse)
async def update_item(request: Request, post_id: int, post_leasable: bool, db: Session = Depends(get_db)):
    item = update_leasable(db=db, post_id=post_id, post_leasable=post_leasable)
    return templates.TemplateResponse("detail.html", {"request": request, "item": item})


@app.put("/api/posts/{post_id}", response_model=schemas.Post)
async def update_item_api(post_id: int, post_leasable: bool, db: Session = Depends(get_db)):
    item = update_leasable(db=db, post_id=post_id, post_leasable=post_leasable)
    return item


# 回傳指定 id 文章詳細資料，id 為資料庫內的 id 非網站上文章 id
@app.get("/posts/{post_id}", response_class=HTMLResponse)
async def read_post_detail(request: Request, post_id: int, db: Session = Depends(get_db)):
    message = ""
    item_data = get_post(db, post_id)
    if not item_data:
        message = "找不到此筆資料"
    return templates.TemplateResponse("detail.html",
                                      {"request": request, "item_data": item_data, "message": message})


@app.get("/api/posts/{post_id}", response_model=schemas.Post)
async def read_post_detail_api(post_id: int, db: Session = Depends(get_db)):
    item_data = get_post(db, post_id)
    return item_data


# 手動刪除一筆租屋資料 # 暫不使用
# @app.delete("/api/posts/template/{post_id}", response_class=HTMLResponse)
# async def read_item(request: Request, item_id: int):
#     delete_data(item_id)
#     return templates.TemplateResponse("detail.html", {"request": request, "message": "已刪除資料"})

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
