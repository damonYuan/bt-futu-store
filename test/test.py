from futu import *
from time import sleep


def set_futu_debug_model(on_off=True):
    common.set_debug_model(on_off)


set_futu_debug_model(True)


class TradeOrderTest(TradeOrderHandlerBase):
    """ order update push"""

    def on_recv_rsp(self, rsp_pb):
        ret, content = super(TradeOrderTest, self).on_recv_rsp(rsp_pb)

        if ret == RET_OK:
            print("* TradeOrderTest content=\n{}\n".format(content['order_type']))

        return ret, content


class TradeDealTest(TradeDealHandlerBase):
    def on_recv_rsp(self, rsp_pb):
        ret, content = super(TradeDealTest, self).on_recv_rsp(rsp_pb)

        if ret == RET_OK:
            print("* TradeDealTest content=\n{}\n".format(content))

        return ret, content


trd_ctx = OpenUSTradeContext(host='127.0.0.1', port=11111)
trd_ctx.set_handler(TradeOrderTest())
trd_ctx.set_handler(TradeDealTest())
# print(trd_ctx.unlock_trade(pwd_unlock))
# print(trd_ctx.get_acc_list())
# print(trd_ctx.accinfo_query(trd_env=TrdEnv.SIMULATE))
print(trd_ctx.place_order(price=1610.0, qty=1, code="US.GOOG", trd_side=TrdSide.BUY, trd_env=TrdEnv.SIMULATE))
# sleep(1000000)
trd_ctx.close()
