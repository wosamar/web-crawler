from pydantic import BaseModel, validator
from datetime import date, datetime, timedelta
from fastapi import HTTPException, status


class PostBase(BaseModel):  # 基本資料格式
    title: str | None = None
    size: float | None = None
    floor: str | None = None
    address: str | None = None
    rent: int | None = None
    contact: str | None = None
    poster: str | None = None
    area: str | None = None

    post_update: date | None = None
    url: str | None = None
    leasable: bool | None = None
    source: str | None = None
    crawler_update: datetime | None = None

    @validator('title')
    def title_too_long(cls, v):
        if len(v) >= 255:
            return v[:255]
        else:
            return v


class PostInRequestBase(PostBase):
    class Config:
        schema_extra = {
            "example": {
                "title": "標題範例",
                "size": 3,
                "floor": "2/3",
                "address": "106台北市大安區信義路四段",
                "rent": 12000,
                "contact": "屋主",
                "poster": "賈小姐",
                "area": "台北市",
                "url": "https://testtest.com.tw/",
                "leasable": True,
                "source": "手動新增",
            }
        }

    @validator('title')
    def title_len_too_long(cls, v):
        if v:
            if len(v) > 30:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                    detail="標題最多可輸入30個字元")
            return v

    @validator('size')
    def size_must_be_float(cls, v):
        if v:
            if not isinstance(v, int) and not isinstance(v, float):
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                    detail="坪數必須為數字")
            return v

    @validator('floor')
    def floor_len_too_long(cls, v):
        if v:
            if len(v) > 20:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                    detail="樓層最多可輸入20個字元")
            return v

    @validator('address')
    def address_len_too_long(cls, v):
        if v:
            if len(v) >= 55:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                    detail="地址最多可輸入55個字元")
            return v

    @validator('rent')
    def rent_must_be_int(cls, v):
        if v:
            if not isinstance(v, int):
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                    detail="租金格式不正確")
            return v

    @validator('contact')
    def contact_len_too_long(cls, v):
        if v:
            if len(v) > 10:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                    detail="聯絡人最多可輸入10個字元")
            return v

    @validator('area')
    def area_not_correct(cls, v):
        if v:
            if v == "台北市" or v == "新北市":
                pass
            else:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                    detail="地區格式不正確")
            return v



class PostInDatabase(PostBase):
    id: int = None

    class Config:
        orm_mode = True


class PostInRequest(PostInRequestBase):
    id: int = None

    class Config:
        orm_mode = True


class PostInResponse(PostInRequest):
    pass


class PostCreate(PostBase):
    pass


class PostUpdate(PostBase):
    pass


class PostCreateFromAPI(PostInRequestBase):
    pass


class PostUpdateFromAPI(PostInRequest):
    pass


class APICreatePost(PostInRequestBase):
    pass


class LogData(BaseModel):
    start_time: datetime
    end_time: datetime
    status: str = None
    source: str
    area: str | None
    page_num: int
    error_message: str = None
    count: int


class WriteLogData(LogData):
    id: int = None
