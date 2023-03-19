#!/usr/bin/python
# coding: utf-8

# 使用方法：
# 运行此脚本后，3秒内将鼠标放置在左上角的方块，等待即可

# 注意事项：
# 1. 游戏内需要调整控件：点击方块改为q键，标记雷区为e键
# 2. 鼠标放置的初始位置最好是左上角的一块，但一些情况可能需要调整位置
#   - 初始块的右上和右下无相邻块时不行
#   - 初始块的右侧第二列没有方块时不行
#   - 初始块右侧第一列或第二列存在黑色挡板时不行

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
    """
        识别器
        会缓存每一个坐标的安全状态
    """

    class BlockState(Enum):
        SAFE = 0
        DANGGEROUS = 1
        UNPROBED = 2
        BACKGROUND = 3

    def __init__(self):
        self.pos_state_map = {}

    @staticmethod
    def __pos_key(pos):
        """
            返回坐标对应的在缓存表中的key
        :param pos: (0, 0)
        :return: "0_0"
        """
        return "{}_{}".format(int(pos[0]), int(pos[1]))

    def get_pos_cache_state(self, pos):
        """
            从缓存表获取当前坐标的安全状态
        :param pos: (0, 0)
        :return: 0
        """
        return self.pos_state_map.get(self.__pos_key(pos), None)

    def is_pos_cache_state(self, pos, state):
        """
            当前坐标的安全状态是否是state
        :param pos: (0, 0)
        :param state: 0，int，代表block的状态
        :return: True
        """
        cache_state = self.get_pos_cache_state(pos)
        if cache_state == state:
            return True
        return False

    def is_pos_background_block(self, pos):
        """
            当前坐标是否是背景块
        :param pos: (0, 0)
        :return: True
        """
        if self.is_pos_cache_state(pos, self.BlockState.BACKGROUND.value):
            return True

        cur_rgb = pyautogui.screenshot().getpixel(pos)
        if cur_rgb == RGB.BACKGROUND.value:
            self.record_pos_state(pos, self.BlockState.BACKGROUND.value)
            return True
        return False

    def is_pos_unprobed_block(self, pos):
        """
            当前坐标是否是未探测过的方块
        :param pos: (0, 0)
        :return: True
        """
        cur_rgb = pyautogui.screenshot().getpixel(pos)
        if cur_rgb == RGB.UNPROBED.value or cur_rgb == RGB.ANOTHER_UNPROBED.value:
            return True
        return False

    def is_pos_safe_block(self, pos):
        """
            当前坐标是否是安全方块
        :param pos: (0, 0)
        :return: True
        """
        if self.is_pos_cache_state(pos, self.BlockState.SAFE.value):
            return True
        return False

    def is_pos_dangerous_block(self, pos):
        """
            当前坐标是否是雷区
        :param pos: (0, 0)
        :return: True
        """
        if self.is_pos_cache_state(pos, self.BlockState.DANGGEROUS.value):
            return True
        return False

    @staticmethod
    def is_pos_error_block(pos):
        """
            当前坐标是否是出错方块（点错时会在1秒钟内展示为红色方块）
        :param pos: (0, 0)
        :return: True
        """
        cur_rgb = pyautogui.screenshot().getpixel(pos)
        if cur_rgb == RGB.ERROR.value:
            return True
        return False

    def record_pos_state(self, pos, state):
        """
            将当前坐标的安全状态记录到缓存表钟
        :param pos: (0, 0)
        :param state: 0
        :return:
        """
        self.pos_state_map[self.__pos_key(pos)] = state


class Mover:
    """鼠标移动者"""
    def __init__(self, frame, pos):
        # 左上到右下的四个坐标：((x1, y1), (x2, y2))
        self.frame = frame
        self.init_pos = pos

        self.dx, self.dy = None, None
        # -1向上，1向下
        self.direction = 1

        self.__get_dx(pos)
        self.__get_dy(pos)
        print("dx: {}, dy: {}".format(self.dx, self.dy))

        pyautogui.moveTo(pos)

    @staticmethod
    def __ignored_rgb(rgb):
        """
            当前颜色是否可忽略
            该函数给计算dx,dy时使用，为了消除渐变颜色的干扰
        :param rgb: (255, 255, 255)
        :return: True
        """
        if rgb != RGB.UNPROBED.value and rgb != RGB.BACKGROUND.value:
            return True
        return False

    def __get_dx(self, pos):
        """
            计算dx，即两个相邻列之前的差距，并更新self.dx
            大致思路：以初始块开始，向左向右探测直到一个循环节，该节段的长度除以二即为dx
        :param pos: (0, 0)
        :return:
        """
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
        """
            计算dy，即两个相邻行之前的差距，并更新self.dy
            大致思路，向上向下探测直到一个循环节，该节段的长度即为dy
        :param pos: (0, 0)
        :return:
        """
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

    @staticmethod
    def leftclick_block():
        """
            点击安全块
        :return:
        """
        pydirectinput.keyDown("q")
        pydirectinput.keyUp("q")

    @staticmethod
    def rightclick_block():
        """
            点击雷块
        :return:
        """
        pydirectinput.keyDown("e")
        pydirectinput.keyUp("e")

    def move_back(self, pos):
        """
            往回移动两列，用于点错时回退
        :param pos: (0, 0)
        :return: (0, 0)
        """
        back_pos = (pos[0] - 2*self.dx, pos[1])
        pyautogui.moveTo(self.init_pos)
        return back_pos

    def move_to_next(self, pos):
        """
            移动至下一个坐标
            路径：先向下，到底后向右移动一格，再向上
        :param pos: (0, 0)
        :return: (0, 0)
        """
        # 先上下再右
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
    # 初始化识别器和鼠标移动器
    recognizer = Recognizer()

    init_pos = pyautogui.position()
    mover = Mover(frame=((155, 100), (1260, 690)), pos=init_pos)
    pos = init_pos

    # 开始循环点击方块阶段
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
        # time.sleep(0.2)
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
