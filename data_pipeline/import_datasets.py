import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import random
from datetime import datetime, timedelta
import json
from backend.database import SessionLocal, engine
from backend import models
from ml_services.sentiment import analyze_sentiment

def parse_genres(genres_str):
    try:
        genres_list = json.loads(genres_str)
        names = [g['name'] for g in genres_list]
        return ",".join(names) if names else "Drama"
    except Exception:
        return "Drama"

def translate_language(lang_code):
    mapping = {
        "en": "English",
        "hi": "Hindi",
        "es": "Spanish",
        "ko": "Korean",
        "ja": "Japanese",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "cn": "Chinese",
        "zh": "Chinese",
        "ru": "Russian",
        "pt": "Portuguese"
    }
    return mapping.get(str(lang_code).lower(), str(lang_code).upper())

def parse_cast(cast_str):
    try:
        cast_list = json.loads(cast_str)
        names = [c['name'] for c in cast_list[:3]] # top 3 actors
        return ", ".join(names)
    except Exception:
        return ""

def parse_director(crew_str):
    try:
        crew_list = json.loads(crew_str)
        for c in crew_list:
            if c.get('job') == 'Director':
                return c.get('name')
        return ""
    except Exception:
        return ""

def import_custom_datasets():
    dest_dir = os.path.dirname(os.path.abspath(__file__))
    ds1_path = os.path.join(dest_dir, "dataset1.csv") # credits
    ds2_path = os.path.join(dest_dir, "dataset2.csv") # movies
    
    if not os.path.exists(ds1_path) or not os.path.exists(ds2_path):
        print("Error: dataset CSV files not found. Please verify download.")
        return
        
    try:
        df_movies = pd.read_csv(ds2_path)
        df_credits = pd.read_csv(ds1_path)
        print(f"Loaded movies shape: {df_movies.shape}, credits shape: {df_credits.shape}")
        
        # Merge on title
        df = pd.merge(df_movies, df_credits, on='title')
        print(f"Merged datasets shape: {df.shape}")
    except Exception as e:
        print(f"Failed to read and merge CSV files: {e}")
        return

    # Clear and recreate database tables
    print("Clearing old tables and recreating schemas...")
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 1. Create Users
    users = []
    # Admins
    users.append(models.User(name="Admin Alice", email="alice@ott.com", password_hash="hashed_admin_1", role="company_admin"))
    users.append(models.User(name="Admin Bob", email="bob@ott.com", password_hash="hashed_admin_2", role="company_admin"))
    # 48 normal viewers
    for i in range(1, 49):
        users.append(models.User(
            name=f"Viewer {i}",
            email=f"viewer{i}@example.com",
            password_hash="hashed_password",
            role="viewer"
        ))
    db.add_all(users)
    db.commit()
    print(f"Created {len(users)} users.")

    # 2. Create Platforms
    platform_names = ["Netflix", "Amazon Prime", "Disney+ Hotstar", "Zee5", "SonyLIV"]
    platforms = []
    for name in platform_names:
        p = models.Platform(platform_name=name)
        platforms.append(p)
    db.add_all(platforms)
    db.commit()
    print("Created platforms.")

    # 3. Process and Insert Movies from TMDB
    print("Processing and inserting TMDB movies with cast & director...")
    movies = []
    unique_titles = set()
    
    # Sort by popularity to prioritize popular movies in default queries
    df_sorted = df.sort_values(by='popularity', ascending=False)
    
    for idx, row in df_sorted.iterrows():
        title = str(row['title']).strip()
        if not title or title == 'nan' or title in unique_titles:
            continue
        unique_titles.add(title)
        
        # Parse Genres
        genres = parse_genres(row['genres'])
        
        # Parse Overview
        overview = str(row['overview']) if not pd.isna(row['overview']) else "No overview description available."
        
        # Parse Year
        year = 2015
        if not pd.isna(row['release_date']):
            try:
                date_str = str(row['release_date'])
                year = int(date_str.split('-')[0])
            except Exception:
                pass
                
        # Parse Language
        lang = translate_language(row['original_language'])
        
        # Numeric values
        popularity = float(row['popularity']) if not pd.isna(row['popularity']) else 10.0
        vote_average = float(row['vote_average']) if not pd.isna(row['vote_average']) else 7.0
        vote_count = int(row['vote_count']) if not pd.isna(row['vote_count']) else 100
        runtime = int(row['runtime']) if not pd.isna(row['runtime']) else 110
        if runtime <= 0: runtime = 110
        
        # Parse Cast & Director
        cast = parse_cast(row['cast'])
        director = parse_director(row['crew'])
        
        m = models.Movie(
            title=title,
            overview=overview,
            genres=genres,
            release_year=year,
            language=lang,
            runtime=runtime,
            popularity=round(popularity, 2),
            vote_average=vote_average,
            vote_count=vote_count,
            poster_url=f"https://via.placeholder.com/300x450/1e293b/f8fafc?text={title.replace(' ', '+')}",
            cast=cast,
            crew=director
        )
        movies.append(m)
        
    db.add_all(movies)
    db.commit()
    print(f"Imported {len(movies)} unique movies into database.")

    # 4. Map Movies to Platforms
    print("Mapping movies to streaming platforms...")
    movie_platforms = []
    for m in movies:
        assigned_p = random.sample(platforms, random.randint(1, 3))
        for p in assigned_p:
            mp = models.MoviePlatform(
                movie_id=m.movie_id,
                platform_id=p.platform_id,
                availability_status=True
            )
            movie_platforms.append(mp)
    db.add_all(movie_platforms)
    db.commit()

    # 5. Populate Ratings & Reviews
    print("Generating dense user rating and review matrices...")
    top_popular_subset = movies[:300]
    
    ratings = []
    reviews = []
    
    pos_reviews = [
        "Absolutely amazing! One of the best movies of all time.",
        "A visual masterpiece and a narrative triumph. Loved every single detail.",
        "Highly recommended! The acting was superb and the plot kept me hooked.",
        "Brilliant screenplay and incredible music score. I will watch it again."
    ]
    neg_reviews = [
        "A complete waste of time. The story was full of plot holes.",
        "Worst movie I have seen this year. Extremely boring and way too long.",
        "Disappointing effort. It was slow, confusing, and uninteresting."
    ]
    neu_reviews = [
        "It was okay. Had some good visual moments but predictable.",
        "Average movie. Good for a one-time watch.",
        "Decent performances but the pacing was off."
    ]

    for user in users:
        # Rate 15 to 25 movies from the popular subset
        num_to_rate = random.randint(15, 25) if user.role == "viewer" else 5
        rated_movies = random.sample(top_popular_subset, num_to_rate)
        
        for m in rated_movies:
            base = m.vote_average / 2.0
            r = round(clip(random.normalvariate(base, 0.5), 1.0, 5.0), 1)
            
            timestamp = datetime.utcnow() - timedelta(days=random.randint(1, 360))
            rating_obj = models.Rating(
                user_id=user.user_id,
                movie_id=m.movie_id,
                rating=r,
                timestamp=timestamp
            )
            ratings.append(rating_obj)
            
            if random.random() < 0.5:
                text = random.choice(pos_reviews) if r >= 4.0 else random.choice(neg_reviews) if r <= 2.5 else random.choice(neu_reviews)
                sentiment_label, score = analyze_sentiment(text)
                
                review_obj = models.Review(
                    movie_id=m.movie_id,
                    review_text=text,
                    sentiment=sentiment_label,
                    sentiment_score=score
                )
                reviews.append(review_obj)

    db.add_all(ratings)
    db.add_all(reviews)
    db.commit()
    print(f"Generated {len(ratings)} ratings and {len(reviews)} reviews.")

    # 6. Generate TrendData (last 12 months for 7 major genres)
    print("Generating search interest trends...")
    trend_genres = ["Sci-Fi", "Action", "Drama", "Comedy", "Thriller", "Romance", "Horror"]
    trends = []
    
    base_scores = {
        "Sci-Fi": (50, 4.0),
        "Action": (70, 0.5),
        "Drama": (60, -1.0),
        "Comedy": (65, 0.8),
        "Thriller": (55, 2.5),
        "Romance": (45, -2.0),
        "Horror": (30, 1.5)
    }

    start_date = datetime.utcnow() - timedelta(days=365)
    for month_offset in range(12):
        current_month = start_date + timedelta(days=month_offset * 30.5)
        for g in trend_genres:
            start, slope = base_scores[g]
            score = round(clip(start + (slope * month_offset) + random.uniform(-5.0, 5.0), 10.0, 100.0), 2)
            t = models.TrendData(
                keyword=f"{g} movies",
                genre=g,
                date=current_month,
                trend_score=score
            )
            trends.append(t)
    db.add_all(trends)

    # 7. Generate Churn Predictions
    print("Generating subscriber churn profiles...")
    churn_predictions = []
    device_options = ["Smart TV", "Mobile", "Laptop", "Tablet"]
    payment_options = ["Credit Card", "UPI", "Net Banking", "Wallets"]

    for viewer in users:
        if viewer.role != "viewer":
            continue
            
        profile_type = random.choice(["high_engagement", "medium_engagement", "at_risk"])
        
        if profile_type == "high_engagement":
            watch_time = random.randint(80, 180)
            logins = random.randint(15, 30)
            complaints = random.randint(0, 1)
            prev_cancels = 0
            monthly_charges = random.choice([9.99, 14.99])
        elif profile_type == "medium_engagement":
            watch_time = random.randint(30, 80)
            logins = random.randint(6, 15)
            complaints = random.randint(0, 2)
            prev_cancels = 0
            monthly_charges = random.choice([14.99, 19.99])
        else: # at_risk
            watch_time = random.randint(2, 25)
            logins = random.randint(1, 5)
            complaints = random.randint(2, 5)
            prev_cancels = random.choice([0, 1, 1])
            monthly_charges = 19.99
            
        prob = 0.1
        if watch_time < 20: prob += 0.35
        if logins < 5: prob += 0.25
        if complaints >= 3: prob += 0.20
        if prev_cancels > 0: prob += 0.15
        
        prob = clip(prob + random.uniform(-0.05, 0.05), 0.05, 0.95)
        risk = "High" if prob > 0.65 else "Medium" if prob > 0.35 else "Low"
        
        features_dict = {
            "watch_time": watch_time,
            "logins": logins,
            "monthly_charges": monthly_charges,
            "support_complaints": complaints,
            "previous_cancellations": prev_cancels,
            "device_usage": random.choice(device_options),
            "payment_method": random.choice(payment_options)
        }
        
        churn_pred = models.ChurnPrediction(
            customer_id=viewer.user_id,
            churn_probability=round(prob, 2),
            risk_level=risk,
            important_features=json.dumps(features_dict)
        )
        churn_predictions.append(churn_pred)

    db.add_all(churn_predictions)
    db.commit()
    db.close()
    print("Database built and merged custom TMDB movies + credits dataset loaded successfully!")

def clip(val, min_val, max_val):
    return max(min_val, min(val, max_val))

if __name__ == "__main__":
    import_custom_datasets()
