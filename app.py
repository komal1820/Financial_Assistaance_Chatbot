from flask import Flask, request, redirect, url_for, render_template,session, flash,jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import re
from flask import jsonify
from chat import get_response
from flask_migrate import Migrate
from datetime import datetime, timedelta


app = Flask(__name__)
app.secret_key = '1221' 

# Adjust the URI to match your database's name and credentials
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost:8889/Maestro_database'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Adjust this model to reflect the structure of your 'Maestro' table
class Maestro(db.Model):
    __tablename__ = 'Maestro'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    # Add or adjust columns to match your existing table schema

class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    mobile_number = db.Column(db.String(15), nullable=False)
    appointment_type = db.Column(db.String(50), nullable=False)

@app.route('/submit_appointment', methods=['GET', 'POST'])
def submit_appointment():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        date_str = request.form['date'].strip()
        time_str = request.form['time'].strip()
        mobile = request.form['mobile'].strip()
        appointment_type = request.form['type'].strip()

        if not (name and email and date_str and time_str and mobile and appointment_type):
            flash('All fields are required.', 'error')
            return redirect(url_for('appointment'))

        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            flash('Invalid email format.', 'error')
            return redirect(url_for('appointment'))

        if datetime.strptime(date_str, '%Y-%m-%d').date() <= datetime.now().date():
            flash('Appointment date must be a future date.', 'error')
            return redirect(url_for('appointment'))

        appointment_time = datetime.strptime(time_str, '%H:%M').time()
        if not (datetime.strptime('10:00', '%H:%M').time() <= appointment_time <= datetime.strptime('18:00', '%H:%M').time()):
            flash('Appointment time must be between 10 AM and 6 PM.', 'error')
            return redirect(url_for('appointment'))

        if not re.fullmatch(r'[1-9][0-9]{9}', mobile):
            flash('Mobile number must be exactly 10 digits and not start with zero.', 'error')
            return redirect(url_for('appointment'))

        new_appointment = Appointment(
            name=name,
            email=email,
            appointment_date=datetime.strptime(date_str, '%Y-%m-%d').date(),
            appointment_time=appointment_time,
            mobile_number=mobile,
            appointment_type=appointment_type
        )

        db.session.add(new_appointment)
        db.session.commit()
        flash('Appointment scheduled successfully.', 'success')
        return redirect(url_for('appointment'))

    tomorrow = datetime.now().date() + timedelta(days=1)
    return render_template("appointment.html", tomorrow=tomorrow.strftime('%Y-%m-%d'))


@app.route('/login_action', methods=['POST'])
def login_action():
    email = request.form['email'].strip().lower()
    password = request.form['password'].strip()
    
    user = Maestro.query.filter_by(email=email).first()
    
    if user and check_password_hash(user.password, password):
        session['user_email'] = user.email
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login_page', message='Invalid email or password'))

@app.route('/logout_action')
def logout_action():
    session.pop('user_email', None)
    return redirect(url_for('home'))

@app.route('/signup_action', methods=['POST'])
def signup_action():
    email = request.form['email'].lower().strip()
    password = request.form['password']

    # Email format validation
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return redirect(url_for('signup_page', error='Invalid email format.'))

    if not re.match(r'^(?=.*[A-Z])(?=.*\d)(?=.*[\W_])[a-zA-Z\d\W_]{5,}$', password):
        return redirect(url_for('signup_page', error='Password must be at least 5 characters long, include at least one uppercase letter, one number, and one special character.'))

    # Check if email already exists
    if Maestro.query.filter_by(email=email).first():
        return redirect(url_for('signup_page', error='Email already exists. Please use a different email.'))

    # Proceed with creating the user if validations pass
    hashed_password = generate_password_hash(password)
    user = Maestro(email=email, password=hashed_password)

    try:
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login_page'))
    except Exception:
        db.session.rollback()
        return redirect(url_for('signup_page', error='An unexpected error occurred. Please try again.'))

# Home page
@app.route('/')
def home():
    return render_template('home.html')  # Your main page

@app.route('/login_page')
def login_page():
    return render_template('login.html')  # Login form page

@app.route('/signup_page')
def signup_page():
    error_message = request.args.get('error', '')
    return render_template('signup.html', error=error_message)

@app.route('/reset_password_action', methods=['POST'])
def reset_password_action():
    email = request.form['email'].strip().lower()
    # Assume some logic here to check if the user exists and send a reset email
    print("Attempt to send password reset instructions to", email)  # Placeholder for email logic

    # Redirect to the login page with a message as a query parameter
    return redirect(url_for('login_page', message='If this email is registered, you will receive reset instructions shortly.'))

# Additional routes for demonstration
@app.route("/ourTeam")
def ourTeam():
    return render_template("ourTeam.html")

@app.route('/contact')
def contact():
    message = request.args.get('message')
    return render_template('contact.html', message=message)

@app.route("/faq")
def faq():
    return render_template("FAQ.html")

@app.route("/edu")
def edu():
    return render_template("edu.html")

@app.route("/appointment")
def appointment():
    return render_template("appointment.html")

class Inquiry(db.Model):
    __tablename__ = 'inquiries'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    registered_email = db.Column(db.String(255), nullable=True)  # Ensure this matches your database and model.
    name = db.Column(db.String(255), nullable=False)

def is_valid_email(email):
    """
    Check if the email address is in a valid format.
    """
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email)


@app.route('/submit_inquiry', methods=['POST'])
def submit_inquiry():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    message = request.form.get('message', '').strip()

    if not name or not email or not message or not is_valid_email(email):
        # Redirect with an error message, assuming you have a mechanism to display it
        return redirect(url_for('contact', message='error-email'))

    # Determine if the email belongs to a registered user
    registered_email = None
    if Maestro.query.filter_by(email=email).first():
        registered_email = email  # Set registered_email if it matches an entry in the Maestro table

    # Create the inquiry instance
    new_inquiry = Inquiry(email=email, message=message, registered_email=registered_email, name=name)
    
    try:
        db.session.add(new_inquiry)
        db.session.commit()
        return redirect(url_for('contact', message='success'))
    except Exception as e:
        db.session.rollback()
        print(e)  # It's a good practice to log the error
        return redirect(url_for('contact', message='error'))
        print(submit_inquiry)
        print(f"Name: {name}, Email: {email}, Message: {message}, Registered Email: {registered_email}")

@app.post("/predict")
def predict():
    text = request.get_json().get("message")
    # TODO: check if text is valid
    response = get_response(text)
    message = {"answer": response}
    return jsonify(message)

if __name__ == "__main__":
    app.run(debug=True)
