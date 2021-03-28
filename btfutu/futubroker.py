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

import collections
import json

from backtrader import BrokerBase, OrderBase, BuyOrder, SellOrder, CommInfoBase
from backtrader.commissions import CommInfo
from backtrader.position import Position
from backtrader.utils.py3 import queue, with_metaclass

from . import FutuStore


class FutuOrder(OrderBase):
    pass


class FutuCommInfo(CommInfoBase):
    pass


class MetaFutuBroker(BrokerBase.__class__):
    def __init__(cls, name, bases, dct):
        '''Class has already been created ... register'''
        # Initialize the class
        super(MetaFutuBroker, cls).__init__(name, bases, dct)
        FutuStore.BrokerCls = cls


class FutuBroker(with_metaclass(MetaFutuBroker, BrokerBase)):

    def __init__(self, **kwargs):
        super(FutuBroker, self).__init__()

        self.store = FutuStore(**kwargs)
        self.orders = collections.OrderedDict()
        self.notifs = collections.deque()
        self.opending = collections.defaultdict(list)
        self.brackets = dict()

        self.startingcash = self.cash = 0.0
        self.startingvalue = self.value = 0.0
        self.positions = collections.defaultdict(Position)

        self._ocos = dict()
        self._ocol = collections.defaultdict(list)
        self._pchildren = collections.defaultdict(collections.deque)

    def start(self):
        super(FutuBroker, self).start()
        self.store.start(broker=self)
        self.startingcash = self.cash = cash = self.store.get_cash()
        self.startingvalue = self.value = self.store.get_value()

        # comminfo = OandaV20CommInfo(
        #     leverage=self.o.get_leverage(),
        #     stocklike=False,
        #     commtype=CommInfoBase.COMM_FIXED)
        # # set as default comminfo
        # self.addcommissioninfo(comminfo, name=None)
        #
        # if self.p.use_positions:
        #     positions = self.o.get_positions()
        #     if positions is None:
        #         return
        #     for p in positions:
        #         size = float(p['long']['units']) + float(p['short']['units'])
        #         price = (
        #             float(p['long']['averagePrice']) if size > 0
        #             else float(p['short']['averagePrice']))
        #         self.positions[p['instrument']] = Position(size, price)

    def stop(self):
        super(FutuBroker, self).stop()
        self.store.stop()

    def getcash(self):
        # This call cannot block if no answer is available from oanda
        self.cash = cash = self.store.get_cash()
        return cash

    def getvalue(self, datas=None):
        self.value = self.store.get_value()
        return self.value

    def getposition(self, data, clone=True):
        # return self.o.getposition(data._dataname, clone=clone)
        pos = self.positions[data._dataname]
        if clone:
            pos = pos.clone()

        return pos

    def orderstatus(self, order):
        o = self.orders[order.ref]
        return o.status

    def buy(self, owner, data,
            size, price=None, plimit=None,
            exectype=None, valid=None, tradeid=0, oco=None,
            trailamount=None, trailpercent=None,
            parent=None, transmit=True,
            histnotify=False, _checksubmit=True,
            **kwargs):
        order = BuyOrder(owner=owner, data=data,
                         size=size, price=price, pricelimit=plimit,
                         exectype=exectype, valid=valid, tradeid=tradeid,
                         trailamount=trailamount, trailpercent=trailpercent,
                         parent=parent, transmit=transmit,
                         histnotify=histnotify)

        order.addinfo(**kwargs)
        self._ocoize(order, oco)
        return self.submit(order, check=_checksubmit)

    def sell(self, owner, data,
             size, price=None, plimit=None,
             exectype=None, valid=None, tradeid=0, oco=None,
             trailamount=None, trailpercent=None,
             parent=None, transmit=True,
             histnotify=False, _checksubmit=True,
             **kwargs):
        order = SellOrder(owner=owner, data=data,
                          size=size, price=price, pricelimit=plimit,
                          exectype=exectype, valid=valid, tradeid=tradeid,
                          trailamount=trailamount, trailpercent=trailpercent,
                          parent=parent, transmit=transmit,
                          histnotify=histnotify)

        order.addinfo(**kwargs)
        self._ocoize(order, oco)
        return self._transmit(order)

    def notify(self, order):
        self.notifs.append(order.clone())

    def _transmit(self, order):
        oref = order.ref
        pref = getattr(order.parent, 'ref', oref)  # parent ref or self

        if order.transmit:
            if oref != pref:  # children order
                # get pending orders, parent is needed, child may be None
                pending = self.opending.pop(pref)
                # ensure there are two items in list before unpacking
                while len(pending) < 2:
                    pending.append(None)
                parent, child = pending
                # set takeside and stopside
                if order.exectype in [order.StopTrail, order.Stop]:
                    stopside = order
                    takeside = child
                else:
                    takeside = order
                    stopside = child
                for o in parent, stopside, takeside:
                    if o is not None:
                        self.orders[o.ref] = o  # write them down
                self.brackets[pref] = [parent, stopside, takeside]
                self.o.order_create(parent, stopside, takeside)
                return takeside or stopside

            else:  # Parent order, which is being transmitted
                self.orders[order.ref] = order
                return self.store.order_create(order)

        # Not transmitting
        self.opending[pref].append(order)
        return order
