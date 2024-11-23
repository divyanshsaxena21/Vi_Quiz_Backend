import os
import pymongo
import cv2
import numpy as np
from flask import Flask, render_template, Response, request, jsonify
from cvzone.HandTrackingModule import HandDetector
from dotenv import load_dotenv  # Optional, for loading environment variables in development
from dbconnector import DatabaseOperations

# Load environment variables from .env file (if present)
load_dotenv()

app = Flask(__name__)

# Instantiate the DatabaseOperations class for MongoDB
databaseConnection = DatabaseOperations()
detector = HandDetector(detectionCon=0.9)

current_question_index = 0
questions = []

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
    global questions
    try:
        questions = databaseConnection.get_questions_from_database("demo")
        return jsonify(questions), 200
    except Exception as e:
        print("Error fetching questions:", e)
        return jsonify({"error": "Failed to fetch questions"}), 500

def frames():
    global current_question_index
    cap = cv2.VideoCapture(0)  # Open the webcam

    while True:
        success, frame = cap.read()
        if not success:
            break

        # Flip the frame horizontally for a selfie-view effect
        frame = cv2.flip(frame, 1)

        if questions and current_question_index < len(questions):
            question = questions[current_question_index]
            text = question["question"]
            choices = [
                question["choice1"],
                question["choice2"],
                question["choice3"],
                question["choice4"]
            ]
            
            # Draw question text
            cv2.putText(frame, text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            # Draw choices
            for i, choice in enumerate(choices):
                choice_text = f"{i + 1}. {choice}"
                cv2.putText(frame, choice_text, (50, 100 + i * 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # Hand detection and answer selection logic
        hands, frame = detector.findHands(frame)  # Find hands in the frame
        if hands:  # If hands are detected
            hand = hands[0]  # Get the first hand
            x, y, w, h = hand['bbox']  # Get the bounding box of the hand

            # Check if the hand is hovering over any of the choices
            for i in range(len(choices)):
                if 100 + i * 40 < y < 100 + i * 40 + 40:  # Check if hand is over the choice
                    cv2.rectangle(frame, (50, 100 + i * 40), (400, 140 + i * 40), (0, 255, 0), 2)  # Highlight choice
                    if hand['lmList'][8][1] < 200:  # If index finger is up (or you can set another condition)
                        current_question_index += 1
                        if current_question_index >= len(questions):  # Reset to zero if the quiz is complete
                            current_question_index = 0
                        break

        # Show the frame
        cv2.imshow('Video Feed', frame)

        # Press 'q' to quit the window
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Default to 5000 if PORT is not set
    app.run(host='0.0.0.0', port=port)
