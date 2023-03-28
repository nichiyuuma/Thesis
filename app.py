from flask import Flask, request,jsonify
from detect import inference

app = Flask(__name__)




print ("hello")
inference()


@app.route('/')
def hello():
    return 'Hello, World!'

# @app.route('/video_feed')
# def detect_image():    
    
    
    # detect = Detect()


    # detect.config('weights/v5lite-s.pt', 'ref/50.jpg', 0, True, False)

    # detect.detect()

    # person, plabel = detect.width_in_rf, detect.label

    # detect.config('weights/v5lite-s.pt', 'ref/dog50.jpg', 17, True, False)

    # detect.detect()

    # phone, phLabel = detect.width_in_rf, detect.label

    # print(f'{plabel}: {person} | {phLabel}: {phone}')

    # focal_person = detect.focalLength(person)
    # focal_phone = detect.focalLength(phone)

    # print(f'focal length of person: {focal_person} | focal length of phone: {focal_phone}')

    # detect.config('weights/v5lite-c.pt', 'ref/dog50.jpg', None, False, False)

    # detect.detect()

    # return results

@app.route('/api/haptics/right', methods=['GET'])
def haptics_right():
    active = request.args.get('right', type=str).lower() == 'true'
    return jsonify({"right": active})


@app.route('/api/haptics/left', methods=['GET'])
def haptics_left():
    active = request.args.get('left', type=str).lower() == 'true'
    return jsonify({"left": active})

@app.route('/api/haptics', methods=['GET'])
def haptics():
    right_active = request.args.get('right', type=str).lower() == 'true'
    left_active = request.args.get('left', type=str).lower() == 'true'

    response = {
        "right_active": right_active,
        "left_active": left_active
    }

    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True) 
