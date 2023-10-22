from pathlib import Path


# 递归获取一个目录下的所有子目录
def get_all_file(path):
    for item in path:
        if Path(item).is_dir():
            yield from get_all_file(Path(item).iterdir())
        else:
            yield str(item)


def get_all_image(path: str) -> tuple:
    """
    递归获取一个目录下的所有图片
    :param path: 目录路径
    :return: 一个目录下的所有图片
    """

    def is_image(item):
        return Path(item).suffix in ['.jpg', '.png', '.jpeg', '.bmp', '.tif', '.tiff', 'JPG', 'PNG', 'JPEG', 'BMP',
                                     'TIF', 'TIFF']

    return tuple(filter(is_image, get_all_file([path])))


if __name__ == '__main__':
    images = get_all_image(r"D:\Workspace\Pycharm\tanze\BenthicIdentification")
    print(images)
