import logging
from .observer import Observer
import json
import time
import os
import math
import sys
import traceback
import config

class BasicBot(Observer):
    def __init__(self):
        super().__init__()

        self.orders = []

        self.max_maker_volume = config.MAKER_MAX_VOLUME
        self.min_maker_volume = config.MAKER_MIN_VOLUME
        self.max_taker_volume = config.TAKER_MAX_VOLUME
        self.min_taker_volume = config.TAKER_MIN_VOLUME

        logging.info('BasicBot Setup complete')

    def process_message(self,message):
        pass

    def msg_server(self):
        import zmq
        context = zmq.Context()
        socket = context.socket(zmq.PULL)
        socket.bind("tcp://*:%s"%config.ZMQ_PORT)

        logging.info("zmq msg_server start...")
        while not self.is_terminated:
            # Wait for next request from client
            message = socket.recv()
            logging.info("new pull message: %s", message)
            self.process_message(message)

            time.sleep (1) # Do some 'work'

    def notify_obj(self, pyObj):
        import zmq
        try:
            context = zmq.Context()
            socket = context.socket(zmq.PUSH)

            socket.connect ("tcp://%s:%s" % (config.ZMQ_HOST, config.ZMQ_PORT))
            time.sleep(1)

            logging.info( "notify message %s", json.dumps(pyObj))

            socket.send_string(json.dumps(pyObj))
        except Exception as e:
            logging.warn("notify_msg Exception")
            pass

    def notify_msg(self, type, price):
        message = {'type':type, 'price':price}
        self.notify_obj(message)

    def new_order(self, market, type, maker_only=False, amount=None, price=None):
        if type == 'buy' or type == 'sell':
            if not price or not amount:
                print(price)
                print(amount)
                assert(False)

            if maker_only:                
                if type == 'buy':
                    order_id = self.clients[market].buy_maker(amount, price)
                else:
                    order_id = self.clients[market].sell_maker(amount, price)
            else:
                if type == 'buy':
                    order_id = self.clients[market].buy_limit(amount, price)
                else:
                    order_id = self.clients[market].sell_limit(amount, price)

            if not order_id or order_id == -1:
                logging.warn("%s @%s %f/%f failed, %s" % (type, market, amount, price, order_id))
                return None
    

            order = {
                'market': market, 
                'order_id': order_id,
                'price': price,
                'amount': amount,
                'deal_amount':0,
                'deal_index': 0, 
                'type': type,
                'time': time.time()
            }
            self.orders.append(order)
            logging.verbose("submit order %s" % (order))

            return order

        return None


    def remove_order(self, order_id):
        self.orders = [x for x in self.orders if not x['order_id'] == order_id]

    def get_order(self, order_id):
        for x in self.orders:
            if x['order_id'] == order_id:
                return x

    def get_orders(self, type):
        orders_snapshot = [x for x in self.orders if x['type'] == type]
        return orders_snapshot

    def get_order_ids(self):
        order_ids = [x['order_id'] for x in self.orders]
        return order_ids

    def selling_len(self):
        return len(self.get_orders('sell'))

    def buying_len(self):
        return len(self.get_orders('buy'))

    def is_selling(self):
        return len(self.get_orders('sell')) > 0

    def is_buying(self):
        return len(self.get_orders('buy')) > 0

    def get_sell_price(self):
        return self.sprice

    def get_buy_price(self):
        return self.bprice

    def get_spread(self):
        return self.sprice - self.bprice
        
    def cancel_order(self, market, type, order_id):
        result = self.clients[market].cancel_order(order_id)
        if not result:
            logging.warn("cancel %s #%s failed" % (type, order_id))
            return False
        else:
            logging.info("cancel %s #%s ok" % (type, order_id))
            return True

    def cancel_all_orders(self, market):
        orders = self.clients[market].get_orders_history()

        print(orders)
        if not orders:
            return

        for order in orders:
            logging.info("Cancelling: %s %s @ %s" % (order['type'], order['amount'], order['price']))
            while True:
                result = self.cancel_order(market, order['type'], order['order_id']); 
                if not result:
                    time.sleep(10) 
                else:
                    break