from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asymmetric_padding
from cryptography.hazmat.primitives import serialization, hashes,padding
from datetime import datetime
import firebase_admin
from firebase_admin import credentials,storage
from firebase_admin import firestore
import uuid

# Initialize Firebase with your own credentials
cred = credentials.Certificate('./config.json')
firebase_admin.initialize_app(cred,{'storageBucket': 'cloud-5ea4f.appspot.com'})

def generate_keys(id):
    # Generate a new private/public key pair
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()

    # Serialize the keys to PEM format
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Write the keys to Firebase
    db = firestore.client()

    # Write the public key to the "public_keys" collection
    public_key_ref = db.collection('public_keys').document(id)
    public_key_ref.set({'public_key': public_key_pem.decode('utf-8')})

    # Write the private key to the "users" collection
    user_ref = db.collection('users').document(id)
    user_ref.set({'private_key': private_key_pem.decode('utf-8'),
                  'secure_group':[]})

    # Return the keys as strings
    return private_key_pem.decode('utf-8'), public_key_pem.decode('utf-8')

def get_private_key(group_id):
    db = firestore.client()
    # Get a reference to the user document in the "users" collection
    user_ref = db.collection('users').document(group_id)
    # Retrieve the user document
    user_doc = user_ref.get()
    # Check if the user document exists
    if user_doc.exists:
        # Extract the private key from the user document
        private_key_pem = user_doc.to_dict().get('private_key')
        # If the private key is not None, return it as a cryptography PrivateKey object
        if private_key_pem is not None:
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode('utf-8'),
                password=None
            )
            return private_key
    # If the user document does not exist or the private key is None, return None
    return None

def get_public_key(user_id):
    db = firestore.client()
    # Get a reference to the user document in the "public-keys" collection
    user_ref = db.collection('public_keys').document(user_id)
    # Retrieve the user document
    user_doc = user_ref.get()
    # Check if the user document exists
    if user_doc.exists:
        # Extract the public key from the user document
        public_key_pem = user_doc.to_dict().get('public_key')
        # If the private key is not None, return it as a cryptography PrivateKey object
        if public_key_pem is not None:
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode('utf-8')
            )
            return public_key
    # If the user document does not exist or the private key is None, 
    return None

def encrypt_file(public_key, file_contents):
    # Generate a random key for the file encryption
    symmetric_key = Fernet.generate_key()
    f = Fernet(symmetric_key)

    # Encrypt the file with the symmetric key
    encrypted_contents = f.encrypt(file_contents)

    # Encrypt the symmetric key with the RSA public key
    encrypted_key = public_key.encrypt(
        symmetric_key,
        asymmetric_padding.OAEP(
            mgf=asymmetric_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted_key + encrypted_contents
    

    # Save the encrypted contents and encrypted key to a file
    # with open(encrypted_file_path, 'wb') as file:
    #     file.write(encrypted_key)
    #     file.write(encrypted_contents)


def decrypt_file(encrypted_contents, group_id,user_id):
    if in_group(group_id,user_id):
        private_key = get_private_key(group_id)
    else: 
        return encrypted_contents
    # Extract the encrypted key from the encrypted contents
    encrypted_key = encrypted_contents[:private_key.key_size // 8]
    
    # Decrypt the symmetric key using the RSA private key
    symmetric_key = private_key.decrypt(
        encrypted_key,
        asymmetric_padding.OAEP(
            mgf=asymmetric_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    # Decrypt the file contents using the symmetric key
    f = Fernet(symmetric_key)
    decrypted_contents = f.decrypt(encrypted_contents[private_key.key_size // 8:])
    return decrypted_contents

def get_group(user_id):
    db = firestore.client()
    user_ref = db.collection('users').document(user_id)
    # Retrieve the user document
    user_doc = user_ref.get()
    # Check if the user document exists
    if user_doc.exists:
        # Extract the private key from the user document
        return user_doc.to_dict().get('secure_group')
    generate_keys(user_id)
    return get_group


def in_group(group_id,user_id):
    if group_id == user_id: 
        return True
    # Get a reference to the user document in Firestore
    db = firestore.client()
    group_ref = db.collection('users').document(group_id)

    # Get the list of users in secure group
    group_data = group_ref.get().to_dict()
    group_members = group_data.get('secure_group', [])

    # Check if the user is in the specified group
    return user_id in group_members


def write_to_storage(blob_name, data, author_id):
    # Generate a unique id for the file being stored
    file_id = str(uuid.uuid4())

    # Store the file under the generated id name
    bucket = storage.bucket()
    blob = bucket.blob(file_id)
    blob.upload_from_string(data)

    # Add an object to the firestore database with the file id, name, author id, date added, and size
    db = firestore.client()
    file_ref = db.collection('files').document(file_id)
    file_ref.set({
        'name': blob_name,
        'author': author_id,
        'date_added': datetime.utcnow(), # Add the date added attribute with the current UTC time
        'size': len(data) # Add the size attribute with the length of the data
    })

    return file_id

def get_from_storage(file_id):
    # Retrieve the file from storage using its id
    bucket = storage.bucket()
    blob = bucket.blob(file_id)
    return blob.download_as_string()



# private_key, public_key = generate_keys("1")
# file_path = 'test'
# file_extension = 'png'

# encrypted_data = encrypt_file(public_key, f'{file_path}.{file_extension}')

# write_to_storage(f'{file_path}_enc.{file_extension}',encrypted_data,"1")
# data_to_decrypt = get_from_storage(f'{file_path}_enc.{file_extension}',"1")
# remove_from_group("1","2")
# decrypted_contents = decrypt_file(data_to_decrypt, "1","1")
# with open(f'{file_path}_d.{file_extension}', 'wb') as file:
#         file.write(decrypted_contents)

# print('Private key:', private_key)
# print('Public key:', public_key)

