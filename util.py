import os
import re
from enum import Enum

import cv2
from queue import PriorityQueue

from PySide6.QtGui import QImage
from html2image import Html2Image

coords_pq = PriorityQueue()
words = []
transcribe_dict = {'ū': 'v', 'š': 's', 'ž': 'z'}


class Orientation(Enum):
    NULL = ('', ''),
    LEFT = ('left', 'l'),
    RIGHT = ('right', 'r')


def read_word_images(path):
    files = os.listdir(path)
    images = {}
    for i in range(len(files)):
        if files[i].endswith('.png') and files[i].split('.')[0].isdigit():
            images[int(files[i].split('.')[0])] = {
                'filename': files[i],
                'image': QImage(f'{path}/{files[i]}'),
                'position': (0, 0)
            }

    return images


def read_romanizations(recognition_text_file):
    notations = []
    with open(recognition_text_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            split_items = line.split(',')
            index = int(split_items[1].split('：')[1])
            notation = split_items[2].split('：')[1].strip()
            notations.append(notation_transcribe(notation))
    return notations


def get_required_items(path, files_to_find):
    file_list = os.listdir(path)
    required_items = []
    for i in files_to_find:
        for j in i:
            if j in file_list:
                required_items.append(f'{path}/{j}')
                break
    return required_items


def is_orientation_valid(files: list, orientation: Orientation):
    # is_valid = True
    # orientation =
    # for file in files:

    pass


def rename(check_list, page_number, word_images_directory, phonetic_notations, images: dict, orientation: Orientation):
    images_files = {}
    for f in os.listdir(word_images_directory):
        images_files[int(f.split('.')[0])] = f
    # images_files = [{int(f.split('.')[0]): f} for f in os.listdir(word_images_directory)]
    # images_files.sort(key=lambda x: x['index'])
    # position_list = get_position_list(page_image_file, word_images_directory)
    # tmp = [n[2] for n in position_list]
    # remove_list = []
    # for i in range(len(images_files)):
    #     if images_files[i]['index'] not in tmp:
    #         remove_list.append(i)
    # for i in remove_list:
    #     images_files.pop(i)
    # for i in range(len(images_files)):
    for index in images.keys():
        notation = phonetic_notations[index]
        col = images[index]['position'][0]
        row = images[index]['position'][1]
        os.rename(f'{word_images_directory}/{images_files[index]}',
                  f'{word_images_directory}/{int(not check_list[index])}_{page_number}{orientation.value[1]}_{col}_{row}_{notation_transcribe(notation)}.png')


def notation_transcribe(notation: str):
    for k in transcribe_dict.keys():
        notation = notation.replace(k, transcribe_dict[k])
    notation = notation.replace('z', 'R')
    return notation


def get_best_fit_coordinate(page, word, threshold=0.8):
    page_gray = cv2.cvtColor(page, cv2.COLOR_BGR2GRAY)
    word_gray = cv2.cvtColor(word, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(page_gray, word_gray, cv2.TM_CCOEFF_NORMED)
    return res


def fun():
    columns = []
    tmp_col = [coords_pq.get()]
    index = tmp_col[0][0]
    while not coords_pq.empty():
        top = coords_pq.get()
        if abs(top[0] - index) < 75:
            tmp_col.append(top)
        else:
            index = top[0]
            # duplicated_index = []
            # for i in range(len(tmp_col) - 1):
            #     for j in range(i + 1, len(tmp_col) - 1):
            #         if abs(tmp_col[i][0] - tmp_col[j][0]) + abs(tmp_col[i][1] - tmp_col[j][1]) < 30:
            #             duplicated_index.append(i)
            # for i in duplicated_index:
            #     tmp_col.pop(i)
            columns.append(tmp_col)
            tmp_col = [top]

    columns.append(tmp_col)
    position_list = []

    col = 1
    row = 1

    for i in range(len(columns)):
        columns[i].sort(key=lambda x: x[1])
        row = 1
        for j in range(len(columns[i])):
            if abs(columns[i][j - 1][0] - columns[i][j][0]) + abs(columns[i][j - 1][1] - columns[i][j][1]) < 60:
                row -= 1
                position_list.append((col, row, columns[i][j][2]))
            else:
                position_list.append((col, row, columns[i][j][2]))
            row += 1
        col += 1
    position_list.sort(key=lambda x: x[2])
    return position_list


def get_position_list(page_image_file, word_images_directory):
    page_image = cv2.imread(page_image_file)

    word_image_files = os.listdir(word_images_directory)
    word_image_files.sort(key=lambda x: int(x.split('.')[0]))

    for f in word_image_files:
        words.append(
            {'index': int(f.split('.')[0]), 'image': cv2.imread(f'{word_images_directory}/{f}')})
    for w in words:
        res = get_best_fit_coordinate(page_image, w['image'])
        coords_pq.put((cv2.minMaxLoc(res)[-1][0], cv2.minMaxLoc(res)[-1][1], w['index']))
    return fun()


def get_page_numbers(path):
    page_numbers = []
    for f in os.listdir(path):
        matched = re.match('Image_[0-9]+', f)
        if matched is not None:
            page_numbers.append(int(matched.group().split('_')[1]))
    page_numbers = set(page_numbers)
    return page_numbers


def text2img(notation: str, temp_dir: str):
    h2i = Html2Image(output_path=temp_dir)
    manchu_str = convert_manchu(notation)
    h2i.screenshot(html_str=get_html_str(manchu_str), save_as=f'{notation}.png',
                   size=(max(100, 25 * len(manchu_str)), 100))


def get_html_str(word: str):
    html_str = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="UTF-8">
        <title>Title</title>
        </head>
        <body style="background-color: white">
        <p style="font-size: 80px; margin: 0">{word}</p>
        </body>
        </html>
    """
    return html_str


def convert_manchu(s):
    tmp = ""
    if len(s) > 0:
        for i in range(len(s)):
            val = s[i]
            prev = " "
            if i > 0:
                prev = s[i - 1]
            if val == "a":
                tmp += "ᠠ"
            elif val == "e":
                tmp += "ᡝ"
            elif val == "i":
                tmp += "ᡳ"
            elif val == "o":
                tmp += "ᠣ"
            elif val == "u":
                tmp += "ᡠ"
            elif val == "v" or val == "@":
                tmp += "ᡡ"
            elif val == "n":
                tmp += "ᠨ"
            elif val == "N":
                tmp += "ᠩ"
            elif val == "b":
                tmp += "ᠪ"
            elif val == "p":
                tmp += "ᡦ"
            elif val == "x" or val == "S":
                tmp += "ᡧ"
            elif val == "k":
                tmp += "ᡴ"
            elif val == "g":
                if prev == "ᠨ" or prev == "n":
                    tmp = tmp[:-1] + "ᠩ"
                else:
                    tmp += "ᡤ"
            elif val == "h":
                tmp += "ᡥ"
            elif val == "m":
                tmp += "ᠮ"
            elif val == "l":
                tmp += "ᠯ"
            elif val == "t":
                tmp += "ᡨ"
            elif val == "d":
                tmp += "ᡩ"
            elif val == "s":
                if prev == "ᡨ" or prev == "t":
                    tmp = tmp[:-1] + "ᡮ"
                else:
                    tmp += "ᠰ"
            elif val == "c":
                tmp += "ᠴ"
            elif val == "j":
                tmp += "ᠵ"
            elif val == "y":
                tmp += "ᠶ"
            elif val == "r":
                tmp += "ᡵ"
            elif val == "w":
                tmp += "ᠸ"
            elif val == "f":
                tmp += "ᡶ"
            elif val == "K":
                tmp += "ᠺ"
            elif val == "G":
                tmp += "ᡬ"
            elif val == "H":
                tmp += "ᡭ"
            elif val == "J":
                tmp += "ᡷ"
            elif val == "C":
                tmp += "ᡱ"
            elif val == "R":
                tmp += "ᡰ"
            elif val == "z":
                if prev == "ᡩ" or prev == "d":
                    tmp = tmp[:-1] + "ᡯ"
                else:
                    tmp += "z"
            elif val == "'":
                tmp += "\u180B"
            elif val == "\"":
                tmp += "\u180C"
            elif val == "`":
                tmp += "\u180D"
            elif val == "_":
                tmp += "\u180E"
            elif val == "-":
                tmp += "\u202F"
            elif val == "*":
                tmp += "\u200D"
            else:
                tmp += val
    return tmp

# @Slot
# def finished_handler():
#
# # def fetch_image(notation):
# #
# #
# #
