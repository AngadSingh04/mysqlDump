from cryptography.fernet import Fernet

key = b'xNblDyLbMcwzpoLAndmSKeOPFduG4RPQEy4uCabSbxA=' 

cipher = Fernet(key)

enc_file_path = "/Users/angadsingh04/Downloads/party_20250223063808.csv.enc"


with open(enc_file_path, "rb") as enc_file:
    encrypted_data = enc_file.read()

decrypted_data = cipher.decrypt(encrypted_data)

decrypted_file_path = enc_file_path.replace(".enc", "_decrypted.csv")
with open(decrypted_file_path, "wb") as dec_file:
    dec_file.write(decrypted_data)

print(f"File decrypted successfully! Saved as: {decrypted_file_path}")
