from datetime import date, datetime, timedelta
import fastapi
from fastapi import FastAPI, Request, Depends, Query, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette import status
from definition import AreaName
from sql_app import schemas
import uvicorn
from sql_app.crud import posts as posts_crud

from sql_app.db_utils import get_db

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# 產生上下頁連結
def page_up_down(offset, limit, find_poster=None, find_area=None, find_lease=True, find_update=None):
    next_page = f"/posts?offset={offset + limit}&limit={limit}&"
    last_page = f"/posts?offset={offset - limit}&limit={limit}&"

    if find_poster:
        next_page += f"find_poster={find_poster}&"
        last_page += f"find_poster={find_poster}&"
    if find_area:
        next_page += f"find_area={find_area.title()}&"
        last_page += f"find_area={find_area.title()}&"
    if not find_lease:
        next_page += f"find_lease={find_lease}&"
        last_page += f"find_lease={find_lease}&"
    if find_update:
        next_page += f"find_update={find_update}&"
        last_page += f"find_update={find_update}&"

    return {"next_page": next_page, "last_page": last_page}


# 表單轉字典
async def form_to_item(title: str | None = Form(), area: str | None = Form(), address: str | None = Form(),
                       rent: int | None = Form(), size: int | str = Form(), floor: str | None = Form(),
                       contact: str | None = Form(),
                       poster: str | None = Form()):
    return schemas.PostInRequestBase(title=title, area=area, rent=rent, address=address, size=size, floor=floor, contact=contact,
                            poster=poster)


# 預設回傳最新的50筆，並且能夠提供分頁（limit, offset），提供發文者、更新日期、地區、是否可以被租賃等參數進行查詢
@app.get("/posts", response_class=HTMLResponse, tags=["data api"])
async def read_posts_page(request: Request, offset: int = 0, limit: int = 50, find_poster: str | None = None,
                          find_area: AreaName | None = None, find_lease: bool = True, find_update: str | None = None,
                          db: Session = Depends(get_db)):
    find_update = find_update if find_update else None
    results = posts_crud.select_posts(db, offset=offset, limit=limit,
                           condition=schemas.SelectPosts(poster=find_poster, area=find_area, post_update=find_update,
                                                         leasable=find_lease))
    results = [schemas.PostInResponse.from_orm(rs) for rs in results]
    links = page_up_down(offset=offset, limit=limit, find_poster=find_poster, find_area=find_area,
                         find_lease=find_lease, find_update=find_update)
    return templates.TemplateResponse("main.html",
                                      {"request": request, "posts_data": results, "links": links, "offset": offset,
                                       "limit": limit})


@app.get("/api/posts", response_model=list[schemas.PostInResponse], tags=["api template"])
async def read_posts_api(offset: int = 0, limit: int = 50, find_poster: str = None,
                         find_area: AreaName = None, find_lease: bool = True, find_update: str = None,
                         db: Session = Depends(get_db)):
    results = posts_crud.select_posts(db, offset=offset, limit=limit,
                           condition=schemas.SelectPosts(poster=find_poster, area=find_area, post_update=find_update,
                                                         leasable=find_lease))
    if results:
        return results
    else:
        raise Exception("找不到資料")


# API回傳指定條件下的統計資訊，包含文章總數，並提供更新日期、地區等參數進行過濾
@app.get("/api/statistics", response_model=int, tags=["api template"])
async def read_item_api(select_area: AreaName = None, lower_rent: int = 0, upper_rent: int = None,
                        from_update: date = Query(default=date.today() - timedelta(days=3),
                                                  title="開始時間"),
                        end_update: date = Query(default=date.today(), title="結束時間"),
                        db: Session = Depends(get_db)):
    records = posts_crud.count_posts(db=db,
                          condition=schemas.GetStatistics(area=select_area, lower_rent=lower_rent,
                                                          upper_rent=upper_rent,
                                                          from_update=from_update, end_update=end_update))
    return records


# 手動建立一筆租屋資料
@app.get("/posts/new", response_class=HTMLResponse, tags=["data api"])
async def add_post_form(request: Request):
    return templates.TemplateResponse("update_post.html", {"request": request, "item_data": None})


@app.post("/posts", response_class=RedirectResponse, tags=["data api"])
async def add_post_page(post: schemas.PostBase = Depends(form_to_item), db: Session = Depends(get_db)):
    item = schemas.PostCreateFromAPI(**post.dict())
    item.post_update = datetime.now().strftime("%Y-%m-%d")
    item.leasable = True
    item.source = "手動新增"
    db_post: schemas.PostInRequest = posts_crud.create_post(db=db, item=item)
    response = fastapi.responses.RedirectResponse(url=f'/posts/{db_post.id}', status_code=status.HTTP_302_FOUND)
    return response


@app.post("/api/posts", response_model=schemas.Post, tags=["api template"])
async def add_post_api(post: schemas.APICreatePost, db: Session = Depends(get_db)):
    item = schemas.PostCreateFromAPI(**post.dict())
    item.post_update = datetime.now().strftime("%Y-%m-%d")
    item.leasable = True
    item.source = "手動新增"
    db_post: schemas.PostCreateFromAPI = posts_crud.create_post(db=db, item=item)
    return db_post


# 手動修改租屋資料
@app.post("/posts/update", response_class=HTMLResponse, tags=["data api"])
async def update_post_form(request: Request, post: schemas.PostBase = Depends(form_to_item), post_id: int = Form(),
                           source: str = Form()):
    return templates.TemplateResponse("update_post.html",
                                      {"request": request, "item_data": post, "post_id": post_id, "source": source})


@app.post("/posts/{post_id}", response_class=HTMLResponse, tags=["data api"])
async def update_item(request: Request, post_data: schemas.PostInRequestBase = Depends(form_to_item), post_id: int = None,
                      source: str = Form(), leasable: bool = Form(), db: Session = Depends(get_db)):
    if source == '手動新增':
        item: schemas.PostUpdateFromAPI = schemas.PostUpdateFromAPI(**post_data.dict())
        item.id = post_id
        item.leasable = leasable
        item.post_update = datetime.now().strftime("%Y-%m-%d")
        item = posts_crud.update_data_by_id(db=db, item=item)
        return templates.TemplateResponse("detail.html", {"request": request, "item_data": item, "post_id": post_id})
    else:
        raise HTTPException(status_code=401, detail="無權限進行更改")


@app.put("/posts/{post_id}", response_class=HTMLResponse, tags=["data api"])
async def update_item_put(request: Request, post_data: schemas.PostUpdate, post_id: int, db: Session = Depends(get_db)):
    if post_data.source == '手動新增':
        update_post_data: schemas.APIUpdatePost = schemas.APIUpdatePost(**post_data.dict())
        update_post_data.id = post_id
        item = posts_crud.update_data_by_id(db=db, item=update_post_data)
        return templates.TemplateResponse("detail.html", {"request": request, "item": item, "post_id": post_id})
    else:
        raise HTTPException(status_code=401, detail="無權限進行更改")


@app.put("/api/posts/{post_id}", response_model=schemas.Post, tags=["api template"])
async def update_item_api(post_data: schemas.PostUpdate, post_id: int, db: Session = Depends(get_db)):
    if post_data.source == "手動新增":
        update_post_data: schemas.APIUpdatePost = schemas.APIUpdatePost(**post_data.dict())
        update_post_data.id = post_id
        item = posts_crud.update_data_by_id(db=db, item=update_post_data)
        return item
    else:
        raise HTTPException(status_code=401, detail="無權限進行更改")


# 回傳指定 id 文章詳細資料
@app.get("/posts/{post_id}", response_class=HTMLResponse, tags=["data api"])
async def read_post_detail(request: Request, post_id: int, db: Session = Depends(get_db)):
    item_data = posts_crud.get_post(db=db, post_id=post_id)
    return templates.TemplateResponse("detail.html",
                                      {"request": request, "item_data": item_data, "post_id": post_id})


@app.get("/api/posts/{post_id}", response_model=schemas.Post, tags=["api template"])
async def read_post_detail_api(post_id: int, db: Session = Depends(get_db)):
    item_data = posts_crud.get_post(db=db, post_id=post_id)
    if not item_data:
        raise HTTPException(status_code=404, detail="id錯誤，找不到此筆資料")
    return item_data


# 手動刪除一筆租屋資料
@app.post("/posts/delete/{post_id}", response_class=HTMLResponse, tags=["data api"])
async def delete_post(request: Request, post_id: int, source: str = Form(), db: Session = Depends(get_db)):
    if source == "手動新增":
        posts_crud.delete_data(db=db, item_id=post_id)
        return templates.TemplateResponse("detail.html", {"request": request, "item_data": None})
    else:
        raise HTTPException(status_code=401, detail="無權限進行刪除")


@app.delete("/posts/{post_id}", response_class=HTMLResponse, tags=["data api"])
async def delete_post_delete(request: Request, post_id: int, db: Session = Depends(get_db)):
    item = posts_crud.get_post(db=db, post_id=post_id)
    if item.source == "手動新增":
        posts_crud.delete_data(db=db, item_id=post_id)
        return templates.TemplateResponse("detail.html", {"request": request, "item_data": None})
    else:
        raise HTTPException(status_code=401, detail="無權限進行刪除")


@app.delete("/api/posts/{post_id}", response_model=int, tags=["api template"])
async def delete_post_api(post_id: int, db: Session = Depends(get_db)):
    item = posts_crud.get_post(db=db, post_id=post_id)
    if item.source == "手動新增":
        posts_crud.delete_data(db=db, item_id=post_id)
        return post_id
    else:
        raise HTTPException(status_code=401, detail="無權限進行刪除")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
