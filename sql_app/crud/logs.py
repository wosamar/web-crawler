# 寫log
from sqlalchemy.orm import Session

from sql_app import models, schemas


def write_log(db: Session, log: schemas.WriteLogData):
    db_item = models.LogData(**log.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
