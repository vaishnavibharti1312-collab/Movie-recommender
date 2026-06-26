from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="viewer") # 'viewer' or 'company_admin'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Movie(Base):
    __tablename__ = "movies"
    movie_id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    overview = Column(Text)
    genres = Column(String) # Comma-separated or JSON string
    release_year = Column(Integer)
    language = Column(String)
    runtime = Column(Integer)
    popularity = Column(Float)
    vote_average = Column(Float)
    vote_count = Column(Integer)
    poster_url = Column(String)
    cast = Column(Text) # Top actors
    crew = Column(Text) # Director name

class Platform(Base):
    __tablename__ = "platforms"
    platform_id = Column(Integer, primary_key=True, index=True)
    platform_name = Column(String, unique=True, index=True)

class MoviePlatform(Base):
    __tablename__ = "movie_platforms"
    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.movie_id"))
    platform_id = Column(Integer, ForeignKey("platforms.platform_id"))
    availability_status = Column(Boolean, default=True)

class Rating(Base):
    __tablename__ = "ratings"
    rating_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    movie_id = Column(Integer, ForeignKey("movies.movie_id"))
    rating = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class Review(Base):
    __tablename__ = "reviews"
    review_id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.movie_id"))
    review_text = Column(Text)
    sentiment = Column(String) # 'positive', 'neutral', 'negative'
    sentiment_score = Column(Float)

class Recommendation(Base):
    __tablename__ = "recommendations"
    recommendation_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    movie_id = Column(Integer, ForeignKey("movies.movie_id"))
    recommendation_type = Column(String)
    score = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ChurnPrediction(Base):
    __tablename__ = "churn_predictions"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.user_id"))
    churn_probability = Column(Float)
    risk_level = Column(String)
    important_features = Column(String) # JSON string
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class TrendData(Base):
    __tablename__ = "trend_data"
    trend_id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String)
    genre = Column(String)
    date = Column(DateTime)
    trend_score = Column(Float)

class ChatbotLog(Base):
    __tablename__ = "chatbot_logs"
    log_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    query = Column(Text)
    response = Column(Text)
    chatbot_type = Column(String) # 'viewer' or 'company'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
