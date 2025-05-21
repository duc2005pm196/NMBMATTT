from flask import Flask, render_template, request, send_file
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def adjust_key(key):
    key = key.encode('utf-8')
    if len(key) < 16:
        key = key.ljust(16, b'0')
    elif 16 < len(key) < 24:
        key = key.ljust(24, b'0')
    elif 24 < len(key) < 32:
        key = key.ljust(32, b'0')
    return key[:32]  # truncate if longer than 32

def encrypt_file(input_path, output_path, key):
    with open(input_path, 'rb') as f:
        data = f.read()
    cipher = AES.new(key, AES.MODE_CBC)
    ciphertext = cipher.encrypt(pad(data, AES.block_size))
    with open(output_path, 'wb') as f:
        f.write(cipher.iv + ciphertext)

def decrypt_file(input_path, output_path, key):
    with open(input_path, 'rb') as f:
        iv = f.read(16)
        ciphertext = f.read()
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
    with open(output_path, 'wb') as f:
        f.write(plaintext)

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ''
    if request.method == 'POST':
        action = request.form['action']
        file = request.files.get('file')
        password = request.form.get('password', '')

        if not file or not password:
            message = 'Vui lòng chọn file và nhập khóa.'
        else:
            filename = file.filename
            input_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(input_path)

            key = adjust_key(password)

            if action == 'encrypt':
                output_path = os.path.join(UPLOAD_FOLDER, 'encrypted_' + filename)
                encrypt_file(input_path, output_path, key)
                return send_file(output_path, as_attachment=True)
            elif action == 'decrypt':
                output_path = os.path.join(UPLOAD_FOLDER, 'decrypted_' + filename)
                try:
                    decrypt_file(input_path, output_path, key)
                    return send_file(output_path, as_attachment=True)
                except Exception:
                    message = 'Sai khóa hoặc file bị hỏng.'

    return render_template('index.html', message=message)

if __name__ == '__main__':
    app.run(debug=True)
