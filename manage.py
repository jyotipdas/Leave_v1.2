from sqlalchemy import create_engine, String, DateTime,Integer,Boolean,ForeignKey,Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker,relationship,backref

engine = create_engine('sqlite:///d3_leave.db')
Session = sessionmaker(bind=engine)
db = Session()
Base = declarative_base()

class User(Base):
    __tablename__='users'

    id = Column(Integer, primary_key=True)
    username = Column(String(15), nullable=False)
    password = Column(String(80), nullable=False)
    balance = Column(Integer,nullable=False)

class Leavedetail(Base):
    __tablename__='leavedetail'

    id = Column(Integer, primary_key=True)
    start_date = Column(DateTime,nullable=False)
    end_date = Column(DateTime, nullable=False)
    days = Column(Integer,nullable=False)
    raised_time = Column(DateTime, nullable=False)
    reason = Column(String(300))
    active = Column(Boolean,default=True)
    compoff = Column(Boolean,default=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User",backref=backref('leavedetail',order_by=user_id))

class Compoff(Base):
    __tablename__ = 'compoff'

    id = Column(Integer, primary_key=True)
    worked_date = Column(DateTime,nullable=False)
    logged_date = Column(DateTime,nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", backref=backref('leavedetail', order_by=user_id))
