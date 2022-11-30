from datetime import date
import fastapi
from fastapi import FastAPI, Request, Depends, Query, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette import status
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
async def form_to_item(title: str | None = Form(), area: str | None = Form(), address: str | None = Form(),
                       rent: int | None = Form(), size: int | str = Form(), floor: str | None = Form(),
                       contact: str | None = Form(),
                       poster: str | None = Form()):
    return schemas.ItemBase(title=title, area=area, rent=rent, address=address, size=size, floor=floor, contact=contact,
                            poster=poster)


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
    if results:
        return results
    else:
        raise Exception("找不到資料")


# API回傳指定條件下的統計資訊，包含文章總數，並提供更新日期、地區等參數進行過濾
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
    return templates.TemplateResponse("update_post.html", {"request": request, "item_data": None})


@app.post("/posts", response_class=RedirectResponse)
async def add_post_page(post: schemas.ItemBase = Depends(form_to_item), db: Session = Depends(get_db)):
    item = schemas.PostCreate(**post.dict())
    item.post_update = datetime.now().strftime("%Y-%m-%d")
    item.leasable = True
    item.source = "手動新增"
    db_post: schemas.Post = create_post(db=db, item=item)
    response = fastapi.responses.RedirectResponse(url=f'/posts/{db_post.id}', status_code=status.HTTP_302_FOUND)
    return response


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
async def update_post_form(request: Request, post: schemas.ItemBase = Depends(form_to_item), post_id: int = Form(),
                           source: str = Form()):
    return templates.TemplateResponse("update_post.html",
                                      {"request": request, "item_data": post, "post_id": post_id, "source": source})


@app.post("/posts/{post_id}", response_class=HTMLResponse)
async def update_item(request: Request, post_data: schemas.ItemBase = Depends(form_to_item), post_id: int = None,
                      source: str = Form(), leasable: bool = Form(), db: Session = Depends(get_db)):
    if source == '手動新增':
        item: schemas.APIUpdatePost = schemas.APIUpdatePost(**post_data.dict())
        item.id = post_id
        item.leasable = leasable
        item.post_update = datetime.now().strftime("%Y-%m-%d")
        item = api_update_data(db=db, item=item)
        return templates.TemplateResponse("detail.html", {"request": request, "item_data": item, "post_id": post_id})
    else:
        raise HTTPException(status_code=401, detail="無權限進行更改")


@app.put("/posts/{post_id}", response_class=HTMLResponse)
async def update_item_put(request: Request, post_data: schemas.PostUpdate, post_id: int, db: Session = Depends(get_db)):
    if post_data.source == '手動新增':
        update_post_data: schemas.APIUpdatePost = schemas.APIUpdatePost(**post_data.dict())
        update_post_data.id = post_id
        item = api_update_data(db=db, item=update_post_data)
        return templates.TemplateResponse("detail.html", {"request": request, "item": item, "post_id": post_id})
    else:
        raise HTTPException(status_code=401, detail="無權限進行更改")


@app.put("/api/posts/{post_id}", response_model=schemas.Post)
async def update_item_api(post_data: schemas.PostUpdate, post_id: int, db: Session = Depends(get_db)):
    if post_data.source == "手動新增":
        update_post_data: schemas.APIUpdatePost = schemas.APIUpdatePost(**post_data.dict())
        update_post_data.id = post_id
        item = api_update_data(db=db, item=update_post_data)
        return item
    else:
        raise HTTPException(status_code=401, detail="無權限進行更改")


# 回傳指定 id 文章詳細資料
@app.get("/posts/{post_id}", response_class=HTMLResponse)
async def read_post_detail(request: Request, post_id: int, db: Session = Depends(get_db)):
    item_data = get_post(db=db, post_id=post_id)
    return templates.TemplateResponse("detail.html",
                                      {"request": request, "item_data": item_data, "post_id": post_id})


@app.get("/api/posts/{post_id}", response_model=schemas.Post)
async def read_post_detail_api(post_id: int, db: Session = Depends(get_db)):
    item_data = get_post(db=db, post_id=post_id)
    if not item_data:
        raise HTTPException(status_code=404, detail="id錯誤，找不到此筆資料")
    return item_data


# 手動刪除一筆租屋資料
@app.post("/posts/delete/{post_id}", response_class=HTMLResponse)
async def delete_post(request: Request, post_id: int, source: str = Form(), db: Session = Depends(get_db)):
    if source == "手動新增":
        delete_data(db=db, item_id=post_id)
        return templates.TemplateResponse("detail.html", {"request": request, "item_data": None})
    else:
        raise HTTPException(status_code=401, detail="無權限進行刪除")


@app.delete("/posts/{post_id}", response_class=HTMLResponse)
async def delete_post_delete(request: Request, post_id: int, db: Session = Depends(get_db)):
    item = get_post(db=db, post_id=post_id)
    if item.source == "手動新增":
        delete_data(db=db, item_id=post_id)
        return templates.TemplateResponse("detail.html", {"request": request, "item_data": None})
    else:
        raise HTTPException(status_code=401, detail="無權限進行刪除")


@app.delete("/api/posts/{post_id}", response_model=int)
async def delete_post_api(post_id: int, db: Session = Depends(get_db)):
    item = get_post(db=db, post_id=post_id)
    if item.source == "手動新增":
        delete_data(db=db, item_id=post_id)
        return post_id
    else:
        raise HTTPException(status_code=401, detail="無權限進行刪除")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
