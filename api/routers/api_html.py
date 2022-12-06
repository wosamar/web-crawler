from datetime import datetime
import fastapi
from fastapi import Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette import status

from definition import AreaName
from sql_app import schemas
from sql_app.crud import posts as posts_crud
from sql_app.db_utils import get_db
from fastapi import APIRouter

router = APIRouter(prefix="/posts", tags=["api template"])
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


# 表單轉物件
async def form_to_item(title: str | None = Form(), area: str | None = Form(), address: str | None = Form(),
                       rent: int | None = Form(), size: int | str = Form(), floor: str | None = Form(),
                       contact: str | None = Form(),
                       poster: str | None = Form()):
    return schemas.PostInRequestBase(title=title, area=area, rent=rent, address=address, size=size, floor=floor,
                                     contact=contact,
                                     poster=poster)


# 主頁
@router.get("/", response_class=HTMLResponse)
async def read_posts_page(request: Request, offset: int = 0, limit: int = 50, find_poster: str | None = None,
                          find_area: AreaName | None = None, find_lease: bool = True, find_update: str | None = None,
                          db: Session = Depends(get_db)):
    if offset >= 0 and limit > 0:
        find_update = find_update if find_update else None
        condition = {}
        condition.update(poster=find_poster, area=find_area, from_update=find_update, end_update=find_update,
                         leasable=find_lease)
        results = posts_crud.select_posts(db, offset=offset, limit=limit, **condition)
        results = [schemas.PostInResponse.from_orm(rs) for rs in results]
        links = page_up_down(offset=offset, limit=limit, find_poster=find_poster, find_area=find_area,
                             find_lease=find_lease, find_update=find_update)
        return templates.TemplateResponse("main.html",
                                          {"request": request, "posts_data": results, "links": links, "offset": offset,
                                           "limit": limit})
    else:
        raise HTTPException(status_code=401, detail="參數輸入錯誤")


# 建立一筆租屋資料
@router.get("/new", response_class=HTMLResponse)
async def add_post_form(request: Request):
    return templates.TemplateResponse("update_post.html", {"request": request, "item_data": None})


@router.post("/", response_class=RedirectResponse)
async def add_post_page(post: schemas.PostBase = Depends(form_to_item), db: Session = Depends(get_db)):
    item = schemas.PostCreateFromAPI(**post.dict())
    item.post_update = datetime.now().strftime("%Y-%m-%d")
    item.leasable = True
    item.source = "手動新增"
    db_post: schemas.PostInRequest = posts_crud.create_post(db=db, item=item)
    response = fastapi.responses.RedirectResponse(url=f'/posts/{db_post.id}', status_code=status.HTTP_302_FOUND)
    return response


# 修改租屋資料
@router.get("/update/{post_id}", response_class=HTMLResponse)
async def update_post_form(request: Request, post_id: int, db: Session = Depends(get_db)):
    post = posts_crud.get_post(db=db, post_id=post_id)
    return templates.TemplateResponse("update_post.html",
                                      {"request": request, "item_data": post, "post_id": post_id,
                                       "source": post.source})


@router.post("/{post_id}", response_class=HTMLResponse)
async def update_post(request: Request, post_data: schemas.PostInRequestBase = Depends(form_to_item),
                      post_id: int = None, leasable: bool = Form(), db: Session = Depends(get_db)):
    post = posts_crud.get_post(db=db, post_id=post_id)
    source = post.source
    if source == '手動新增':
        item: schemas.PostUpdateFromAPI = schemas.PostUpdateFromAPI(**post_data.dict())
        item.id = post_id
        item.leasable = leasable
        item.post_update = datetime.now().strftime("%Y-%m-%d")
        item = posts_crud.update_data_by_id(db=db, item=item)
        return templates.TemplateResponse("detail.html", {"request": request, "item_data": item, "post_id": post_id})
    else:
        raise HTTPException(status_code=401, detail="無權限進行更改")


@router.put("/{post_id}", response_class=HTMLResponse)
async def update_post_put(request: Request, post_data: schemas.PostUpdate, post_id: int, db: Session = Depends(get_db)):
    if post_data.source == '手動新增':
        update_post_data: schemas.PostUpdateFromAPI = schemas.PostUpdateFromAPI(**post_data.dict())
        update_post_data.id = post_id
        item = posts_crud.update_data_by_id(db=db, item=update_post_data)
        return templates.TemplateResponse("detail.html", {"request": request, "item": item, "post_id": post_id})
    else:
        raise HTTPException(status_code=401, detail="無權限進行更改")


# 回傳詳細資料
@router.get("/{post_id}", response_class=HTMLResponse)
async def read_post_detail(request: Request, post_id: int, db: Session = Depends(get_db)):
    item_data = posts_crud.get_post(db=db, post_id=post_id)
    return templates.TemplateResponse("detail.html",
                                      {"request": request, "item_data": item_data, "post_id": post_id})


# 刪除一筆租屋資料
@router.post("/delete/{post_id}", response_class=HTMLResponse)
async def delete_post(request: Request, post_id: int, db: Session = Depends(get_db)):
    post_data = posts_crud.get_post(db=db, post_id=post_id)
    if post_data:
        if post_data.source == "手動新增":
            posts_crud.delete_data(db=db, item_id=post_id)
            response = fastapi.responses.RedirectResponse(url=f'/posts', status_code=status.HTTP_302_FOUND)
            return response
        else:
            raise HTTPException(status_code=401, detail="無權限進行刪除")
    else:
        raise HTTPException(status_code=404, detail="找不到此筆資料")


@router.delete("/{post_id}", response_class=HTMLResponse)
async def delete_post_delete(request: Request, post_id: int, db: Session = Depends(get_db)):
    post_data = posts_crud.get_post(db=db, post_id=post_id)
    if post_data:
        if post_data.source == "手動新增":
            posts_crud.delete_data(db=db, item_id=post_id)
            return templates.TemplateResponse("detail.html", {"request": request, "item_data": None})
        else:
            raise HTTPException(status_code=401, detail="無權限進行刪除")
