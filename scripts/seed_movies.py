import os
import sys
import json
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal, engine
from app.core.models import Base, User, Quiz, Question

def setup_movie_database():
    """Builds a strict relational SQLite database with PKs and FKs from CSVs."""
    print("📦 Building normalized movies.db from raw CSV files...")
    
    # 1. Define Paths
    raw_data_dir = "raw_data/sql_fundamentals/" # Where we read the CSVs from
    app_data_dir = "datasets" # Where we save the finished DB to
    
    db_path = os.path.join(app_data_dir, "movies.db")
    os.makedirs(app_data_dir, exist_ok=True)
    
    # Remove old DB if exists to start fresh with strict schema
    if os.path.exists(db_path):
        os.remove(db_path)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 2. Define strict schemas
    schemas = {
        "movies": """
            CREATE TABLE movies (
                movie_id INTEGER PRIMARY KEY,
                title TEXT,
                genre TEXT,
                runtime INTEGER,
                year_of_release INTEGER,
                renting_price REAL
            )
        """,
        "customers": """
            CREATE TABLE customers (
                customer_id INTEGER PRIMARY KEY,
                name TEXT,
                country TEXT,
                gender TEXT,
                date_of_birth TEXT,
                date_account_start TEXT
            )
        """,
        "actors": """
            CREATE TABLE actors (
                actor_id INTEGER PRIMARY KEY,
                name TEXT,
                year_of_birth INTEGER,
                nationality TEXT,
                gender TEXT
            )
        """,
        "renting": """
            CREATE TABLE renting (
                renting_id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                movie_id INTEGER,
                rating REAL,
                date_renting TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
                FOREIGN KEY (movie_id) REFERENCES movies(movie_id)
            )
        """,
        "actsin": """
            CREATE TABLE actsin (
                actsin_id INTEGER PRIMARY KEY,
                movie_id INTEGER,
                actor_id INTEGER,
                FOREIGN KEY (movie_id) REFERENCES movies(movie_id),
                FOREIGN KEY (actor_id) REFERENCES actors(actor_id)
            )
        """
    }

    # Create tables
    for table_name, schema_query in schemas.items():
        cursor.execute(schema_query)
        print(f"   ↳ Created table schema for: {table_name}")

    conn.commit()

    # 3. Load Data from the raw_data folder into the strict schema
    csv_files = {
        "movies": os.path.join(raw_data_dir, "movies.csv"),
        "customers": os.path.join(raw_data_dir, "customers.csv"),
        "actors": os.path.join(raw_data_dir, "actors.csv"),
        "renting": os.path.join(raw_data_dir, "renting.csv"),
        "actsin": os.path.join(raw_data_dir, "actsin.csv")
    }
    
    for table_name, file_path in csv_files.items():
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            if 'index' in df.columns:
                df = df.drop(columns=['index'])
            
            # Use 'append' so we don't overwrite our strict schema definitions
            df.to_sql(table_name, conn, if_exists="append", index=False)
            print(f"   ↳ Loaded {len(df)} rows into {table_name}")
        else:
            print(f"   ⚠️ Warning: {file_path} not found. Ensure your CSVs are inside the raw_data/ folder!")
            
    conn.close()
    print(f"✅ Successfully built normalized {db_path}!")
    return db_path

def seed_movie_modules():
    print("Initializing Database connection...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Ensure the Master Admin exists
        admin = db.query(User).filter(User.email == "larryvander580@gmail.com").first()
        if not admin:
            admin = User(email="larryvander580@gmail.com", name="Master Admin", password="admin123", role="instructor", is_master=True)
            db.add(admin)
            db.commit()

        print("Creating Module: Comprehensive Data Analytics (SQL)...")
        
        quiz = Quiz(
            title="SQL Fundamentals: Exploring the Movies Dataset",
            description="Objective: Dive into a comprehensive movie database to build your foundational data analysis skills. In this module, you will get hands-on experience writing core SQL queries, filtering records, and using JOINs to connect multiple tables and uncover insights.",
            active=True,
            due_date=datetime.utcnow() + timedelta(days=14) 
        )
        db.add(quiz)
        db.flush() 

        db.add_all([
            Question(
                quiz_id=quiz.quiz_id, question_text="Which genre has the most movies in the database?",
                question_type="sql_mcq", points=5, dataset_path="datasets/movies.db",
                options=json.dumps({"A": "drama", "B": "comedy", "C": "animation", "D": "Mystery & Suspense", "Correct": "A"}),
                expected_answer="SELECT genre, COUNT(*) as movie_num\nFROM movies\nGROUP BY genre\nORDER BY movie_num desc\nLIMIT 1;"
            ),
            Question(
                quiz_id=quiz.quiz_id, question_text="Which of these actors appeared in 8 movies?",
                question_type="sql_mcq", points=10, dataset_path="datasets/movies.db",
                options=json.dumps({"A": "Nicolas Cage", "B": "None appeared in 8 movies", "C": "Sean Penn", "D": "Emma Watson", "Correct": "D"}),
                expected_answer="SELECT ac.name, COUNT(m.movie_id) as movie_num\nFROM movies m\nJOIN actsin an\n\tON m.movie_id = an.movie_id\nJOIN actors ac\n\tON an.actor_id = ac.actor_id\nGROUP BY ac.name\nORDER BY movie_num desc;"
            ),
            Question(
                quiz_id=quiz.quiz_id, question_text="Which actors haven't acted in any movie?",
                question_type="sql_mcq", points=10, dataset_path="datasets/movies.db",
                options=json.dumps({"A": "Nicolas Cage", "B": "All have acted", "C": "Sean Penn", "D": "Emma Watson", "Correct": "B"}),
                expected_answer="SELECT ac.name, m.movie_id\nFROM actors ac\nLEFT JOIN actsin an\n\tON ac.actor_id = an.actor_id\nLEFT JOIN movies m\n\tON an.movie_id = m.movie_id\nWHERE m.movie_id IS NULL;"
            ),
            Question(
                quiz_id=quiz.quiz_id, question_text="What is the second-best movie by average rating?",
                question_type="sql_mcq", points=10, dataset_path="datasets/movies.db",
                options=json.dumps({"A": "The Fellowship of the Ring", "B": "Astro Boy", "C": "Harry Potter and the Half-Blood Prince", "D": "Young Adult", "Correct": "A"}),
                expected_answer="SELECT m.movie_id, m.title, AVG(r.rating) as avg_rating\nFROM movies m\nJOIN renting r\nON m.movie_id = r.movie_id\nGROUP BY m.movie_id\nORDER BY avg_rating DESC;"
            ),
            Question(
                quiz_id=quiz.quiz_id, question_text="What countries have the lowest number of registered customers?",
                question_type="sql_mcq", points=5, dataset_path="datasets/movies.db",
                options=json.dumps({"A": "Italy and Spain", "B": "USA and Spain", "C": "USA and Austria", "D": "Italy and Austria", "Correct": "C"}),
                expected_answer="SELECT country, COUNT(customer_id) AS num\nFROM customers\nGROUP BY country\nORDER BY num ASC\nLIMIT 2;"
            ),
            Question(
                quiz_id=quiz.quiz_id, question_text="Which of the following country has both actors and customers?",
                question_type="sql_mcq", points=10, dataset_path="datasets/movies.db",
                options=json.dumps({"A": "Belgium", "B": "Austria", "C": "Great Britan", "D": "France", "Correct": "B"}),
                expected_answer="SELECT country\nFROM customers\nINTERSECT\nSELECT nationality\nFROM actors;"
            ),
            Question(
                quiz_id=quiz.quiz_id, question_text="Which customer has watched movies featuring the largest number of different actors?",
                question_type="sql_mcq", points=15, dataset_path="datasets/movies.db",
                options=json.dumps({"A": "Avelaine Corbeil with 31 actors", "B": "Avelaine Corbeil with 42 actors", "C": "Lucy Centeno Barrios with 36 actors", "D": "Lucy Centeno Barrios with 45 actors", "Correct": "C"}),
                expected_answer="SELECT c.customer_id, c.name, COUNT(DISTINCT a.actor_id) AS no_of_actors\nFROM customers c\nJOIN renting r ON c.customer_id = r.customer_id\nJOIN movies m ON r.movie_id = m.movie_id\nJOIN actsin an ON m.movie_id = an.movie_id\nJOIN actors a ON an.actor_id = a.actor_id\nGROUP BY c.customer_id, c.name\nORDER BY no_of_actors DESC;"
            ),
            Question(
                quiz_id=quiz.quiz_id, question_text="Which female actor has appeared in movies with the highest total runtime?",
                question_type="sql_mcq", points=15, dataset_path="datasets/movies.db",
                options=json.dumps({"A": "actor_id 42", "B": "actor_id 56", "C": "actor_id 23", "D": "actor_id 34", "Correct": "A"}),
                expected_answer="SELECT a.actor_id, a.name, SUM(m.runtime) AS total_runtime\nFROM actors a\nJOIN actsin an ON a.actor_id = an.actor_id\nJOIN movies m ON an.movie_id = m.movie_id\nWHERE a.gender = 'female'\nGROUP BY a.actor_id, a.name\nORDER BY total_runtime DESC;"
            ),
            Question(
                quiz_id=quiz.quiz_id, question_text="Which country's customers have given the lowest average rating to movies?",
                question_type="sql_mcq", points=10, dataset_path="datasets/movies.db",
                options=json.dumps({"A": "Great Britan", "B": "Belgium", "C": "USA", "D": "Austria", "Correct": "D"}),
                expected_answer="SELECT country, AVG(rating) AS avg_rating\nFROM customers c\nJOIN renting r\n  ON c.customer_id = r.customer_id\nGROUP BY country\nORDER BY avg_rating ASC;"
            ),
            Question(
                quiz_id=quiz.quiz_id, question_text="Which genres of movies released after 2010 have generated total renting revenue between 15 to 25?",
                question_type="sql_mcq", points=15, dataset_path="datasets/movies.db",
                options=json.dumps({"A": "Action & Adventure", "B": "Drama", "C": "Mystery & Suspense", "D": "Science Fiction & Fantasy", "Correct": "D"}),
                expected_answer="SELECT m.genre, SUM(m.renting_price) AS total_revenue\nFROM movies m\nJOIN renting r\n  ON m.movie_id = r.movie_id\nWHERE m.year_of_release > 2010\nGROUP BY m.genre\nHAVING SUM(m.renting_price) between 15 and 25;"
            ),
            Question(
                quiz_id=quiz.quiz_id, question_text="Which gender has spent the most on renting drama movies?",
                question_type="sql_mcq", points=10, dataset_path="datasets/movies.db",
                options=json.dumps({"A": "Nulls are the highest", "B": "females are the highest", "C": "both are the same", "D": "males are the highest", "Correct": "B"}),
                expected_answer="SELECT c.gender, SUM(m.renting_price) AS total_price\nFROM renting r\nJOIN customers c ON r.customer_id = c.customer_id\nJOIN movies m ON r.movie_id = m.movie_id\nWHERE m.genre = 'Drama'\nGROUP BY c.gender\nORDER BY total_price DESC;"
            ),
            Question(
                quiz_id=quiz.quiz_id, question_text="Which scenario would cause COUNT(customer_id) to give a different result from COUNT(*)?",
                question_type="multiple_choice", points=5, dataset_path="datasets/movies.db",
                options=json.dumps({"A": "When there are duplicate customer IDs", "B": "When the customer_id doesn't follow the right sequence", "C": "When some customer_id values are NULL", "D": "When the rows are above a certain number", "Correct": "C"}),
                expected_answer="COUNT(*) counts all rows in the table regardless of data. COUNT(column_name) counts all rows where that specific column is NOT NULL."
            )
        ])

        db.commit()
        print("✅ Success! 12 Questions injected into the portal using your SQL queries.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    setup_movie_database()
    seed_movie_modules()