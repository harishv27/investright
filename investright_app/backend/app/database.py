from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def ensure_schema():
    Base.metadata.create_all(bind=engine)
    user_columns = {column["name"] for column in inspect(engine).get_columns("users")}
    if "full_name" not in user_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR"))

    # Seed admin user if not present or ensure password is admin@1234
    try:
        from app import auth
        from app.models import User
        with SessionLocal() as session:
            for admin_ident in ("admin", "admin@investright.com"):
                admin_user = session.query(User).filter(User.email == admin_ident).first()
                if not admin_user:
                    admin_user = User(
                        email=admin_ident,
                        full_name="Administrator",
                        hashed_password=auth.hash_password("admin@1234"),
                        age=30,
                    )
                    session.add(admin_user)
                else:
                    admin_user.hashed_password = auth.hash_password("admin@1234")
            session.commit()
    except Exception as e:
        print(f"Admin seeding notice: {e}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
