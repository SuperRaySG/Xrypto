from .observer import Observer
import json
import time
import os
import logging


class HistoryDumper(Observer):
    out_dir = 'history/'

    def __init__(self):
        try:
            os.mkdir(self.out_dir)
        except:
            pass

    def begin_opportunity_finder(self, depths):
        filename = self.out_dir + 'order-book-' + \
            str(int(time.time())) + '.json'
        fp = open(filename, 'w')
        json.dump(depths, fp)
        logging.debug (depths)

        for depth in depths:
            print(depth)

    def end_opportunity_finder(self):
        pass

    def opportunity(self, profit, volume, bprice, kask, sprice, kbid, perc, w_bprice, w_sprice):
        pass
