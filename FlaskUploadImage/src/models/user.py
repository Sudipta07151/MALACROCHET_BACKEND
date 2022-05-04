import json

class User:
    def __init__(self,email='',password='',name='',isAdmin=False):
        self.email=email
        self.password=password
        self.isAdmin=isAdmin
        self.name=name
    def getUser(self):
        user_obj = {"name":self.name,"email":self.email,"isAdmin": self.isAdmin,"password":self.password}
        return user_obj