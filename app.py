import os
import pymongo
from flask import Flask, render_template, Response, request, jsonify
from cvzone.HandTrackingModule import HandDetector
from dotenv import load_dotenv  # Optional, for loading environment variables in development
from dbconnector import DatabaseOperations
# Load environment variables from .env file (if present)
load_dotenv()

app = Flask(__name__)

# Instantiate the DatabaseOperations class for MongoDB
# class DatabaseOperations:
#     def __init__(self):
#         # Use the environment variable for MongoDB connection
#         self.client = pymongo.MongoClient(os.environ.get("MONGODB_URI"))
#         self.db = self.client['viquiz']  # Database name
#         self.collection = self.db['questions']  # Collection name

#     def insert_question(self, collection_name, document):
#         try:
#             self.db[collection_name].insert_one(document)
#             return True
#         except Exception as e:
#             print("Error inserting question:", e)
#             return False

#     def get_questions_from_database(self, collection_name):
#         return list(self.db[collection_name].find())

databaseConnection = DatabaseOperations()
detector = HandDetector(detectionCon=0.9)

@app.route('/')
@app.route('/home')
def index():
    return render_template('homepage.html')

@app.route('/video_feed')
def video_feed():
    return Response(frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/add_question', methods=['POST'])
def add_question():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Prepare the document to be inserted
    question_document = {
        "qNo": data.get("qNo"),
        "question": data.get("question"),
        "choice1": data.get("choice1"),
        "choice2": data.get("choice2"),
        "choice3": data.get("choice3"),
        "choice4": data.get("choice4"),
        "answer": data.get("answer")
    }

    # Insert the document into MongoDB
    if databaseConnection.insert_question("demo", question_document):
        return jsonify({"message": "Question added successfully"}), 201
    else:
        return jsonify({"error": "Failed to add question"}), 500

@app.route('/get_questions', methods=['GET'])
def get_questions():
    try:
        questions = databaseConnection.get_questions_from_database("demo")
        return jsonify(questions), 200
    except Exception as e:
        print("Error fetching questions:", e)
        return jsonify({"error": "Failed to fetch questions"}), 500

def frames():
    # This is where you would handle video frames if needed.
    # Implement this if server-side processing of video is required.
    pass  # Placeholder for now

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Default to 5000 if PORT is not set
    app.run(host='0.0.0.0', port=port)
