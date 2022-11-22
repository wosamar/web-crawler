from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from SqlAlchemy_data.database_CRUD import *
from pydantic import BaseModel, validator
from datetime import date
from enum import Enum
import uvicorn

class ItemBase(BaseModel):  # 定義資料格式
    title: str
    size: float
    floor: str
    address: str
    rent: int
    contact: str
    poster: str
    area: str

    @validator('title')
    def title_must_be_input(cls, v):
        if v == 'string':
            raise ValueError('請輸入標題')
        return v.title()

    @validator('size')
    def size_must_be_float(cls, v):
        if v != int and v != float:
            raise ValueError('坪數必須為數字')
        return v.title()

    @validator('floor')
    def floor_len_too_long(cls, v):
        if len(v) >= 10:
            raise ValueError('樓層最多可輸入10個字元')
        return v.title()

    @validator('address')
    def address_len_too_long(cls, v):
        if len(v) >= 10:
            raise ValueError('地址最多可輸入55個字元')
        return v.title()

    @validator('rent')
    def rent_must_be_int(cls, v):
        if v != int:
            raise ValueError('租金格式不正確')
        return v.title()

    @validator('contact')
    def contact_len_too_long(cls, v):
        if len(v) >= 10:
            raise ValueError('聯絡人最多可輸入10個字元')
        return v.title()

    @validator('poster')
    def poster_len_too_long(cls, v):
        if len(v) >= 10:
            raise ValueError('發文者名稱最多可輸入10個字元')
        return v.title()


class ItemInfo(ItemBase):  # 系統控制的資料
    update: date | None = None
    leased: bool | None = None
    source: str

class AreaName(str, Enum):
    Taipei = "台北市"
    New_Taipei = "新北市"

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
@app.get("/api/posts/template", response_class=HTMLResponse)
async def read_item_template(request: Request, offset: int = 0, limit: int = 50, find_poster: str = "",
                             find_area: str = "", find_lease: bool = False, find_update: str = ""):
    if find_poster or find_area or find_lease or find_update:  # 如果表單有接收任何值則查詢
        items = {"poster": find_poster, "area": find_area, "update": find_update,
                 "leased": find_lease}
        results = get_posts_data(offset=offset, limit=limit, condition=items)
    else:
        results = get_posts_data(offset=offset, limit=limit, condition={})  # 若無表單資料則回傳全部資料

    to_page = page_up_down(offset, limit, results)
    return templates.TemplateResponse("item.html", {"request": request, "posts_data": results, "to_page": to_page})


# 同上 for api
@app.get("/api/posts", response_class=HTMLResponse)
async def read_item(offset: int = 0, limit: int = 50, find_poster: str = "", find_area: str = "",
                    find_lease: bool = False, find_update: str = ""):
    if find_poster or find_area or find_lease or find_update:  # 如果表單有接收任何值則查詢
        items = {"poster": find_poster, "area": find_area, "update": find_update,
                 "leased": find_lease}
        results = get_posts_data(offset=offset, limit=limit, condition=items)
    else:
        results = get_posts_data(offset=offset, limit=limit, condition={})  # 若無表單資料則顯示全部資料
    return results


# 回傳指定條件下的統計資訊，包含文章總數，並提供更新日期、地區等參數進行過濾 #搜尋的API
# 統計區域的貼文數、統計一萬以下的租房
@app.get("/api/statistics", response_class=HTMLResponse)
async def read_item(area: AreaName = "", rent: int = 0):
    posts_data = count_posts_data({"area": area, "rent": rent})
    print(f"找到{posts_data}筆資料")
    return f"地區:{area}\n租金:{rent}\n符合資料筆數：{posts_data}"


# 手動建立一筆租屋資料
@app.post("/api/posts/new", response_class=HTMLResponse)
async def add_post(request: Request, item: ItemBase):
    item = ItemInfo(**item.dict(), source="手動新增")
    create_data(item.__dict__)  # 網址設定為資料庫內id?
    return templates.TemplateResponse("item.html", {"request": request, "item_data": item})


# 手動修改一筆租屋資料
@app.put("/api/posts/template/{post_id}", response_class=HTMLResponse)
async def read_item(request: Request, item: ItemBase):
    return templates.TemplateResponse("detail.html", {"request": request, "item_id": [123, 213, 456]})


# 手動刪除一筆租屋資料
@app.delete("/api/posts/template/{post_id}", response_class=HTMLResponse)
async def read_item(request: Request, item_id: int):
    delete_data(item_id)
    return templates.TemplateResponse("detail.html", {"request": request, "message": "已刪除資料"})


# 回傳指定 id 文章詳細資料，id 為資料庫內的 id 非網站上文章 id
@app.get("/api/posts/template/{post_id}", response_class=HTMLResponse)
async def read_item(request: Request, post_id: int):
    message = ""
    item_data = select_lease_data({"id": post_id})
    if not item_data:
        message = "找不到此筆資料"
    return templates.TemplateResponse("detail.html",
                                      {"request": request, "item_data": item_data, "message": message})


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
