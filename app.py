import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='assets', static_url_path='/assets')
app.secret_key = 'super_secret_key'
# --- FIX FOR LOCALHOST LOGIN ---
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# -------------------------------

# Configuration
UPLOAD_FOLDER = 'assets/uploads'
REPORT_FOLDER = 'assets/reports'  # NEW: Folder for PDF reports
DATA_FILE = 'data.json'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'pdf'} # Added PDF

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['REPORT_FOLDER'] = REPORT_FOLDER

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['REPORT_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"certificates": [], "projects": []}
    with open(DATA_FILE, 'r') as f:
        try:
            data = json.load(f)
            # Ensure both keys exist even if file is old
            if "certificates" not in data: data["certificates"] = []
            if "projects" not in data: data["projects"] = []
            return data
        except:
            return {"certificates": [], "projects": []}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- ROUTES ---


@app.route('/')
def index():
    data = load_data()
    
    # --- VISITOR COUNTER LOGIC ---
    # If 'visitors' doesn't exist, start at 0
    current_visitors = data.get('visitors', 0)
    
    # Add 1 to the count
    new_count = current_visitors + 1
    
    # Save it back to data.json
    data['visitors'] = new_count
    save_data(data)
    # -----------------------------

    # Pass the 'visitors' number to the HTML page
    return render_template('index.html', 
                           certificates=data['certificates'], 
                           projects=data['projects'],
                           visitors=new_count)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'logged_in' not in session:
        return render_template('admin_login.html')
    
    data = load_data()
    return render_template('admin.html', 
                           certificates=data['certificates'], 
                           projects=data['projects'])

@app.route('/login', methods=['POST'])
# --- UPDATE THIS BLOCK IN app.py ---

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    # Load credentials from .env file
    valid_user = os.getenv('ADMIN_USERNAME')
    valid_pass = os.getenv('ADMIN_PASSWORD')

    # Check if the typed email and password match the .env file
    if username == valid_user and password == valid_pass:
        session['logged_in'] = True
        return redirect(url_for('admin'))
    else:
        return render_template('admin_login.html', error="Invalid Credentials")

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

# --- CERTIFICATE UPLOAD ---
@app.route('/add_certificate', methods=['POST'])
def add_certificate():
    if 'logged_in' not in session: return redirect(url_for('admin'))
    
    title = request.form['title']
    file = request.files['image']

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        data = load_data()
        data['certificates'].append({"title": title, "image": filename})
        save_data(data)
        
    return redirect(url_for('admin'))

@app.route('/delete_certificate/<int:index>')
def delete_certificate(index):
    if 'logged_in' not in session: return redirect(url_for('admin'))
    data = load_data()
    if 0 <= index < len(data['certificates']):
        # Optional: Delete actual file here
        data['certificates'].pop(index)
        save_data(data)
    return redirect(url_for('admin'))

# --- NEW: PROJECT UPLOAD ---
@app.route('/add_project', methods=['POST'])
def add_project():
    if 'logged_in' not in session: return redirect(url_for('admin'))
    
    title = request.form['title']
    category = request.form['category'] # e.g., Web App, Database
    description = request.form['description']
    
    # Handle Image
    img_file = request.files['image']
    img_filename = ""
    if img_file and allowed_file(img_file.filename):
        img_filename = secure_filename(img_file.filename)
        img_file.save(os.path.join(app.config['UPLOAD_FOLDER'], img_filename))

    # Handle Report (PDF) - Optional
    report_file = request.files['report']
    report_filename = ""
    if report_file and allowed_file(report_file.filename):
        report_filename = secure_filename(report_file.filename)
        report_file.save(os.path.join(app.config['REPORT_FOLDER'], report_filename))

    # Save to JSON
    data = load_data()
    data['projects'].append({
        "title": title,
        "category": category,
        "description": description,
        "image": img_filename,
        "report": report_filename # This might be empty string "" if no report uploaded
    })
    save_data(data)
        
    return redirect(url_for('admin'))

@app.route('/delete_project/<int:index>')
def delete_project(index):
    if 'logged_in' not in session: return redirect(url_for('admin'))
    data = load_data()
    if 0 <= index < len(data['projects']):
        data['projects'].pop(index)
        save_data(data)
    return redirect(url_for('admin'))
# --- NEW: DYNAMIC PROJECT DETAILS PAGE ---
@app.route('/project/<int:id>')
def project_details(id):
    data = load_data()
    projects = data.get('projects', [])
    
    # Check if the project exists
    if 0 <= id < len(projects):
        project = projects[id]
        return render_template('project_details.html', project=project)
    
    # If not found, go back home
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)