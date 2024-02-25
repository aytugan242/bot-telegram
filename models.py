import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class UserWord(Base):
    __tablename__ = 'user_words'
    id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey('users.id'))
    word = sq.Column(sq.String)
class User(Base):
    __tablename__ = 'users'
    id = sq.Column(sq.Integer, primary_key=True)
    chat_id = sq.Column(sq.Integer)
    words = relationship('UserWord', backref='user')

def create_tables(engine):
    # Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    print('Находимся в файле моделей, запускайте main.py')