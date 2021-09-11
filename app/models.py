import pymongo
from bson import ObjectId

class Mongo:
    def __init__(self, database):
        mongo_uri = pymongo.MongoClient()
        self.db = mongo_uri[database]


class Folders(Mongo):
    def __init__(self):
        super(Folders, self).__init__('LOCAL_FOLDERS')
        self.collection = self.db['LOCAL_FOLDERS']

    def insert_folder(self, folder):
        self.collection.insert_one(folder)

    def find_folder(self, folder_id):
        return self.collection.find_one({'_id': ObjectId(folder_id)})