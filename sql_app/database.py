from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 初始化
# engine_url = "mysql+pymysql://root:eland1234@10.10.10.55:3306/crawler_database"
engine_url = "mysql+pymysql://root:eland1234@10.10.10.55:3306/my_database"

engine = create_engine(
    engine_url, connect_args={}  # , echo=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
