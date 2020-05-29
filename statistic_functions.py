# coding: utf-8
# importing reduce()
from functools import reduce

def Average(lst):
    return reduce(lambda a, b: a + b, lst) / len(lst)