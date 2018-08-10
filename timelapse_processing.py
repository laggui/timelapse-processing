import cv2
import numpy as np
from collections.abc import MutableSequence

def loadImage(path):
    return cv2.imread(path, 1)

def toRGB(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

def histMatch(sourceImage, expImage):
    '''
    Matches the histogram of expImage to sourceImage in order to fix lightness/exposure
    of the expImage.
    '''
    expImage = sourceImage
    return expImage

class Image:
    '''
    An Image object.
    '''
    def __init__(self, img):
        self.img = img
        self.lightness = self._getLightness()
    
    def _getLightness(self):
        lab = cv2.cvtColor(self.img, cv2.COLOR_BGR2LAB)
        l_channel,_,_ = cv2.split(lab)
        return int(np.mean(l_channel))

class ImageList(MutableSequence):
    '''
    A class that behaves like a list, containing the Image frames in the time-lapse animation,
    as well as statistics on the lightness of the images in the list such as the median and 
    median absolute deviation (mad). These stats are useful for processing.
    '''
    @staticmethod
    def __checkValue(value):
        if not isinstance(value, Image):
            raise TypeError('Invalid instance passed when trying to set item value.')
    
    def __init__(self):
        self._imgList = []
        self.lightMed = 0
        self.lightMad = 0
    
    def computeStats(self):
        lightness = np.array((img.lightness for img in self._imgList))
        self.lightMed = np.median(lightness)
        self.lightMad = np.median(abs(lightness - self.lightMed))
    
    def fixExposure(self):
        for i, img in enumerate(self._imgList):
            if (img.lightness < (self.lightMed - self.lightMad) or 
                img.lightness > (self.lightMed + self.lightMad)):
                self._imgList[i].img = histMatch(self._imgList[i-1].img, img)
    
    def __len__(self):
        return len(self._imgList)

    def __getitem__(self, index):
        return self._imgList[index]

    def __delitem__(self, index):
        del self._imgList[index]

    def __setitem__(self, index, value):
        self.__checkValue(value)
        self._imgList[index] = value
    
    def insert(self, index, value):
        self._imgList.insert(index, value)