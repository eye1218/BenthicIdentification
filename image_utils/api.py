import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from cv2 import GaussianBlur

from image_utils.core import cluster_image, closing, get_connect_part, get_area
import importlib.resources as pkg_resources


def get_connect_part_of_image(image: str, piex_threshold: int = 5000) -> SimpleNamespace:
    """
    获取连通区域
    :param image: 图像路径
    :param piex_threshold: 像素阈值,连通区域像素值小于piex_threshold的进行过滤。 piex_threshold默认为0
    :return: 连通区域
    """
    assert Path(image).exists(), "image must be exists"
    image = np.array(Image.open(image))
    image = GaussianBlur(image, (5, 5), 0)
    image = cluster_image(image, n_clusters=2)
    image = (255 - image * 255).astype(np.uint8)
    image = closing(image, kernel_size=5, iterations=5)
    connected_part = get_connect_part(image, piex_threshold=piex_threshold)
    return connected_part


def get_result(origin_image: str, connect_info: SimpleNamespace = None,
               piex_threshold: int = 5000) -> SimpleNamespace:
    """
    将图片进行处理后的最终结果
    :param origin_image: 原始图像数组（格式RGB）或者原始图像路径
    :param connect_info: 连通区域信息
    :param piex_threshold: 连通部分像素阈值，小于阈值的连通区域将被认为是噪声
    :return:
    """
    assert Path(origin_image).exists(), "image must be exists"
    if not connect_info:
        connect_info = get_connect_part_of_image(origin_image, piex_threshold=piex_threshold)
    image = np.array(Image.open(origin_image))
    foreground = connect_info.labeled_img.astype(np.uint8)
    foreground = np.dstack((image, foreground))
    return SimpleNamespace(
        image=image,
        foreground=foreground,
        cls=connect_info.number_cls,
        area=[get_area(item).mm for item in connect_info.piex],
        boxes=connect_info.boxes,
        filename=Path(origin_image).name
    )


def cut(connect_info: SimpleNamespace, origin_path: str = None, foreground_path=None,
        origin_cut_path: str = None, foreground_cut_path: str = None):
    """
    将图片进行处理后的最终结果
    :param connect_info: 连通区域信息
    :param origin_path: 原始图像保存路径
    :param foreground_path: 前景图像保存路径
    :param origin_cut_path: 原始图像保存路径
    :param foreground_cut_path: 前景图像保存路径
    :return:
    """
    # 路径校验
    if origin_path and not Path(origin_path).exists():
        Path(origin_path).mkdir(parents=True)
    if foreground_path and not Path(foreground_path).exists():
        Path(foreground_path).mkdir(parents=True)
    if origin_cut_path and not Path(origin_cut_path).exists():
        Path(origin_cut_path).mkdir(parents=True)
    if foreground_cut_path and not Path(foreground_cut_path).exists():
        Path(foreground_cut_path).mkdir(parents=True)

    if origin_path:
        img_o = Image.fromarray(connect_info.image, 'RGB')
        draw_o = ImageDraw.Draw(img_o)
    if foreground_path:
        img_f = Image.fromarray(connect_info.foreground, 'RGBA')
        draw_f = ImageDraw.Draw(img_f)
    font = ImageFont.truetype(
        'msyh.ttc',
        30)

    index_font = ImageFont.truetype(
        'msyhbd.ttc',
        60)
    color = (255, 0, 0)
    boundary_width = 4

    for index in range(connect_info.cls):
        box = connect_info.boxes[index]
        filename = f'{index + 1}_{connect_info.area[index]}mm2_{Path(connect_info.filename).stem}.png'
        if origin_cut_path:
            Image.fromarray(connect_info.image[box[0]:box[2], box[1]:box[3], :], 'RGB').save(
                Path(origin_cut_path) / filename)
        if foreground_cut_path:
            Image.fromarray(connect_info.foreground[box[0]:box[2], box[1]:box[3], :], 'RGBA').save(
                Path(foreground_cut_path) / filename)

        # 画框并添加文字
        if origin_path:
            # 使用PIL画框
            draw_o.rectangle((box[1], box[0], box[3], box[2]), outline=color, width=boundary_width)
            draw_o.text((box[1] + (box[3] - box[1] - 30) // 2, box[0]), f'{index + 1}', font=index_font, fill=color)
            draw_o.text((box[1] + 10, box[2] - 40), f'{connect_info.area[index]}', font=font, fill=color)

        if foreground_path:
            # 使用PIL画框
            draw_f.rectangle((box[1], box[0], box[3], box[2]), outline=color, width=boundary_width)
            draw_f.text((box[1] + (box[3] - box[1] - 30) // 2, box[0]), f'{index + 1}', font=index_font, fill=color)
            draw_f.text((box[1] + 10, box[2] - 40), f'{connect_info.area[index]}', font=font, fill=color)

    if origin_path:
        img_o.save(Path(origin_path) / connect_info.filename)
    if foreground_path:
        img_f.save(Path(foreground_path) / connect_info.filename)


def get_image_save_path(image_path: str, save_path: str, source_dir: str):
    """
    获取图像保存路径
    :param image_path: 图像绝对路径
    :param save_path: 图像保存目录
    :param source_dir: 图片所在源目录
    :return: origin_path, foreground_path, origin_cut_path, foreground_cut_path
    """
    source_dir_parts = Path(source_dir).parts
    dir_name = Path(source_dir).name
    save_path_parts = Path(save_path).parts
    image_path_parts = Path(image_path).parts
    origin_path = save_path_parts + Path(dir_name).parts + Path('source').parts + image_path_parts[
                                                                                  len(source_dir_parts):-1]
    foreground_path = save_path_parts + Path(dir_name).parts + Path('foreground').parts + image_path_parts[
                                                                                          len(source_dir_parts):-1]
    origin_cut_path = save_path_parts + Path(dir_name).parts + Path('source_cut').parts + image_path_parts[
                                                                                          len(source_dir_parts):-1]
    foreground_cut_path = save_path_parts + Path(dir_name).parts + Path('foreground_cut').parts + image_path_parts[
                                                                                                  len(source_dir_parts):-1]
    return SimpleNamespace(
        origin_path=str(Path(*origin_path)),
        foreground_path=str(Path(*foreground_path)),
        origin_cut_path=str(Path(*origin_cut_path)),
        foreground_cut_path=str(Path(*foreground_cut_path)),
    )


def main(image: str, save_path: str, source_dir: str, cut_image: bool = False, foreground: bool = False,
         piex_threshold: int = 5000):
    """
    :param image: 原始图像路径
    :param save_path: 保存路径
    :param source_dir: 原始图像所在目录
    :param cut_image: 是否进行切割
    :param foreground: 是否保存前景图像
    :param piex_threshold: 连通部分像素阈值，小于阈值的连通区域将被认为是噪声
    :return:
    """

    start = time.time()
    assert Path(image).exists(), "image must be exists"
    assert Path(save_path).exists(), "save_path must be exists"
    assert Path(source_dir).exists(), "source_dir must be exists"

    path = get_image_save_path(image, save_path, source_dir)
    origin_path = path.origin_path
    foreground_path = path.foreground_path
    origin_cut_path = path.origin_cut_path
    foreground_cut_path = path.foreground_cut_path
    if not cut_image:
        foreground_cut_path = None
        origin_cut_path = None
    if not foreground:
        foreground_path = None
        foreground_cut_path = None

    connect_info = get_result(image, piex_threshold=piex_threshold)
    cut(connect_info, origin_path=origin_path, foreground_path=foreground_path, origin_cut_path=origin_cut_path,
        foreground_cut_path=foreground_cut_path)
    end = time.time()
    return SimpleNamespace(
        image_path=image,
        cls=connect_info.cls,
        area=connect_info.area,
        boxes=connect_info.boxes,
        filename=connect_info.filename,
        time=end - start,
    )


if __name__ == '__main__':
    print(pkg_resources.files('image_utils').joinpath('font/yahei.ttf').__str__())
