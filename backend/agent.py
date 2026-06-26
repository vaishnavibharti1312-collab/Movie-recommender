import os
import logging
from typing import List, Dict, Any, Optional
import google.generativeai as genai

from backend.database import SessionLocal
from backend import models
from ml_services.recommendation import get_hybrid_recommendations, get_content_recommendations
from ml_services.churn import predict_churn_for_user
from ml_services.trends import forecast_genre_trends
from ml_services.ad_placement import get_ad_recommendations

logger = logging.getLogger(__name__)

# Configure Gemini API
API_KEY = os.environ.get("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

def is_agent_active() -> bool:
    """Checks if the Gemini API key is configured and the agent can run."""
    return bool(os.environ.get("GEMINI_API_KEY"))

# --- Define Tools for the Agent ---

def search_movies_db(
    title: Optional[str] = None,
    genre: Optional[str] = None,
    platform: Optional[str] = None,
    min_rating: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Search the movie database using filters.
    
    Args:
        title: Optional substring of the movie title to search for.
        genre: Optional genre name (e.g. Action, Sci-Fi, Drama, Comedy, Thriller, Romance, Horror).
        platform: Optional streaming platform name (e.g. Netflix, Amazon Prime, Disney+ Hotstar, Zee5, SonyLIV).
        min_rating: Optional minimum average rating (out of 10).
        
    Returns:
        A list of matching movie dictionaries containing title, genres, release year, vote average, and streaming platforms.
    """
    db = SessionLocal()
    try:
        query = db.query(models.Movie)
        if title:
            query = query.filter(models.Movie.title.like(f"%{title}%"))
        if genre:
            query = query.filter(models.Movie.genres.like(f"%{genre}%"))
            
        if platform:
            db_platform = platform
            p_lower = platform.lower()
            if "netflix" in p_lower: db_platform = "Netflix"
            elif "amazon" in p_lower or "prime" in p_lower: db_platform = "Amazon Prime"
            elif "disney" in p_lower or "hotstar" in p_lower: db_platform = "Disney+ Hotstar"
            elif "zee" in p_lower: db_platform = "Zee5"
            elif "sony" in p_lower or "liv" in p_lower: db_platform = "SonyLIV"
            
            query = query.join(models.MoviePlatform).join(models.Platform).filter(
                models.Platform.platform_name.like(f"%{db_platform}%")
            )
            
        if min_rating:
            query = query.filter(models.Movie.vote_average >= min_rating)
            
        movies = query.limit(10).all()
        
        results = []
        for m in movies:
            plat_names = db.query(models.Platform.platform_name).join(models.MoviePlatform).filter(models.MoviePlatform.movie_id == m.movie_id).all()
            platforms_list = [p[0] for p in plat_names]
            
            results.append({
                "movie_id": m.movie_id,
                "title": m.title,
                "genres": m.genres,
                "release_year": m.release_year,
                "vote_average": m.vote_average,
                "overview": m.overview,
                "platforms": platforms_list
            })
        return results
    except Exception as e:
        logger.error(f"Error in search_movies_db tool: {e}")
        return []
    finally:
        db.close()

def get_user_recommendations(user_id: int) -> List[Dict[str, Any]]:
    """
    Retrieve personalized hybrid machine learning recommendations for a specific viewer profile.
    
    Args:
        user_id: The integer ID of the viewer user profile.
        
    Returns:
        A list of recommended movie dicts containing title, similarity reason, and streaming platforms.
    """
    try:
        return get_hybrid_recommendations(user_id=user_id, top_n=3)
    except Exception as e:
        logger.error(f"Error in get_user_recommendations tool: {e}")
        return []

def get_similar_movies(movie_title: str) -> List[Dict[str, Any]]:
    """
    Find content-based recommendations for movies similar to a given title.
    
    Args:
        movie_title: The title of the movie to find matches for (e.g. 'Inception').
        
    Returns:
        A list of similar movie dicts or an empty list if the movie is not cataloged.
    """
    db = SessionLocal()
    try:
        m = db.query(models.Movie).filter(models.Movie.title.like(f"%{movie_title}%")).first()
        if m:
            return get_content_recommendations(m.movie_id, top_n=3)
        return []
    except Exception as e:
        logger.error(f"Error in get_similar_movies tool: {e}")
        return []
    finally:
        db.close()

def get_business_dashboard_kpis() -> Dict[str, Any]:
    """
    Fetch platform operational stats and business metrics.
    
    Returns:
        A summary dictionary containing total movies, total user profiles, average rating, sentiment ratios, and churn counts.
    """
    db = SessionLocal()
    try:
        total_movies = db.query(models.Movie).count()
        total_users = db.query(models.User).count()
        avg_rating = db.query(models.Movie.vote_average).filter(models.Movie.vote_average > 0).all()
        avg_score = sum(r[0] for r in avg_rating) / len(avg_rating) if avg_rating else 0.0
        
        reviews = db.query(models.Review).all()
        pos = sum(1 for r in reviews if r.sentiment == 'positive')
        neg = sum(1 for r in reviews if r.sentiment == 'negative')
        neu = sum(1 for r in reviews if r.sentiment == 'neutral')
        total_reviews = len(reviews)
        
        sentiment_ratios = {
            "positive": (pos / total_reviews * 100) if total_reviews else 0.0,
            "negative": (neg / total_reviews * 100) if total_reviews else 0.0,
            "neutral": (neu / total_reviews * 100) if total_reviews else 0.0
        }
        
        churns = db.query(models.ChurnPrediction).all()
        high = sum(1 for c in churns if c.risk_level == "High")
        med = sum(1 for c in churns if c.risk_level == "Medium")
        low = sum(1 for c in churns if c.risk_level == "Low")
        
        return {
            "total_movies": total_movies,
            "total_users": total_users,
            "average_rating": round(avg_score, 2),
            "total_reviews": total_reviews,
            "sentiment_ratios": sentiment_ratios,
            "churn_summary": {"High": high, "Medium": med, "Low": low}
        }
    except Exception as e:
        logger.error(f"Error in get_business_dashboard_kpis tool: {e}")
        return {}
    finally:
        db.close()

def get_churn_risk_profile(user_id: int) -> Dict[str, Any]:
    """
    Run the Random Forest ML churn model to predict churn probability and risk factors for a subscriber.
    
    Args:
        user_id: The integer ID of the subscriber profile.
        
    Returns:
        A dictionary containing the calculated churn probability, risk level (High/Medium/Low), and primary risk factors.
    """
    try:
        return predict_churn_for_user(user_id)
    except Exception as e:
        logger.error(f"Error in get_churn_risk_profile tool: {e}")
        return {}

def get_genre_trends_forecast() -> Dict[str, Any]:
    """
    Fetch linear regression forecasts projecting monthly popularity trends for major content genres.
    
    Returns:
        A trend dict with top growing genres, top declining genres, and slope growth metrics.
    """
    try:
        return forecast_genre_trends()
    except Exception as e:
        logger.error(f"Error in get_genre_trends_forecast tool: {e}")
        return {}

def get_ad_targeting(movie_title: str) -> Dict[str, Any]:
    """
    Evaluate ad suitability, matching score, and targeted ad categories for a content title.
    
    Args:
        movie_title: The title of the movie (e.g. 'Inception').
        
    Returns:
        Ad campaigns matching the movie profile, or empty dict if not found.
    """
    db = SessionLocal()
    try:
        m = db.query(models.Movie).filter(models.Movie.title.like(f"%{movie_title}%")).first()
        if m:
            return get_ad_recommendations(m.movie_id)
        return {}
    except Exception as e:
        logger.error(f"Error in get_ad_targeting tool: {e}")
        return {}
    finally:
        db.close()

# --- Agentic RAG Execution Engine ---

def run_agentic_chat(query: str, is_business_analyst: bool = False, user_id: int = 3) -> str:
    """
    Run the Agentic RAG system. The LLM selects tools automatically, queries the SQLite database/models, 
    and synthesizes a natural language response.
    """
    if not is_agent_active():
        raise ValueError("Gemini API key is not configured.")
        
    try:
        # Define the set of tools available to the model
        tools = [
            search_movies_db,
            get_user_recommendations,
            get_similar_movies,
            get_business_dashboard_kpis,
            get_churn_risk_profile,
            get_genre_trends_forecast,
            get_ad_targeting
        ]
        
        # Configure instructions depending on whether the persona is viewer or business admin
        if is_business_analyst:
            system_instruction = (
                "You are an Advanced Business Analyst Agent for an OTT Platform. "
                "Use the provided tools to query business KPIs, churn risk profiles, and genre trends to answer "
                "analytical questions. Speak professionally, cite the numbers retrieved from the tools, and "
                "structure your answers with bold text and summaries."
            )
        else:
            system_instruction = (
                f"You are a friendly, helpful Movie Discovery Assistant. The current user is profile ID {user_id}. "
                "Use the provided tools to search for movies, suggest recommendations, find similar titles, "
                "and explain movie details. Always mention which streaming platforms movies are available on. "
                "Format your responses nicely with HTML tags like <strong>, <em>, and bullet points."
            )
            
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            tools=tools,
            system_instruction=system_instruction
        )
        
        # Start a chat with automatic tool resolution enabled
        chat = model.start_chat(enable_automatic_function_calling=True)
        response = chat.send_message(query)
        
        return response.text
    except Exception as e:
        logger.error(f"Error in Agentic RAG chat execution: {e}")
        raise e
