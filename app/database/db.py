from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session as S
from contextlib import contextmanager
from dotenv import load_dotenv
import os

load_dotenv()
db_name = os.environ.get('DB_NAME')
username = os.environ.get('DB_USERNAME')
password = os.environ.get('DB_PASSWORD')

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

def get_session_cursor(session_db: S, dictionary=False):
    connection = session_db.connection()
    cursor = connection.connection.cursor(dictionary=dictionary)
    return cursor