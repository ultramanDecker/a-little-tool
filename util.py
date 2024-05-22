import os

import cv2
from queue import PriorityQueue

coords_pq = PriorityQueue()
words = []
transcribe_dict = {'ū': 'v', 'š': 's', 'ž': 'z'}


def get_phonetic_info(recognition_text_file):
    phonetic_notations = []
    with open(recognition_text_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            split_items = line.split(',')
            index = int(split_items[1].split('：')[1])
            notation = split_items[2].split('：')[1].strip()
            phonetic_notations.append({'index': index, 'notation': notation})
    phonetic_notations.sort(key=lambda x: x['index'])
    return phonetic_notations


def rename(check_list, page_number, page_image_file, word_images_directory, phonetic_notations):
    images_files = [{'index': int(f.split('.')[0]), 'filename': f} for f in os.listdir(word_images_directory)]
    images_files.sort(key=lambda x: x['index'])
    position_list = get_position_list(page_image_file, word_images_directory)
    tmp = [n[2] for n in position_list]
    remove_list = []
    for i in range(len(images_files)):
        if images_files[i]['index'] not in tmp:
            remove_list.append(i)
    for i in remove_list:
        images_files.pop(i)
    for i in range(len(images_files)):
        notation = phonetic_notations[i]['notation']
        index = phonetic_notations[i]['index']
        col = position_list[i][0]
        row = position_list[i][1]
        os.rename(f'{word_images_directory}/{images_files[i]["filename"]}',
                  f'{word_images_directory}/{int(not check_list[i])}_{page_number}_{row}_{col}_{notation_transcribe(notation)}.png')


def notation_transcribe(notation: str):
    for k in transcribe_dict.keys():
        notation = notation.replace(k, transcribe_dict[k])
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
            duplicated_index = []
            for i in range(len(tmp_col) - 1):
                for j in range(i + 1, len(tmp_col) - 1):
                    if abs(tmp_col[i][0] - tmp_col[j][0]) + abs(tmp_col[i][1] - tmp_col[j][1]) < 30:
                        duplicated_index.append(i)
            for i in duplicated_index:
                tmp_col.pop(i)
            columns.append(tmp_col)
            tmp_col = [top]

    columns.append(tmp_col)
    position_list = []
    for i in range(len(columns)):
        columns[i].sort(key=lambda x: x[1])
        for j in range(len(columns[i])):
            position_list.append((i + 1, j + 1, columns[i][j][2]))
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
