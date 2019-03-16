import numpy as np
import matplotlib.pyplot as plt
import scipy.misc
import matplotlib as mpl

########## Required for Clean Printing ###########
from pprint import pprint

########## Required for Parallel Processing ###########

from MCAIncludes import *
from joblib import Parallel, delayed
import multiprocessing
import time

import copy


########## Require for Tree Expansion ###################

def GenerateImageVariations_Minima(image):
    ######### Global Variables ###########################

    NEIGHBORS = np.array([[0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0], [-1, +1]])

    # Test Image

    # image = misc.face(gray=True)
    # image = misc.imresize(image,(64,64))
    TotalParallelExecutionTime = 0

    # image= np.array([[20,27,24,26],[16,23,30,32],[22,22,20,19],[22,10,35,19]])
    # print(type(image))
    # print(image.shape)

    ############ Calculating LBP of the Image ####################
    start_time = time.time()
    # -- Takes a numpy array and append rows and columns, i.e new image is of dimensions [m+2,n+2]
    iData = LoadImage(image)
    row = iData[0]
    col = iData[1]
    cImage = iData[2]
    print(cImage.shape)
    # -- calculates LBP for each of the pixel in the image
    # -- Following data structure
    # -- [i,j,pixelval,lbpval,[constraintval]] where constraint value are can be 0 (equal), 1 (greater), and -1 (smaller)
    PixelLBP = [calculateLBP(i, j, NEIGHBORS, cImage) for i, j in np.ndindex(cImage.shape) if
                i > 0 and i < row - 1 and j > 0 and j < col - 1]
    # print("For Serial Execution,LBP Procedure took--- %s seconds ---" % (time.time() - start_time))
    TotalParallelExecutionTime = TotalParallelExecutionTime + ((time.time() - start_time))
    pprint(PixelLBP)

    ####################### Boiler Plate for Plateau, Minima, and Maxima Extraction ###############
    start_time = time.time()
    # -- create a data structure to maintain the plateaus in the image
    # -- key : (i,j) - pixel index
    # -- value : [(i1,j1),..,(in,jn)] - List of co-ordinates in the image
    platoDict = getConstNeigh(PixelLBP, NEIGHBORS, row, col, 0)
    MinimaRefereces = getConstNeigh(PixelLBP, NEIGHBORS, row, col, 1)
    MaximaRefereces = getConstNeigh(PixelLBP, NEIGHBORS, row, col, -1)
    pprint(platoDict)
    pprint(MinimaRefereces)
    pprint(MaximaRefereces)

    conMatplateaus = {}
    for pixel in PixelLBP:
        conMatplateaus[(pixel[0] - 1, pixel[1] - 1)] = pixel[4]
    pprint(conMatplateaus)

    TotalParallelExecutionTime = TotalParallelExecutionTime + ((time.time() - start_time))

    ####################### Code for Plateau, Minima, and Maxima Extraction ###############
    start_time = time.time()
    pData = ExtractPlateau(image, platoDict, conMatplateaus)
    plateuPixel = pData[0]
    plateutree = pData[1]
    PointIndex = pData[2]
    minima = pData[3]
    maxima = pData[4]
    plateutreeVal = pData[5]

    pprint(plateuPixel)
    pprint(plateutree)
    pprint(PointIndex)
    pprint(minima)
    pprint(maxima)
    pprint(plateutreeVal)

    TotalParallelExecutionTime = TotalParallelExecutionTime + ((time.time() - start_time))

    ####################### Code for Tree Expansion - Minima ###############

    num_cores = multiprocessing.cpu_count()

    # print(num_cores, " cores are availble for execution")

    start_time = time.time()
    minForest_Parallel = Parallel(n_jobs=-1, backend="multiprocessing", batch_size=num_cores, pre_dispatch='1.5*n_jobs',
                                  verbose=5) \
        (delayed(expandTree_Minima)(minima[i], MinimaRefereces, plateutree, PointIndex) for i in range(0, len(minima)))

    TotalParallelExecutionTime = TotalParallelExecutionTime + ((time.time() - start_time))
    pprint(minForest_Parallel)

    #################### Code for Image Generation _L1 #################
    start_time = time.time()

    PassImages_L1 = CreateImageFromTree_Minima(minForest_Parallel, row, col, plateutree)
    pass1_Image_Minima = PassImages_L1[0]
    pass1_LevelImage_Minima = PassImages_L1[1]

    pprint(pass1_Image_Minima)
    pprint(pass1_LevelImage_Minima)

    TotalParallelExecutionTime = TotalParallelExecutionTime + ((time.time() - start_time))

    ###########  Add Code for Updating the root of the tree #############
    ## After max assignmet
    ## for each tree determine the max value and tree number
    ## take difference of max value with depth and update tree root.
    ## Fill the tree with the new root value and update the tree.
    minForest_L2_Parallel = []
    minForest_L3_Parallel = []
    minForest_L4_Parallel = []
    for index, minTree in enumerate(minForest_Parallel):
        maxDepth = []
        maxDepthNodeID = []
        rootNodeID = -1
        for key in minTree.keys():
            maxDepth.append(minTree[key][0][1])
            maxDepthNodeID.append(minTree[key][0][0])
            if minTree[key][0][0] == 0:
                rootNodeID = key

        # for rootNodeID go into the original image and fetch the actual value of the local minima
        # and set it to maxTree[rootNodeID][0][1] and pass it to update tree depth to generate the image, the one
        # with root node initialzed to actual value of the minima.
        pprint(minTree)
        pprint(rootNodeID)
        stepSize = 1

        # We are taking the max value because at the depth of the true will be a value equal to depth Since we initialize the root with 0 and increment with +1 at each step
        rootValueFromTreeDepth = max(maxDepth)

        # We take the node ID of the Pixel at the Depth of the tree and get it's subsequent index in the imaege and use the value from pass 1 images, this will be minima value
        # influenced from the global constraints
        treeDepth_Ind = np.argmax(maxDepth)
        treeDepthNodeID = maxDepthNodeID[treeDepth_Ind]
        rootValueFromPass1Image = pass1_Image_Minima[plateutree[treeDepthNodeID][0]]

        # we take the root node id and take it's subsequent index in the image and use the value from original image
        minimaActualValue = plateutreeVal[rootNodeID]


        minTree_L2 = copy.deepcopy(minTree)
        minTree_L3 = copy.deepcopy(minTree)
        minTree_L4 = copy.deepcopy(minTree)

        # Initializing the tree root with the Max Depth Value
        minTree_L2[rootNodeID][0][1] = rootValueFromTreeDepth
        minTree_L2 = UpdateTreeDepth_Minima(rootNodeID, minTree_L2)
        minForest_L2_Parallel.append(minTree_L2)

        # Initializing the tree root with the Value Derived from Global Constraints
        minTree_L3[rootNodeID][0][1] = rootValueFromPass1Image
        minTree_L3 = UpdateTreeDepth_Minima(rootNodeID, minTree_L3)
        minForest_L3_Parallel.append(minTree_L3)

        # Initializing the tree root with the Actual Value of Minima
        minTree_L4[rootNodeID][0][1] = minimaActualValue
        minTree_L4 = UpdateTreeDepth_Minima(rootNodeID, minTree_L4, stepSize)
        minForest_L4_Parallel.append(minTree_L4)

    #################### Code for Image Generation _L2 #################
    start_time = time.time()

    PassImages_L2 = CreateImageFromTree_Minima(minForest_L2_Parallel, row, col, plateutree)
    pass2_Image_Minima = PassImages_L2[0]
    pass2_LevelImage_Minima = PassImages_L2[1]

    pprint(pass2_Image_Minima)
    pprint(pass2_LevelImage_Minima)

    PassImages_L3 = CreateImageFromTree_Minima(minForest_L3_Parallel, row, col, plateutree)
    pass3_Image_Minima = PassImages_L3[0]
    pass3_LevelImage_Minima = PassImages_L3[1]

    pprint(pass3_Image_Minima)
    pprint(pass3_LevelImage_Minima)

    PassImages_L4 = CreateImageFromTree_Minima(minForest_L4_Parallel, row, col, plateutree)
    pass4_Image_Minima = PassImages_L4[0]
    pass4_LevelImage_Minima = PassImages_L4[1]

    pprint(pass4_Image_Minima)
    pprint(pass4_LevelImage_Minima)

    TotalParallelExecutionTime = TotalParallelExecutionTime + ((time.time() - start_time))

    #################### Compare if the generated image and the orignal image are same - L1 #################
    start_time = time.time()

    originalLBP = GenerateLBPImage(image, NEIGHBORS)
    pass1LBP = GenerateLBPImage(pass1_Image_Minima, NEIGHBORS)

    if ((originalLBP == pass1LBP).all()):
        print("Success L1 generated")
    else:
        print("Failure L1 generated")

    TotalParallelExecutionTime = TotalParallelExecutionTime + (time.time() - start_time)

    #################### Compare if the generated image and the orignal image are same - L2 #################
    start_time = time.time()

    originalLBP = GenerateLBPImage(image, NEIGHBORS)
    pass2LBP = GenerateLBPImage(pass2_Image_Minima, NEIGHBORS)

    if ((originalLBP == pass2LBP).all()):
        print("Success L2 generated")
    else:
        print("Failure L2 generated")


    return [pass1_Image_Minima, pass2_Image_Minima, pass3_Image_Minima, pass4_Image_Minima]



image = np.array([[20, 27, 24, 26], [16, 23, 30, 32], [22, 22, 20, 19], [22, 10, 35, 19]])
print(type(image))
print(image.shape)
print(image)

lena = scipy.misc.imread('lena.png', mode='F')
image = scipy.misc.imresize(lena, (64, 64))

ImgLst = GenerateImageVariations_Minima(image)

pass1_Image_Minima=ImgLst[0]
pass2_Image_Minima=ImgLst[1]
pass3_Image_Minima=ImgLst[2]
pass4_Image_Minima=ImgLst[3]

imageLabel = 1

print("Image Label is : " + str(imageLabel))
plt.figure(1)
plt.title("Image Label is : " + str(imageLabel))

ax = plt.subplot(231)
ax.set_title("Original Image", fontsize=7)
ax.set_axis_off()
ax.imshow(image, cmap=mpl.cm.gray)

ax = plt.subplot(232)
ax.set_title("Minima Initialized with 0", fontsize=7)
ax.set_axis_off()
ax.imshow(pass1_Image_Minima, cmap=mpl.cm.gray)

ax = plt.subplot(233)
ax.set_title("Minima Initialized with Tree Depth", fontsize=7)
ax.set_axis_off()
ax.imshow(pass2_Image_Minima, cmap=mpl.cm.gray)

ax = plt.subplot(234)
ax.set_title("Minima Initialized with Value Derived from Global Constraints", fontsize=7)
ax.set_axis_off()
ax.imshow(pass3_Image_Minima, cmap=mpl.cm.gray)

ax = plt.subplot(235)
ax.set_title("Minima Initialized with Priors", fontsize=7)
ax.set_axis_off()
ax.imshow(pass4_Image_Minima, cmap=mpl.cm.gray)


plt.show()