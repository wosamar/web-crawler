from datetime import datetime
from sqlalchemy.orm import Session
from sql_app import schemas, models


def test_write_log(db: Session, logs_crud=None):
    db = db
    log = schemas.WriteLogData(start_time=datetime.now(), end_time=datetime.now(), status="Test", source="pytest",
                               area="台北市", page_num=0, error_message="爬蟲完成", count=10)
    result = logs_crud.write_log(db=db, log=log)
    assert result is None
    result = db.query(models.LogData).filter(models.LogData.source == log.source).first()
    print(result.__dict__)
    assert result.status == log.status