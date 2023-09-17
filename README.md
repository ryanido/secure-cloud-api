# ************************Introduction************************

The objective of this project is to develop a secure cloud storage application that can be used with existing storage platforms such as Google Cloud, which is used in this implementation. The application allows for users to create a secure group in which they can add and remove other users from. Members of a user’s secure group are able to access the decrypted version of files uploaded by the creator of the group. Users that are not in a user’s secure group are only able to access the encrypted version of files previously uploaded by the creator of the group. The application also implements a key-management system that makes use of cryptographic algorithms, public and private keys to encrypt and decrypt files.

## **************Implementation**************

### Technologies

In this application, I used the following technologies

- **React** to provide a user interface for the application
- **Python FastAP**I to provide an API for retrieving user information, implementing cryptographic algorithms, and handling user uploading and downloading files
- **Firebase** for file storage, user authentication, and user data storage

### API

********************Libraries******************** 

- ******************************cryptography:****************************** This library provides cryptographic algorithms as well as public and private key generation for encryption and decryption
- ******************datetime:****************** This library provides access to todays date used to store in file metadata
- **************uuid :************** This library allows for the generation of unique id’s to use as naming for the encrypted file data
- ******************************firebase_admin :****************************** This library allows for firebase integration in the api
- ******************fastapi:****************** This library allows for the creation of the api aswell as response types

### Utils.py

This program defines functions used by the api to allow for the application to operate as intended.

******************Functions******************

- **`generate_keys(id)`**: This function generates a new private/public key pair for the user with the given ID. The private key is encrypted and stored in the **`users`** collection in Firebase, while the public key is stored in the **`public_keys`** collection.
- **`get_private_key(group_id)`**: This function retrieves the private key for the user with the given group ID from Firebase.
- **`get_public_key(user_id)`**: This function retrieves the public key for the user with the given ID from Firebase.
- **`encrypt_file(public_key, file_contents)`**: This function encrypts the given file contents using symmetric and asymmetric encryption. First, a random symmetric key is generated using the **`Fernet`** class from the **`cryptography`** library. The file contents are then encrypted using the symmetric key. The symmetric key is also encrypted using the given RSA public key. The concatenation of the encrypted symmetric key and encrypted file contents is returned
- **`decrypt_file(encrypted_contents, group_id, user_id)`**: This function decrypts the given encrypted file contents using symmetric and asymmetric decryption. The function first checks if the user with the given user ID is in the secure group with the given group ID. If the user is in the group, the function retrieves the private key for the group from Firebase and uses it to decrypt the symmetric key. The function then uses the symmetric key to decrypt the file contents. If the user is not in the group, the function returns the encrypted contents unchanged.
- **`get_group(user_id)`**: This function retrieves the list of user IDs in the secure group for the user with the given ID from Firebase.
- **`in_group(group_id,user_id)`:**  This function checks if the **`user_id`** is a member of the **`group_id`** by checking the group of **`group_id`** in the firebase database.
- **`write_to_storage(blob_name, data, author_id)`:** This function generates a unique ID for the file being stored, stores the file in Google Cloud Storage this ID, and adds an object to the Firestore database containing metadata about the file.
- **`get_from_storage(file_id)` :** This function retrieves a file from Google Cloud Storage using its ID and returns its content as a string.

### Main.py

This program defines the endpoints for the applications api.

- **`/get-group/{id}`**: GET request that retrieves information about a specific group id.
- **`/add-to-group`**: POST request that adds a user with id **`user_id`**  to a group with id **`group_id`**  .
- **`/remove-from-group`**: POST request that removes a user with id **`user_id`**  from a group with id**`group_id`** .
- **`/get-file`**: GET request that retrieves a specific file of id **`file_id`**  and decrypts it depending on the value of **`id`**  to generate a temporary file that is returned as a response.
- **`/get-files-data`**: GET request that retrieves information about all available files.
- **`/upload-file`**: POST request that uploads a file and encrypts it using the public key associated with **`id`.**

## Conclusion

In conclusion, the development of a Secure Cloud Storage application has been successfully implemented with the use of technologies such as React, Python, FastAPI and Firebase. This application provides users a way to upload and download files, as well as create a secure group in which the members are able to decrypt files. Overall, the development of this Application has been a successful project and is a useful tool for uploading cloud storage in a secure manner.

A live implementation of this application can be found here: https://secure-cloud-website.herokuapp.com/
