import cv2
import numpy as np
from collections.abc import MutableSequence

def loadImage(path):
    return cv2.imread(path, 1)

def toRGB(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

def histMatch(sourceImage, templateImage):
    '''
    Matches the histogram of sourceImage to the templateImage in order to fix lightness/exposure
    of the sourceImage.
    '''
    if sourceImage.ndim > 2:
        # Convert to LAB color space to work on lightness channel
        sourceLab = cv2.cvtColor(sourceImage, cv2.COLOR_BGR2LAB)
        sourceL,sourceA,sourceB = cv2.split(sourceLab)
        tempLab = cv2.cvtColor(templateImage, cv2.COLOR_BGR2LAB)
        tempL,_,_ = cv2.split(tempLab)

        # Get histogram of lightness channel for images
        sVal, binIdx, sCounts = np.unique(sourceL.ravel(), return_inverse=True, return_counts=True)
        scdf = np.cumsum(sCounts).astype(np.float64) # cumulative distribution function
        scdf /= scdf[-1] # normalize

        tVal, tCounts = np.unique(tempL.ravel(), return_counts=True)
        tcdf = np.cumsum(tCounts).astype(np.float64) # cumulative distribution function
        tcdf /= tcdf[-1] # normalize

        # Use linear interpolation of cdf to map new pixel values
        matched = np.rint(np.interp(scdf, tcdf, tVal)).astype(np.uint8)
        sourceL = matched[binIdx].reshape(sourceL.shape)
        matchedImage = cv2.merge([sourceL, sourceA, sourceB])
        matchedImage = cv2.cvtColor(matchedImage.astype(np.uint8), cv2.COLOR_LAB2BGR)
    elif sourceImage.ndim == 1:
        # Get histogram of gray images
        sVal, binIdx, sCounts = np.unique(sourceImage.ravel(), return_inverse=True, return_counts=True)
        scdf = np.cumsum(sCounts).astype(np.float64) # cumulative distribution function
        scdf /= scdf[-1] # normalize

        tVal, tCounts = np.unique(templateImage.ravel(), return_counts=True)
        tcdf = np.cumsum(tCounts).astype(np.float64) # cumulative distribution function
        tcdf /= tcdf[-1] # normalize

        # Use linear interpolation of cdf to map new pixel values
        matched = np.rint(np.interp(scdf, tcdf, tVal)).astype(np.uint8)
        matchedImage = matched[binIdx].reshape(sourceImage.shape)
    return matchedImage

class Image:
    '''
    An Image object.
    '''
    def __init__(self, img):
        self.img = img
        self.lightness = self._getLightness()
    
    def _getLightness(self):
        lab = cv2.cvtColor(self.img, cv2.COLOR_BGR2LAB)
        lightness,_,_ = cv2.split(lab)
        return int(np.mean(lightness))

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
    
    def __init__(self, images=[]):
        self._imgList = images
        self.lightMed = 0
        self.lightMad = 0
    
    def computeStats(self):
        lightness = np.array([img.lightness for img in self._imgList])
        self.lightMed = np.median(lightness)
        self.lightMad = np.median(abs(lightness - self.lightMed))
    
    def fixExposure(self):
        temp = next(obj for obj in self._imgList if obj.lightness==self.lightMed)
        for i, obj in enumerate(self._imgList):
            if (obj.lightness < (self.lightMed - self.lightMad) or 
                obj.lightness > (self.lightMed + self.lightMad)):
                fixed = histMatch(obj.img, temp.img)
                self._imgList[i] = Image(fixed)
    
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