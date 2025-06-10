# from flask import Flask
# app = Flask(__name__)

# @app.route('/')
# def hello_world():
#     return 'Hello, World!'
    
# if __name__ == '__main__':
#   app.run(host='0.0.0.0',port=5000)


# import os
# import pandas as pd
# from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, send_file
# from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas
# from werkzeug.utils import secure_filename
# from datetime import datetime, timedelta
# from dotenv import load_dotenv
# from io import BytesIO

# load_dotenv()

# # 环境变量读取
# AZURE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
# CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER", "AssignmentOne")
# FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "default-secret-key-2025")

# # Azure Blob Storage 客户端
# blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
# container_client = blob_service_client.get_container_client(CONTAINER_NAME)
# try:
#     container_client.get_container_properties()
# except Exception:
#     container_client = blob_service_client.create_container(CONTAINER_NAME)

# # 修改容器创建时的访问策略（如果允许公开读取）
# try:
#     container_client.create_container(public_access='blob')  # 添加公共读取权限
# except Exception as e:
#     print(f"Container exists or error: {str(e)}")

# # Flask 配置
# app = Flask(__name__)
# app.secret_key = FLASK_SECRET_KEY
# ALLOWED_EXTENSIONS = {'csv'}
# ALLOWED_PHOTO_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

# # 全局数据
# people_data = {}

# def allowed_file(filename, extensions):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions

# def load_csv_data_from_blob(blob_name):
#     """从Azure Blob加载CSV数据"""
#     try:
#         blob_client = container_client.get_blob_client(blob_name)
#         stream = blob_client.download_blob().readall()
#         df = pd.read_csv(BytesIO(stream))
#         data = {}
#         for _, row in df.iterrows():
#             name = str(row.get('Name', '')).strip()
#             if name and name != 'nan':
#                 data[name] = {
#                     'State': str(row.get('State', '')),
#                     'Salary': str(row.get('Salary', '')),
#                     'Grade': str(row.get('Grade', '')),
#                     'Room': str(row.get('Room', '')),
#                     'Telnum': str(row.get('Telnum', '')),
#                     'Picture': str(row.get('Picture', '')),
#                     'Keywords': str(row.get('Keywords', ''))
#                 }
#         return data
#     except Exception as e:
#         flash(f'Error loading CSV: {str(e)}')
#         return {}

# def get_blob_url(filename, expiry_hours=1):
#     """生成带SAS的Blob访问URL"""
#     sas_token = generate_blob_sas(
#         account_name=blob_service_client.account_name,
#         container_name=CONTAINER_NAME,
#         blob_name=filename,
#         account_key=blob_service_client.credential.account_key,
#         permission=BlobSasPermissions(read=True),
#         expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
#     )
#     url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{CONTAINER_NAME}/{filename}?{sas_token}"
#     return url

# @app.route('/')
# def index():
#     return render_template('index.html', people_data=people_data)

# @app.route('/upload_csv', methods=['POST'])
# def upload_csv():
#     global people_data
#     if 'csv_file' not in request.files:
#         flash('No CSV file selected')
#         return redirect(url_for('index'))
#     file = request.files['csv_file']
#     if file.filename == '':
#         flash('No CSV file selected')
#         return redirect(url_for('index'))
#     if file and allowed_file(file.filename, ALLOWED_EXTENSIONS):
#         filename = secure_filename(file.filename)
#         blob_client = container_client.get_blob_client(filename)
#         blob_client.upload_blob(file, overwrite=True)
#         people_data.clear()
#         people_data.update(load_csv_data_from_blob(filename))
#         flash(f'CSV uploaded successfully! Loaded {len(people_data)} records.')
#     else:
#         flash('Invalid file type. Please upload a CSV file.')
#     return redirect(url_for('index'))

# @app.route('/upload_photos', methods=['POST'])
# def upload_photos():
#     if 'photo_files' not in request.files:
#         flash('No photos selected')
#         return redirect(url_for('index'))
#     files = request.files.getlist('photo_files')
#     uploaded_count = 0
#     for file in files:
#         if file.filename == '':
#             continue
#         if file and allowed_file(file.filename, ALLOWED_PHOTO_EXTENSIONS):
#             filename = secure_filename(file.filename)
#             blob_client = container_client.get_blob_client(filename)
#             try:
#                 blob_client.upload_blob(file, overwrite=True)
#                 uploaded_count += 1
#             except Exception as e:
#                 flash(f'Upload error for {filename}: {str(e)}')
#         else:
#             flash(f'Invalid photo type: {file.filename}')
#     flash(f'Uploaded {uploaded_count} photos successfully!')
#     return redirect(url_for('index'))

# # 修改 serve_photo 路由的 SAS 有效期（从1小时延长至24小时）
# @app.route('/photo/<filename>')
# def serve_photo(filename):
#     return redirect(get_blob_url(filename, expiry_hours=24))  # 延长至24小时

# @app.route('/search', methods=['POST'])
# def search():
#     search_type = request.form.get('search_type')
#     results = []
#     if search_type == 'name':
#         name = request.form.get('search_name', '').strip()
#         if name in people_data:
#             results = [{'name': name, 'data': people_data[name]}]
#     elif search_type == 'state':
#         state = request.form.get('search_state', '').strip().upper()
#         for name, data in people_data.items():
#             if data['State'].upper() == state:
#                 results.append({'name': name, 'data': data})
#     elif search_type == 'salary':
#         min_salary = request.form.get('min_salary', '')
#         max_salary = request.form.get('max_salary', '')
#         for name, data in people_data.items():
#             salary_str = data['Salary']
#             if salary_str and salary_str != 'nan' and salary_str != '':
#                 try:
#                     salary = float(salary_str)
#                     include = True
#                     if min_salary and float(min_salary) > salary:
#                         include = False
#                     if max_salary and float(max_salary) < salary:
#                         include = False
#                     if include:
#                         results.append({'name': name, 'data': data})
#                 except ValueError:
#                     continue
#     return render_template('index.html', people_data=people_data, search_results=results)

# @app.route('/get_person/<name>')
# def get_person(name):
#     if name in people_data:
#         return jsonify({'success': True, 'data': people_data[name]})
#     return jsonify({'success': False, 'message': 'Person not found'})

# @app.route('/update_person', methods=['POST'])
# def update_person():
#     global people_data
#     name = request.form.get('name')
#     if name not in people_data:
#         flash('Person not found')
#         return redirect(url_for('index'))
#     people_data[name]['State'] = request.form.get('state', '')
#     people_data[name]['Salary'] = request.form.get('salary', '')
#     people_data[name]['Grade'] = request.form.get('grade', '')
#     people_data[name]['Room'] = request.form.get('room', '')
#     people_data[name]['Telnum'] = request.form.get('telnum', '')
#     people_data[name]['Keywords'] = request.form.get('keywords', '')
#     flash(f'Updated information for {name}')
#     return redirect(url_for('index'))

# @app.route('/add_photo/<name>', methods=['POST'])
# def add_photo(name):
#     if name not in people_data:
#         flash('Person not found')
#         return redirect(url_for('index'))
#     if 'photo_file' not in request.files:
#         flash('No photo selected')
#         return redirect(url_for('index'))
#     file = request.files['photo_file']
#     if file.filename == '' or not allowed_file(file.filename, ALLOWED_PHOTO_EXTENSIONS):
#         flash('Invalid photo file')
#         return redirect(url_for('index'))
#     filename = secure_filename(file.filename)
#     blob_client = container_client.get_blob_client(filename)
#     blob_client.upload_blob(file, overwrite=True)
#     people_data[name]['Picture'] = filename
#     flash(f'Photo added for {name}')
#     return redirect(url_for('index'))

# @app.route('/delete_photo/<name>', methods=['POST'])
# def delete_photo(name):
#     global people_data
#     if name not in people_data:
#         flash('Person not found')
#         return redirect(url_for('index'))
#     picture = people_data[name].get('Picture', '')
#     if not picture:
#         flash('No photo to delete for this person')
#         return redirect(url_for('index'))
#     blob_client = container_client.get_blob_client(picture)
#     try:
#         blob_client.delete_blob()
#     except Exception:
#         pass
#     people_data[name]['Picture'] = ''
#     flash(f'Photo deleted for {name}')
#     return redirect(url_for('index'))

# @app.route('/remove_person/<name>', methods=['POST'])
# def remove_person(name):
#     global people_data
#     if name in people_data:
#         picture = people_data[name].get('Picture', '')
#         if picture:
#             blob_client = container_client.get_blob_client(picture)
#             try:
#                 blob_client.delete_blob()
#             except Exception:
#                 pass
#         del people_data[name]
#         flash(f'Removed {name} from database')
#     else:
#         flash('Person not found')
#     return redirect(url_for('index'))

# @app.route('/photo/<filename>')
# def serve_photo(filename):
#     # 生成带SAS的URL并重定向
#     return redirect(get_blob_url(filename))

# if __name__ == '__main__':
#     app.run(host='0.0.0.0',port=5000)

# # 修改启动代码，关闭调试模式
# # if __name__ == '__main__':
# #     # 仅开发环境使用 debug
# #     if os.getenv("FLASK_ENV") == "development":
# #         app.run(debug=True, host='0.0.0.0', port=8000)
# #     else:
# #         # 生产环境配置
# #         from waitress import serve
# #         serve(app, host="0.0.0.0", port=8000)

from flask import Flask, request, render_template, redirect, url_for
import pandas as pd
import os
from azure.storage.blob import BlobServiceClient
from werkzeug.utils import secure_filename
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Read sensitive data from environment variables
AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
CONTAINER_NAME = "peopledemo"

blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

# Check if the container exists, create if it doesn't
# try:
#     container_client.get_container_properties()
#     print("Container exists.")
# except Exception as e:
#     print("Container does not exist. Creating it now...")
#     container_client = blob_service_client.create_container(CONTAINER_NAME)
#     print("Container created successfully.")


# Flask app
app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    # Upload people.csv
    people_file = request.files["people"]
    if people_file.filename:
        filename = secure_filename(people_file.filename)
        people_file.save(os.path.join(UPLOAD_FOLDER, filename))
        # Upload to Blob
        blob_client = container_client.get_blob_client("people.csv")
        with open(os.path.join(UPLOAD_FOLDER, filename), "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

    # Upload picture
    picture = request.files["picture"]
    if picture.filename:
        filename = secure_filename(picture.filename)
        picture.save(os.path.join(UPLOAD_FOLDER, filename))
        # Upload to Blob
        blob_client = container_client.get_blob_client(filename)
        with open(os.path.join(UPLOAD_FOLDER, filename), "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

    return redirect(url_for("index"))

@app.route("/search", methods=["POST"])
def search():
    name = request.form["name"]

    # Download CSV
    blob_client = container_client.get_blob_client("people.csv")
    with open(os.path.join(UPLOAD_FOLDER, "people.csv"), "wb") as f:
        f.write(blob_client.download_blob().readall())

    # Read CSV
    df = pd.read_csv(os.path.join(UPLOAD_FOLDER, "people.csv"), header=None)
    df.columns = ["Name", "State", "Salary", "Grade", "Room", "Telnum", "Picture", "Keywords"]


    # Search
    person = df[df["Name"].str.lower() == name.lower()].to_dict(orient="records")
    if person:
        person = person[0]
        # Get picture URL from Blob
        blob_client = container_client.get_blob_client(person["Picture"])
        pic_url = blob_client.url
        return render_template("result.html", person=person, pic_url=pic_url)
    else:
        return "Person not found!"

@app.route("/update", methods=["POST"])
def update():
    name = request.form["name"]
    new_keywords = request.form["keywords"]

    # Download CSV
    blob_client = container_client.get_blob_client("people.csv")
    with open(os.path.join(UPLOAD_FOLDER, "people.csv"), "wb") as f:
        f.write(blob_client.download_blob().readall())

    df = pd.read_csv(os.path.join(UPLOAD_FOLDER, "people.csv"), header=None)
    df.columns = ["Name", "State", "Salary", "Grade", "Room", "Telnum", "Picture", "Keywords"]

    df.loc[df["Name"].str.lower() == name.lower(), "Keywords"] = new_keywords
    df.to_csv(os.path.join(UPLOAD_FOLDER, "people.csv"), header=False, index=False)

    # Re-upload CSV
    with open(os.path.join(UPLOAD_FOLDER, "people.csv"), "rb") as data:
        blob_client.upload_blob(data, overwrite=True)

    return "Keywords updated!"

if __name__ == "__main__":
    app.run(debug=True)