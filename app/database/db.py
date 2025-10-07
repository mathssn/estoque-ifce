from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager


db_name = 'refeitorio_ifce'
username = 'root'
password = '1234'

db = create_engine(f"mysql+mysqlconnector://{username}:{password}@localhost:3306")

with db.connect() as conn:
    conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {db_name}"))

db = create_engine(f"mysql+mysqlconnector://{username}:{password}@localhost:3306/{db_name}")
Session = sessionmaker(bind=db, expire_on_commit=False)


@contextmanager
def get_session():
    with Session() as session:
        try:
            yield session
            session.commit()   
        except:
            session.rollback()
            raise             