from fastapi import FastAPI
from pydantic import BaseModel, ValidationError, validator


class Item(BaseModel):  # 定義資料格式
    name: str
    description: str | None = None  # 原為Union[str, None]
    price: float
    tax: float | None = None

    @validator('name')
    def name_must_be_input(cls, v):
        if v == 'string':
            raise ValueError('請輸入名稱')
        return v.title()

class TestPost(BaseModel):
    title : str
    size : int
    floor : int
    area : str

    # 使用者不能自行添加參數
    class Config:
        extra = 'forbid'


    @validator('size')
    def size_must_be_int(cls, v):
        if v > 100:
            raise ValueError('坪數最大為100坪')
        return v.title()


app = FastAPI()


# 請求體 Request Body
@app.post("/items/")
async def create_item(item: Item):
    item_dict = item.dict()  # Pydantic 的方法，將 Pydantic model 轉成 dict type
    if item.tax:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})
    return item_dict


@app.put("/items/{item_id}")  # 加上路徑參數
async def create_item(item_id: int, item: Item):
    return {"item_id": item_id, **item.dict()}


@app.put("/items/{item_id}")  # 加上路徑參數、查詢參數
async def create_item(item_id: int, item: Item, q: str | None = None):
    result = {"item_id": item_id, **item.dict()}
    if q:
        result.update({"q": q})
    return result

# TestPost
@app.post("/items/posts")
async def create_item(pos:TestPost):
    return {**pos.dict()}