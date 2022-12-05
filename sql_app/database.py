from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os



# 初始化
load_dotenv()
engine_url = os.getenv('engine_url')

engine = create_engine(
    engine_url, connect_args={}  # , echo=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()