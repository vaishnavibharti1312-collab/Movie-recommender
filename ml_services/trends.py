import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.database import SessionLocal
from backend.models import TrendData, Movie, Rating

def get_trending_genres():
    db = SessionLocal()
    # Simple recent logic: genres of movies rated in the last 30 days
    recent_date = datetime.utcnow() - timedelta(days=30)
    ratings = db.query(Rating).filter(Rating.timestamp >= recent_date).all()
    
    if not ratings:
        # Fallback to general top rated
        top_movies = db.query(Movie).order_by(Movie.vote_average.desc()).limit(20).all()
        genre_counts = {}
        for m in top_movies:
            for g in m.genres.split(','):
                g = g.strip()
                genre_counts[g] = genre_counts.get(g, 0) + 1
        sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
        db.close()
        return {"trending_genres": [g[0] for g in sorted_genres[:3]]}
        
    movie_ids = [r.movie_id for r in ratings]
    movies = db.query(Movie).filter(Movie.movie_id.in_(movie_ids)).all()
    db.close()
    
    genre_counts = {}
    for movie in movies:
        for g in movie.genres.split(','):
            g = g.strip()
            genre_counts[g] = genre_counts.get(g, 0) + 1
            
    sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
    return {"trending_genres": [g[0] for g in sorted_genres[:3]]}

def forecast_genre_trends():
    db = SessionLocal()
    trend_records = db.query(TrendData).order_by(TrendData.date.asc()).all()
    db.close()
    
    if not trend_records:
        return {
            "forecasts": {},
            "top_growing": ["Sci-Fi", "Thriller"],
            "top_declining": ["Romance"],
            "investment_recommendation": "No historical trend data found to generate recommendations."
        }
        
    # Group by genre
    data_by_genre = {}
    for r in trend_records:
        if r.genre not in data_by_genre:
            data_by_genre[r.genre] = []
        data_by_genre[r.genre].append({
            "date": r.date.strftime("%Y-%m-%d"),
            "score": r.trend_score
        })
        
    forecasts = {}
    growth_rates = {}
    
    for genre, history in data_by_genre.items():
        if len(history) < 2:
            continue
            
        scores = [h['score'] for h in history]
        x = np.arange(len(scores))
        y = np.array(scores)
        
        # Fit linear regression: y = m * x + c
        m, c = np.polyfit(x, y, 1)
        growth_rates[genre] = float(m)
        
        # Forecast next 3 months (indices 12, 13, 14)
        last_date_str = history[-1]['date']
        last_date = datetime.strptime(last_date_str, "%Y-%m-%d")
        
        forecast_points = []
        for i in range(1, 4):
            forecast_date = last_date + timedelta(days=i * 30.5)
            forecast_idx = len(scores) - 1 + i
            pred_score = max(0.0, min(100.0, float(m * forecast_idx + c)))
            forecast_points.append({
                "date": forecast_date.strftime("%Y-%m-%d"),
                "score": round(pred_score, 2),
                "is_forecast": True
            })
            
        forecasts[genre] = {
            "history": history,
            "forecast": forecast_points,
            "slope": round(float(m), 2),
            "status": "Rising" if m > 1.5 else "Declining" if m < -1.5 else "Stable"
        }
        
    # Sort genres by growth slope
    sorted_genres = sorted(growth_rates.items(), key=lambda x: x[1], reverse=True)
    top_growing = [g[0] for g in sorted_genres if g[1] > 1.0][:3]
    top_declining = [g[0] for g in sorted_genres if g[1] < -1.0][:2]
    
    # Generate content investment suggestions
    growing_str = ", ".join(top_growing) if top_growing else "none"
    declining_str = ", ".join(top_declining) if top_declining else "none"
    
    recommendation = (
        f"Based on 12-month search interest forecasting: "
        f"Demand for {growing_str} shows solid upward momentum. We recommend shifting content acquisition budgets "
        f"towards acquiring new releases in these growing genres. "
        f"Conversely, interest in {declining_str} is soft or declining; content licensing renewals for these genres should be reviewed and scaled back."
    )
    
    return {
        "forecasts": forecasts,
        "top_growing": top_growing,
        "top_declining": top_declining,
        "investment_recommendation": recommendation
    }

if __name__ == "__main__":
    import json
    print(json.dumps(forecast_genre_trends(), indent=2))
