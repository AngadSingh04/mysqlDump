import argparse
import os
import pandas as pd
import mysql.connector
from cryptography.fernet import Fernet
import datetime

db_host = os.getenv("DB_HOST") #root user is having restriction
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")

export_dir = "encrypted_files"
os.makedirs(export_dir, exist_ok=True)

def encrypt_key():
    return Fernet.generate_key()

def encrypt_file(file_path, key):
    with open(file_path, "rb") as file:
        data=file.read()
    encrypted_data = Fernet(key).encrypt(data)
    
    enc_file_path = file_path + ".enc"
    with open(enc_file_path, "wb") as file:
        file.write(encrypted_data)
    
    os.remove(file_path) 
    return enc_file_path

def export_table_to_csv(db_name, table_name):
    conn = mysql.connector.connect(host=db_host, user=db_user, password=db_password, database=db_name)
    cursor = conn.cursor()
    

    query = f"select * from {table_name}"
    cursor.execute(query)
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]


    filename = f"{table_name}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    file_path = os.path.join(export_dir, filename)
    
    df = pd.DataFrame(rows, columns=columns)
    df.to_csv(file_path, index=False)

    conn.close()
    return file_path, filename

def store_file_info(filename, password):
    conn = mysql.connector.connect(host=db_host, user=db_user, password=db_password, database=db_name)
    cursor = conn.cursor()
    
    query = "insert into file_info (filename, password) VALUES (%s, %s)"
    cursor.execute(query, (filename, password.decode()))
    conn.commit()
    
    conn.close()
    
def main(db_name, table_name):
    file_path, filename = export_table_to_csv(db_name, table_name)
    key = encrypt_key()
    
    enc_file_path = encrypt_file(file_path, key)
    store_file_info(filename + ".enc", key)

    print(f"Encrypted file saved at: {enc_file_path}")
    print(f"Decryption key stored in database.")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export MySQL table to encrypted CSV")
    parser.add_argument("database", help="Database name")
    parser.add_argument("table", help="Table name")
    args = parser.parse_args()

    main(args.database, args.table)