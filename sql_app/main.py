from database import engine
from sql_app import models


def create_table():
    models.Base.metadata.create_all(bind=engine)


def drop_table():
    models.Base.metadata.drop_all(bind=engine)


if __name__ == '__main__':
    drop_table()
    create_table()
