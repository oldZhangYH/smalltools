# -*- encoding: utf-8 -*-
'''
@File : Utils.py    
@Modify Time : 2021/3/31 下午2:53        
@Author : oldzhang
@Description ： 工具类
'''
import os
from json import load
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import SubElement

from cv2 import cv2

from pycocotools.coco import COCO


def getMessageFromCoco(cocoPath):
    """
    从coco数据集获取数据
    :param cocoPath:
    :return: [img,objs]
    objs[obj[label,bbox]]
    """
    coco = COCO(cocoPath)
    imgIds = coco.getImgIds()
    res = []
    for imgId in imgIds:
        annIds = coco.getAnnIds(imgId)
        anns = coco.loadAnns(annIds)
        img = coco.loadImgs(imgId)[0]

        objs = []
        for ann in anns:
            bbox = ann["bbox"]
            label = coco.loadCats(ann["category_id"])[0]["name"]
            obj = [label, bbox]
            objs.append(obj)
        temp = [img, objs]
        res.append(temp)
    return res


def getMessageFormJson(jsonPath):
    """
    从labelme格式的json文件中获取坐标和类别
    :param jsonPath:labelme格式的json文件路径
    :return:<list>所有坐标和类别
    """
    res = []
    with open(jsonPath) as f:
        json = load(f)
        if len(json) == 0:
            return
        for i in json["shapes"]:
            temp = []
            temp.append(i["label"])
            for j in i["points"]:
                temp.append(j)
            res.append(temp)
    return res


def prettyXml(element, indent, newline, level=0):
    # 判断element是否有子元素
    if element:
        # 如果element的text没有内容
        if element.text == None or element.text.isspace():
            element.text = newline + indent * (level + 1)
        else:
            element.text = newline + indent * (level + 1) + element.text.strip() + newline + indent * (level + 1)
            # 此处两行如果把注释去掉，Element的text也会另起一行
    # else:
    # element.text = newline + indent * (level + 1) + element.text.strip() + newline + indent * level
    temp = list(element)  # 将elemnt转成list
    for subelement in temp:
        # 如果不是list的最后一个元素，说明下一个行是同级别元素的起始，缩进应一致
        if temp.index(subelement) < (len(temp) - 1):
            subelement.tail = newline + indent * (level + 1)
        else:  # 如果是list的最后一个元素， 说明下一行是母元素的结束，缩进应该少一个
            subelement.tail = newline + indent * level
            # 对子元素进行递归操作
        prettyXml(subelement, indent, newline, level=level + 1)


def getMessageFromVoc(vocPath):
    """
    从voc xml中获取数据
    :param vocPath:voc 路径
    :return:res[img,obj]
            img[filename,w,h]
            obj[bbox]
            bbox[label,xmin,ymin,xmax,ymax]
    """
    files = sorted(os.listdir(vocPath))
    res = []
    for file in files:
        fileData = []
        img = []
        tree = ET.parse(vocPath + file)
        root = tree.getroot()
        objs = root.findall("object")
        imgName = root.find("filename").text
        if len(objs) == 0:
            res.append(imgName)
            continue
        size = root.find("size")
        w = size.findtext("width")
        h = size.findtext("height")
        img.append(imgName)
        img.append(float(h))
        img.append(float(w))
        fileData.append(img)
        objList = []
        for obj in objs:
            objTemp = []
            label = obj.findtext("name")
            bbox = obj.find("bndbox")
            xmin = bbox.findtext("xmin")
            ymin = bbox.findtext("ymin")
            xmax = bbox.findtext("xmax")
            ymax = bbox.findtext("ymax")
            objTemp.append(label)
            objTemp.append(float(xmin))
            objTemp.append(float(ymin))
            objTemp.append(float(xmax))
            objTemp.append(float(ymax))
            objList.append(objTemp)
        fileData.append(objList)
        res.append(fileData)
    return res


def createVocXml(bboxs, img):
    """
    :param bboxs: [label,[xmin,ymin],[xmax,ymax]]
    :param img: [imgName,[height,width,depth]]
    :return:Element
    """
    # create xml
    annotation = Element('annotation')
    folder = SubElement(annotation, 'folder')
    folder.text = "菜品数据标注"
    filename = SubElement(annotation, 'filename')
    filename.text = img[0]

    size = SubElement(annotation, "size")
    depth = SubElement(size, "depth")
    height = SubElement(size, "height")
    width = SubElement(size, "width")
    depth.text = str(img[1][2])
    width.text = str(img[1][1])
    height.text = str(img[1][0])

    segmented = SubElement(annotation, "segmented")
    segmented.text = "1"

    # create object
    for bbox in bboxs:
        object = SubElement(annotation, "object")
        name = SubElement(object, "name")
        name.text = bbox[0]
        pose = SubElement(object, "pose")
        pose.text = "top"
        truncated = SubElement(object, "truncated")
        truncated.text = "0"
        difficult = SubElement(object, "difficult")
        difficult.text = "0"

        bndbox = SubElement(object, "bndbox")
        xmin = SubElement(bndbox, "xmin")
        ymin = SubElement(bndbox, "ymin")
        xmax = SubElement(bndbox, "xmax")
        ymax = SubElement(bndbox, "ymax")
        xmin.text = str(bbox[1][0])
        ymin.text = str(bbox[1][1])
        xmax.text = str(bbox[2][0])
        ymax.text = str(bbox[2][1])
    return annotation


def createDrakNetTxt(bboxs, img, resPath):
    """
    :param resPath: 保存路径
    :param bboxs: [label,[xmin,ymin],[xmax,ymax]]
    :param img: [imgName,[height,width,depth]]
    """
    res = []
    txtName = img[0][:img[0].rfind(".")] + ".txt"
    tw = img[1][1]
    th = img[1][0]
    for bbox in bboxs:
        label = bbox[0]
        x1 = bbox[1][0]
        y1 = bbox[1][1]
        x2 = bbox[2][0]
        y2 = bbox[2][1]

        # 计算中心点坐标
        xc = (x1 + x2) / (2 * tw)
        yc = (y1 + y2) / (2 * th)
        width = abs(x2 - x1) / tw
        height = abs(y2 - y1) / th
        temp = [label, xc, yc, width, height]
        res.append(temp)

    with open(resPath + txtName, "w") as f:
        for i in res:
            for j in i:
                f.write(str(j))
                f.write("\t")
            f.write("\n")


def createCocoAnnotation(bbox, categories, annotation):
    """

    :param bbox:  [label,[xmin,ymin],[xmax,ymax]]
    :param categories: {"id": int,
                        "name": str,
                        "supercategory": "null"
                        }
    :param annotation: {"id": 0,
                        "image_id": int,
                        "category_id": int,
                        "segmentation": "null",
                        "area": float,
                        "bbox": [x, y, w, h],
                        "iscrowd": 0}
    :return: annotation
    """
    for cat in categories:
        if cat["name"][0] == bbox[0]:
            annotation["category_id"] = cat["id"]
            break
    x = bbox[1][0]
    y = bbox[1][1]
    w = bbox[2][0] - x
    h = bbox[2][1] - y
    annotation["bbox"][0] = x
    annotation["bbox"][1] = y
    annotation["bbox"][2] = w
    annotation["bbox"][3] = h
    annotation["area"] = h * w
    return annotation


def createCocoImage(imgPath, imgName, imgId):
    """
    :param imgPath:
    :param imgName:
    :param imgId:
    :return: image
    """
    imgSize = cv2.imread(imgPath + imgName).shape
    image = {"id": imgId,
             "width": imgSize[1],
             "height": imgSize[0],
             "file_name": imgName,
             "license": 0,
             "flickr_url": "null",
             "coco_url": "null",
             "date_captured": "null"}
    return image
