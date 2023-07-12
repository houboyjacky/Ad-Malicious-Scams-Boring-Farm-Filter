'''
Copyright (c) 2023 Jacky Hou

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

from Logger import logger
import cv2
import faiss
import numpy as np
import os
import Query_API

DB_Name = "ImageKey"
image_feaure_index = None

def HaveHuman(image_file):
    # 載入 HOG+SVM 預訓練模型
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    # 讀取圖像
    image = cv2.imread(image_file)
    # 執行人體檢測
    boxes, weights = hog.detectMultiScale(image)

    return len(boxes), boxes

def Image_Analysis(image):

    # 創建SURF對象
    #surf = cv2.SIFT_create()
    #keypoints, descriptors = surf.detectAndCompute(image, None)

    # 使用ORB算法提取特徵
    orb = cv2.ORB_create(
        nfeatures = 5000,                   # The maximum number of features to retain.
        scaleFactor = 1.5,                  # Pyramid decimation ratio, greater than 1
        nlevels = 8,                        # The number of pyramid levels.
        #edgeThreshold = 7,                  # This is size of the border where the features are not detected. It should roughly match the patchSize parameter
        firstLevel = 0,                     # It should be 0 in the current implementation.
        #WTA_K = 2,                          # The number of points that produce each element of the oriented BRIEF descriptor.
        #scoreType = cv2.ORB_HARRIS_SCORE,   # The default HARRIS_SCORE means that Harris algorithm is used to rank features (the score is written to KeyPoint::score and is
                                            # used to retain best nfeatures features); FAST_SCORE is alternative value of the parameter that produces slightly less stable
                                            # keypoints, but it is a little faster to compute.
        #scoreType = cv2.ORB_FAST_SCORE,
        #patchSize = 7                       # size of the patch used by the oriented BRIEF descriptor. Of course, on smaller pyramid layers the perceived image area covered
                                            # by a feature will be larger.
    )
    keypoints, descriptors = orb.detectAndCompute(image, None)

    return descriptors

def Add_Image_Sample(image_file):

    collection = Query_API.Read_Collection(DB_Name,DB_Name)
    fs = Query_API.Load_GridFS(DB_Name)
    amount, boxes = HaveHuman(image_file)

    # 加載圖像
    load_image = cv2.imread(image_file)
    file_ids = []
    if amount:
        for (x, y, w, h) in boxes:
            logger.info(f"{x},{y},{w},{h}")
            if w*h > 100*100:
                continue
            cropped_image = load_image[y:y+h, x:x+w]

            descriptors = Image_Analysis(cropped_image)

            if descriptors is not None and len(descriptors) > 0:
                # 將特徵描述子轉換為二進制數據
                descriptors_bytes = descriptors.tobytes()

                # 寫入GridFS

                file_id = Query_API.Write_GridFS(fs, descriptors_bytes)
                file_ids.append(file_id)

    # 整個圖片特徵點
    descriptors = Image_Analysis(load_image)

    # 將特徵描述子轉換為二進制數據
    descriptors_bytes = descriptors.tobytes()

    # 寫入GridFS
    file_id = Query_API.Write_GridFS(fs, descriptors_bytes)
    file_ids.append(file_id)

    # 建立要插入的文檔
    feature_doc = {
        'image_id': os.path.basename(image_file),
        'file_id': file_ids
    }

    # 插入文檔到集合中
    Query_API.Write_Document(collection, feature_doc)

    Load_Image_Feature()

    return

def Load_Image_Feature_Sub(NAME):

    collection = Query_API.Read_Collection(NAME,NAME)
    fs = Query_API.Load_GridFS(NAME)

    cursor = collection.find({})

    features = []
    for doc in cursor:
        for file_id in doc['file_id']:
            file_content = Query_API.Read_GridFS(fs, file_id)
            feature = np.frombuffer(file_content, dtype=np.uint8)
            feature = feature.reshape(-1, 32)  # 根據特徵描述子的維度進行重新形狀
            features.append(feature)

    # 將特徵值堆疊成一個大矩陣
    features = np.vstack(features)

    index = faiss.IndexFlatL2(features.shape[1])  # 使用L2距離度量
    index.add(features)

    return index

def Load_Image_Feature():
    global image_feaure_index, DB_Name
    if not Query_API.Get_DB_len(DB_Name, DB_Name):
        logger.info(f"{DB_Name} is No Data")
    else:
        image_feaure_index = Load_Image_Feature_Sub(DB_Name)

    return

def Search_Same_Image(image_file):
    global image_feaure_index, DB_Name

    result, _ = HaveHuman(image_file)
    if not Query_API.Get_DB_len(DB_Name, DB_Name):
        logger.info(f"{DB_Name} is No Data")
        return

    # 加載圖像
    image = cv2.imread(image_file)
    query_descriptors = Image_Analysis(image)

    # 使用faiss進行相似度搜索
    k = 3  # 搜尋的最近鄰居數量
    query_descriptors = query_descriptors.astype(np.float32)  # faiss要求輸入為float32類型
    distances, indices = image_feaure_index.search(query_descriptors, k)

    distances_point = 0
    indices_point = 0
    for i in range(len(distances)):
        #logger.info(f"[{i}] => {distances[i]}, {indices[i]}")
        for j in range(k):
            number = int(distances[i][j])
            if number < 50000:
                distances_point+=1

            number = int(indices[i][j])
            if number < 100:
                indices_point+=1

    logger.info(f"distances : indices = {str(distances_point)} : {str(indices_point)}")

    return distances_point