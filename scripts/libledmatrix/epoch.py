#!/usr/bin/env python3
import time

#TODO take delta in seconds instead of number of epochs
def delta(base_epoch, epoch_delta):
    d = Epoch()
    d._min = base_epoch._min + epoch_delta
    return d


class Epoch():
    def __init__(self):
        self._min = time.time() // 60

    def set(self, float_time):
        self._min = float_time // 60

    def next(self):
        self._min += 1

    def __eq__(self, other):
        if isinstance(other, Epoch):
            return self._min == other._min
        return False

    def __lt__(self, other):
        if isinstance(other, Epoch):
            return self._min < other._min
        return False

    def __gt__(self, other):
        if isinstance(other, Epoch):
            return self._min > other._min
        return False

    def __repr__(self):
        return str(self._min)

    def seconds(self):
        return self._min * 60

