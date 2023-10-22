import cv2
from sklearn import cluster
import numpy as np
from types import SimpleNamespace


def cluster_image(image: np.ndarray, n_clusters: int = 2, init: np.ndarray = None):
    """
    图像聚类
    :param image: 图像数组, 格式为RGB
    :param n_clusters: 聚类数量, 默认为2
    :param init: 聚类中心，默认为[[140, 128, 104], [78, 123, 175]]
    :return: 聚类结果
    """
    assert isinstance(image, np.ndarray), "image must be numpy.ndarray"
    assert image.ndim in [2, 3], "image must be 2 or 3 dimension"
    shape = image.shape
    image = image.reshape((-1, image.ndim))

    if init is None:
        init = np.array([[140, 128, 104], [78, 123, 175]], dtype=np.uint8)

    cluster_labels = cluster.KMeans(
        n_clusters=n_clusters, init=init, n_init="auto"
    ).fit_predict(image)
    return cluster_labels.reshape(shape[:-1])


def closing(
        image: np.ndarray,
        kernel_size: int = 3,
        iterations: int = 1,
        dst: np.ndarray = None,
):
    """
    闭运算
    :param image: 图像数组, 为一个二值图像
    :param kernel_size: 卷积核大小, 默认为3
    :param iterations: 迭代次数, 默认为1
    :param dst: 输出图像, 默认为None
    :return: 闭运算结果
    """
    assert isinstance(image, np.ndarray), "image must be numpy.ndarray"
    assert image.ndim == 2, "image must be 2 dimension"
    kernel = np.ones((kernel_size, kernel_size), dtype=np.uint8)

    return cv2.morphologyEx(
        image, cv2.MORPH_CLOSE, kernel, iterations=iterations, dst=dst
    )


def get_connect_part(image: np.ndarray, piex_threshold: int = 0) -> SimpleNamespace:
    """
    获取连通区域
    :param image: 图像数组, 为一个二值图像
    :param piex_threshold: 像素阈值,连通区域像素值小于piex_threshold的进行过滤。 piex_threshold默认为0
    :return: 连通区域
    """
    assert isinstance(image, np.ndarray), "image must be numpy.ndarray"
    assert image.ndim == 2, "image must be 2 dimension"
    number_cls, labeled_img = cv2.connectedComponents(image, connectivity=8)
    piex = []
    boxes = []
    for i in range(1, number_cls):
        connect = np.where(labeled_img == i)
        if len(connect[0]) < piex_threshold:
            labeled_img[connect] = 0
            continue
        else:
            labeled_img[connect] = 255
            piex.append(len(connect[0]))  # 记录连通区域的像素值
            x_min, x_max = np.min(connect[0]), np.max(connect[0])
            y_min, y_max = np.min(connect[1]), np.max(connect[1])
            boxes.append([x_min, y_min, x_max, y_max])  # 记录连通区域的坐标
    return SimpleNamespace(
        number_cls=len(piex),
        labeled_img=labeled_img,
        piex=piex,
        boxes=boxes,
    )


def get_area(piex: int) -> SimpleNamespace:
    """ "像素与面积的转换"""
    assert isinstance(piex, int), "piex must be int"
    area = 0.0106044538 ** 2 * piex
    return SimpleNamespace(
        um=round(area * 10000, 2),
        mm=round(area, 2),
        cm=round(area / 100, 2),
        m=round(area / 1000000, 2),
    )
