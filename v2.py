import numpy as np
import time
import cv2
import os
import imutils
from playsound import playsound
import subprocess
from gtts import gTTS


 
LABELS = open("D:/Projects/object-detection-with-voice-feedback/object-detection-with-voice-feedback/coco.names").read().strip().split("\n")
with open("D:/Projects/object-detection-with-voice-feedback/object-detection-with-voice-feedback/coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]
colors = np.random.uniform(0, 255, size=(len(classes), 3))

# load our YOLO object detector trained on COCO dataset (80 classes)
print("[INFO] loading YOLO from disk...")
net = cv2.dnn.readNetFromDarknet("D:/Projects/object-detection-with-voice-feedback/object-detection-with-voice-feedback/yolov3.cfg", "D:/Projects/object-detection-with-voice-feedback/object-detection-with-voice-feedback/yolov3.weights")
font = cv2.FONT_HERSHEY_PLAIN

# determine only the *output* layer names that we need from YOLO
lane = net.getLayerNames()
lane = [lane[i - 1] for i in net.getUnconnectedOutLayers()]

# initialize
cap = cv2.VideoCapture(0)

frame_count = 0
start = time.time()
first = True
frames = []
flag=1
output_counter=1
while True:
	frame_count += 1
    # Capture frame-by-frame
	ret, frame = cap.read()
	cv2.imshow("Camera", frame)
	frames.append(frame)


	if cv2.waitKey(25) & 0xFF == ord('q'):
		break
	if ret:
		key = cv2.waitKey(1)
		if frame_count % 60 == 0:
			end = time.time()
			
			(H, W) = frame.shape[:2]
	
			blob = cv2.dnn.blobFromImage(frame, 1/ 255.0, (416, 416),
				swapRB=True, crop=False)
			net.setInput(blob)
			layerOutputs = net.forward(lane)

			
			boxes = []
			confidences = []
			classIDs = []
			centers = []

			# loop over each of the layer outputs
			for output in layerOutputs:
				# loop over each of the detections
				for detection in output:
					# extract the class ID and confidence (i.e., probability) of
					# the current object detection
					scores = detection[5:]
					classID = np.argmax(scores)
					confidence = scores[classID]

					# filter out weak predictions by ensuring the detected
					# probability is greater than the minimum probability
					if confidence > 0.5:
						# scale the bounding box coordinates back relative to the
						# size of the image, keeping in mind that YOLO actually
						# returns the center (x, y)-coordinates of the bounding
						# box followed by the boxes' width and height
						box = detection[0:4] * np.array([W, H, W, H])
						(centerX, centerY, width, height) = box.astype("int")

						# use the center (x, y)-coordinates to derive the top and
						# and left corner of the bounding box
						x = int(centerX - (width / 2))
						y = int(centerY - (height / 2))

						# update our list of bounding box coordinates, confidences,
						# and class IDs
						boxes.append([x, y, int(width), int(height)])
						confidences.append(float(confidence))
						classIDs.append(classID)
						centers.append((centerX, centerY))

			# apply non-maxima suppression to suppress weak, overlapping bounding
			# boxes
			idxs = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.3)

			for i in range(len(boxes)):
				if i in idxs:
					x, y, w, h = boxes[i]
					label = str(classes[classIDs[i]])
					confidence = confidences[i]
					color = colors[classIDs[i]]
					cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
					cv2.putText(frame, label + " " + str(round(confidence, 2)), (x, y + 30), font, 3, color, 3)


			texts = ["You have infront of you a:"]

			# ensure at least one detection exists
			if len(idxs) > 0:
				# loop over the indexes we are keeping
				for i in idxs.flatten():
					# find positions
					centerX, centerY = centers[i][0], centers[i][1]
					
					if centerX <= W/3:
						W_pos = "left "
					elif centerX <= (W/3 * 2):
						W_pos = "center "
					else:
						W_pos = "right "
					
					if centerY <= H/3:
						H_pos = "top "
					elif centerY <= (H/3 * 2):
						H_pos = "mid "
					else:
						H_pos = "bottom "

					texts.append(H_pos + W_pos + LABELS[classIDs[i]]+" "+"with confidence"+" "+str(confidences[i]))
					flag=0

			print(texts)
			
			if (flag==0):
				description = ', '.join(texts)
				output_filename = f"D:/Projects/Test{output_counter}.mp3"
				tts = gTTS(description, lang='en')
				tts.save(output_filename)
				playsound(output_filename)
				output_counter += 1
				

cap.release()
cv2.destroyAllWindows()
