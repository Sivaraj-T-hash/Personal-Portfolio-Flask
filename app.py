import cloudinary
import cloudinary.uploader
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

# --- CLOUDINARY CONFIGURATION (ACTION REQUIRED) ---
cloudinary.config(
    cloud_name = "doqgziycf", 
    api_key = "636344164192868", 
    api_secret = "gMBO2pdLflJByR1IFqhcZDG8M1M",
    secure = True
)
# --------------------------------------------------

DATA_FILE = 'data.json'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"certificates": [], "projects": []}
    with open(DATA_FILE, 'r') as f:
        try:
            data = json.load(f)
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
    current_visitors = data.get('visitors', 0)
    new_count = current_visitors + 1
    data['visitors'] = new_count
    save_data(data)
    # -----------------------------

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
def login():
    username = request.form['username']
    password = request.form['password']
    
    # Updated credentials
    # Username: admin
    # Password: Sivaraj9677
    valid_user = os.getenv('ADMIN_USERNAME', 'admin') 
    valid_pass = os.getenv('ADMIN_PASSWORD', 'Sivaraj9677')

    if username == valid_user and password == valid_pass:
        session['logged_in'] = True
        return redirect(url_for('admin'))
    else:
        return render_template('admin_login.html', error="Invalid Credentials")

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

# --- CERTIFICATE UPLOAD (UPDATED FOR CLOUDINARY) ---
@app.route('/add_certificate', methods=['POST'])
def add_certificate():
    if 'logged_in' not in session: return redirect(url_for('admin'))
    
    title = request.form['title']
    file = request.files['image']

    if file and allowed_file(file.filename):
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(file)
        # Get the URL of the uploaded image
        image_url = upload_result["secure_url"]
        
        data = load_data()
        # Save the URL instead of the filename
        data['certificates'].append({"title": title, "image": image_url})
        save_data(data)
        
    return redirect(url_for('admin'))

@app.route('/delete_certificate/<int:index>')
def delete_certificate(index):
    if 'logged_in' not in session: return redirect(url_for('admin'))
    data = load_data()
    if 0 <= index < len(data['certificates']):
        data['certificates'].pop(index)
        save_data(data)
    return redirect(url_for('admin'))

# --- PROJECT UPLOAD (UPDATED FOR CLOUDINARY) ---
@app.route('/add_project', methods=['POST'])
def add_project():
    if 'logged_in' not in session: return redirect(url_for('admin'))
    
    title = request.form['title']
    category = request.form['category'] 
    description = request.form['description']
    
    # Handle Image Upload
    img_file = request.files['image']
    img_url = "" # Default to empty if no image
    if img_file and allowed_file(img_file.filename):
        upload_result = cloudinary.uploader.upload(img_file)
        img_url = upload_result["secure_url"]

    # Handle Report (PDF) Upload
    report_file = request.files['report']
    report_url = "" # Default to empty if no report
    if report_file and allowed_file(report_file.filename):
        # Cloudinary handles PDFs automatically too!
        report_result = cloudinary.uploader.upload(report_file, resource_type="auto")
        report_url = report_result["secure_url"]

    # Save to JSON
    data = load_data()
    data['projects'].append({
        "title": title,
        "category": category,
        "description": description,
        "image": img_url,   # Now storing the Cloudinary URL
        "report": report_url # Now storing the Cloudinary URL
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

@app.route('/project/<int:id>')
def project_details(id):
    data = load_data()
    projects = data.get('projects', [])
    
    if 0 <= id < len(projects):
        project = projects[id]
        return render_template('project_details.html', project=project)
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
