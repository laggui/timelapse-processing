import cv2
import numpy as np
from collections.abc import MutableSequence

def loadImage(path):
    return cv2.imread(path, 1)

class Image:
    '''
    An Image object.
    '''
    def __init__(self, img):
        self.img = img
        self.lightness = self._getLightness()
    
    def _getLightness(self):
        lab_img = cv2.cvtColor(self.img, cv2.COLOR_BGR2LAB)
        l_channel,_,_ = cv2.split(lab_img)
        return int(np.mean(l_channel))

class ImageList(MutableSequence):
    '''
    A class that behaves like a list, containing the Image frames in the time-lapse animation,
    as well as statistics on the lightness of the images in the list such as the median and 
    median absolute deviation (mad). These stats are useful for processing.
    '''
    def __init__(self):
        self._imglist = []
        self.lightMed = 0
        self.lightMad = 0
    
    def computeStats(self):
        lightness = np.array((img.lightness for img in self._imglist))
        self.lightMed = np.median(lightness)
        self.lightMad = np.median(abs(lightness - self.lightMed))
    
    def __checkValue(value):
        if not isinstance(value, Image):
            raise TypeError()
    
    def __len__(self):
        return len(self._imglist)

    def __getitem__(self, index):
        return self._imglist[index]

    def __delitem__(self, index):
        del self._imglist[index]

    def __setitem__(self, index, value):
        self.__checkValue(value)
        self._imglist[index] = value
    
    def insert(self, index, value):
        self._imglist.insert(index, value)