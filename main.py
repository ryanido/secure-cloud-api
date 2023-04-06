from fastapi import FastAPI,Request,UploadFile
from fastapi.responses import JSONResponse, Response, FileResponse
from utils import *
from firebase_admin import credentials,storage
from firebase_admin import firestore


app = FastAPI()
@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/get-group/{id}")
async def get_group_handler(id: str):
    group = get_group(id)
    return JSONResponse(group)

@app.post("/add-to-group")
async def add_to_group(group_id: str, user_id: str):
    db = firestore.client()
    user_ref = db.collection('users').document(group_id)
    if not user_ref.get().exists:
        return {"message": f"Group {group_id} does not exist"}
    # Add user to group
    if in_group(group_id,user_id): return {"message": f"User {user_id} already in {group_id}"}
    user_ref.update({
        'secure_group': firestore.ArrayUnion([user_id])
    })
    return JSONResponse({"message": f"User {user_id} added to group {group_id}"})

@app.post("/remove-from-group")
async def remove_from_group(group_id: str, user_id: str):
    # Remove user from group
    if not in_group(group_id,user_id): return {"message": f"User {user_id} not in {group_id}"}
    db = firestore.client()
    user_ref = db.collection('users').document(group_id)
    user_ref.update({
        'secure_group': firestore.ArrayRemove([user_id])
    })
    return {"message": f"User {user_id} removed from group {group_id}"}

@app.get("/get-file")
async def get_file(id: str, file_id: str):
    encrypted_contents = get_from_storage(file_id) 
    db = firestore.client()
    file_ref = db.collection('files').document(file_id)
    file_data = file_ref.get().to_dict()
    decrypted_contents = decrypt_file(encrypted_contents, file_data['author'], id)

    # Save the decrypted contents to a temporary file
    # Change the file extension to match the original file
    
    with open(file_data['name'], "wb") as f:
        f.write(decrypted_contents)

    # Return the file as a response
    return FileResponse(path=file_data['name'], filename=file_data['name'])

@app.get("/get-files-data")
async def get_files_data():
    db = firestore.client()
    files_ref = db.collection('files')
    files_data = []
    for file_doc in files_ref.stream():
        file_data = file_doc.to_dict()
        file_data['id'] = file_doc.id
        files_data.append(file_data)
    return JSONResponse(files_data)
    
@app.post("/upload-file")
def upload(id:str ,file: UploadFile):
    contents = file.file.read()
    public_key = get_public_key(id)
    encrypted_file = encrypt_file(public_key,contents)
    write_to_storage(file.filename,encrypted_file,id)
    return {"message": f"Successfully uploaded {file.filename}"}