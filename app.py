from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4'}

def load_users():
    try:
        with open('users.txt', 'r') as f:
            users = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        users = {}
    return users

def save_users(users):
    with open('users.txt', 'w') as f:
        json.dump(users, f)

users = load_users()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    if 'username' in session:
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], session['username'])
        files = os.listdir(user_folder) if os.path.isdir(user_folder) else []
        return render_template('index.html', files=files)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        if username in users:
            return jsonify({'success': False, 'message': 'Username already exists'}), 400
        else:
            users[username] = generate_password_hash(password)
            save_users(users)
            os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], username), exist_ok=True)
            return jsonify({'success': True, 'message': 'Registration successful. Please login'}), 200
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        if username in users and check_password_hash(users[username], password):
            session['username'] = username
            return jsonify({'success': True, 'message': 'Login successful'}), 200
        else:
            return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 403
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No selected file'}), 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], session['username'], filename)
            file.save(file_path)
            return jsonify({'success': True, 'message': 'File successfully uploaded'}), 200
    return render_template('upload.html')

@app.route('/download/<filename>')
def download(filename):
    if 'username' not in session:
        return redirect(url_for('login'))
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], session['username']), filename)

@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 403
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], session['username'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({'success': True, 'message': 'File deleted successfully'}), 200
    else:
        return jsonify({'success': False, 'message': 'File does not exist'}), 404

@app.route('/admin')
def admin():
    if 'username' not in session or session['username'] != 'admin':
        flash('You do not have permission to access this page.')
        return redirect(url_for('index'))
    users = load_users()
    return render_template('admin.html', users=users)

@app.route('/admin/delete/<username>', methods=['POST'])
def delete_user(username):
    if 'username' not in session or session['username'] != 'admin':
        flash('You do not have permission to perform this action.')
        return redirect(url_for('index'))
    users = load_users()
    if username in users:
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
        if os.path.isdir(user_folder):
            for file in os.listdir(user_folder):
                os.remove(os.path.join(user_folder, file))
            os.rmdir(user_folder)
        del users[username]
        save_users(users)
        flash(f'User {username} deleted successfully.')
    return redirect(url_for('admin'))
@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    user = load_user(session['username'])
    return render_template('profile.html', user=user)

def load_user(username):
    users = load_users()
    return users.get(username, {})
@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        email = request.form['email']
        bio = request.form['bio']
        users = load_users()
        users[session['username']] = {
            'username': session['username'],
            'password': users[session['username']]['password'],
        }
        save_users(users)
        flash('Profile updated successfully.')
        return redirect(url_for('profile'))
    user = load_user(session['username'])
    return render_template('edit_profile.html', user=user)
if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)