from datetime import date

import fastapi
from fastapi import FastAPI, Request, Depends, Query, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette import status

# from starlette.responses import RedirectResponse

from definition import AreaName
from sql_app.crud import *
from sql_app import schemas
import uvicorn

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# 產生上下頁連結
def page_up_down(offset, limit, results):
    if results:  # 最後一頁
        next_page = f"/posts?offset={offset + limit}&limit={limit}"
    else:
        next_page = ""
    if offset >= limit:  # 第一頁
        last_page = f"/posts?offset={offset - limit}&limit={limit}"
    else:
        last_page = f"/posts?offset={offset}&limit={limit}"
    return {"next_page": next_page, "last_page": last_page}


# 表單轉字典
async def form_to_dict(title: str | None = Form(), area: str | None = Form(), address: str | None = Form(),
                       rent: int | None = Form(), size: int | str = Form(), floor: str | None = Form(),
                       contact: str | None = Form(),
                       poster: str | None = Form()):
    return {"title": title, "area": area, "rent": rent, "address": address, "size": size, "floor": floor,
            "contact": contact, "poster": poster}


# 預設回傳最新的50筆，並且能夠提供分頁（limit, offset），提供發文者、更新日期、地區、是否可以被租賃等參數進行查詢
@app.get("/posts", response_class=HTMLResponse)
async def read_posts_page(request: Request, offset: int = 0, limit: int = 50, find_poster: str | None = None,
                          find_area: AreaName | None = None, find_lease: bool = True, find_update: str | None = None,
                          db: Session = Depends(get_db)):
    if find_update == '':
        find_update = None
    results = select_posts(db, offset=offset, limit=limit,
                           condition=schemas.SelectPosts(poster=find_poster, area=find_area, post_update=find_update,
                                                         leasable=find_lease))
    to_page = page_up_down(offset, limit, results)
    return templates.TemplateResponse("item.html", {"request": request, "posts_data": results, "to_page": to_page})


@app.get("/api/posts", response_model=list[schemas.Post])
async def read_posts_api(offset: int = 0, limit: int = 50, find_poster: str = None,
                         find_area: AreaName = None, find_lease: bool = True, find_update: str = None,
                         db: Session = Depends(get_db)):
    results = select_posts(db, offset=offset, limit=limit,
                           condition=schemas.SelectPosts(poster=find_poster, area=find_area, post_update=find_update,
                                                         leasable=find_lease))
    return results


# 回傳指定條件下的統計資訊，包含文章總數，並提供更新日期、地區等參數進行過濾
@app.get("/api/statistics", response_model=int)
async def read_item_api(select_area: AreaName = None, lower_rent: int = 0, upper_rent: int = None,
                        from_update: date = Query(default=date.today() - timedelta(days=3),
                                                  title="開始時間"),
                        end_update: date = Query(default=date.today(), title="結束時間"),
                        db: Session = Depends(get_db)):
    records = count_posts(db=db,
                          condition=schemas.GetStatistics(area=select_area, lower_rent=lower_rent,
                                                          upper_rent=upper_rent,
                                                          from_update=from_update, end_update=end_update))
    return records


# 手動建立一筆租屋資料
@app.get("/posts/new", response_class=HTMLResponse)
async def add_post_form(request: Request):
    return templates.TemplateResponse("update_post.html", {"request": request,"item_data":None})


@app.post("/posts", response_class=RedirectResponse)
async def add_post_page(request: Request, post: dict = Depends(form_to_dict), db: Session = Depends(get_db)):
    # try:
    item = schemas.PostCreate(**post)
    item.post_update = datetime.now().strftime("%Y-%m-%d")
    item.leasable = True
    item.source = "手動新增"
    db_post: schemas.Post = create_post(db=db, item=item)
    # return templates.TemplateResponse("detail.html", {"request": request, "item_data": db_post, "post_id": db_post.id})
    response = fastapi.responses.RedirectResponse(url=f'/posts/{db_post.id}', status_code=status.HTTP_302_FOUND)
    return response
    # except HTTPException:
    #     return templates.TemplateResponse("detail.html", {"request": request, "item_data": None})


@app.post("/api/posts", response_model=schemas.Post)
async def add_post_api(post: schemas.APICreatePost, db: Session = Depends(get_db)):
    item = schemas.PostCreate(**post.dict())
    item.post_update = datetime.now().strftime("%Y-%m-%d")
    item.leasable = True
    item.source = "手動新增"
    db_post: schemas.PostCreate = create_post(db=db, item=item)
    return db_post


# 手動修改租屋資料
@app.post("/posts/update", response_class=HTMLResponse)
async def update_post_form(request: Request, post: dict = Depends(form_to_dict), post_id: int = Form()):
    return templates.TemplateResponse("update_post.html", {"request": request, "item_data": post, "post_id": post_id})


@app.post("/posts/{post_id}", response_class=HTMLResponse)
async def update_item(request: Request, post_data: dict = Depends(form_to_dict), post_id: int = None,
                      leasable: bool = Form(), db: Session = Depends(get_db)):
    item: schemas.APIUpdatePost = schemas.APIUpdatePost(**post_data)
    item.id = post_id
    item.leasable = leasable
    item.post_update = datetime.now().strftime("%Y-%m-%d")
    item = api_update_data(db=db, item=item)
    return templates.TemplateResponse("update_post.html", {"request": request, "item_data": item, "post_id": post_id})


@app.put("/posts/{post_id}", response_class=HTMLResponse)
async def update_item_put(request: Request, post_data: schemas.PostUpdate, post_id: int, db: Session = Depends(get_db)):
    update_post_data: schemas.APIUpdatePost = schemas.APIUpdatePost(**post_data.dict())
    update_post_data.id = post_id
    item = api_update_data(db=db, item=update_post_data)
    return templates.TemplateResponse("detail.html", {"request": request, "item": item, "post_id": post_id})


@app.put("/api/posts/{post_id}", response_model=schemas.Post)
async def update_item_api(post_data: schemas.PostUpdate, post_id: int, db: Session = Depends(get_db)):
    update_post_data: schemas.APIUpdatePost = schemas.APIUpdatePost(**post_data.dict())
    update_post_data.id = post_id
    item = api_update_data(db=db, item=update_post_data)
    return item


# 回傳指定 id 文章詳細資料，id 為資料庫內的 id 非網站上文章 id
@app.get("/posts/{post_id}", response_class=HTMLResponse)
async def read_post_detail(request: Request, post_id: int, db: Session = Depends(get_db)):
    item_data = get_post(db=db, post_id=post_id)
    return templates.TemplateResponse("detail.html",
                                      {"request": request, "item_data": item_data, "post_id": post_id})


@app.get("/api/posts/{post_id}", response_model=schemas.Post)
async def read_post_detail_api(post_id: int, db: Session = Depends(get_db)):
    item_data = get_post(db=db, post_id=post_id)
    return item_data


# 手動刪除一筆租屋資料
@app.post("/posts/delete/{post_id}", response_class=HTMLResponse)
async def delete_post(request: Request, post_id: int, db: Session = Depends(get_db)):
    delete_data(db=db, item_id=post_id)
    return templates.TemplateResponse("detail.html", {"request": request, "item_data": None})


@app.delete("/posts/{post_id}", response_class=HTMLResponse)
async def delete_post_delete(request: Request, post_id: int, db: Session = Depends(get_db)):
    delete_data(db=db, item_id=post_id)
    return templates.TemplateResponse("detail.html", {"request": request, "item_data": None})


@app.delete("/api/posts/{post_id}", response_model=int)
async def delete_post_api(post_id: int, db: Session = Depends(get_db)):
    delete_data(db=db, item_id=post_id)
    return post_id


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
