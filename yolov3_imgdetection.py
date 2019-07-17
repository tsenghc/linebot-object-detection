import cv2
import numpy as np
import os


class yolo_detection:
    def __init__(self,  yolo_weight, yolo_classes,
                 yolo_config, inpWidth, inpHeight):

        self.yolo_weight = yolo_weight
        self.yolo_config = yolo_config
        self.yolo_classes = yolo_classes
        self.inpWidth = inpWidth  # Width of network's input image
        self.inpHeight = inpHeight

    def get_output_layers(net):

        layer_names = net.getLayerNames()

        output_layers = [layer_names[i[0] - 1]
                         for i in net.getUnconnectedOutLayers()]

        return output_layers

    def draw_prediction(img, classes, class_id, confidence,
                        x, y, x_plus_w, y_plus_h):

        label = str(classes[class_id])+str(round(confidence, 4))
        print(label)
        color = (255, 255, 255)

        cv2.rectangle(img, (x, y), (x_plus_w, y_plus_h), color, 2)

        cv2.putText(img, label, (x-5, y-10),
                    cv2.FONT_HERSHEY_DUPLEX, 0.8, color, 1)

    def detector(self, img, display, outputfile):

        image = cv2.imread(img)

        Width = image.shape[1]
        Height = image.shape[0]
        scale = 1/255

        classes = None

        with open(self.yolo_classes, 'r') as f:
            classes = [line.strip() for line in f.readlines()]

        net = cv2.dnn.readNet(self.yolo_weight, self.yolo_config)

        blob = cv2.dnn.blobFromImage(
            image, scale, (self.inpWidth, self.inpHeight),
            (0, 0, 0), True, crop=False)

        net.setInput(blob)

        outs = net.forward(yolo_detection.get_output_layers(net))

        class_ids = []
        confidences = []
        boxes = []
        conf_threshold = 0.5
        nms_threshold = 0.4

        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.25:
                    center_x = int(detection[0] * Width)
                    center_y = int(detection[1] * Height)
                    w = int(detection[2] * Width)
                    h = int(detection[3] * Height)
                    x = center_x - w / 2
                    y = center_y - h / 2
                    class_ids.append(class_id)
                    confidences.append(float(confidence))
                    boxes.append([x, y, w, h])

        indices = cv2.dnn.NMSBoxes(
            boxes, confidences, conf_threshold, nms_threshold)

        for i in indices:
            i = i[0]
            box = boxes[i]
            x = box[0]
            y = box[1]
            w = box[2]
            h = box[3]
            yolo_detection.draw_prediction(image, classes, class_ids[i],
                                           confidences[i],
                                           round(x), round(y), round(x+w),
                                           round(y+h))
        if display:
            cv2.imshow("object detection", image)
            cv2.waitKey(2000)
        elif outputfile:
            filename = os.path.splitext(img)[0]
            cv2.imwrite(filename+"_yolo.jpeg", image)


if __name__ == '__main__':

    yolo_weight = 'yolov3/yolov3.weights'
    yolo_classes = 'yolov3/coco.names'
    yolo_config = 'yolov3/yolov3.cfg'
    inpHeight = 416
    inpWidth = 416
    yolov3 = yolo_detection(yolo_weight,
                            yolo_classes,
                            yolo_config,
                            inpWidth,
                            inpHeight)
    yolov3.detector('people.jpg', False, True)
