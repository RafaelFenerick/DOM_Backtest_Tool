# -*- coding: utf-8 -*-

import pandas as pd
from Execution_Time import *

def time2int(time, milisec=False, avoid_day=False):
    '''From time h:m:s,m (mili is optional) return int value.'''

    hour = ""
    minute = ""
    second = ""
    mili = ""
    trigger = 0
    if avoid_day:
        trigger = -1
    for c in time:
        if trigger == -1:
            if c == " ":
                trigger += 1
            continue
        if c == ":" or c == "." or c == ",":
            trigger += 1
            continue
        if trigger == 0:
            hour += c
        if trigger == 1:
            minute += c
        if trigger == 2:
            second += c
        if trigger == 3:
            mili += c
    if milisec:
        return int(hour)*60*60*1000 + int(minute)*60*1000 + int(second)*1000 + int(mili)
    else:
        return int(hour)*60*60 + int(minute)*60 + int(second)

def int2time(inteiro, level=0):
    '''Return time from int in given level
    0 -> milisecond
    1 -> second
    2 -> minute
    '''

    if level == 2:
        hour = inteiro / 60
        minute = inteiro - hour * 60
        hour_str = str(hour) if len(str(hour)) == 2 else "0" + str(hour)
        minute_str = str(minute) if len(str(minute)) == 2 else "0" + str(minute)
        return hour_str + ":" + minute_str

    elif level == 1:
        hour = inteiro / (60 * 60)

        minute = inteiro - (hour * 60 * 60)
        minute = minute / 60

        second = inteiro - (minute * 60) - (hour * 60 * 60)

        hour_str = str(hour) if len(str(hour)) == 2 else "0" + str(hour)
        minute_str = str(minute) if len(str(minute)) == 2 else "0" + str(minute)
        second_str = str(second) if len(str(second)) == 2 else "0" + str(second)
        return hour_str + ":" + minute_str + ":" + second_str

    else:
        hour = inteiro / (60 * 60 * 1000)

        minute = inteiro - (hour * 60 * 60 * 1000)
        minute = minute / (60 * 1000)

        second = inteiro - (minute * 60 * 1000) - (hour * 60 * 60 * 1000)
        second = second / 1000

        mili = inteiro - (second * 1000) - (minute * 60 * 1000) - (hour * 60 * 60 * 1000)

        hour_str = str(hour) if len(str(hour)) == 2 else "0" + str(hour)
        minute_str = str(minute) if len(str(minute)) == 2 else "0" + str(minute)
        second_str = str(second) if len(str(second)) == 2 else "0" + str(second)
        mili_str = str(mili)
        while len(mili_str) < 3:
            mili_str = "0" + mili_str
        return hour_str + ":" + minute_str + ":" + second_str + "." + mili_str

def ArrangeDealsData(string):
    '''De string no formato "day time,type,price,vomule"
     para int date, string type, float price, int volume.'''

    hour = ""
    minute = ""
    seconds = ""
    mili = ""

    type = ""
    price = ""
    volume = ""

    position = -1
    for l in string:
        # Pular dia
        if position == -1:
            if l == " ":
                position += 1
            continue

        # Encontrar divisões de dados
        # ":" e "." - time
        if l == ":" or l == "," or (position < 5 and l == "."):
            position += 1
            continue

        # Registrar valores
        if position == 0:
            hour += l
        elif position == 1:
            minute += l
        elif position == 2:
            seconds += l
        elif position == 3:
            mili += l
        elif position == 4:
            type += l
        elif position == 5:
            price += l
        elif position == 6:
            volume += l

    miliseconds = 60*60*1000*int(hour) + 60*1000*int(minute) + 1000*int(seconds) + int(mili)

    return miliseconds, type, float(price), int(volume)

def makedate(date):

    dia = ""
    mes = ""
    trigger = 0
    for c in date:
        if c == "#":
            trigger += 1
            continue
        if trigger == 0:
            dia += c
        else:
            mes += c
    if len(dia) == 1:
        dia = "0" + dia
    if len(mes) == 1:
        mes = "0" + mes

    return dia, mes

class Market():
    '''Classe responsável por atualização do DOM e comunicação entre player e book.'''

    def __init__(self, player, lot, divisor):
        self.deals = {}
        self.offers = {}
        self.deals_index = 0
        self.offers_index = 0
        self.player = player

        self.lot = lot
        self.divisor = divisor

    def Initiate(self, deals_file, offers_file):
        '''Criar lista de negócios e books e definir book inicial.'''

        self.deals = self.ReadDealsFile(deals_file)
        self.offers = self.ReaOffersFile(offers_file)

        if len(self.deals) == 0 or len(self.offers) == 0:
            print "ERROR 0001 - Length 0", len(self.deals), len(self.offers)
            return False

        self.current_book = DOM(*self.offers[self.offers_index])

        self.player.Update(self.current_book, self.GetOrders(self.current_book.orders), [])

        self.offers_index += 1

        return True

    def ReadDealsFile(self, file_name):
        '''Partindo de deals file retorna array com todas as informações sobre negócios do dia
        no formato [time, type, price, volume].'''

        path = "Historical_Data\\Deals\\Daily_Data\\"

        # Checar se separated day file já existe
        day_exists = True
        try:
            if ativo not in ["dol", "wdo", "ind", "win"]:
                print "ERROR 0011 - Ativo inválido", file_name
                return []

            open(path + file_name + "_" + ativo + ".txt", "r")

        except:
            day_exists = False

        # Ler file
        if day_exists:
            file = open(path + file_name + "_" + ativo + ".txt", "r")
            lines = file.readlines()
        else:
            file = open("Historical_Data\\Deals\\Data_" + ativo + ".txt", "r")
            lines = file.readlines()
            write_file = open(path + file_name + "_" + ativo + ".txt", "w")

        deals_array = []
        dia, mes = makedate(file_name)
        day = "2017." + mes + "." + dia
        for line in lines:
            # Checar se dia do negócio é dia analisado
            current_day = ""
            for char in line:
                if char == " ":
                    break
                current_day += char
            if current_day != day:
                continue

            # Escrever day file
            if not day_exists:
                write_file.write(line)

            # Não registrar info ticks
            if line[len(line) - 2] == ")":
                continue

            # Destacar matched orders
            if 'B' in line and 'S' in line:
                line = line.replace('B', 'M')

            time, type, price, volume = ArrangeDealsData(line)
            deals_array.append([time, type, price, volume])

        if not day_exists:
            write_file.close()

        return deals_array

    def ReaOffersFile(self, file_name):
        '''Partindo de offers file retorna array com todas as informações de books no dia
        no formato [deal_position, time, bid, ask, last, sell_book, buy_book].'''

        Init_Execution(10)

        data = pd.read_csv(file_name, sep=",", header=None)
        data = data.transpose()
        books_register = []

        for index in data:
            bid = data[index][35]
            ask = data[index][33]
            deal_position = data[index][0]
            last = self.deals[deal_position - 1][2]

            # Valor de last deal deve ser igual a bid ou ask
            if last != bid and last != ask:
                if self.deals[deal_position - 1][1] == 'B':
                    last = ask
                else:
                    last = bid

            sell_book = list(reversed(list(data[index][3:33])))
            buy_book = list(data[index][36:66])
            sup_array = [deal_position, index, time2int(data[index][1]), bid, ask, last, sell_book, buy_book]

            # Não está em leilão
            if ask > bid:
                books_register.append(sup_array)
            #books_register.append(sup_array)

        # Primeiro spread igual a 0.5
        while books_register[0][4] - books_register[0][3] != 0.5:
            books_register.pop(0)

        print "Offers File loaded:", End_Execution(10)

        return books_register

    def Update(self):
        '''Atualizar DOM e obter informações sobre ordens do player.'''

        if self.offers_index != len(self.offers) - 1:
            to_match_orders, to_modify_orders, to_open_orders = self.player.Decisions()
        else:
            to_match_orders, to_modify_orders, to_open_orders = [], [], []
        for orders in to_match_orders:
            if not self.current_book.MatchOrders(orders[0], orders[1]):
                print "ERROR 0022 - MatchOrders", orders
                return False
        for order in to_modify_orders:
            if not self.current_book.ModifyOrder(order):
                print "ERROR 0023 - ModifyOrder", order
                return False
        for order in to_open_orders:
            if not self.current_book.SendOrder(order):
                print "ERROR 0024 - SendOrder", order
                return False

        if not self.current_book.Update(*self.offers[self.offers_index]):
            print "ERROR 0025 - Update book", self.offers[self.offers_index]
            return False

        if not self.player.Update(self.current_book, self.GetOrders(self.current_book.orders), []):
            print "ERROR 0021 - Update player"
            return False

        self.offers_index += 1

        return True

    def GetOrders(self, orders):
        '''Passagem por valor e não por referência'''

        new_orders = []
        for order in orders:
            new_order = {}
            for key in order:
                new_order[key] = order[key]
            new_orders.append(new_order)

        return new_orders

    def EndDay(self):
        '''Checar se o dia chegou ao fim e garantir que qualquer posição aberta seja fechada.'''

        if self.offers_index == len(self.offers) - 1:
            if not self.current_book.CloseAllOrders():
                print "ERROR 0041 - CloseAllOrders"
            return False

        if self.offers_index == len(self.offers):
            return True

        return False

class ExpertPlayer(object):
    '''Classe responsável pelo controle das ordens e decisões do player.'''

    def __init__(self):
        # Variáveis referentes a registro do book e negócios
        self.sell_book = []
        self.buy_book = []
        self.bid = 0
        self.ask = 0
        self.last = 0
        self.booktime = 0
        self.deals = []

        # Variáveis referentes a ordens e posições
        self.previous_history_orders = []
        self.history_orders = []

    def Decisions(self):
        '''Função que deve ser sobreposta pela implementação de classe Player
        herdeira customizada.'''

        return [], [], []

    def Update(self, book, orders, deals):
        '''Obter status do book atual.'''

        self.sell_book = book.sell_book
        self.buy_book = book.buy_book
        self.book_index = book.index
        self.bid = book.bid
        self.ask = book.ask
        self.last = book.last
        self.booktime = book.time

        self.previous_history_orders = self.history_orders
        self.history_orders = orders

        self.deals = deals

        return True

    def GetOrder(self, number, previous=False):

        if previous:
            for order in self.previous_history_orders:
                if order["number"] == number:
                    return order
        else:
            for order in self.history_orders:
                if order["number"] == number:
                    return order

        return self.GetCleanDOMOrder()

    def GetClearToModifyOrder(self):
        '''Retorna uma ordem para modificação "limpa".'''

        return {"number": 0, "price": 0.0, "sl": 0.0, "tp": 0.0, "action": "none"}

    def GetCleanToOpenOrder(self):
        '''Retorna uma ordem para abertura "limpa".'''

        return {"number": 0, "type": "N", "entry": "none", "price": 0.0, "volume": 0, "sl": 0.0, "tp": 0.0}

    def GetCleanDOMOrder(self):
        '''Retorna uma ordem para abertura para DOM "limpa".'''

        return {"number": 0, "type": "N", "entry": "none", "price": 0.0, "volume": 0, "level": -1, "spot": -1, "status": "none", "tp": 0.0, "sl": 0.0}

class DOM():
    '''Classe responsável por armazenar valores do book atual e controlar o desenvolvimento
    de ordens a mercado e pendentes (ofertas) enviadas pelo player.'''

    def __init__(self, deal_position, book_index, time, bid, ask, last, sell_book, buy_book):
        '''Obter valores do primeiro book do dia'''

        self.deal_position = deal_position
        self.time = time
        self.bid = bid
        self.ask = ask
        self.last = last
        self.sell_book = sell_book
        self.buy_book = buy_book
        self.index = book_index

        self.orders = []

    def Update(self, deal_position, book_index, time, bid, ask, last, sell_book, buy_book):
        '''Atualizar book atual e gerenciar mudanças nas ordens do player.'''

        delta, diffs, bid, ask, sell_book, buy_book = self.GetBooksVariance(self.deal_position, self.ask, self.bid,
                                                                       deal_position, ask, bid, last, self.sell_book,
                                                                       self.buy_book, sell_book, buy_book)

        new_orders = []
        for order in self.orders:
            if order["status"] == "done" or order["status"] == "canceled":
                continue

            # --- Lidar com ordens não consumidas
            if order["status"] == "placed" and order["entry"] == "limit":

                # Checagem de potenciais erros
                if order["spot"] < 0:
                    print "Error - Update - Order spot < 0."
                if order["level"] < 10:
                    if order["type"] == "B":
                        total_offers = self.buy_book[order["level"]]
                    else:
                        total_offers = self.sell_book[order["level"]]
                    if order["spot"] > total_offers:
                        #print "Error - Update - Order spot > full size."
                        order["spot"] = total_offers
                if order["level"] < 10:
                    if order["type"] == "B":
                        if order["level"] != int((self.bid - order["price"])/market.divisor):
                            print "Error - Update - Order level is wrong."
                    if order["type"] == "S":
                        if order["level"] != int((order["price"] - self.ask) / market.divisor):
                            print "Error - Update - Order level is wrong."

                # Definir lado da ordem
                index = 3
                if order["type"] == "S":
                    index = 2

                # Variação do book a favor da ordem
                if (order["type"] == "B" and delta <= 0) or (order["type"] == "S" and delta >= 0):
                    # Ordem consumida
                    if order["level"] < abs(delta):
                        order["status"] = "filled"

                    # Ordem potencialmente consumida
                    elif order["level"] == abs(delta):

                        # Movimentação na fila por ordens removidas
                        if order["level"] < 10:
                            if diffs[index][0] < 0:
                                if index == 3:
                                    total_offers = self.buy_book[order["level"]]
                                else:
                                    total_offers = self.sell_book[order["level"]]
                                offers_to_remove = self.GetOffersToRemove(order["spot"], abs(diffs[index][0]), total_offers)

                                # Check
                                if offers_to_remove < 0:
                                    print "Error - Update - offers_to_remove > 0."

                                order["spot"] -= offers_to_remove
                        order["level"] -= abs(delta)

                        # Check
                        if diffs[index-2] < 0:
                            print "Error - Update - deals < 0."

                        # Movimentação na fila por negócios
                        if diffs[index-2] <= order["spot"]:
                            order["spot"] -= diffs[index-2]
                        else:
                            order["status"] = "filled"

                    # Ordem não consumida
                    else:
                        # Movimentação na fila por ordens removidas
                        if order["level"] < 10:
                            if diffs[index][order["level"] - abs(delta)] < 0:
                                if index == 3:
                                    total_offers = self.buy_book[order["level"]]
                                else:
                                    total_offers = self.sell_book[order["level"]]
                                offers_to_remove = self.GetOffersToRemove(order["spot"], abs(diffs[index][order["level"] - abs(delta)]),
                                                              total_offers)

                                # Check
                                if offers_to_remove < 0:
                                    print "Error - Update - offers_to_remove > 0."

                                order["spot"] -= offers_to_remove
                        order["level"] -= abs(delta)

                # Variação do book contra a ordem
                else:
                    # Movimentação na fila por negócios
                    if order["level"] == 0:

                        # Check
                        if diffs[index - 2] < 0:
                            print "Error - Update - deals < 0."

                        if diffs[index - 2] <= order["spot"]:
                            order["spot"] -= diffs[index - 2]
                        else:
                            order["status"] = "filled"

                    # Movimentação na fila por ordens removidas
                    if order["level"] < 10:
                        if diffs[index][order["level"]] < 0 and order["status"] != "filled":
                            if index == 3:
                                total_offers = self.buy_book[order["level"]]
                            else:
                                total_offers = self.sell_book[order["level"]]
                            offers_to_remove = self.GetOffersToRemove(order["spot"], abs(diffs[index][order["level"]]), total_offers)

                            # Check
                            if offers_to_remove < 0:
                                print "Error - Update - offers_to_remove > 0."

                            order["spot"] -= offers_to_remove
                    order["level"] += abs(delta)

                if order["level"] < 10:
                    if order["type"] == "B":
                        total_offers = buy_book[order["level"]]
                    else:
                        total_offers = sell_book[order["level"]]
                    if order["spot"] > total_offers and order["status"] != "filled":
                        #print "Error - Update - order spot > full size2."
                        order["spot"] = total_offers

            # --- Lidar com ordens consumidas (checar se sl e tp foram atingidos)
            executed_price = 0.0
            if order["status"] == "filled":
                if order["type"] == "B":
                    if order["tp"] <= self.last and order["tp"] != 0.0:
                        order["status"] = "done"
                    if order["sl"] >= self.last and order["sl"] != 0.0:
                        order["status"] = "done"
                    executed_price = self.bid
                if order["type"] == "S":
                    if order["tp"] >= self.last and order["tp"] != 0.0:
                        order["status"] = "done"
                    if order["sl"] <= self.last and order["sl"] != 0.0:
                        order["status"] = "done"
                    executed_price = self.ask

                # --- Gerar ordem de TP ou SL
                if order["status"] == "done":
                    new_order = self.GetCleanDOMOrder()
                    new_order["number"] = -1*order["number"]
                    new_order["type"] = "B"
                    if order["type"] == "B":
                        new_order["type"] = "S"
                    new_order["entry"] = "market"
                    new_order["price"] = executed_price
                    new_order["volume"] = order["volume"]
                    new_order["status"] = "done"
                    new_orders.append(new_order)

            # --- Lidar com ordens a mercado
            if (order["status"] == "placed" or order["status"] == "placedclose") and order["entry"] == "market":
                if order["type"] == "B":
                    order["price"] = self.ask
                if order["type"] == "S":
                    order["price"] = self.bid
                if order["status"] == "placed":
                    order["status"] = "filled"
                else:
                    order["status"] = "done"

        # Inserir ordens de SL e TP
        for order in new_orders:
            self.orders.append(order)

        # Atualizar book
        self.deal_position = deal_position
        self.time = time
        self.index = book_index
        self.bid = bid
        self.ask = ask
        self.last = last
        self.sell_book = sell_book
        self.buy_book = buy_book

        return True

    def GetOffersToRemove(self, current_spot, total_offers_removed, full_level_offers):
        '''Define, partindo do total de ofertas removidas em dado level, qual a proporção
        de ofertas removidas estaria, teoricamente, posicionada a frente da oferta do player
        na fila de ofertas.'''

        # Checar potenciais erros
        if current_spot > full_level_offers or total_offers_removed > full_level_offers:
            print "Error - GetOffersToRemove - current_spot or total_offers_removed > full_level_offers"

        spot_proportion = current_spot / float(full_level_offers)
        offers_to_remove = int(total_offers_removed * spot_proportion)

        # Aprimorar!!!
        if total_offers_removed > 20:
            while offers_to_remove % market.lot != 0:
                offers_to_remove -= 1
        else:
            while offers_to_remove % market.lot != 0:
                offers_to_remove += 1
            if offers_to_remove > total_offers_removed:
                offers_to_remove = total_offers_removed

        # Checar potenciais erros
        if offers_to_remove > current_spot:
            print "Error - GetOffersToRemove - offers_to_remove > current_spot"

        offers_not_to_remove = total_offers_removed - offers_to_remove
        if offers_not_to_remove > full_level_offers - current_spot:
            print "Error - GetOffersToRemove - offers_not_to_remove > full_level_offers - current_spot"

        return offers_to_remove

    def GetBooksVariance(self, previous_deal_position, previous_ask, previous_bid, deal_position, ask, bid, last,
                         previous_sell_book, previous_buy_book, sell_book, buy_book):
        '''Retorna variação entre books subsequentes e negócios realizados no interim (nos níveis mais
        extremos de preço - novos bid e ask).'''

        # Checar potenciais erros
        if previous_ask - previous_bid != market.divisor:
            print "Error - GetBooksVariance - Previous bid and ask does not match."

        if last != bid and last != ask:
            print "Error - GetBooksVariance - Last is different from ask and bid."

        # --- Make spread = 0.5
        spread = ask - bid - market.divisor

        if spread < 0:
            print "Error - GetBooksVariance - Ask is lower than bid."

        # Ajustar book para baixo
        if last == bid:
            ask -= spread
            for i in range(0, int(spread / market.divisor)):
                sell_book.pop(len(sell_book) - 1)
                sell_book.insert(0, 0)

        # Ajustar book para cima
        if last == ask:
            bid += spread
            for i in range(0, int(spread / market.divisor)):
                buy_book.pop(len(buy_book) - 1)
                buy_book.insert(0, 0)

        # --- Detectar variações no book
        delta = int((bid - previous_bid) / market.divisor)

        if previous_bid - bid != previous_ask - ask:
            print "Error - GetBooksVariance - Different deltas."

        # Variáveis para identificar excesso de variações entre books
        total_buy_diffs = 0
        total_sell_diffs = 0

        diffs_sell_book = []
        diffs_buy_book = []
        abs_delta = abs(delta)
        for i in range(0, len(buy_book) - abs_delta):
            new_i = i + abs_delta
            # Book para cima
            if delta >= 0:
                # Contar diferenças
                if previous_buy_book[i] != buy_book[new_i]:
                    total_buy_diffs += 1
                if previous_sell_book[new_i] != sell_book[i]:
                    total_sell_diffs += 1

                # Registrar valor das diferenças
                diffs_buy_book.append(buy_book[new_i] - previous_buy_book[i])
                diffs_sell_book.append(sell_book[i] - previous_sell_book[new_i])

            # Book para baixo
            else:
                # Contar diferenças
                if previous_buy_book[new_i] != buy_book[i]:
                    total_buy_diffs += 1
                if previous_sell_book[i] != sell_book[new_i]:
                    total_sell_diffs += 1

                # Registrar valor das diferenças
                diffs_buy_book.append(buy_book[i] - previous_buy_book[new_i])
                diffs_sell_book.append(sell_book[new_i] - previous_sell_book[i])

        if total_buy_diffs > 20 or total_sell_diffs > 20:
            # Muitas ocorrências devido a falhas do banco de dados
            # print "Error - getbooksvariation - n diffs in books."
            pass

        # --- Diferenciar ofertar removidas de negócios

        # Registrar volume de negócios de compra e venda
        sell_deals = 0
        buy_deals = 0
        deals = market.deals
        for i in range(previous_deal_position, deal_position):
            if delta >= 0:
                if deals[i][1] == "B" and deals[i][2] == ask:
                    buy_deals += deals[i][3]
                elif deals[i][1] == "S" and deals[i][2] == previous_bid:
                    sell_deals += deals[i][3]
            else:
                if deals[i][1] == "B" and deals[i][2] == previous_ask:
                    buy_deals += deals[i][3]
                elif deals[i][1] == "S" and deals[i][2] == bid:
                    sell_deals += deals[i][3]

        # Registro de negócios ocorridos
        diffs_sell_book[0] += sell_deals
        diffs_buy_book[0] += buy_deals

        # Checar potenciais erros
        for i in range(0, len(diffs_sell_book)):
            new_i = i + abs_delta
            # Book para cima ou estático
            if delta >= 0:
                value = diffs_sell_book[i]
                if value < 0 and abs(value) > previous_sell_book[new_i]:
                    print "Error - GetBooksVariance - Offers removed more than existed."
                value = diffs_buy_book[i]
                if value < 0 and abs(value) > previous_buy_book[i]:
                    print "Error - GetBooksVariance - Offers removed more than existed."
            # Book para baixo
            else:
                value = diffs_sell_book[i]
                if value < 0 and abs(value) > previous_sell_book[i]:
                    print "Error - GetBooksVariance - Offers removed more than existed."
                value = diffs_buy_book[i]
                if value < 0 and abs(value) > previous_buy_book[new_i]:
                    print "Error - GetBooksVariance - Offers removed more than existed."

        differences_array = [sell_deals, buy_deals, diffs_sell_book, diffs_buy_book]

        return delta, differences_array, bid, ask, sell_book, buy_book

    def IsPriceValid(self, price):
        '''Checar se valor de preço definido é válido.'''

        # Ordem a mercado
        if price == 0.0:
            return True

        int_divisor = market.divisor
        while int_divisor < 0:
            int_divisor *= 10
            price *= 10

        # Não Divisível por 5
        if int(price) % int_divisor != 0:
            return False

        # Mais de uma casa decimal
        if int(price * 10) / float(price) != 10:
            return False

        return True

    def MatchOrders(self, in_orders, out_orders):
        '''Casar ordens de lados opostos que não são intrinsecamente opostas, ex:
        Ordem limitada de venda funcionando como tp para uma ordem de compra.'''

        # Informações das ordens de "entrada"
        in_volume = 0
        in_side = "N"
        for order in in_orders:
            to_match_order = self.GetOrder(order["number"])
            if to_match_order["status"] != "filled":
                print "ERROR 0051 - MatchOrders - Orders status isn't filled."
                return False
            if in_side == "N":
                in_side = to_match_order["type"]
            else:
                if to_match_order["type"] != in_side:
                    print "ERROR 0052 - MatchOrders - Orders side diverge."
                    return False
            in_volume += to_match_order["volume"]
            to_match_order["status"] = "done"

        # Informações das ordens de "saída"
        out_volume = 0
        out_side = "N"
        for order in out_orders:
            to_match_order = self.GetOrder(order["number"])
            if to_match_order["status"] != "filled":
                print "ERROR 0053 - MatchOrders - Orders status isn't filled."
                return False
            if out_side == "N":
                out_side = to_match_order["type"]
            else:
                if to_match_order["type"] != out_side:
                    print "ERROR 0054 - Matchorders - Orders side diverge."
                    return False
            out_volume += to_match_order["volume"]
            to_match_order["status"] = "done"

        if in_side == out_side:
            print "ERROR 0055 - MatchOrders - Orders in and out sides are equal."
            return False

        if in_volume != out_volume:
            print "ERROR 0056 - MatchOrders - Orders in and out volumes diverge."
            return False

        return True

    def ModifyOrder(self, order):
        '''Modificar ordem previamente enviada.'''

        # Deletar ordens ainda não consumidas
        if order["action"] == "delete":
            to_modify_order = self.GetOrder(order["number"])
            if order["number"] == 0:
                print "ERROR 0061 - modifyorder - No order with given number."
                return False
            if to_modify_order["status"] != "placed":
                print "ERROR 0062 - modifyorder - Order status isn't placed."
                return False
            else:
                to_modify_order["status"] = "canceled"

        # Fechar ordens já consumidas
        elif order["action"] == "close":
            to_modify_order = self.GetOrder(order["number"])
            if order["number"] == 0:
                print "ERROR 0063 - modifyorder - No order with given number."
                return False
            if to_modify_order["status"] != "filled":
                print "ERROR 0064 - modifyorder - Order status isn't filed."
                return False
            else:
                to_modify_order["status"] = "done"

                # Enviar ordem de fechamento
                new_order = self.GetCleanPlayerOrder()
                new_order["number"] = -1*to_modify_order["number"]
                new_order["type"] = "B"
                if to_modify_order["type"] == "B":
                    new_order["type"] = "S"
                new_order["entry"] = "market"
                new_order["volume"] = to_modify_order["volume"]
                if not self.SendOrder(new_order):
                    return False

        # Alterar valores de sl e tp
        elif order["action"] == "outs":
            to_modify_order = self.GetOrder(order["number"])
            if order["number"] == 0:
                print "ERROR 0065 - modifyorder - No order with given number."
                return False
            if to_modify_order["status"] != "placed" and to_modify_order["status"] != "filled":
                print "ERROR 0066 - modifyorder - Order status isn't placed or filled."
                return False
            else:
                if to_modify_order["type"] == "B":
                    if order["tp"] < order["sl"]:
                        print "ERROR 0067a - modifyorder - TP and SL values incorrect."
                        return False
                    if order["tp"] <= self.ask:
                        print "ERROR 0068a - modifyorder - TP incorrect."
                        return False
                    if order["sl"] >= self.bid:
                        print "ERROR 0069a - modifyorder - SL incorrect."
                        return False
                else:
                    if order["tp"] > order["sl"]:
                        print "ERROR 0067b - modifyorder - TP and SL values incorrect."
                        return False
                    if order["tp"] >= self.bid:
                        print "ERROR 0068b - modifyorder - TP incorrect."
                        return False
                    if order["sl"] <= self.ask:
                        print "ERROR 0069b - modifyorder - SL incorrect."
                        return False

                to_modify_order["tp"] = order["tp"]
                to_modify_order["sl"] = order["sl"]

        # Mudar preço de ordem ainda não consumida (deletar e colocar nova ordem)
        else:
            pass

        return True

    def SendOrder(self, order):
        '''Enviar nova ordem.'''

        if self.GetOrder(order["number"])["number"] != 0:
            print "ERROR 0071 - SendOrder - Order with given number already exists", order["number"]
            return False

        # Informações sobre a ordem
        new_order = self.GetCleanDOMOrder()
        new_order["number"] = order["number"]
        new_order["type"] = order["type"]
        new_order["entry"] = order["entry"]
        new_order["price"] = order["price"]
        new_order["volume"] = order["volume"]
        new_order["tp"] = order["tp"]
        new_order["sl"] = order["sl"]
        if new_order["type"] == "B":
            if new_order["tp"] < new_order["sl"] and new_order["tp"] != 0.0 and new_order["sl"] != 0.0:
                print "ERROR 0072 - sendorder - TP and SL values incorrect."
                return False
        else:
            if new_order["tp"] > new_order["sl"] and new_order["tp"] != 0.0 and new_order["sl"] != 0.0:
                print "ERROR 0073 - sendorder - TP and SL values incorrect."
                return False

        # Status da ordem
        if order["number"] > 0:
            new_order["status"] = "placed"
        else:
            new_order["status"] = "placedclose"
            if order["entry"] == "limit":
                print "ERROR 0074 - sendorder - Placedclose order can't have limit entry."
                return False

        # Checar validade do preço
        if not self.IsPriceValid(order["price"]):
            print "Order Price not valid."
            new_order["status"] = "canceled"

        # Definir level e spot da ordem
        if order["entry"] == "limit":
            if order["type"] == "B":
                new_order["level"] = int((self.bid - order["price"]) / market.divisor)
                if new_order["level"] < 0:
                    new_order["status"] = "canceled"
                    print "Order Price level error."
                else:
                    new_order["spot"] = self.buy_book[new_order["level"]]
            if order["type"] == "S":
                new_order["level"] = int((order["price"] - self.ask) / market.divisor)
                if new_order["level"] < 0:
                    new_order["status"] = "canceled"
                    print "Order Price level error."
                else:
                    new_order["spot"] = self.sell_book[new_order["level"]]

        # Inserir ordem
        self.orders.append(new_order)

        return True

    def CloseAllOrders(self):
        '''Fechar todas as ordens ainda abertas.'''

        for order in self.orders:
            # Deletar ordens não consumidas
            if order["status"] == "placed":
                modified_order = self.GetCleanToModifyOrder()
                modified_order["number"] = order["number"]
                modified_order["action"] = "delete"
                if not self.ModifyOrder(modified_order):
                    print "ERROR 0031 - ModifyOrder", modified_order
                    return False

            # Fechar ordens consumidas
            if order["status"] == "filled":
                modified_order = self.GetCleanToModifyOrder()
                modified_order["number"] = order["number"]
                modified_order["action"] = "close"
                if not self.ModifyOrder(modified_order):
                    print "ERROR 0032 - ModifyOrder", modified_order
                    return False

        return True

    def GetOrder(self, number):
        '''Encontrar ordem com dado número no histórico.'''

        for order in self.orders:
            if order["number"] == number:
                return order

        return self.GetCleanDOMOrder()

    def GetCleanToModifyOrder(self):
        '''Retorna uma ordem para modificação "limpa".'''

        return {"number": 0, "price": 0.0, "sl": 0.0, "tp": 0.0, "action": "none"}

    def GetCleanPlayerOrder(self):
        '''Retorna uma ordem para abertura "limpa".'''

        return {"number": 0, "type": "N", "entry": "none", "price": 0.0, "volume": 0, "sl": 0.0, "tp": 0.0}

    def GetCleanDOMOrder(self):
        '''Retorna uma ordem para abertura para DOM "limpa".'''

        return {"number": 0, "type": "N", "entry": "none", "price": 0.0, "volume": 0, "level": -1, "spot": -1, "status": "none", "tp": 0.0, "sl": 0.0}

def RunSimulator(date, current_ativo, lot, divisor, player):
    '''Managment of market development and player's situation.'''

    global ativo, market
    ativo = current_ativo
    market = Market(player, lot, divisor)

    deals_file = date
    offers_file = "Historical_Data\\Books\\" + date + "_" + ativo + ".txt"
    if not market.Initiate(deals_file, offers_file):
        return False

    print "Books amount:", len(market.offers)

    tempo_executado = 0.0
    tempo_restante = 0.0

    Init_Execution(11)

    while not market.EndDay():

        ###
        books_done = market.offers_index
        if books_done != 0:
            tempo_restante = (len(market.offers) - books_done)*((tempo_executado*1000)/float(books_done))
        if books_done % int(len(market.offers)/10) == 0:
            print "Tempo Restante: " + int2time(int(tempo_restante)) + " (" + str(books_done) + "/" + str(len(market.offers)) + ")"
        ###

        Init_Execution(12)
        if not market.Update():
            return False
        tempo_executado += End_Execution(12, printt=False)

    print "Tempo Total de Execução:", End_Execution(11)

    player.DisplayResult()

    del player
    del market.current_book
    del market

    return True