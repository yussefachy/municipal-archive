from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///municipal_archive.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'assets/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

# Ensure upload folder exists
try:
    os.makedirs(app.config['UPLOAD_FOLDER'])
except OSError:
    pass

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    reservations = db.relationship('Reservation', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(200))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    reservations = db.relationship('Reservation', backref='document', lazy=True)

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    reservation_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    appointment_date = db.Column(db.DateTime, nullable=False)
    appointment_time = db.Column(db.String(5), nullable=False)
    status = db.Column(db.String(20), default='pending')
    notes = db.Column(db.Text)

# Admin check decorator
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('You do not have permission to access this page', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Routes
@app.route('/')
def index():
    documents = Document.query.all()
    return render_template('index.html', documents=documents)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        print(f"Login attempt for username: {username}")
        
        user = User.query.filter_by(username=username).first()
        if user:
            print(f"User found: {user}")
            if check_password_hash(user.password_hash, password):
                session['user_id'] = user.id
                session['is_admin'] = user.is_admin
                flash('Login successful!', 'success')
                if user.is_admin:
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('index'))
            else:
                print("Password check failed")
        else:
            print(f"No user found with username: {username}")
            
        flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        print(f"Registration attempt for username: {username}, email: {email}")
        
        if User.query.filter_by(username=username).first():
            print(f"Username {username} already exists")
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            print(f"Email {email} already registered")
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
            
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        try:
            db.session.add(user)
            db.session.commit()
            print(f"Successfully created user: {user}")
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            print(f"Error creating user: {str(e)}")
            flash('An error occurred during registration', 'error')
            return redirect(url_for('register'))
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))

# Admin routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    documents = Document.query.all()
    users = User.query.all()
    reservations = Reservation.query.all()
    return render_template('admin/dashboard.html', 
                         documents=documents,
                         users=users,
                         reservations=reservations)

@app.route('/admin/documents/add', methods=['GET', 'POST'])
@admin_required
def add_document():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        file = request.files.get('image')
        
        if not title or not description:
            flash('Title and description are required', 'error')
            return redirect(url_for('add_document'))
            
        try:
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                image_path = f'assets/uploads/{filename}'
            else:
                image_path = 'assets/placeholder.png'
                
            document = Document(
                title=title,
                description=description,
                image_path=image_path
            )
            db.session.add(document)
            db.session.commit()
            flash('Document added successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding document: {str(e)}', 'error')
            return redirect(url_for('add_document'))
            
    return render_template('admin/add_document.html')

@app.route('/admin/documents/<int:document_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_document(document_id):
    document = Document.query.get_or_404(document_id)
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        file = request.files.get('image')
        
        if not title or not description:
            flash('Title and description are required', 'error')
            return redirect(url_for('edit_document', document_id=document_id))
            
        try:
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                document.image_path = f'assets/uploads/{filename}'
                
            document.title = title
            document.description = description
            db.session.commit()
            flash('Document updated successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating document: {str(e)}', 'error')
            return redirect(url_for('edit_document', document_id=document_id))
            
    return render_template('admin/edit_document.html', document=document)

@app.route('/admin/documents/<int:document_id>/delete', methods=['POST'])
@admin_required
def delete_document(document_id):
    document = Document.query.get_or_404(document_id)
    try:
        # Delete the image file if it's not the placeholder
        if document.image_path != 'assets/placeholder.png':
            try:
                os.remove(document.image_path)
            except:
                pass  # Ignore if file doesn't exist
                
        db.session.delete(document)
        db.session.commit()
        flash('Document deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting document: {str(e)}', 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/book/<int:document_id>', methods=['GET', 'POST'])
def book_document(document_id):
    if 'user_id' not in session:
        flash('Please login to reserve documents', 'error')
        return redirect(url_for('login'))
        
    document = Document.query.get_or_404(document_id)
    
    if request.method == 'POST':
        try:
            appointment_date = datetime.strptime(request.form.get('appointment_date'), '%Y-%m-%d')
            appointment_time = request.form.get('appointment_time')
            notes = request.form.get('notes', '')

            # Validate appointment date (must be in the future)
            if appointment_date.date() < datetime.now().date():
                flash('Appointment date must be in the future', 'error')
                return redirect(url_for('book_document', document_id=document_id))

            # Check if the time slot is available
            existing_reservation = Reservation.query.filter_by(
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status='confirmed'
            ).first()

            if existing_reservation:
                flash('This time slot is already booked. Please choose another time.', 'error')
                return redirect(url_for('book_document', document_id=document_id))

            reservation = Reservation(
                user_id=session['user_id'],
                document_id=document_id,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                notes=notes
            )
            db.session.add(reservation)
            db.session.commit()
            flash('Document reserved successfully! Please arrive at your scheduled time.', 'success')
            return redirect(url_for('index'))
        except ValueError:
            flash('Invalid date format', 'error')
            return redirect(url_for('book_document', document_id=document_id))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while making the reservation', 'error')
            return redirect(url_for('book_document', document_id=document_id))
        
    # Generate available time slots (9 AM to 5 PM, 30-minute intervals)
    time_slots = []
    for hour in range(9, 17):
        for minute in ['00', '30']:
            time_slots.append(f"{hour:02d}:{minute}")
    
    # Get the next 7 days for the date picker
    available_dates = []
    for i in range(1, 8):
        date = datetime.now() + timedelta(days=i)
        available_dates.append(date.strftime('%Y-%m-%d'))
        
    return render_template('book.html', 
                         document=document, 
                         time_slots=time_slots,
                         available_dates=available_dates)

@app.route('/confirm/<int:reservation_id>')
def confirm_reservation(reservation_id):
    if 'user_id' not in session:
        flash('Please login to confirm reservations', 'error')
        return redirect(url_for('login'))
        
    reservation = Reservation.query.get_or_404(reservation_id)
    if reservation.user_id != session['user_id']:
        flash('Unauthorized access', 'error')
        return redirect(url_for('index'))
        
    reservation.status = 'confirmed'
    db.session.commit()
    flash('Reservation confirmed!', 'success')
    return redirect(url_for('index'))

# Serve static files
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('assets', filename)

@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory('css', filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory('js', filename)

# Initialize database and add sample data
def init_db():
    with app.app_context():
        db.create_all()
        
        # Create admin user if none exists
        if not User.query.filter_by(is_admin=True).first():
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
        
        # Add sample documents if none exist
        if not Document.query.first():
            sample_documents = [
                Document(
                    title='Historical Records 1950-1960',
                    description='Collection of municipal records from the 1950s to 1960s.',
                    image_path='assets/placeholder.png'
                ),
                Document(
                    title='City Planning Documents',
                    description='Urban development plans and architectural drawings.',
                    image_path='assets/placeholder.png'
                ),
                Document(
                    title='Public Meeting Minutes',
                    description='Historical records of city council meetings.',
                    image_path='assets/placeholder.png'
                )
            ]
            db.session.add_all(sample_documents)
            db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5001) 