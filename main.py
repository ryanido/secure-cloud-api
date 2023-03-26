from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asymmetric_padding
from cryptography.hazmat.primitives import serialization, hashes,padding

import firebase_admin
from firebase_admin import credentials,storage
from firebase_admin import firestore

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

def encrypt_file(public_key_str, file_path):
    # Load the public key from the PEM string
    public_key = serialization.load_pem_public_key(
        public_key_str.encode('utf-8')
    )
    # Generate a random key for the file encryption
    symmetric_key = Fernet.generate_key()
    f = Fernet(symmetric_key)

    # Encrypt the file with the symmetric key
    with open(file_path, 'rb') as file:
        file_contents = file.read()
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

def decrypt_file(private_key_str, encrypted_file_path, decrypted_file_path):
    # Load the private key from the PEM string
    private_key = serialization.load_pem_private_key(
        private_key_str.encode('utf-8'),
        password=None
    )
    # Load the encrypted contents and encrypted key from the file
    with open(encrypted_file_path, 'rb') as file:
        encrypted_key = file.read(private_key.key_size // 8)
        encrypted_contents = file.read()

    # Decrypt the symmetric key using the RSA private key
    symmetric_key = private_key.decrypt(
        encrypted_key,
        asymmetric_padding.OAEP(
            mgf=asymmetric_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    f = Fernet(symmetric_key)

    # Decrypt the file contents using the symmetric key
    decrypted_contents = f.decrypt(encrypted_contents)

    # Save the decrypted contents to a file
    with open(decrypted_file_path, 'wb') as file:
        file.write(decrypted_contents)


def add_to_group(user_id, group_id):
    # Add user to group
    db = firestore.client()
    user_ref = db.collection('users').document(user_id)
    user_ref.update({
        'secure_group': firestore.ArrayUnion([group_id])
    })


def remove_from_group(user_id, group_id):
    # Remove user from group
    db = firestore.client()
    user_ref = db.collection('users').document(user_id)
    user_ref.update({
        'secure_group': firestore.ArrayRemove([group_id])
    })

def in_group(user_id, group_id):
    # Get a reference to the user document in Firestore
    db = firestore.client()
    group_ref = db.collection('users').document(group_id)

    # Get the list of users in secure group
    group_data = group_ref.get().to_dict()
    group_members = group_data.get('secure_group', [])

    # Check if the user is in the specified group
    return user_id in group_members

def write_to_storage(blob_name, data, id):
    bucket = storage.bucket()
    blob = bucket.blob(blob_name)
    blob.upload_from_string(data)

private_key, public_key = generate_keys("1")
file_path = 'test'
file_extension = 'png'

encrypted_data = encrypt_file(public_key, f'{file_path}.{file_extension}')

write_to_storage(f'{file_path}_enc.{file_extension}',encrypted_data,id)

# decrypt_file(private_key, f'{file_path}_enc.{file_extension}', f'{file_path}_dec.{file_extension}')


print('Private key:', private_key)
print('Public key:', public_key)

