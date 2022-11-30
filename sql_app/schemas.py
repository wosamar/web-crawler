from pydantic import BaseModel, validator
from datetime import date, datetime


class ItemBase(BaseModel):  # 基本資料格式
    title: str | None = None
    size: float | None = None
    floor: str | None = None
    address: str | None = None
    rent: int | None = None
    contact: str | None = None
    poster: str | None  = None
    area: str | None = None

    @validator('title')
    def title_must_be_input(cls, v):
        if v == 'string':
            raise ValueError('請輸入標題')
        return v

    @validator('title')
    def title_len_too_long(cls, v):
        if len(v) > 30:
            raise ValueError(f'輸入內容：{v}，標題最多可輸入30個字元')
        return v

    @validator('size')
    def size_must_be_float(cls, v):
        if not isinstance(v, int) and not isinstance(v, float):
            raise ValueError('坪數必須為數字')
        return v

    @validator('floor')
    def floor_len_too_long(cls, v):
        if len(v) > 20:
            raise ValueError(f'輸入內容：{v}，樓層最多可輸入20個字元')
        return v

    @validator('address')
    def address_len_too_long(cls, v):
        if len(v) >= 55:
            raise ValueError('地址最多可輸入55個字元')
        return v

    @validator('rent')
    def rent_must_be_int(cls, v):
        if not isinstance(v, int):
            raise ValueError('租金格式不正確')
        return v

    @validator('contact')
    def contact_len_too_long(cls, v):
        if len(v) > 10:
            raise ValueError('聯絡人最多可輸入10個字元')
        return v


class PostInfo(ItemBase):
    post_update: date | None = None
    url: str | None = None
    leasable: bool | None = None
    source: str | None = None
    crawler_update: datetime | None = None

class Post(PostInfo):  # 系統控制的資料
    id: int = None

    class Config:
        orm_mode = True

class PostCreateOrUpdate(PostInfo):
    pass


class PostCreate(PostInfo):
    pass


class PostUpdate(PostInfo):
    pass


class SelectPosts(PostInfo):
    pass


class APICreatePost(ItemBase):
    pass

class APIUpdatePost(Post):
    pass





# class Count(ItemBase):  # 查詢統計資料
#     count: int = None

    # class Config:
    #     orm_mode = True


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



class GetStatistics(BaseModel):
    area: str | None
    lower_rent: int | None
    upper_rent: int | None
    from_update: date | None
    end_update: date | None
