import os
import cloudinary
import cloudinary.uploader
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
import certifi
from bson.objectid import ObjectId

app = Flask(__name__, static_folder='assets', static_url_path='/assets')
app.secret_key = 'super_secret_key'

# --- MONGODB CONNECTION ---
# Using the connection string you found earlier
MONGO_URI = "mongodb+srv://admin:Sivaraj9677@cluster0.bisuniq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['portfolio_db']

certificates_col = db['certificates']
projects_col = db['projects']
visitors_col = db['visitors'] # New collection for counting views
# --------------------------

# --- CLOUDINARY CONFIG ---
cloudinary.config(
    cloud_name = "doqgziycf", 
    api_key = "636344164192868", 
    api_secret = "gMBO2pdLflJByR1IFqhcZDG8M1M",
    secure = True
)
# -------------------------

@app.route('/')
def index():
    # 1. VISITOR COUNTER (Total Views)
    # This finds the counter and adds +1. If it doesn't exist, it creates it.
    visitor_data = visitors_col.find_one_and_update(
        {'_id': 'site_stats'},
        {'$inc': {'count': 1}},
        upsert=True,
        return_document=True
    )
    total_views = visitor_data['count']

    # 2. FETCH DATA (Sorted by position)
    certificates = list(certificates_col.find().sort('position', 1))
    projects = list(projects_col.find().sort('position', 1))
    
    return render_template('index.html', 
                           certificates=certificates, 
                           projects=projects,
                           visitors=total_views)

@app.route('/admin')
def admin():
    if 'logged_in' not in session: return render_template('admin_login.html')
    
    certificates = list(certificates_col.find().sort('position', 1))
    projects = list(projects_col.find().sort('position', 1))
    
    return render_template('admin.html', 
                           certificates=certificates, 
                           projects=projects)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
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

@app.route('/add_certificate', methods=['POST'])
def add_certificate():
    if 'logged_in' not in session: return redirect(url_for('login'))
    title = request.form['title']
    image = request.files['image']
    if image:
        upload_result = cloudinary.uploader.upload(image)
        certificates_col.insert_one({
            'title': title, 'image': upload_result['secure_url'], 'position': 0 
        })
    return redirect(url_for('admin'))

@app.route('/delete_certificate/<string:id>')
def delete_certificate(id):
    if 'logged_in' not in session: return redirect(url_for('admin'))
    certificates_col.delete_one({'_id': ObjectId(id)})
    return redirect(url_for('admin'))

@app.route('/add_project', methods=['POST'])
def add_project():
    if 'logged_in' not in session: return redirect(url_for('login'))
    title = request.form['title']
    category = request.form['category']
    image = request.files['image']
    if image:
        upload_result = cloudinary.uploader.upload(image)
        projects_col.insert_one({
            'title': title, 'category': category, 
            'image': upload_result['secure_url'], 'position': 0
        })
    return redirect(url_for('admin'))

@app.route('/delete_project/<string:id>')
def delete_project(id):
    if 'logged_in' not in session: return redirect(url_for('admin'))
    projects_col.delete_one({'_id': ObjectId(id)})
    return redirect(url_for('admin'))

# --- REORDER LOGIC ---
@app.route('/reorder', methods=['POST'])
def reorder():
    if 'logged_in' not in session: return "Unauthorized", 401
    data = request.get_json()
    collection = certificates_col if data.get('collection') == 'certificates' else projects_col
    for index, item_id in enumerate(data.get('order')):
        collection.update_one({'_id': ObjectId(item_id)}, {'$set': {'position': index}})
    return "OK", 200
@app.route('/project/<int:index>')
def project_details(index):
    # Fetch all projects sorted by position
    projects = list(projects_col.find().sort('position', 1))
    
    # Check if the index is valid
    if 0 <= index < len(projects):
        project = projects[index]
        return render_template('project_details.html', project=project)
    
    # If project not found, go back home
    return redirect(url_for('index'))
if __name__ == '__main__':
    app.run(debug=True)