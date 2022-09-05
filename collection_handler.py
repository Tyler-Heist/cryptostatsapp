from pymongo import MongoClient


# class used for MongoDB CRUD functionality
class Handler:
    def __init__(self):
        # FIXME: Add authentication
        # init connect to mongodb without authentication
        self.client = MongoClient('mongodb://localhost:27017/')
        # defines database to be used
        self.database = self.client['BTC']

    # inserts document into database
    def create(self, collection, data):
        if data:
            if collection == 'Price':
                insert = self.database.Price.insert_one(data)
            elif collection == 'Stats':
                insert = self.database.Stats.insert_one(data)
            else:
                raise Exception("'Collection' must be defined")
            if insert:
                # return True if document creation is successful, False if not
                return True
            else:
                return False
        else:
            raise Exception("Nothing to save, because data parameter is empty")

    # reads a document from database
    def read(self, collection, data):
        if data:
            if collection == 'Price':
                cursor = self.database.Price.find(data, {'_id': False})
            elif collection == 'Stats':
                cursor = self.database.Stats.find(data, {'_id': False})
            else:
                raise Exception("'Collection' must be defined")
            # return a cursor (pointer) to a list of results (Documents)
            return cursor
        else:
            raise Exception("Nothing to read, because data parameter is empty")

    # reads all documents in collection
    def read_all(self, collection, data):
        if collection == 'Price':
            cursor = self.database.Price.find(data, {'_id': False})
        elif collection == 'Stats':
            cursor = self.database.Stats.find(data, {'_id': False})
        else:
            raise Exception("'Collection' must be defined")
        return cursor

    # updates a document in a collection
    def update(self, collection, search_data, update_data):
        if search_data and update_data:
            if collection == 'Price':
                updater = self.database.Price.update_one(search_data, {"$set": update_data})
            elif collection == 'Stats':
                updater = self.database.Stats.update_one(search_data, {"$set": update_data})
            else:
                raise Exception("'Collection' must be defined")
            # return result of update command so user knows if it was successful or not
            return updater
        else:
            raise Exception("One or more data fields is missing, try again")

    # deletes a document in a collection
    def delete(self, collection, data):
        if data:
            if collection == 'Price':
                deleter = self.database.Price.delete_one(data)
            elif collection == 'Stats':
                deleter = self.database.Stats.delete_one(data)
            else:
                raise Exception("'Collection' must be defined")
            # return result of delete command so user knows if it was successful or not
            return deleter
        else:
            raise Exception("Nothing to delete, because data parameter is empty")

    # returns the number of documents in a given collection
    def count(self, collection):
        if collection == 'Price':
            return self.database.Price.count_documents({})
        elif collection == 'Stats':
            return self.database.Stats.count_documents({})
        else:
            raise Exception("'Collection' must be defined")
