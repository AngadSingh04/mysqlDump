from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import mysql.connector
from cryptography.fernet import Fernet
import secrets
import logging
import subprocess
import os

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")
export_dir = "encrypted_files"

def get_tables():
    conn = mysql.connector.connect(host=db_host, user=db_user, password=db_password, database=db_name)
    cursor = conn.cursor()
    cursor.execute("show tables")
    tables = [table[0] for table in cursor.fetchall()]
    conn.close()
    return tables

def get_stored_files():
    conn = mysql.connector.connect(host=db_host, user=db_user, password=db_password, database=db_name)
    cursor = conn.cursor()
    cursor.execute("select filename, password from file_info")
    files = cursor.fetchall()
    conn.close()
    return files

@app.route("/", methods=["GET", "POST"])
def index():
    tables = get_tables()
    files = get_stored_files()

    if request.method == "POST":
        table_name = request.form["table"]
        subprocess.run(["python", "csvDump_encrypt.py", db_name, table_name])
        return redirect(url_for("index"))

    return render_template("index.html", tables=tables, files=files)

@app.route("/decrypt/<filename>", methods=["POST"])
def decrypt(filename):
    password = request.form.get("password")
    
    conn = mysql.connector.connect(host=db_host, user=db_user, password=db_password, database=db_name)
    cursor = conn.cursor()
    cursor.execute("select password from file_info where filename = %s", (filename,))
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0] == password:
        decrypted_file_path = decrypt_file(os.path.join(export_dir, filename), result[0].encode())

        if decrypted_file_path and os.path.exists(decrypted_file_path):
            return send_file(decrypted_file_path, as_attachment=True)
        else:
            flash("Decryption failed or file not found.", "error")
    else:
        flash("Invalid password.", "error")

    return redirect(url_for("index"))

    
@app.route("/delete/<filename>", methods=["POST"])
def delete(filename):
    try:
        os.remove(os.path.join(export_dir, filename))
        conn = mysql.connector.connect(host=db_host, user=db_user, password=db_password, database=db_name)
        cursor = conn.cursor()
        cursor.execute("delete from file_info WHERE filename = %s", (filename,))
        conn.commit()
        conn.close()
        flash("File deleted successfully.", "success")
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        flash("An error occurred while deleting the file.", "error")
    return redirect(url_for("index"))

@app.route("/download/<filename>")
def download(filename):
    return send_file(os.path.join(export_dir, filename), as_attachment=True)

def decrypt_file(filepath, key):
    try:
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            return None

        with open(filepath, "rb") as file:
            encrypted_data = file.read()
        decrypted_data = Fernet(key).decrypt(encrypted_data)
        
        decrypted_filepath = filepath.replace(".enc", "_decrypted.csv")
        with open(decrypted_filepath, "wb") as file:
            file.write(decrypted_data)

        return decrypted_filepath
    except Exception as e:
        logger.error(f"Error decrypting file: {e}")
        return None


if __name__ == "__main__":
    app.run(debug=True)
