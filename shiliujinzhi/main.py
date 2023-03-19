#!/usr/bin/python
# coding: utf-8

# 使用方法：鼠标放置在左上角一格，运行此程序即可

import pyautogui
import pydirectinput
import time

from enum import Enum

pyautogui.PAUSE = 0

class RGB(Enum):
    UNPROBED = (163, 163, 163)
    # 相邻块被探测后的未探测块的颜色
    ANOTHER_UNPROBED = (255, 255, 255)
    BACKGROUND = (226, 225, 255)
    # 点错的颜色
    ERROR = (255, 0, 0)


class Recognizer:
    """识别器"""

    class BlockState(Enum):
        SAFE = 0
        DANGGEROUS = 1
        UNPROBED = 2
        BACKGROUND = 3

    def __init__(self):
        self.pos_state_map = {}

    def __pos_key(self, pos):
        return "{}_{}".format(int(pos[0]), int(pos[1]))

    def get_pos_cache_state(self, pos):
        return self.pos_state_map.get(self.__pos_key(pos), None)

    def is_pos_cache_state(self, pos, state):
        cache_state = self.get_pos_cache_state(pos)
        if cache_state == state:
            return True
        return False

    def is_pos_background_block(self, pos):
        if self.is_pos_cache_state(pos, self.BlockState.BACKGROUND.value):
            return True

        cur_rgb = pyautogui.screenshot().getpixel(pos)
        if cur_rgb == RGB.BACKGROUND.value:
            self.record_pos_state(pos, self.BlockState.BACKGROUND.value)
            return True
        return False

    def is_pos_unprobed_block(self, pos):
        cur_rgb = pyautogui.screenshot().getpixel(pos)
        if cur_rgb == RGB.UNPROBED.value or cur_rgb == RGB.ANOTHER_UNPROBED.value:
            return True
        return False

    def is_pos_safe_block(self, pos):
        if self.is_pos_cache_state(pos, self.BlockState.SAFE.value):
            return True
        return False

    def is_pos_dangerous_block(self, pos):
        if self.is_pos_cache_state(pos, self.BlockState.DANGGEROUS.value):
            return True
        return False

    def is_pos_error_block(self, pos):
        cur_rgb = pyautogui.screenshot().getpixel(pos)
        if cur_rgb == RGB.ERROR.value:
            return True
        return False

    def record_pos_state(self, pos, state):
        self.pos_state_map[self.__pos_key(pos)] = state


class Mover:
    """鼠标移动者"""
    def __init__(self, frame, pos):
        # 左上到右下的四个坐标：((x1, y1), (x2, y2))
        self.init_pos = pos
        self.frame = frame
        self.dx, self.dy = None, None
        # -1向上，1向下
        self.direction = 1
        # 鼠标移至该列时的初始y坐标
        self.entry_y = pos[1]

        self.__get_dx(pos)
        self.__get_dy(pos)
        print("dx: {}, dy: {}".format(self.dx, self.dy))

        pyautogui.moveTo(pos)

    def __ignored_rgb(self, rgb):
        if rgb != RGB.UNPROBED.value and rgb != RGB.BACKGROUND.value:
            return True
        return False

    def __get_dx(self, pos):
        # 向左探测当前block的左边界
        left_probe_pos = pos
        rgb = pyautogui.screenshot().getpixel(left_probe_pos)
        while rgb == RGB.UNPROBED.value or self.__ignored_rgb(rgb):
            left_probe_pos = (left_probe_pos[0] - 1, left_probe_pos[1])
            rgb = pyautogui.screenshot().getpixel(left_probe_pos)
        left_pos = left_probe_pos

        # 向右探测下一块block的左边界
        right_probe_pos = pos
        rgb = pyautogui.screenshot().getpixel(right_probe_pos)
        while rgb == RGB.UNPROBED.value or self.__ignored_rgb(rgb):
            right_probe_pos = (right_probe_pos[0] + 1, right_probe_pos[1])
            rgb = pyautogui.screenshot().getpixel(right_probe_pos)
        # 到达当前块的右边界
        right_pos1 = right_probe_pos
        while rgb == RGB.BACKGROUND.value or self.__ignored_rgb(rgb):
            right_probe_pos = (right_probe_pos[0] + 1, right_probe_pos[1])
            rgb = pyautogui.screenshot().getpixel(right_probe_pos)
        # 可能到达了下一块的左边界，也可能到达了相邻块的左边界
        right_pos2 = right_probe_pos
        # 根据走过的背景像素的多少判断是否到达了下一块的左边界
        if right_pos2[0] - right_pos1[0] + 5 > right_pos1[0] - pos[0]:
            right_pos = right_pos2
        # 没走到下一块而是遇到了相邻块，则继续向右探测
        else:
            while rgb == RGB.UNPROBED.value or self.__ignored_rgb(rgb):
                right_probe_pos = (right_probe_pos[0] + 1, right_probe_pos[1])
                rgb = pyautogui.screenshot().getpixel(right_probe_pos)
            while rgb == RGB.BACKGROUND.value or self.__ignored_rgb(rgb):
                right_probe_pos = (right_probe_pos[0] + 1, right_probe_pos[1])
                rgb = pyautogui.screenshot().getpixel(right_probe_pos)
            right_pos3 = right_probe_pos
            right_pos = right_pos3

        self.dx = (right_pos[0] - left_pos[0] - 1)/2 - 1

    def __get_dy(self, pos):
        # 先x方向移动半格，防止左上角只有一个block导致探测失败
        cur_pos = (pos[0] + self.dx, pos[1])
        rgb = pyautogui.screenshot().getpixel(cur_pos)
        rgb1 = rgb
        rgb2 = RGB.UNPROBED.value if rgb == RGB.BACKGROUND.value else RGB.BACKGROUND.value

        # 向上探测一个颜色，向下探测两个颜色，因此需要注意初始鼠标位置最好偏上一点，防止特殊地图探测失败
        up_probe_pos = cur_pos
        rgb = pyautogui.screenshot().getpixel(up_probe_pos)
        while rgb == rgb1 or self.__ignored_rgb(rgb):
            up_probe_pos = (up_probe_pos[0], up_probe_pos[1] - 1)
            rgb = pyautogui.screenshot().getpixel(tuple(up_probe_pos))
        up_pos = up_probe_pos
        down_probe_pos = cur_pos
        rgb = pyautogui.screenshot().getpixel(down_probe_pos)
        while rgb == rgb1 or self.__ignored_rgb(rgb):
            down_probe_pos = (down_probe_pos[0], down_probe_pos[1] + 1)
            rgb = pyautogui.screenshot().getpixel(down_probe_pos)
        while rgb == rgb2 or self.__ignored_rgb(rgb):
            down_probe_pos = (down_probe_pos[0], down_probe_pos[1] + 1)
            rgb = pyautogui.screenshot().getpixel(down_probe_pos)
        down_pos = down_probe_pos

        self.dy = down_pos[1] - up_pos[1] - 1

    def leftclick_block(self):
        pydirectinput.keyDown("q")
        pydirectinput.keyUp("q")

    def rightclick_block(self):
        pydirectinput.keyDown("e")
        pydirectinput.keyUp("e")

    def move_to_init(self):
        self.direction = 1
        pyautogui.moveTo(self.init_pos)
        return self.init_pos

    def move_back(self, pos):
        back_pos = (pos[0] - 2*self.dx, pos[1])
        pyautogui.moveTo(self.init_pos)
        return back_pos

    def move_to_next(self, pos):
        # 先上后下再右
        # 先上下走，看下一个坐标会不会超出边框，不超出直接返回
        next_pos = (pos[0], pos[1] + self.dy * self.direction)
        if self.frame[0][1] < next_pos[1] < self.frame[1][1]:
            pass
        # 向下也超出边框，则移动x轴
        else:
            # 下一个y坐标，看上一次的上下方向决定上移还是下移
            next_pos_y_up = pos[1] - self.dy/2
            next_pos_y_down = pos[1] + self.dy/2
            if self.direction == 1:
                if self.frame[0][1] < next_pos_y_down < self.frame[1][1]:
                    next_pos_y = next_pos_y_down
                else:
                    next_pos_y = next_pos_y_up
            else:
                if self.frame[0][1] < next_pos_y_up < self.frame[1][1]:
                    next_pos_y = next_pos_y_up
                else:
                    next_pos_y = next_pos_y_down
            next_pos = (pos[0] + self.dx, next_pos_y)
            self.direction = -self.direction

        pyautogui.moveTo(next_pos)
        print("cur_pos: {}, next_pos: {}".format(pos, next_pos))

        return next_pos


def main():
    recognizer = Recognizer()

    init_pos = pyautogui.position()
    mover = Mover(frame=((155, 100), (1260, 690)), pos=init_pos)
    pos = init_pos

    while True:
        # 如果当前块的安全指标已知，则点击，背景则忽略
        if recognizer.is_pos_safe_block(pos):
            mover.leftclick_block()
            pos = mover.move_to_next(pos)
            continue
        elif recognizer.is_pos_dangerous_block(pos):
            mover.rightclick_block()
            pos = mover.move_to_next(pos)
            continue
        elif recognizer.is_pos_background_block(pos):
            pos = mover.move_to_next(pos)
            continue

        # 如果当前块未探测过，则认为是安全的并尝试点击，再查看当前块的状态
        # 1. 如果当前块状态为unprobed，则说明点错了，识别器记录当前块信息，然后从头开始再点
        # 2. 如果当前块不是unprobed，则说q明点对了，继续下一个
        mover.leftclick_block()
        time.sleep(0.2)
        if recognizer.is_pos_error_block(pos) or recognizer.is_pos_unprobed_block(pos):
            time.sleep(1)
            recognizer.record_pos_state(pos=pos, state=recognizer.BlockState.DANGGEROUS.value)
            pos = mover.move_back(pos)
        else:
            recognizer.record_pos_state(pos=pos, state=recognizer.BlockState.SAFE.value)
            pos = mover.move_to_next(pos)

        # 鼠标移至最右自动退出
        if pos[0] > mover.frame[1][0]:
            exit(0)


if __name__ == '__main__':
    time.sleep(3)
    main()

