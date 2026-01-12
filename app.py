import os
import cloudinary
import cloudinary.uploader
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient # ADDED
import certifi # ADDED
from bson.objectid import ObjectId # ADDED

app = Flask(__name__, static_folder='assets', static_url_path='/assets')
app.secret_key = 'super_secret_key'

# --- 1. MONGODB CONNECTION (THE MISSING PART) ---
# I added your correct password with the special %40 symbol
MONGO_URI = "mongodb+srv://admin:Sivaraj%409677@cluster0.bisuniq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['portfolio_db'] # The database name
certificates_col = db['certificates'] # The collection for certificates
projects_col = db['projects'] # The collection for projects
# -----------------------------------------------

# --- CLOUDINARY CONFIGURATION ---
cloudinary.config(
    cloud_name = "doqgziycf", 
    api_key = "636344164192868", 
    api_secret = "gMBO2pdLflJByR1IFqhcZDG8M1M",
    secure = True
)
# --------------------------------

# --- ROUTES ---

@app.route('/')
def index():
    # FETCH FROM MONGODB (Sorted by position)
    certificates = list(certificates_col.find().sort('position', 1))
    projects = list(projects_col.find().sort('position', 1))
    
    return render_template('index.html', 
                           certificates=certificates, 
                           projects=projects)

@app.route('/admin')
def admin():
    if 'logged_in' not in session:
        return render_template('admin_login.html')
    
    # FETCH FROM MONGODB
    certificates = list(certificates_col.find().sort('position', 1))
    projects = list(projects_col.find().sort('position', 1))
    
    return render_template('admin.html', 
                           certificates=certificates, 
                           projects=projects)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    # Your Credentials
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

# --- ADD CERTIFICATE (Saves to MongoDB) ---
@app.route('/add_certificate', methods=['POST'])
def add_certificate():
    if 'logged_in' not in session: return redirect(url_for('login'))

    title = request.form['title']
    image = request.files['image']

    if image:
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(image)
        image_url = upload_result['secure_url']
        
        # Save to MongoDB
        certificates_col.insert_one({
            'title': title,
            'image': image_url,
            'position': 0 
        })
        
    return redirect(url_for('admin'))

# --- DELETE CERTIFICATE (Fixed for MongoDB) ---
@app.route('/delete_certificate/<int:index>')
def delete_certificate(index):
    if 'logged_in' not in session: return redirect(url_for('admin'))
    
    # Get all certs, find the one at this index, and delete it by ID
    all_certs = list(certificates_col.find().sort('position', 1))
    if 0 <= index < len(all_certs):
        cert_to_delete = all_certs[index]
        certificates_col.delete_one({'_id': cert_to_delete['_id']})
        
    return redirect(url_for('admin'))

# --- ADD PROJECT (Saves to MongoDB) ---
@app.route('/add_project', methods=['POST'])
def add_project():
    if 'logged_in' not in session: return redirect(url_for('login'))

    title = request.form['title']
    category = request.form['category']
    image = request.files['image']
    # description = request.form['description'] # Add this line if you use descriptions

    if image:
        upload_result = cloudinary.uploader.upload(image)
        image_url = upload_result['secure_url']
        
        # Save to MongoDB
        projects_col.insert_one({
            'title': title,
            'category': category,
            'image': image_url,
            # 'description': description,
            'position': 0
        })

    return redirect(url_for('admin'))

# --- DELETE PROJECT (Fixed for MongoDB) ---
@app.route('/delete_project/<int:index>')
def delete_project(index):
    if 'logged_in' not in session: return redirect(url_for('admin'))
    
    all_projects = list(projects_col.find().sort('position', 1))
    if 0 <= index < len(all_projects):
        proj_to_delete = all_projects[index]
        projects_col.delete_one({'_id': proj_to_delete['_id']})
        
    return redirect(url_for('admin'))

# --- PROJECT DETAILS (Fixed for MongoDB) ---
@app.route('/project/<int:id>')
def project_details(id):
    # Fetch all projects to match the index from the URL
    projects = list(projects_col.find().sort('position', 1))
    
    if 0 <= id < len(projects):
        project = projects[id]
        return render_template('project_details.html', project=project)
    
    return redirect(url_for('index'))

# --- REORDER LOGIC (From previous step) ---
@app.route('/reorder', methods=['POST'])
def reorder():
    if 'logged_in' not in session: return "Unauthorized", 401
    
    data = request.get_json()
    collection_name = data.get('collection') 
    new_order = data.get('order') 
    
    if collection_name == 'certificates':
        collection = certificates_col
    else:
        collection = projects_col
    
    for index, item_id in enumerate(new_order):
        collection.update_one({'_id': ObjectId(item_id)}, {'$set': {'position': index}})
        
    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True)