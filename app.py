from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, abort
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import mysql.connector
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# 🔧 MySQL Config (for Docker)
conn = mysql.connector.connect(
    host="db",
    user="root",
    password="root",
    database="cloud_storage"
)
cursor = conn.cursor(dictionary=True)

# 🔐 Login Manager Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 📁 Upload folder
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ✅ User Class
class User(UserMixin):
    def __init__(self, id, username, password, is_admin):
        self.id = id
        self.username = username
        self.password = password
        self.is_admin = is_admin

@login_manager.user_loader
def load_user(user_id):
    cursor.execute("SELECT id, username, password, is_admin FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if user:
        return User(**user)
    return None

# 🔑 Login Route
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
#         cursor.execute("SELECT id, username, password, is_admin FROM users WHERE username = %s", (username,))
#         user = cursor.fetchone()
#         if user and check_password_hash(user['password'], password):
#             login_user(User(**user))
#             # Redirect to admin panel if user is admin, otherwise to index
#             if user['is_admin']:
#                 return redirect(url_for('admin_panel'))
#             else:
#                 return redirect(url_for('index'))
#         return "Invalid credentials"
#     return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor.execute("SELECT id, username, password, is_admin FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if user and check_password_hash(user['password'], password):
            login_user(User(**user))
            # ✅ রিডাইরেক্ট করবে /admin অথবা /index অনুযায়ী
            if user['is_admin']:
                return redirect(url_for('admin_panel'))
            else:
                return redirect(url_for('index'))
        return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')


# 🚪 Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# 📝 Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        return redirect(url_for('login'))
    return render_template('signup.html')

# 🏠 Dashboard
@app.route('/')
@login_required
def index():
    return render_template('index.html')

# 📂 Upload
@app.route('/upload', methods=['POST'])
@login_required
def upload():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    filename = secure_filename(file.filename)
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.username)
    os.makedirs(user_folder, exist_ok=True)
    file.save(os.path.join(user_folder, filename))
    return redirect(url_for('index'))

# 📄 List Files
@app.route('/files')
@login_required
def files():
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.username)
    os.makedirs(user_folder, exist_ok=True)
    return jsonify(os.listdir(user_folder))

# 📥 Download
@app.route('/download/<filename>')
@login_required
def download(filename):
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.username)
    file_path = os.path.join(user_folder, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "File not found"

# 🌐 Open
@app.route('/open/<filename>')
@login_required
def open_file(filename):
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.username)
    file_path = os.path.join(user_folder, filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return "File not found"

# ❌ Delete
@app.route('/delete/<filename>', methods=['DELETE'])
@login_required
def delete(filename):
    path = os.path.join(app.config['UPLOAD_FOLDER'], current_user.username, filename)
    if os.path.exists(path):
        os.remove(path)
        return jsonify({'message': 'File deleted'})
    return jsonify({'error': 'File not found'})

# 🛠️ Admin Panel
@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    cursor.execute("SELECT id, username FROM users WHERE is_admin = FALSE")
    users = cursor.fetchall()
    return render_template('admin.html', users=users)

@app.route('/admin/add_user', methods=['POST'])
@login_required
def add_user():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    username = request.form['username']
    password = generate_password_hash(request.form['password'])
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
    conn.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    cursor.execute("DELETE FROM users WHERE id = %s AND is_admin = FALSE", (user_id,))
    conn.commit()
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)