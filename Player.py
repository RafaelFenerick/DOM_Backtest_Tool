# -*- coding: utf-8 -*-

from Market_Structure import *

class Player(ExpertPlayer):

    '''Compras e vendas alternadas com sl e tp equidistantes'''

    def __init__(self, volume):

        super(Player, self).__init__()

        self.volume = volume
        self.number = 1
        self.trade_side = 1

        self.previous_order = self.GetCleanToOpenOrder()
        self.current_order = self.GetCleanToOpenOrder()

    def CheckMatch(self):

        return []

    def CheckModify(self):

        ## Deletar ordens enviadas e não consumidas em mais de 1 minuto
        if self.current_order["status"] == "placed":
            if self.booktime - self.current_order_time > 60*1:
                order = self.GetClearToModifyOrder()
                order["number"] = self.current_order["number"]
                order["action"] = "delete"
                return [order]

        return []

    def CheckOpen(self):

        # Checar se já existe alguma ordem enviada
        if self.current_order["status"] == "placed" or self.current_order["status"] == "filled":
            return []

        # Alternar compra e venda
        result = 1 if self.trade_side % 2 == 1 else -1
        self.trade_side += 1

        new_order = self.GetCleanToOpenOrder()
        if result > 0:
            new_order["number"] = self.number
            new_order["type"] = "B"
            new_order["entry"] = "limit"
            new_order["price"] = self.bid
            new_order["volume"] = self.volume
            new_order["tp"] = self.bid + 2.5
            new_order["sl"] = self.bid - 2.0
            self.current_order_time = self.booktime
            self.number += 1

            return [new_order]

        if result < 0:
            new_order["number"] = self.number
            new_order["type"] = "S"
            new_order["entry"] = "limit"
            new_order["price"] = self.ask
            new_order["volume"] = self.volume
            new_order["tp"] = self.ask - 2.5
            new_order["sl"] = self.ask + 2.0
            self.current_order_time = self.booktime
            self.number += 1

            return [new_order]

        return []

    def Decisions(self):

        # Status atual
        previous_order_number = 0
        for order in self.previous_history_orders:
            if order["status"] != "done" and order["status"] != "canceled":
                previous_order_number = order["number"]

        current_order_number = 0
        for order in self.history_orders:
            if order["status"] != "done" and order["status"] != "canceled":
                current_order_number = order["number"]

        self.previous_order = self.GetOrder(previous_order_number, previous=True)
        self.current_order = self.GetOrder(current_order_number)

        return self.CheckMatch(), self.CheckModify(), self.CheckOpen()

    def DisplayResult(self):

        multiplicador = 50

        # Obter posições
        positions = {}
        for order in self.history_orders:
            if order["status"] == "done":
                if abs(order["number"]) not in positions:
                    positions[abs(order["number"])] = []
                positions[abs(order["number"])].append(order)

        ### Checar possíveis erros
        for key in positions:
            position = positions[key]
            if len(position) != 2:
                print "Position length error", position

            if position[0]["type"] == position[1]["type"]:
                print "Order types error"
        ###

        ### Cálculo de Retorno
        gain = 0
        loss = 0
        gain_op = 0
        loss_op = 0
        positions_return = []
        for key in positions:
            position = positions[key]
            if position[0]["type"] == "B":
                sell = position[1]["price"]*position[1]["volume"]
                buy = position[0]["price"]*position[0]["volume"]
            else:
                sell = position[0]["price"] * position[0]["volume"]
                buy = position[1]["price"] * position[1]["volume"]

            return_ = multiplicador * (sell - buy)
            positions_return.append(return_)

            if return_ >= 0:
                gain += return_
                gain_op += 1
            else:
                loss += -return_
                loss_op += 1
        ###

        ### Cálculo de Retorno 2 para checagem de erro
        total = 0.0
        buy_orders = 0
        sell_orders = 0
        for order in self.history_orders:
            if order["status"] == "done":
                if order["type"] == "B":
                    total -= order["price"] * order["volume"] * multiplicador
                    buy_orders += 1
                if order["type"] == "S":
                    total += order["price"] * order["volume"] * multiplicador
                    sell_orders += 1
        ###

        if total != sum(positions_return):
            print "########## Erro de resultado 1"

        if buy_orders != len(positions_return):
            print "########## Erro de resultado 2"

        if buy_orders != sell_orders:
            print "########## Erro de resultado 3"

        if buy_orders != gain_op + loss_op:
            print "########## Erro de resultado 4"

        if total != gain - loss:
            print "########## Erro de resultado 5"

        print "\n"
        print "Total de Operações:            ", gain_op + loss_op
        print "Total de operações positivas:  ", gain_op
        print "Total de operações negativas:  ", loss_op
        if gain_op + loss != 0:
            print "Taxa de Acerto:                ", round(gain_op / float(gain_op + loss_op), 2)
        print "Lucro:                         ", gain
        print "Perda:                         ", loss
        if loss != 0:
            print "Fator de Lucro:                ", round(gain / float(loss), 2)
        print "Saldo Final (sem custos):      ", round((gain - loss), 2)
        print "Saldo Final (sem corretagem):  ", round((gain - loss) - self.volume * 2 * custo * (gain_op + loss_op), 2)
        print "Saldo Final (com custos):      ", round((gain - loss) - self.volume * 2 * (custo + corretagem) * (gain_op + loss_op), 2)

        global a, b, c, d

        a += gain_op
        b += loss_op
        c += gain
        d += loss

        file = open("General_Player_Operations_Result.txt", "w")
        for order in self.history_orders:
            file.write(str(order["number"]))
            for key in order:
                if key != "number":
                    file.write("," + str(order[key]))
            file.write("\n")
        file.close()

days = ["5#10"]
ativo = "dol"

Init_Execution(0)

a = 0
b = 0
c = 0
d = 0

corretagem = 5
custo = 2.5
volume = 5

for day in days:
    print day
    general_player = Player(5)
    if not RunSimulator(day, ativo, 5, 0.5, general_player):
        print "RunSimulator ERROR!!!"
        del general_player
        break
    del general_player

    print "\n"

print "Total de Operações:            ", a + b
print "Total de operações positivas:  ", a
print "Total de operações negativas:  ", b
if a + b != 0:
    print "Taxa de Acerto:                ", round(a / float(a + b), 2)
print "Lucro:                         ", c
print "Perda:                         ", d
if d != 0:
    print "Fator de Lucro:                ", round(c / float(d), 2)
print "Saldo Final (sem custos):      ", round((c-d), 2)
print "Saldo Final (sem corretagem):  ", round((c-d) - 2 * volume * custo * (a + b), 2)
print "Saldo Final (com custos):      ", round((c-d) - 2 * volume * (custo + corretagem) * (a + b), 2)

End_Execution(0)