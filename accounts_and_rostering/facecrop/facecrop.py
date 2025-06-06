# Based loosely off this and others: https://github.com/shantnu/FaceDetect/blob/master/face_detect.py
# More about OpenCV and face detection: https://realpython.com/face-recognition-with-python/

# Install OpenCV for the platform you're on
# MacOS: brew install opencv
import sys
import os, re
#sys.path.append('/usr/local/lib/python2.7/site-packages')
#sys.path.append('/usr/local/lib/python2.7/site-packages')
sys.path.append('/usr/local/lib/python3.13/site-packages')

import cv2
import glob

cascPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "haarcascade_frontalface_default.xml")
# cascPath = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml") #This should work as well based off of https://pypi.org/project/opencv-python/

print("cascPath is: " + cascPath)

# Create the haar cascade
faceCascade = cv2.CascadeClassifier(cascPath)

files = glob.glob("*.JPG") # This is case sensitive, change to .jpg or .JPG if nothing is happening.
files = files + glob.glob("*.jpg")
print(files)
for file in files:

    # Read the image
    image = cv2.imread(file)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Detect faces in the image
    faces = faceCascade.detectMultiScale(
        gray,
        scaleFactor=1.2, # modified from 1.1 # had 1.3 before
        minNeighbors=5, # originally 5
        minSize=(30, 30), # originally 30, 30
        #flags = cv2.cv.CV_HAAR_SCALE_IMAGE
        flags = cv2.CASCADE_SCALE_IMAGE
    )

    print("Found {0} faces!".format(len(faces)))
    print("in file " + file)

    croppadding = 300
    # Crop Padding
    left = croppadding # originally 100, adjust based on the original size of the pictures, been using 250 with some success
    right = croppadding # originally 100
    top = croppadding # originally 100
    bottom = croppadding # originally 100

    # Draw a rectangle around the faces
    for (x, y, w, h) in faces:
        print(x, y, w, h)

        # Dubugging boxes, if needed
        # cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)

    # Added below two lines for debugging purposes
    #cv2.imshow("Faces found", image)
    #cv2.waitKey() # nrmally cv2.waitKey(250)

    if (y-top) <= 0:
        ytop = 0
    else:
        ytop = y - top

    image = image[ytop:y+h+bottom, x-left:x+w+right] # was image = image[y-top:y+h+bottom, x-left:x+w+right]

    #cv2.imshow("croppedimage", image)
    #cv2.waitKey()  # nrmally cv2.waitKey(250)

    print("cropped_{1}{0}".format(str(file),str(x)))
    try:
        cv2.imwrite("cropped_{1}_{0}".format(str(file),str(x)), image)
    except:
        print("writing image broke. Might be zero size.")

for filename in os.listdir("."):
    if not os.path.exists(os.path.join(os.getcwd(), "cropped")):
        os.makedirs(os.path.join(os.getcwd(), "cropped"))
    if filename.startswith("cropped_") and os.stat(filename).st_size > 0:
        try:
            new_name = os.path.join("cropped", re.sub(r'cropped_[0-9]*_', '', filename))
            #Below will actually rename the file
            os.rename(filename, new_name)
            print("Renamed " + filename + " to " + new_name)

            # Resize
            img = cv2.imread(new_name)
            print(new_name)

            height, width = img.shape[:2]
            max_height = 500
            max_width = 500

            # only shrink if img is bigger than required
            if max_height < height or max_width < width:
                # get scaling factor
                scaling_factor = max_height / float(height)
                if max_width / float(width) < scaling_factor:
                    scaling_factor = max_width / float(width)
                # resize image
                img = cv2.resize(img, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_AREA)
                cv2.imwrite(new_name, img) # actually do the resize

            cv2.imshow("Cropped and resized image", img)
            key = cv2.waitKey(250)
        except:
            print("Exception occurred. Go back and work on this picture manually.")