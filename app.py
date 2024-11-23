from flask import Flask, render_template, Response, request, jsonify
from cvzone.HandTrackingModule import HandDetector
from dbconnector import DatabaseOperations

app = Flask(__name__)

# Instantiate the DatabaseOperations class for MongoDB
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

def frames():
    # This is where you would handle video frames if needed.
    # Implement this if server-side processing of video is required.
    pass  # Placeholder for now

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5475)
