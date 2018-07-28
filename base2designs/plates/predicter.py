
import cv2
import numpy as np
class Predicter():

  def __init__(self, model, sess, categoryIdx):
    self.model = model
    self.sess = sess
    self.categoryIdx = categoryIdx
    self.imageTensor = model.get_tensor_by_name("image_tensor:0")
    self.boxesTensor = model.get_tensor_by_name("detection_boxes:0")
    self.scoresTensor = model.get_tensor_by_name("detection_scores:0")
    self.classesTensor = model.get_tensor_by_name("detection_classes:0")
    self.numDetections = model.get_tensor_by_name("num_detections:0")

  def genSquareImage(self,image):
    # separate the channels
    blue = image[..., 0]
    green = image[..., 1]
    red = image[..., 2]

    # find the average pixel value for each channel
    blueAv = np.sum(blue) / blue.size
    greenAv = np.sum(green) / green.size
    redAv = np.sum(red) / red.size

    # create a square matrix large enough to fit the largest dimension of the input image, and fill with average pixels
    # save the scaling factors for H and W
    dimMax = max(image.shape[0], image.shape[1])
    hScale = dimMax / image.shape[0]
    wScale = dimMax / image.shape[1]
    imageOut = np.empty((dimMax, dimMax, 3), dtype=np.uint8)
    imageOut[..., 0] = np.uint8(blueAv)
    imageOut[..., 1] = np.uint8(greenAv)
    imageOut[..., 2] = np.uint8(redAv)

    # copy the input image to the new square image
    if image.shape[0] <= image.shape[1]:
      imageOut[0:image.shape[0], ...] = image
    else:
      imageOut[:, 0:image.shape[1], ...] = image

    return imageOut, hScale, wScale

  def predictChars(self, image, plateBox, minConfidence, image_display=False):
    # crop plate from the image, and predict chars
    H, W = image.shape[:2]
    (pbStartY, pbStartX, pbEndY, pbEndX) = (int(plateBox[0] * H),
                                            int(plateBox[1] * W),
                                            int(plateBox[2] * H),
                                            int(plateBox[3] * W))
    plateImage = image[pbStartY: pbEndY, pbStartX: pbEndX, ...]
    plateImage, hScale, wScale = self.genSquareImage(plateImage)
    pbHeight, pbWidth = plateImage.shape[:2]
    if image_display == True:
      cv2.imshow("Plate Image", plateImage)
      cv2.waitKey(0)
    image_tf = cv2.cvtColor(plateImage.copy(), cv2.COLOR_BGR2RGB)
    image_tf = np.expand_dims(image_tf, axis=0)

    (boxes, scores, labels, N) = self.sess.run(
      [self.boxesTensor, self.scoresTensor, self.classesTensor, self.numDetections],
      feed_dict={self.imageTensor: image_tf})
    # squeeze the lists into a single dimension
    boxes = np.squeeze(boxes)
    scores = np.squeeze(scores)
    labels = np.squeeze(labels)

    return boxes, scores, labels, pbHeight, pbWidth, pbStartX, pbStartY

  def predictPlates(self, image):

    # prepare the image for inference input
    image_tf = cv2.cvtColor(image.copy(), cv2.COLOR_BGR2RGB)
    image_tf = np.expand_dims(image_tf, axis=0)

    # perform inference and compute the bounding boxes,
    # probabilities, and class labels
    (boxes, scores, labels, N) = self.sess.run(
      [self.boxesTensor, self.scoresTensor, self.classesTensor, self.numDetections],
      feed_dict={self.imageTensor: image_tf})

    # squeeze the lists into a single dimension
    boxes = np.squeeze(boxes)
    scores = np.squeeze(scores)
    labels = np.squeeze(labels)

    return boxes, scores, labels