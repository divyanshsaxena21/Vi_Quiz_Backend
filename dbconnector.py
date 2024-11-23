from pymongo import MongoClient

class DatabaseOperations:
    def __init__(self, uri="mongodb+srv://admin:kanpur@cluster0.9ltj5c6.mongodb.net/", database_name="project"):
        # Connect to MongoDB
        self.client = MongoClient(uri)
        self.database = self.client[database_name]
        

    def get_questions_from_database(self, collection_name):
        # Retrieve all documents from the specified collection
        collection = self.database[collection_name]
        myresult = list(collection.find({}))  # Fetch all documents
        return myresult

    def insert_question(self, collection_name, question_document):
        # Insert a new question document into the specified collection
        collection = self.database[collection_name]
        try:
            collection.insert_one(question_document)
            return True
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    def close_connection(self):
        # Close the MongoDB connection
        self.client.close()

# Usage example
# database_connection = DatabaseOperations()
# data_all = database_connection.get_questions_from_database("demo")
