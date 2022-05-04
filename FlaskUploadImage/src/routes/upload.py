from audioop import add
from cmath import pi
import json
from pydoc import doc
from flask_restful import Resource,request
import cloudinary
import cloudinary.uploader
from cloudinary.uploader import upload
import cloudinary.api
from cloudinary.utils import cloudinary_url
import os
from bson.json_util import dumps
from bson.objectid import ObjectId
from models.user import User
from models.product import Product

import sys
sys.path.append('../../twilioservice')
from twilioservice.TwilioMsgService import send_sms


import base64 
from Cryptodome.Cipher import AES 
from Cryptodome.Util.Padding import pad,unpad
from pymongo import ReturnDocument



class Upload(Resource):
    def __init__(self,**kwargs):
        self.db=kwargs['db']
    def post(self):
        cloudinary.config(cloud_name = os.getenv('CLOUD_NAME'), api_key=os.getenv('API_KEY'), api_secret=os.getenv('API_SECRET'))
        file_to_upload = request.files['file']
        #name_of_file=request.form['name']
        tag_of_file=request.form['tag']
        #print(file_to_upload)

        if file_to_upload:
            upload_result = cloudinary.uploader.upload(file_to_upload)
            #print(upload_result)
            #self.db.items.insert_one({'name':name_of_file,'tag':tag_of_file,'image_url':upload_result['url']})
            self.db.items.insert_one({'tag':tag_of_file,'image_url':upload_result['url']})
            return {'message': 'success','data':upload_result['url']},200
        return {'message':'fail'}, 400

class GetAllData(Resource): 
    def __init__(self,**kwargs):
        self.db=kwargs['db']           
    def get(self):
        cursor=self.db.items.find()
        json_data=dumps(list(cursor))
        return json_data

class GetSingleImage(Resource): 
    def __init__(self,**kwargs):
        self.db=kwargs['db']           
    def get(self,oid):
        print(ObjectId(oid))
        cursor=self.db.items.find_one({"_id": ObjectId(oid)})
        print(cursor)
        json_data=dumps(list(cursor))
        print(json_data)
        return dumps(cursor)

class SignUpUser(Resource):
    def __init__(self,**kwargs):
        self.db=kwargs['db']
    def post(self):
        email=request.form['email']
        name=request.form['name']
        password=request.form['password']
        isAdmin=request.form['isAdmin']
        user=User(email=email,name=name,password=password,isAdmin=isAdmin)
        user_obj=user.getUser()
        if password=='' or name=='' or email=='':
            return {'upload': False,"message_data":"some fields are empty"}
        try:
            document=self.db.users.find_one({"email":email})
            print(document)
            if document==None:
                self.db.users.insert_one(user_obj)
                return {'upload':True,"message_data":"successfully registered"}
            else:
                return {'upload': False, "message_data":"email already present"}    
        except:
            return {'upload': False,"message_data":"could not upload"}
        
class LoginUser(Resource):
    def __init__(self,**kwargs):
        self.db=kwargs['db']
    def post(self):
        email=request.form['email']
        password=request.form['password']
        if password=='' or email=='':
            return {'login': False,"message_data":"some fields are empty"}
        try:
            document=self.db.users.find_one({"email":email})
            #print('document found',document)

            if document!=None:
                #password decrypt
                iv='BBBBBBBBBBBBBBBB'.encode('utf-8')
                enc=base64.b64decode(document['password'])
                cipher=AES.new('AAAAAAAAAAAAAAAA'.encode('utf-8'), AES.MODE_CBC, iv)
                password_decrypted=unpad(cipher.decrypt(enc),16).decode("utf-8")
                # print(document)
                #print(password_decrypted.decode("utf-8"))

                if password_decrypted==password:
                    return {'login':True,"message_data":"successfully logged in","login_data":dumps({"id":document['_id'],"name":document["name"]})}
                return {'login': False, "message_data":"invalid credentials"}
            else:
                return {'login': False, "message_data":"invalid credentials"}    
        except:
            return {'login': False,"message_data":"could not login"}
        
class PlaceOrder(Resource):
    def __init__(self,**kwargs):
        self.db=kwargs['db']
    def post(self):
        fname=request.form['fname']
        lname=request.form['lname']
        address=request.form['address']
        city=request.form['city']
        landmark=request.form['landmark']
        state=request.form['state']
        pin=request.form['pin']
        phone=request.form['phone']
        products=request.form['products']
        userId=request.form["userid"]
        print('userid:',ObjectId(userId))
        try:
            document=self.db.users.find_one_and_update({"_id":ObjectId(userId)},{'$push':{'orders':dumps(products)}},return_document=ReturnDocument.AFTER)
            print('user doc',document)
            if fname=='' or lname=='' or address=='' or city=='' or landmark=='' or state=='' or pin=='' or phone=='' or products=='':
                return {'upload': False,"message_data":"some fields are empty"}
            try:
                product=Product(fname=fname,lname=lname,address=address,pin=pin,products=products,phone=phone,landmark=landmark,state=state,city=city,userId=userId)
                product_obj=product.getProduct()
                placed_order=self.db.products.insert_one(product_obj)
                print('placed_order:',placed_order.inserted_id)
                self.db.users.find_one_and_update({"_id":ObjectId(userId)},{'$push':{'orderslist':placed_order.inserted_id}},return_document=ReturnDocument.AFTER)
                send_sms(body=f"AN ORDER HAS BEEN PLACED BY {fname+lname} PHONE: {phone} ADDRESS: {address} PIN: {pin} ORDERID: {placed_order.inserted_id}")
                return {'upload':True,"message_data":"successfully ordered","orderid":dumps(placed_order.inserted_id)}
            except:
                return {'upload': False,"message_data":"could not place order"}
        except:
            return {'upload': False,"message_data":"must be logged in to place order"}