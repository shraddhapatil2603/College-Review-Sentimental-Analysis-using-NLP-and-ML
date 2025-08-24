from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from textblob import TextBlob
import hashlib
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='get_college_review'
    )

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('You need to log in first!')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out!')
    return redirect(url_for('login'))

# Homepage - Route to Login/Register
@app.route('/')
def index():
    return render_template('index.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Hashing password for secure comparison
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, hashed_password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['username'] = username
            return redirect(url_for('submit_review'))

        else:
            flash('Invalid Credentials!')
    return render_template('login.html')

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        middle_name = request.form['middle_name']
        last_name = request.form['last_name']
        contact = request.form['contact']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        
        # Hashing password for secure storage
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (first_name, middle_name, last_name, contact, email, username, password) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                       (first_name, middle_name, last_name, contact, email, username, hashed_password))
        conn.commit()
        conn.close()
        flash('Registration Successful! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# View/Display Reviews
@app.route('/reviews', methods=['GET', 'POST'])
def reviews():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get list of colleges for dropdown
    cursor.execute("SELECT DISTINCT college FROM reviews")
    colleges = cursor.fetchall()

    selected_college = None
    reviews = []
    sentiment_score = None
    sentiment_classification = None

    if request.method == 'POST':
        selected_college = request.form['college']

        # Fetch reviews and ratings for the selected college
        cursor.execute("SELECT name, review, rating FROM reviews WHERE college = %s", (selected_college,))
        reviews = cursor.fetchall()

        # Calculate sentimental score
        if reviews:
            total_score = 0
            for review in reviews:
                review_text = review[1]
                rating = review[2]

                # Sentiment analysis for the review
                sentiment_polarity = TextBlob(review_text).sentiment.polarity  # Ranges from -1 to 1
                sentiment_score_review = (sentiment_polarity + 1) * 5  # Scale to 0-10

                # Combine normalized rating and sentiment score
                total_score += (sentiment_score_review + rating) / 2

            # Average sentimental score
            sentiment_score = total_score / len(reviews)

            # Classify the sentiment
            if sentiment_score >= 7:
                sentiment_classification = "Positive"
            elif sentiment_score >= 5:
                sentiment_classification = "Neutral"
            else:
                sentiment_classification = "Negative"

    conn.close()

    return render_template('reviews.html', colleges=colleges, reviews=reviews,
                           selected_college=selected_college, sentiment_score=sentiment_score,
                           sentiment_classification=sentiment_classification)

# Submit Review Route
@app.route('/submit_review', methods=['GET', 'POST'])
@login_required
def submit_review():
    if request.method == 'POST':
        name = request.form['name']
        college = request.form['college']
        college_review = request.form['college_review']
        campus_review = request.form['campus_review']
        faculty_review = request.form['faculty_review']
        hostel_review = request.form['hostel_review']
        overall_facilities_review = request.form['overall_facilities_review']
        rating = request.form['rating']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO review (name, college, college_review, campus_review, faculty_review, hostel_review, overall_facilities_review, rating) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                       (name, college, college_review, campus_review, faculty_review, hostel_review, overall_facilities_review, rating))
        conn.commit()
        conn.close()
        
        flash('Review Submitted Successfully!')
        return redirect(url_for('reviews'))
    
    return render_template('submit_review.html')

if __name__ == '__main__':
    app.run(debug=True)
