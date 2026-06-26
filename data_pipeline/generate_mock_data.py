import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from datetime import datetime, timedelta
import json
from backend.database import SessionLocal, engine
from backend import models
from ml_services.sentiment import analyze_sentiment

def create_mock_data():
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("Generating comprehensive mock data for OTT platform...")

    # 1. Create Users
    users = []
    # Add two admins
    users.append(models.User(name="Admin Alice", email="alice@ott.com", password_hash="hashed_admin_1", role="company_admin"))
    users.append(models.User(name="Admin Bob", email="bob@ott.com", password_hash="hashed_admin_2", role="company_admin"))
    
    # Add 48 normal viewers
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
    print(f"Created {len(platforms)} platforms.")

    # 3. Comprehensive Movies Dataset (60+ items)
    movies_list = [
        # Sci-Fi / Action
        {"title": "Inception", "genre": "Sci-Fi,Action,Thriller", "year": 2010, "rating": 8.8, "lang": "English", "overview": "A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O."},
        {"title": "Interstellar", "genre": "Sci-Fi,Drama,Adventure", "year": 2014, "rating": 8.6, "lang": "English", "overview": "A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival."},
        {"title": "The Matrix", "genre": "Sci-Fi,Action", "year": 1999, "rating": 8.7, "lang": "English", "overview": "A computer hacker learns from mysterious rebels about the true nature of his reality and his role in the war against its controllers."},
        {"title": "The Dark Knight", "genre": "Action,Crime,Drama", "year": 2008, "rating": 9.0, "lang": "English", "overview": "When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice."},
        {"title": "Avengers: Endgame", "genre": "Action,Sci-Fi,Adventure", "year": 2019, "rating": 8.4, "lang": "English", "overview": "After the devastating events of Infinity War, the Avengers assemble once more in order to reverse Thanos' actions and restore balance to the universe."},
        {"title": "Gladiator", "genre": "Action,Drama,Adventure", "year": 2000, "rating": 8.5, "lang": "English", "overview": "A former Roman General sets out to exact vengeance against the corrupt emperor who murdered his family and sent him into slavery."},
        {"title": "Dune", "genre": "Sci-Fi,Adventure,Drama", "year": 2021, "rating": 8.0, "lang": "English", "overview": "Feature adaptation of Frank Herbert's science fiction novel, about the son of a noble family entrusted with the protection of the most valuable asset and most vital element in the galaxy."},
        {"title": "Tenet", "genre": "Sci-Fi,Action,Thriller", "year": 2020, "rating": 7.3, "lang": "English", "overview": "Armed with only one word, Tenet, and fighting for the survival of the entire world, a Protagonist journeys through a twilight world of international espionage on a mission that will unfold in something beyond real time."},
        {"title": "Mad Max: Fury Road", "genre": "Action,Sci-Fi,Adventure", "year": 2015, "rating": 8.1, "lang": "English", "overview": "In a post-apocalyptic wasteland, a woman rebels against a tyrannical ruler in search for her homeland with the aid of a group of female prisoners, a psychotic worshiper, and a drifter named Max."},
        {"title": "John Wick", "genre": "Action,Thriller,Crime", "year": 2014, "rating": 7.4, "lang": "English", "overview": "An ex-hit-man comes out of retirement to track down the gangsters that killed his dog and took everything from him."},
        {"title": "Blade Runner 2049", "genre": "Sci-Fi,Drama,Mystery", "year": 2017, "rating": 8.0, "lang": "English", "overview": "A new blade runner, LAPD Officer K, unearths a long-buried secret that has the potential to plunge what's left of society into chaos."},
        {"title": "Arrival", "genre": "Sci-Fi,Drama,Mystery", "year": 2016, "rating": 7.9, "lang": "English", "overview": "A linguist works with the military to communicate with alien lifecorms after twelve mysterious spacecraft appear around the world."},
        
        # Drama
        {"title": "The Godfather", "genre": "Crime,Drama", "year": 1972, "rating": 9.2, "lang": "English", "overview": "The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son."},
        {"title": "Forrest Gump", "genre": "Drama,Romance", "year": 1994, "rating": 8.8, "lang": "English", "overview": "The presidencies of Kennedy and Johnson, the events of Vietnam, Watergate and other historical events unfold from the perspective of an Alabama man with an IQ of 75."},
        {"title": "Dangal", "genre": "Drama,Action,Biography", "year": 2016, "rating": 8.3, "lang": "Hindi", "overview": "Former wrestler Mahavir Singh Phogat and his two wrestler daughters struggle towards glory at the Commonwealth Games in the face of societal oppression."},
        {"title": "Parasite", "genre": "Thriller,Drama,Comedy", "year": 2019, "rating": 8.5, "lang": "Korean", "overview": "Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan."},
        {"title": "The Shawshank Redemption", "genre": "Drama", "year": 1994, "rating": 9.3, "lang": "English", "overview": "Over the course of several years, two convicts form a friendship, seeking consolation and, eventually, redemption through basic compassion."},
        {"title": "Pulp Fiction", "genre": "Crime,Drama", "year": 1994, "rating": 8.9, "lang": "English", "overview": "The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine in four tales of violence and redemption."},
        {"title": "Fight Club", "genre": "Drama", "year": 1999, "rating": 8.8, "lang": "English", "overview": "An insomniac office worker and a devil-may-care soapmaker form an underground fight club that evolves into something much, much more."},
        {"title": "Whiplash", "genre": "Drama,Music", "year": 2014, "rating": 8.5, "lang": "English", "overview": "A promising young drummer enrolls at a cut-throat music conservatory where his dreams of greatness are mentored by an instructor who will stop at nothing to realize a student's potential."},
        {"title": "The Social Network", "genre": "Drama,Biography", "year": 2010, "rating": 7.8, "lang": "English", "overview": "As Harvard student Mark Zuckerberg creates the social networking site that would become known as Facebook, he is sued by the twins who claimed he stole their idea, and his co-founder who was later squeezed out of the business."},
        {"title": "3 Idiots", "genre": "Comedy,Drama", "year": 2009, "rating": 8.4, "lang": "Hindi", "overview": "Two friends are searching for their long lost companion. They revisit their college days and recall the memories of their friend who inspired them to think differently, even as the world called them idiots."},

        # Comedy
        {"title": "Superbad", "genre": "Comedy", "year": 2007, "rating": 7.6, "lang": "English", "overview": "Two co-dependent high school seniors are forced to deal with separation anxiety after their plan to stage a booze-soaked party goes awry."},
        {"title": "The Hangover", "genre": "Comedy", "year": 2009, "rating": 7.7, "lang": "English", "overview": "Three buddies wake up from a bachelor party in Las Vegas, with no memory of the previous night and the bachelor missing. They make their way around the city in order to find their friend before his wedding."},
        {"title": "Knives Out", "genre": "Comedy,Mystery,Drama", "year": 2019, "rating": 7.9, "lang": "English", "overview": "A detective investigates the death of the patriarch of an eccentric, combative family."},
        {"title": "Groundhog Day", "genre": "Comedy,Fantasy,Romance", "year": 1993, "rating": 8.0, "lang": "English", "overview": "A narcissistic, self-centered weather presenter finds himself inexplicably living the same day over and over again."},
        {"title": "PK", "genre": "Comedy,Drama,Sci-Fi", "year": 2014, "rating": 8.1, "lang": "Hindi", "overview": "An alien on Earth loses the only device he can use to communicate with his spaceship. His innocent questions and childlike curiosity force the country to evaluate the impact of religion on its people."},
        {"title": "Crazy Rich Asians", "genre": "Comedy,Romance,Drama", "year": 2018, "rating": 6.9, "lang": "English", "overview": "This contemporary romantic comedy, based on a global bestseller, follows native New Yorker Rachel Chu to Singapore to meet her boyfriend's family."},
        
        # Romance
        {"title": "Titanic", "genre": "Romance,Drama", "year": 1997, "rating": 7.9, "lang": "English", "overview": "A seventeen-year-old aristocrat falls in love with a kind but poor artist aboard the luxurious, ill-fated R.M.S. Titanic."},
        {"title": "La La Land", "genre": "Romance,Drama,Music", "year": 2016, "rating": 8.0, "lang": "English", "overview": "While navigating their careers in Los Angeles, a pianist and an actress fall in love while attempting to reconcile their aspirations for the future."},
        {"title": "The Notebook", "genre": "Romance,Drama", "year": 2004, "rating": 7.8, "lang": "English", "overview": "An elderly man reads to a woman with Alzheimer's disease from a notebook. The notebook tells the story of a young couple who fall in love in the 1940s."},
        {"title": "Pride & Prejudice", "genre": "Romance,Drama", "year": 2005, "rating": 7.8, "lang": "English", "overview": "Sparks fly when spirited Elizabeth Bennet meets single, rich, and proud Mr. Darcy. But Mr. Darcy reluctantly finds himself falling in love with a woman beneath his class."},
        {"title": "Before Sunrise", "genre": "Romance,Drama", "year": 1995, "rating": 8.1, "lang": "English", "overview": "A young man and woman meet on a train in Europe, and wind up spending one evening together in Vienna. However, both know that this will probably be their only night together."},
        {"title": "Dilwale Dulhania Le Jayenge", "genre": "Romance,Drama,Comedy", "year": 1995, "rating": 8.0, "lang": "Hindi", "overview": "Raj and Simran meet on a trip to Europe. After Raj falls in love with Simran, he travels to India to win her and her family over."},

        # Thriller / Horror
        {"title": "La Casa de Papel", "genre": "Thriller,Drama,Crime", "year": 2017, "rating": 8.2, "lang": "Spanish", "overview": "An unusual group of robbers attempt to carry out the most perfect robbery in Spanish history - stealing 2.4 billion euros from the Royal Mint of Spain."},
        {"title": "Shutter Island", "genre": "Thriller,Mystery,Drama", "year": 2010, "rating": 8.2, "lang": "English", "overview": "In 1954, a U.S. Marshal investigates the disappearance of a murderer who escaped from a hospital for the criminally insane."},
        {"title": "Se7en", "genre": "Thriller,Crime,Mystery", "year": 1995, "rating": 8.6, "lang": "English", "overview": "Two detectives, a rookie and a veteran, hunt a serial killer who uses the seven deadly sins as his motives."},
        {"title": "Gone Girl", "genre": "Thriller,Mystery,Drama", "year": 2014, "rating": 8.1, "lang": "English", "overview": "With his wife's disappearance having become the focus of an intense media circus, a man sees the spotlight turned on him when it's suspected that he may not be innocent."},
        {"title": "The Silence of the Lambs", "genre": "Thriller,Crime,Drama", "year": 1991, "rating": 8.6, "lang": "English", "overview": "A young F.B.I. cadet must receive the help of an incarcerated and manipulative cannibal killer to help catch another serial killer, a madman who skins his victims."},
        {"title": "The Conjuring", "genre": "Horror,Mystery,Thriller", "year": 2013, "rating": 7.5, "lang": "English", "overview": "Paranormal investigators Ed and Lorraine Warren work to help a family terrorized by a dark presence in their farmhouse."},
        {"title": "Get Out", "genre": "Horror,Mystery,Thriller", "year": 2017, "rating": 7.8, "lang": "English", "overview": "A young African-American visits his white girlfriend's parents for the weekend, where his simmering uneasiness about their reception eventually reaches a boiling point."},
        {"title": "Hereditary", "genre": "Horror,Drama,Mystery", "year": 2018, "rating": 7.3, "lang": "English", "overview": "A grieving family is haunted by tragic and disturbing occurrences after the death of their secretive grandmother."},
        {"title": "A Quiet Place", "genre": "Horror,Sci-Fi,Drama", "year": 2018, "rating": 7.5, "lang": "English", "overview": "In a post-apocalyptic world, a family is forced to live in silence while hiding from monsters with ultra-sensitive hearing."},
        {"title": "Tumbbad", "genre": "Horror,Fantasy,Drama", "year": 2018, "rating": 8.2, "lang": "Hindi", "overview": "A mythological story about a goddess who created the entire universe. The plot revolves around the consequences when humans build a temple for her first-born, Hastar."},

        # Animation / Family
        {"title": "Spirited Away", "genre": "Animation,Adventure,Fantasy", "year": 2001, "rating": 8.6, "lang": "Japanese", "overview": "During her family's move to the suburbs, a sullen 10-year-old girl wanders into a world ruled by gods, witches, and spirits, and where humans are changed into beasts."},
        {"title": "Spider-Man: Into the Spider-Verse", "genre": "Animation,Action,Adventure", "year": 2018, "rating": 8.4, "lang": "English", "overview": "Teen Miles Morales becomes the Spider-Man of his universe, and must join with five spider-powered individuals from other dimensions to stop a threat for all realities."},
        {"title": "Inside Out", "genre": "Animation,Comedy,Drama", "year": 2015, "rating": 8.1, "lang": "English", "overview": "After young Riley is uprooted from her Midwest life and moved to San Francisco, her emotions - Joy, Fear, Anger, Disgust and Sadness - conflict on how best to navigate a new city, house and school."},
        {"title": "Coco", "genre": "Animation,Adventure,Comedy", "year": 2017, "rating": 8.4, "lang": "English", "overview": "Aspiring musician Miguel, confronted with his family's ancestral ban on music, enters the Land of the Dead to find his great-great-grandfather, a legendary singer."},
        {"title": "Toy Story", "genre": "Animation,Adventure,Comedy", "year": 1995, "rating": 8.3, "lang": "English", "overview": "A cowboy doll is profoundly threatened and jealous when a new spaceman figure supplants him as top toy in a boy's room."},
        {"title": "My Neighbor Totoro", "genre": "Animation,Family,Fantasy", "year": 1988, "rating": 8.1, "lang": "Japanese", "overview": "When two young girls move to the country to be near their ailing mother, they have adventures with the wondrous forest spirits who live nearby."},
        
        # Adventure / Mystery / Crime
        {"title": "Sherlock Holmes", "genre": "Action,Adventure,Mystery", "year": 2009, "rating": 7.6, "lang": "English", "overview": "Detective Sherlock Holmes and his stalwart partner Watson engage in a battle of wits and brawn with a nemesis whose plot is a threat to all of England."},
        {"title": "The Usual Suspects", "genre": "Crime,Mystery,Thriller", "year": 1995, "rating": 8.5, "lang": "English", "overview": "A sole survivor tells of the twisty events leading up to a horrific gun battle on a boat, which began when five criminals met at a seemingly random police lineup."},
        {"title": "Memento", "genre": "Mystery,Thriller", "year": 2000, "rating": 8.4, "lang": "English", "overview": "A man with short-term memory loss attempts to track down his wife's murderer."},
        {"title": "Zodiac", "genre": "Crime,Drama,Mystery", "year": 2007, "rating": 7.7, "lang": "English", "overview": "Between 1968 and 1983, a San Francisco cartoonist becomes an amateur detective obsessed with tracking down the Zodiac Killer, an unidentified individual who terrorizes the Northern California area with a killing spree."},
        {"title": "Nightcrawler", "genre": "Crime,Drama,Thriller", "year": 2014, "rating": 7.8, "lang": "English", "overview": "When Louis Bloom, a con man desperate for work, muscles into the world of L.A. freelance crime journalism, he blurs the line between observer and participant in a gritty, relentless effort to succeed."},
        {"title": "Gangs of Wasseypur", "genre": "Action,Comedy,Crime", "year": 2012, "rating": 8.2, "lang": "Hindi", "overview": "A clash between Sultan and Shahid Khan leads to the expulsion of Khan from Wasseypur, and ignites a deadly three-generation feud spanning decades."}
    ]

    movies = []
    for data in movies_list:
        m = models.Movie(
            title=data["title"],
            overview=data["overview"],
            genres=data["genre"],
            release_year=data["year"],
            language=data["lang"],
            runtime=random.randint(90, 190),
            popularity=round(random.uniform(30.0, 100.0), 2),
            vote_average=data["rating"],
            vote_count=random.randint(1000, 30000),
            poster_url=f"https://via.placeholder.com/300x450/1e293b/f8fafc?text={data['title'].replace(' ', '+')}"
        )
        movies.append(m)
    db.add_all(movies)
    db.commit()
    print(f"Created {len(movies)} movies in database.")

    # 4. Map Movies to Platforms
    movie_platforms = []
    for m in movies:
        # Each movie is available on 1 to 3 platforms
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
    print(f"Mapped movies to platforms ({len(movie_platforms)} mappings).")

    # 5. Populate Ratings & Reviews
    ratings = []
    reviews = []
    
    # Review texts of different sentiment styles
    pos_reviews = [
        "Absolutely amazing! One of the best movies of all time.",
        "A visual masterpiece and a narrative triumph. Loved every single detail.",
        "Highly recommended! The acting was superb and the plot kept me hooked until the end.",
        "Brilliant screenplay and incredible music score. I will definitely watch it again.",
        "A beautiful story, acted with raw emotion. Truly heartwarming and powerful.",
        "Very entertaining! Exceeded my expectations, a solid 5 stars."
    ]
    neg_reviews = [
        "A complete waste of time. The story was full of plot holes and the acting was wooden.",
        "Worst movie I have seen this year. Extremely boring and way too long.",
        "Disappointing effort. It was slow, confusing, and completely uninteresting.",
        "The characters were annoying and the plot made absolutely no sense.",
        "Terrible writing. They ruined a great concept with poor execution.",
        "I wanted to walk out. Zero emotional depth and terrible editing."
    ]
    neu_reviews = [
        "It was okay. Had some good visual moments but the story felt predictable.",
        "Average movie. Good for a one-time watch if you have nothing else to do.",
        "Decent performances but the pacing was off. Neither great nor terrible.",
        "An alright adaptation, though it leaves out a lot of context from the source material.",
        "Decent effort, but fails to live up to the original classics.",
        "Some funny parts but overall a forgettable experience."
    ]

    for user in users:
        # Viewers rate 8-15 movies, admins rate 3-5
        num_to_rate = random.randint(8, 15) if user.role == "viewer" else random.randint(3, 5)
        rated_movies = random.sample(movies, num_to_rate)
        
        for m in rated_movies:
            # Generate a realistic rating: base it slightly on the movie's actual vote_average
            base = m.vote_average / 2.0 # convert 10-scale to 5-scale
            r = round(clip(random.normalvariate(base, 0.6), 1.0, 5.0), 1)
            
            timestamp = datetime.utcnow() - timedelta(days=random.randint(1, 360))
            
            rating_obj = models.Rating(
                user_id=user.user_id,
                movie_id=m.movie_id,
                rating=r,
                timestamp=timestamp
            )
            ratings.append(rating_obj)
            
            # 60% chance to leave a written review
            if random.random() < 0.6:
                if r >= 4.0:
                    text = random.choice(pos_reviews)
                elif r <= 2.5:
                    text = random.choice(neg_reviews)
                else:
                    text = random.choice(neu_reviews)
                
                # Analyze sentiment using VADER
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
    print(f"Generated {len(ratings)} ratings and {len(reviews)} reviews with VADER analysis.")

    # 6. Generate TrendData (last 12 months for 7 major genres)
    trend_genres = ["Sci-Fi", "Action", "Drama", "Comedy", "Thriller", "Romance", "Horror"]
    trends = []
    
    # Establish distinct trends for genres (e.g. Sci-Fi growing, Romance declining)
    base_scores = {
        "Sci-Fi": (50, 4.0),     # start, growth per month
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
            # Add some randomness to score
            score = round(clip(start + (slope * month_offset) + random.uniform(-5.0, 5.0), 10.0, 100.0), 2)
            
            t = models.TrendData(
                keyword=f"{g} movies",
                genre=g,
                date=current_month,
                trend_score=score
            )
            trends.append(t)
            
    db.add_all(trends)
    db.commit()
    print(f"Generated {len(trends)} trend data points.")

    # 7. Generate Churn Predictions with realistic features (for 48 viewers)
    churn_predictions = []
    # Engagement variables used to calculate risk:
    # watch_time, logins, monthly_charges, complaints, device_usage, previous_cancellations
    device_options = ["Smart TV", "Mobile", "Laptop", "Tablet"]
    payment_options = ["Credit Card", "UPI", "Net Banking", "Wallets"]

    for viewer in users:
        if viewer.role != "viewer":
            continue
            
        # Determine behavior based on a randomized profile type
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
            
        # Calculate churn probability using a formula
        # Base probability
        prob = 0.1
        if watch_time < 20: prob += 0.35
        if logins < 5: prob += 0.25
        if complaints >= 3: prob += 0.20
        if prev_cancels > 0: prob += 0.15
        if monthly_charges == 19.99: prob += 0.05
        
        # Add tiny noise
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
            important_features=json.dumps(features_dict),
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 5))
        )
        churn_predictions.append(churn_pred)

    db.add_all(churn_predictions)
    db.commit()
    print(f"Generated {len(churn_predictions)} subscriber churn predictions.")

    db.close()
    print("Database initialization and mock data pipeline run complete!")

def clip(val, min_val, max_val):
    return max(min_val, min(val, max_val))

if __name__ == "__main__":
    create_mock_data()
