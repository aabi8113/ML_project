import flask
from flask import Flask, render_template, request, redirect, url_for, session
import os
from ultralytics import YOLO

app = Flask(__name__)
app.secret_key = 'your_secret_key'

users = {
    'admin': 'password',
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/index', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        #print(username,password)
        if (username in users) and (users[username] == password):
            session['username'] = username
            return redirect(url_for('upload'))

        else:
            return render_template('index.html', message='Invalid username or password')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Implement your signup logic here
        username = request.form['username']
        password = request.form['password']
        users[username]=password
        return redirect(url_for('index'))
    return render_template('signup.html')

from flask import send_from_directory

@app.route('/display/<filename>')
def display_image(filename):
    if 'username' in session:
        return render_template('display.html', filename=filename, p_destruction=p_destruction, p_commercial=p_commercial, p_residential=p_residential)
    else:
        return redirect(url_for('login'))

@app.route('/annotated_images/<filename>')
def annotated_image(filename):
    detect_dirs = [d for d in os.listdir('runs/detect') if os.path.isdir(os.path.join('runs/detect', d))]
    detect_dirs.sort(key=lambda d: os.path.getmtime(os.path.join('runs/detect', d)), reverse=True)
    latest_detect_dir = detect_dirs[0]
    annotated_images_directory = os.path.join('runs', 'detect', latest_detect_dir)
    return send_from_directory(annotated_images_directory, filename)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'username' in session:
        if request.method == 'POST':
            if not os.path.exists('uploads'):
                os.makedirs('uploads')
            f = request.files['file']
            f.save(os.path.join('uploads', f.filename))
            
            # Perform object detection on the uploaded image
            model = YOLO(r"C:/Users/MY PC/Desktop/minip/myapp/best (6).pt")
            image_path = os.path.join('uploads', f.filename)
            results = model(source=image_path, conf=0.6, save=True, show_labels=False, line_width=3)
            class_counts = {}
            for result in results:
                names = result.names
                for class_name in names.values():
                    class_counts[class_name] = 0
                detected_boxes = result.boxes.xyxy
                confidences = result.boxes.conf
                class_labels = result.boxes.cls
                for box, confidence, class_label in zip(detected_boxes, confidences, class_labels):
                    class_index = int(class_label)  
                    class_name = names[class_index]  
                    class_counts[class_name] += 1
            print(class_counts)
            calculations(class_counts)

            return redirect(url_for('display_image', filename=f.filename))
        return render_template('upload.html')
    else:
        return redirect(url_for('login'))


def calculations(c_c):
    global p_destruction
    global p_commercial
    global p_residential
    
    counts = sum(c_c.values()) 
    p_destruction = ((c_c.get('damagedcommercialbuilding', 0) + c_c.get('damagedresidentialbuilding', 0)) / counts) * 100
    p_residential = (c_c.get('damagedresidentialbuilding', 0) / counts) * 100
    p_commercial = (c_c.get('damagedcommercialbuilding', 0) / counts) * 100

    

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
