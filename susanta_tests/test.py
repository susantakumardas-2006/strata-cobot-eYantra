import cv2 as cv
import numpy as np

img = cv.imread('/home/shreemanta/eYRC_26-27_Strata-Cobot/left0000.jpg')

if img is None:
    print("Error: Could not read image. Verify the file path.")
    exit()

hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)



lower_red = np.array([9, 175, 130])  
upper_red = np.array([10, 255, 255]) #eta perfect ache

# Red masking
r_mask = cv.inRange(hsv, lower_red, upper_red)

#morphological cleaning
mat = np.ones((2, 2), dtype=np.uint8) #eta holo kernal
mask_opened = cv.morphologyEx(r_mask, cv.MORPH_OPEN, mat) #eta opening operation
mask_cleaned = cv.morphologyEx(mask_opened, cv.MORPH_CLOSE, mat) #eta closing operation



cv.imshow('image', img)
#cv.imshow('Red mask', r_mask)
cv.imshow('Opened mask', mask_opened)
cv.imshow('Cleaned mask', mask_cleaned)
cv.waitKey(0)
cv.destroyAllWindows()
