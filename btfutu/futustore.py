#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2020 Damon Yuan <damon.yuan.dev@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import time
import threading
from datetime import datetime
from functools import wraps
import collections

import backtrader as bt
import futu as ft
from backtrader.metabase import MetaParams
from backtrader.utils.py3 import with_metaclass

from btfutu.exceptions import FutuNotSupported


class MetaSingleton(MetaParams):
    """Metaclass to make a metaclassed class a singleton"""

    def __init__(cls, name, bases, dct):
        super(MetaSingleton, cls).__init__(name, bases, dct)
        cls._singleton = None

    def __call__(cls, *args, **kwargs):
        if cls._singleton is None:
            cls._singleton = (
                super(MetaSingleton, cls).__call__(*args, **kwargs))

        return cls._singleton


class FutuTradeOrderHandler(ft.TradeOrderHandlerBase):
    def on_recv_rsp(self, rsp_pb):
        ret, content = super(FutuTradeOrderHandler, self).on_recv_rsp(rsp_pb)

        if ret == ft.RET_OK:
            print("* FutuTradeOrderHandler RET_OK content=\n{}\n".format(content.to_json()))
            order_status = content['order_status']
            oid = content['order_id']
            if order_status == ft.OrderStatus.UNSUBMITTED:
                pass
            elif order_status == ft.OrderStatus.WAITING_SUBMIT:
                pass
            elif order_status == ft.OrderStatus.SUBMITTING:
                pass
            elif order_status == ft.OrderStatus.SUBMITTED:
                pass
            elif order_status == ft.OrderStatus.SUBMIT_FAILED:
                pass
            elif order_status == ft.OrderStatus.FILLED_PART:
                pass
            elif order_status == ft.OrderStatus.FILLED_ALL:
                pass
            elif order_status == ft.OrderStatus.FILL_CANCELLED:
                pass
            elif order_status == ft.OrderStatus.CANCELLING_PART:
                pass
            elif order_status == ft.OrderStatus.CANCELLED_PART:
                pass
            elif order_status == ft.OrderStatus.CANCELLING_ALL:
                pass
            elif order_status == ft.OrderStatus.CANCELLED_ALL:
                pass
            elif order_status == ft.OrderStatus.TIMEOUT:
                pass
            elif order_status == ft.OrderStatus.FAILED:
                pass
            elif order_status == ft.OrderStatus.DISABLED:
                pass
            elif order_status == ft.OrderStatus.DELETED:
                pass
            elif order_status == ft.OrderStatus.NONE:
                pass
            else:
                pass

        else:
            print("* FutuTradeOrderHandler RET_ERROR content=\n{}\n".format(content.to_json))

        return ret, content


class FutuTradeDealHandler(ft.TradeDealHandlerBase):
    def on_recv_rsp(self, rsp_pb):
        ret, content = super(FutuTradeDealHandler, self).on_recv_rsp(rsp_pb)

        if ret == ft.RET_OK:
            print("* TradeDealTest content=\n{}\n".format(content))

        return ret, content


class FutuStoreException(Exception):
    pass


class FutuStore(with_metaclass(MetaSingleton, object)):
    """

    """
    BrokerCls = None  # broker class will autoregister
    DataCls = None  # data class will auto register

    (HKTrade, CNTrade, USTrade, FutureTrade, HKCCTrade) = range(5)

    params = (
        ('host', '127.0.0.1'),
        ('port', '11111'),
        ('trade', HKTrade),
        ('password', '123456'),
        ('trd_env', ft.TrdEnv.SIMULATE),
    )

    @classmethod
    def getdata(cls, *args, **kwargs):
        '''Returns ``DataCls`` with args, kwargs'''
        return cls.DataCls(*args, **kwargs)

    @classmethod
    def getbroker(cls, *args, **kwargs):
        '''Returns broker with *args, **kwargs from registered ``BrokerCls``'''
        return cls.BrokerCls(*args, **kwargs)

    def __init__(self):
        super(FutuStore, self).__init__()
        self.notifs = collections.deque()
        self.broker = None

        self._orders = collections.OrderedDict()
        self._ordersrev = collections.OrderedDict()
        self._transpend = collections.defaultdict(collections.deque)

        self._cash = 0.0
        self._value = 0.0
        self._evt_acct = threading.Event()

        if self.p.trade == self.HKTrade:
            self.trade_ctx = ft.OpenHKTradeContext(host="127.0.0.1", port=11111)
        elif self.p.trade == self.CNTrade:
            self.trade_ctx = ft.OpenCNTradeContext(host="127.0.0.1", port=11111)
        elif self.p.trade == self.USTrade:
            self.trade_ctx = ft.OpenUSTradeContext(host="127.0.0.1", port=11111)
        elif self.p.trade == self.FutureTrade:
            self.trade_ctx = ft.OpenFutureTradeContext(host="127.0.0.1", port=11111)
        elif self.p.trade == self.HKCCTrade:
            self.trade_ctx = ft.OpenHKCCTradeContext(host="127.0.0.1", port=11111)
        else:
            raise FutuStoreException('Unknown trade type')

    def start(self, data=None, broker=None):
        if data is None and broker is None:
            self._cash = None
            return

        if data is not None:
            pass
        elif broker is not None:
            self.broker = broker
            if self.p.trd_env == ft.TrdEnv.REAL:
                self.trade_ctx.unlock_trade(password=self.p.password)
            self.trd_ctx.set_handler(FutuTradeOrderHandler())
            self.trd_ctx.set_handler(FutuTradeDealHandler())
            self.trade_ctx.accinfo_query(trd_env=self.p.trd_env)

    def stop(self):
        self.trade_ctx.close()

    def order_create(self, order, stopside=None, takeside=None, **kwargs):
        price = format(
                order.created.price,
                '.%df' % order.data.contractdetails['displayPrecision'])
        qty = (abs(int(order.created.size)))
        if self.p.trade == FutuStore.HKTrade:
            code = order.data._dataname.upper() + '.HK'
            if order.exectype == bt.Order.Market:
                order_type = ft.OrderType.NORMAL
            elif order.exectype == bt.Order.Close:
                raise FutuNotSupported('NOT SUPPORTED YET')
            elif order.exectype == bt.Order.Limit:
                order_type = ft.OrderType.ABSOLUTE_LIMIT
            elif order.exectype == bt.Order.Stop:
                raise FutuNotSupported('NOT SUPPORTED YET')
            elif order.exectype == bt.Order.StopLimit:
                raise FutuNotSupported('NOT SUPPORTED YET')
            elif order.exectype == bt.Order.StopTrail:
                raise FutuNotSupported('NOT SUPPORTED YET')
            elif order.exectype == bt.Order.StopTrailLimit:
                raise FutuNotSupported('NOT SUPPORTED YET')
            elif order.exectype == bt.Order.Historical:
                raise FutuNotSupported('NOT SUPPORTED YET')

        elif self.p.trade == FutuStore.CNTrade:
            code = order.data._dataname.upper() + '.CN'
            raise FutuNotSupported('NOT SUPPORTED YET')
        elif self.p.trade == FutuStore.USTrade:
            code = order.data._dataname.upper() +'.US'
            raise FutuNotSupported('NOT SUPPORTED YET')
        else:
            raise FutuNotSupported('NOT SUPPORTED YET')

        trd_side = ft.TrdSide.BUY if order.isbuy() else ft.TrdSide.SELL



        okwargs = dict()
        okwargs['instrument'] = order.data._dataname
        okwargs['units'] = (
            abs(int(order.created.size)) if order.isbuy()
            else -abs(int(order.created.size)))  # negative for selling
        okwargs['type'] = self._ORDEREXECS[order.exectype]
        okwargs['replace'] = order.info.get("replace", None)

        if order.exectype != bt.Order.Market:
            okwargs['price'] = format(
                order.created.price,
                '.%df' % order.data.contractdetails['displayPrecision'])
            if order.valid is None:
                okwargs['timeInForce'] = 'GTC'  # good to cancel
            else:
                okwargs['timeInForce'] = 'GTD'  # good to date
                gtdtime = order.data.num2date(order.valid)
                okwargs['gtdTime'] = gtdtime.strftime(self._DATE_FORMAT)

        if order.exectype == bt.Order.StopLimit:
            if "replace" not in okwargs:
                raise Exception("replace param needed for StopLimit order")
            okwargs['price'] = format(
                order.plimit or order.price,
                '.%df' % order.data.contractdetails['displayPrecision'])

        if order.exectype == bt.Order.StopTrail:
            if "replace" not in okwargs:
                raise Exception("replace param needed for StopTrail order")
            trailamount = order.trailamount
            if order.trailpercent:
                trailamount = order.price * order.trailpercent
            okwargs['distance'] = format(
                trailamount,
                '.%df' % order.data.contractdetails['displayPrecision'])

        if stopside is not None:
            if stopside.exectype == bt.Order.StopTrail:
                trailamount = stopside.trailamount
                if stopside.trailpercent:
                    trailamount = order.price * stopside.trailpercent
                okwargs['trailingStopLossOnFill'] = v20.transaction.TrailingStopLossDetails(
                    distance=format(
                        trailamount,
                        '.%df' % order.data.contractdetails['displayPrecision']),
                    clientExtensions=v20.transaction.ClientExtensions(
                        id=self._oref_to_client_id(stopside.ref)
                    ).dict()
                ).dict()
            else:
                okwargs['stopLossOnFill'] = v20.transaction.StopLossDetails(
                    price=format(
                        stopside.price,
                        '.%df' % order.data.contractdetails['displayPrecision']),
                    clientExtensions=v20.transaction.ClientExtensions(
                        id=self._oref_to_client_id(stopside.ref)
                    ).dict()
                ).dict()

        if takeside is not None and takeside.price is not None:
            okwargs['takeProfitOnFill'] = v20.transaction.TakeProfitDetails(
                price=format(
                    takeside.price,
                    '.%df' % order.data.contractdetails['displayPrecision']),
                clientExtensions=v20.transaction.ClientExtensions(
                    id=self._oref_to_client_id(takeside.ref)
                ).dict()
            ).dict()

        # store backtrader order ref in client extensions
        okwargs['clientExtensions'] = v20.transaction.ClientExtensions(
            id=self._oref_to_client_id(order.ref)
        ).dict()

        okwargs.update(**kwargs)  # anything from the user
        self.q_ordercreate.put((order.ref, okwargs,))

        # notify orders of being submitted
        self.broker._submit(order.ref)
        if stopside is not None:  # don't make price on stopside mandatory
            self.broker._submit(stopside.ref)
        if takeside is not None and takeside.price is not None:
            self.broker._submit(takeside.ref)

        return order

    def order_cancel(self, order):
        pass

    def get_cash(self):
        return self._cash

    def get_value(self):
        return self._value

    def get_positions(self):
        pass

    def put_notification(self, msg, *args, **kwargs):
        self.notifs.append((msg, args, kwargs))

    def get_notifications(self):
        self.notifs.append(None)
        return [x for x in iter(self.notifs.popleft, None)]



