# -*- coding: utf-8 -*-
from Execution_Time import *
from Market_Structure import *

class Player(ExpertPlayer):

    def __init__(self):

        super(Player, self).__init__()

        self.volume = 5
        self.order_price = 0.0
        self.number = 1

    def CheckModify(self):
        '''Checar se alguma ordem deve ser modificada.'''

        # Obter status da ordem atual
        current_order_status = "none"
        for order in self.history_orders:
            if order["number"] == self.number - 1:
                current_order_status = order["status"]

        # Deletar ordem placed depois de determinado tempo
        if current_order_status == "placed":
            if self.booktime - self.current_order_time > 60*1:
                order = self.GetClearToModifyOrder()
                order["number"] = self.number - 1
                order["action"] = "delete"
                return [order]

        # Fechar ordem filled depois de determinado tempo
        if current_order_status == "filled":
            if self.booktime - self.current_order_time > 60*15:
                order = self.GetClearToModifyOrder()
                order["number"] = self.number - 1
                order["action"] = "close"
                return [order]

        return []

    def CheckOpen(self):
        '''Checar se nova ordem deve ser aberta.'''

        # Verificar se não há nenhuma ordem já posicionada
        is_placed_order = False
        for order in self.history_orders:
            if order["status"] == "placed":
                is_placed_order = True
                break
        if self.position["status"] != "none" or is_placed_order:
            return []

        # Entrar com ordem comprada
        result = 1
        self.order_price = self.bid - 0.5

        new_order = self.GetCleanToOpenOrder()

        # Preencher ordem de compra
        if result > 0:
            new_order["number"] = self.number
            new_order["type"] = "B"
            new_order["entry"] = "limit"
            new_order["price"] = self.order_price
            new_order["volume"] = self.volume
            new_order["tp"] = self.order_price + 3.0
            new_order["sl"] = self.order_price - 3.0
            self.current_order_time = self.booktime
            self.number += 1
            return [new_order]

        # Preencher ordem de venda
        if result < 0:
            new_order["number"] = self.number
            new_order["type"] = "S"
            new_order["entry"] = "limit"
            new_order["price"] = self.order_price
            new_order["volume"] = self.volume
            new_order["tp"] = self.order_price - 3.0
            new_order["sl"] = self.order_price + 3.0
            self.current_order_time = self.booktime
            self.number += 1
            return [new_order]

        return []

    def Decisions(self):
        '''Retorna decições tomadas pelo player sobre
        modificação e abertura de ordens.'''

        # --- Atualizar tempo da ordem quando consumida
        # Obter status anterior
        current_order_status = "none"
        for order in self.previous_history_orders:
            if order["number"] == self.number - 1:
                current_order_status = order["status"]

        # Obter novo status
        for order in self.history_orders:
            if order["number"] == self.number - 1:
                if current_order_status == "placed" and order["status"] == "filled":
                    # Atualizar tempo
                    self.current_order_time = self.booktime

        return self.CheckModify(), self.CheckOpen()

    def DisplayProduce(self):
        '''Apresentar resultado das operações no dia.'''

        # Custo por abertura e fechamento de ordem (por contrato)
        single_cost = 7.5

        produce = 0.0
        cost = 0.0
        buy_orders = 0
        sell_orders = 0
        for order in self.history_orders:
            if order["status"] == "done":
                if order["type"] == "B":
                    produce -= order["price"]*order["volume"]
                    cost += order["volume"]*single_cost
                    buy_orders += 1
                if order["type"] == "S":
                    produce += order["price"]*order["volume"]
                    cost += order["volume"] * single_cost
                    sell_orders += 1

        # Cada tick no DOL corresponde a R$50,00 por contrato
        produce *= 50

        # Checagem de erros
        if buy_orders != sell_orders:
            print "Error - DisplayProduce - different amount of orders"

        print "Total de Operações:", buy_orders
        print "Resultado Bruto:   ", round(produce, 2)
        print "Resultado Liquido: ", round(produce - cost, 2)

Init_Execution(0)
takeprofit = Player()
RunBacktest("5_10_2017", takeprofit)
End_Execution(0)
