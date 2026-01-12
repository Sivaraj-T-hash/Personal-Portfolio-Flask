import os
import cloudinary
import cloudinary.uploader
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
import certifi
from bson.objectid import ObjectId

app = Flask(__name__, static_folder='assets', static_url_path='/assets')
app.secret_key = 'super_secret_key'

# --- 1. MONGODB CONNECTION ---
MONGO_URI = "mongodb+srv://admin:Sivaraj9677@cluster0.bisuniq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['portfolio_db']

certificates_col = db['certificates']
projects_col = db['projects']
visitors_col = db['visitors']

# --- 2. CLOUDINARY CONFIG ---
cloudinary.config(
    cloud_name = "doqgziycf", 
    api_key = "636344164192868", 
    api_secret = "gMBO2pdLflJByR1IFqhcZDG8M1M",
    secure = True
)

# --- ROUTES ---

@app.route('/')
def index():
    try:
        # Visitor Counter
        visitor_data = visitors_col.find_one_and_update(
            {'_id': 'site_stats'},
            {'$inc': {'count': 1}},
            upsert=True,
            return_document=True
        )
        if visitor_data:
            total_views = visitor_data['count']
        else:
            total_views = 0

        # Fetch Data
        certificates = list(certificates_col.find().sort('position', 1))
        projects = list(projects_col.find().sort('position', 1))
        
        return render_template('index.html', 
                               certificates=certificates, 
                               projects=projects,
                               visitors=total_views)
    except Exception as e:
        return f"<h1 style='color:red;'>Error Found:</h1><p>{str(e)}</p>"

@app.route('/admin')
def admin():
    if 'logged_in' not in session: return render_template('admin_login.html')
    certificates = list(certificates_col.find().sort('position', 1))
    projects = list(projects_col.find().sort('position', 1))
    return render_template('admin.html', certificates=certificates, projects=projects)

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
    description = request.form.get('description', '')
    image = request.files['image']
    report = request.files['report']
    if image:
        upload_result = cloudinary.uploader.upload(image)
        report_url = ""
        if report:
            report_res = cloudinary.uploader.upload(report, resource_type="auto")
            report_url = report_res['secure_url']
        projects_col.insert_one({
            'title': title, 'category': category, 'description': description,
            'image': upload_result['secure_url'], 'report': report_url, 'position': 0
        })
    return redirect(url_for('admin'))

@app.route('/delete_project/<string:id>')
def delete_project(id):
    if 'logged_in' not in session: return redirect(url_for('admin'))
    projects_col.delete_one({'_id': ObjectId(id)})
    return redirect(url_for('admin'))

@app.route('/reorder', methods=['POST'])
def reorder():
    if 'logged_in' not in session: return "Unauthorized", 401
    data = request.get_json()
    collection = certificates_col if data.get('collection') == 'certificates' else projects_col
    for index, item_id in enumerate(data.get('order')):
        collection.update_one({'_id': ObjectId(item_id)}, {'$set': {'position': index}})
    return "OK", 200

# --- THE FIX IS HERE ---
# We changed <int:index> to <int:id> to match your HTML
@app.route('/project/<int:id>')
def project_details(id):
    projects = list(projects_col.find().sort('position', 1))
    if 0 <= id < len(projects):
        project = projects[id]
        return render_template('project_details.html', project=project)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)