import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.database import SessionLocal
from backend.models import Movie, Review
import numpy as np

def get_ad_recommendations(movie_id: int):
    db = SessionLocal()
    movie = db.query(Movie).filter(Movie.movie_id == movie_id).first()
    
    if not movie:
        db.close()
        return []

    # Get movie reviews to assess sentiment
    reviews = db.query(Review).filter(Review.movie_id == movie_id).all()
    avg_sentiment = 0.0
    if reviews:
        avg_sentiment = np.mean([r.sentiment_score for r in reviews])
        
    db.close()
    
    # 5 Ad Categories and default base configurations
    ad_profiles = {
        "Gaming & Tech": {
            "segment": "Teens & Young Adults (15-30)",
            "base_reason": "High-energy entertainment matches gaming consoles, gadgets, and tech brand profiles."
        },
        "Food Delivery & Snacks": {
            "segment": "Binge Watchers & Families (All Ages)",
            "base_reason": "Perfect fit for quick bites, snacks, and meal delivery during immersive viewing."
        },
        "Finance & Insurance": {
            "segment": "Working Professionals (25-50)",
            "base_reason": "Premium content attracts mature audiences looking for trading apps, credit cards, or insurance."
        },
        "Automotive & Travel": {
            "segment": "Active Adults (18-45)",
            "base_reason": "Action and adventure themes align with cars, ride-hailing services, and vacation bookings."
        },
        "Family & Lifestyle": {
            "segment": "Families & Children (All Ages)",
            "base_reason": "Wholesome, positive programming makes it safe for home goods, groceries, and educational apps."
        }
    }
    
    scores = {cat: 30.0 for cat in ad_profiles} # start with base score
    reasons = {cat: ad_profiles[cat]["base_reason"] for cat in ad_profiles}
    
    genres = [g.strip().lower() for g in movie.genres.split(',')]
    
    # Genre-based rules
    if any(g in genres for g in ["action", "sci-fi", "adventure"]):
        scores["Gaming & Tech"] += 35
        scores["Automotive & Travel"] += 20
        reasons["Gaming & Tech"] = "Action/Sci-Fi themes have strong overlap with tech-savvy youth segments who purchase gaming consoles and hardware."
        
    if any(g in genres for g in ["comedy", "animation", "family"]):
        scores["Family & Lifestyle"] += 40
        scores["Food Delivery & Snacks"] += 20
        reasons["Family & Lifestyle"] = "Wholesome comedy and animation are perfect for family-safe household goods and kids' educational campaigns."
        
    if any(g in genres for g in ["thriller", "horror", "mystery"]):
        scores["Food Delivery & Snacks"] += 30
        scores["Gaming & Tech"] += 15
        reasons["Food Delivery & Snacks"] = "Suspenseful thrillers keep viewers glued to their screens, making snack and food delivery ads highly effective during intervals."
        
    if any(g in genres for g in ["drama", "romance"]):
        scores["Automotive & Travel"] += 15
        scores["Family & Lifestyle"] += 20
        reasons["Automotive & Travel"] = "Drama and romance narratives drive emotional engagement, which works well for travel bookings and lifestyle brands."
        
    if any(g in genres for g in ["crime", "biography"]):
        scores["Finance & Insurance"] += 35
        scores["Automotive & Travel"] += 10
        reasons["Finance & Insurance"] = "Documentaries, biographies, and crime thrillers attract highly engaged, professional demographics suited for financial services."

    # Binge Potential (Runtime / Popularity)
    # Long runtimes increase likelihood of ordering food
    if movie.runtime > 120:
        scores["Food Delivery & Snacks"] += 15
        reasons["Food Delivery & Snacks"] += " (Boosted: Long runtime increases binge-watching food ordering probability.)"
        
    # Popularity boost
    if movie.popularity > 70:
        for cat in scores:
            scores[cat] += 10
            
    # Sentiment modifier: positive sentiment benefits finance/premium products
    if avg_sentiment > 0.5:
        scores["Finance & Insurance"] += 10
        reasons["Finance & Insurance"] += " (Boosted: High positive audience sentiment correlates with higher conversion on premium finance products.)"
    elif avg_sentiment < -0.2:
        # Negative reviews: suggest stress-relief products (snacks/food)
        scores["Food Delivery & Snacks"] += 10
        reasons["Food Delivery & Snacks"] += " (Boosted: High negative sentiment content pairs well with comfort-food ad campaigns.)"
        
    # Compile results
    recommendations = []
    for cat, score in scores.items():
        suitability = min(100.0, max(10.0, score))
        recommendations.append({
            "category": cat,
            "suitability_score": round(suitability, 1),
            "target_audience": ad_profiles[cat]["segment"],
            "reason": reasons[cat]
        })
        
    # Sort by suitability score descending
    recommendations = sorted(recommendations, key=lambda x: x["suitability_score"], reverse=True)
    return recommendations

if __name__ == "__main__":
    import json
    print(json.dumps(get_ad_recommendations(1), indent=2))
