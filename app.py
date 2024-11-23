from flask import Flask, render_template, Response, request, jsonify
import cv2
import cvzone
from cvzone.HandTrackingModule import HandDetector
from dbconnector import DatabaseOperations

app = Flask(__name__)

# Initialize video capture and hand detector
cap = cv2.VideoCapture(0)  # Change the index if needed
detector = HandDetector(detectionCon=0.9)

# Instantiate the DatabaseOperations class for MongoDB
databaseConnection = DatabaseOperations()

@app.route('/')
@app.route('/home')
def index():
    return render_template('homepage.html')

@app.route('/video_feed')
def video_feed():
    return Response(frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/add_question', methods=['POST'])
def add_question():
    data = request.get_json()  # Get the JSON data sent in the request
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

    # Insert the document into MongoDB using the insert_question method
    if databaseConnection.insert_question("demo", question_document):
        return jsonify({"message": "Question added successfully"}), 201
    else:
        return jsonify({"error": "Failed to add question"}), 500

def frames():
    class MCQ:
        def __init__(self, data):
            self.qNo = data.get("qNo")
            self.question = data.get("question")
            self.choice1 = data.get("choice1")
            self.choice2 = data.get("choice2")
            self.choice3 = data.get("choice3")
            self.choice4 = data.get("choice4")
            self.answer = int(data.get("answer"))
            self.userAns = None

        def update(self, cursor, bboxs):
            for x, bbox in enumerate(bboxs):
                x1, y1, x2, y2 = bbox
                if x1 < cursor[0] < x2 and y1 < cursor[1] < y2:
                    self.userAns = x + 1  # Update the user answer
                    cv2.rectangle(img, (x1, y1), (x2, y2), (255, 255, 255), cv2.FILLED)

    dataAll = databaseConnection.get_questions_from_database("demo")
    mcqList = [MCQ(q) for q in dataAll]
    qNo = 0
    qTotal = len(mcqList)

    while True:
        success, img = cap.read()  # Read a frame from the camera
        if not success or img is None:  # Check if the frame was captured successfully
            print("Error: Unable to capture video frame.")
            continue  # Skip to the next iteration if the frame is not captured

        img = cv2.flip(img, 1)
        new_width = 1200  # Adjust this value based on your preference
        new_height = 700
        img = cv2.resize(img, (new_width, new_height))

        hands, img = detector.findHands(img, flipType=False)

        if qNo < qTotal:
            mcq = mcqList[qNo]
            img, bbox = cvzone.putTextRect(img, mcq.question, [150, 100], 2, 2, offset=50, border=5)
            img, bbox1 = cvzone.putTextRect(img, mcq.choice1, [150, 300], 2, 2, offset=50, border=5)
            img, bbox2 = cvzone.putTextRect(img, mcq.choice2, [800, 300], 2, 2, offset=50, border=5)
            img, bbox3 = cvzone.putTextRect(img, mcq.choice3, [150, 600], 2, 4, offset=50, border=5)
            img, bbox4 = cvzone.putTextRect(img, mcq.choice4, [800, 600], 2, 2, offset=50, border=5)

            if hands:
                lmList = hands[0]['lmList']
                cursor = lmList[8]
                p1 = (lmList[8][0], lmList[8][1])
                p2 = (lmList[12][0], lmList[12][1])
                length, _, img = detector.findDistance(p1, p2, img)

                if length < 60:
                    mcq.update(cursor, [bbox1, bbox2, bbox3, bbox4])
                    if mcq.userAns is not None:  # Move to next question only if answered
                        qNo += 1  # Increment question number
                        cv2.waitKey(1000)  # Pause to allow users to see their answer

        else:
            score = sum(1 for mcq in mcqList if mcq.answer == mcq.userAns)
            score = round((score / qTotal) * 100, 2)
            img, _ = cvzone.putTextRect(img, "Quiz Completed", [250, 300], 2, 2, offset=50, border=5)
            img, _ = cvzone.putTextRect(img, f"Your Score: {score}%", [700, 300], 2, 2, offset=50, border=5)

        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        cv2.waitKey(1)

@app.teardown_appcontext
def close_camera(exception):
    if cap.isOpened():
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5475)
