from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from backend.models import Movie, Rating, Platform, MoviePlatform
from backend.database import SessionLocal

def get_content_recommendations(movie_id: int, top_n: int = 5):
    db = SessionLocal()
    movies = db.query(Movie).all()
    
    if not movies or len(movies) <= 1:
        db.close()
        return []

    # Prepare DataFrame
    df = pd.DataFrame([{
        "movie_id": m.movie_id,
        "title": m.title,
        "genres": m.genres,
        "vote_average": m.vote_average,
        "poster_url": m.poster_url,
        "combined_features": f"{m.genres} {m.overview} {m.cast} {m.crew}"
    } for m in movies])

    # TF-IDF Vectorization
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df['combined_features'])

    # Cosine Similarity
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    try:
        idx = df.index[df['movie_id'] == movie_id].tolist()[0]
    except IndexError:
        db.close()
        return []

    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:top_n+1] # Skip the movie itself
    
    recs = []
    for i, score in sim_scores:
        row = df.iloc[i].to_dict()
        movie_item = db.query(Movie).filter(Movie.movie_id == int(row['movie_id'])).first()
        
        # Get platforms
        plat_names = db.query(Platform.platform_name).join(MoviePlatform).filter(MoviePlatform.movie_id == movie_item.movie_id).all()
        platforms_list = [p[0] for p in plat_names]
        
        recs.append({
            "movie_id": movie_item.movie_id,
            "title": movie_item.title,
            "genres": movie_item.genres,
            "vote_average": movie_item.vote_average,
            "poster_url": movie_item.poster_url,
            "platforms": platforms_list,
            "similarity_score": round(float(score), 2),
            "reason": f"Highly similar to '{movie_item.title}' with matching themes."
        })
        
    db.close()
    return recs

def get_hybrid_recommendations(user_id: int, top_n: int = 5):
    db = SessionLocal()
    
    # 1. Fetch user ratings
    user_ratings = db.query(Rating).filter(Rating.user_id == user_id).all()
    all_movies = db.query(Movie).all()
    
    if not all_movies:
        db.close()
        return []
        
    # Helper to fetch platforms for a movie
    def get_movie_platforms(movie_id):
        plat_names = db.query(Platform.platform_name).join(MoviePlatform).filter(MoviePlatform.movie_id == movie_id).all()
        return [p[0] for p in plat_names]

    # If the user is new or has very few ratings, fall back to popularity-based recommendations
    if len(user_ratings) < 3:
        # Sort by popularity desc and vote_average desc
        top_popular = db.query(Movie).order_by(Movie.popularity.desc(), Movie.vote_average.desc()).limit(top_n).all()
        recs = []
        for m in top_popular:
            recs.append({
                "movie_id": m.movie_id,
                "title": m.title,
                "genres": m.genres,
                "vote_average": m.vote_average,
                "poster_url": m.poster_url,
                "platforms": get_movie_platforms(m.movie_id),
                "score": 0.9,
                "reason": "Recommended because it is trending with high viewer ratings across the platform."
            })
        db.close()
        return recs

    # 2. Extract user preferences (Favorite genres)
    rated_movie_ids = [r.movie_id for r in user_ratings]
    user_ratings_dict = {r.movie_id: r.rating for r in user_ratings}
    
    # Find movies the user rated highly (rating >= 3.5 on 5.0 scale)
    high_rated_movies = []
    genre_weights = {}
    
    for r in user_ratings:
        movie = db.query(Movie).filter(Movie.movie_id == r.movie_id).first()
        if movie:
            if r.rating >= 3.5:
                high_rated_movies.append(movie)
            # Accumulate genre interest
            for g in movie.genres.split(','):
                g = g.strip()
                genre_weights[g] = genre_weights.get(g, 0) + (r.rating - 2.5) # weight positive ratings higher

    # Normalize genre weights
    total_genre_weight = sum(genre_weights.values()) if genre_weights else 1
    for g in genre_weights:
        genre_weights[g] /= total_genre_weight

    # 3. Content-based TF-IDF Setup
    df = pd.DataFrame([{
        "movie_id": m.movie_id,
        "title": m.title,
        "genres": m.genres,
        "combined_features": f"{m.genres} {m.overview} {m.cast} {m.crew}"
    } for m in all_movies])

    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df['combined_features'])
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    
    movie_id_to_idx = {row['movie_id']: idx for idx, row in df.iterrows()}

    # 4. Score Candidate Movies (movies the user has NOT rated yet)
    candidates = [m for m in all_movies if m.movie_id not in rated_movie_ids]
    candidate_scores = []

    for m in candidates:
        # A. Genre Preference Score (0.0 to 1.0)
        genre_score = 0.0
        m_genres = [g.strip() for g in m.genres.split(',')]
        for g in m_genres:
            genre_score += genre_weights.get(g, 0.0)
        # Normalize by number of genres in movie to prevent penalizing broad movies
        genre_score = min(genre_score * 2.0, 1.0) # Boost slightly
        
        # B. Content Similarity Score (0.0 to 1.0)
        # Average similarity of this candidate to the user's high-rated movies
        content_sim_score = 0.0
        if high_rated_movies and m.movie_id in movie_id_to_idx:
            cand_idx = movie_id_to_idx[m.movie_id]
            sims = []
            for hm in high_rated_movies:
                if hm.movie_id in movie_id_to_idx:
                    hm_idx = movie_id_to_idx[hm.movie_id]
                    sims.append(cosine_sim[cand_idx][hm_idx])
            content_sim_score = np.mean(sims) if sims else 0.0

        # C. Quality / Popularity Score (0.0 to 1.0)
        quality_score = (m.vote_average / 10.0) * 0.7 + (min(m.popularity, 100.0) / 100.0) * 0.3
        
        # D. Combined Hybrid Score
        # Weighting: 40% Genre preference, 30% Content similarity, 30% Overall Quality
        hybrid_score = (0.4 * genre_score) + (0.3 * content_sim_score) + (0.3 * quality_score)
        
        # Determine natural language reason
        top_user_genre = max(genre_weights, key=genre_weights.get) if genre_weights else "Drama"
        matching_user_genres = [g for g in m_genres if g in genre_weights and genre_weights[g] > 0.05]
        
        if matching_user_genres and content_sim_score > 0.2:
            reason = f"Matches your interest in {matching_user_genres[0]} and is similar to other movies you enjoyed."
        elif matching_user_genres:
            reason = f"Matches your preference for {matching_user_genres[0]} movies."
        elif content_sim_score > 0.2:
            reason = f"Recommended because you enjoy themes found in this movie."
        else:
            reason = f"Highly rated on the platform in the {m_genres[0]} genre."

        candidate_scores.append({
            "movie_id": m.movie_id,
            "title": m.title,
            "genres": m.genres,
            "vote_average": m.vote_average,
            "poster_url": m.poster_url,
            "platforms": get_movie_platforms(m.movie_id),
            "score": round(float(hybrid_score), 2),
            "reason": reason
        })

    # Sort candidates by hybrid score descending
    candidate_scores = sorted(candidate_scores, key=lambda x: x['score'], reverse=True)
    
    db.close()
    return candidate_scores[:top_n]
