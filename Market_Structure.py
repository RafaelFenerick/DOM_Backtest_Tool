# -*- coding: utf-8 -*-
import pandas as pd

def DatetimeToSecond(string):
    '''Converter datetime (hour:minute:second) para inteiro em segundos.'''

    # hour, minute, second
    multplier_values = [60*60, 60, 1]
    sup_string = ""
    position = 0
    seconds = 0
    for char in string:
        if char == ":":
            seconds += multplier_values[position]*int(sup_string)
            sup_string = ""
            position += 1
        else:
            sup_string += char

    seconds += multplier_values[position] * int(sup_string)

    return seconds

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

class Market():
    '''Classe responsável por atualização do DOM e comunicação entre player e book.'''

    def __init__(self, player):
        self.deals = {}
        self.offers = {}
        self.deals_index = 0
        self.offers_index = 0
        self.player = player

    def Initiate(self, day):
        '''Criar lista de negócios e books e definir book inicial.'''

        self.deals = self.ReadDealsFile(day)
        self.offers = self.ReaOffersFile(day, self.deals)
        self.current_book = DOM(self.deals, *self.offers[self.offers_index])
        self.offers_index += 1

    def ReadDealsFile(self, day):
        '''Partindo de deals file retorna array com todas as informações sobre negócios do dia
        no formato [time, type, price, volume].'''

        path = "Historical_Data\\"

        file = open(path + day + " DOLX17 - DEALS.txt", "r")
        lines = file.readlines()
        file.close()

        deals_array = []
        for line in lines:
            # Não registrar info ticks
            if line[len(line) - 2] == ")":
                continue

            # Destacar matched orders
            if 'B' in line and 'S' in line:
                line = line.replace('B', 'M')

            time, type, price, volume = ArrangeDealsData(line)
            deals_array.append([time, type, price, volume])

        return deals_array

    def ReaOffersFile(self, day, deals):
        '''Partindo de offers file retorna array com todas as informações de books no dia
        no formato [deal_position, time, bid, ask, last, sell_book, buy_book].'''

        path = "Historical_Data\\"

        data = pd.read_csv(path + day + " DOLX17 - BOOKS.txt", sep=",", header=None)
        data = data.transpose()
        books_register = []

        for index in data:
            bid = data[index][35]
            ask = data[index][33]
            deal_position = data[index][0]
            last = deals[deal_position - 1][2]

            # Valor de last deal dever ser igual a bid ou ask
            if last != bid and last != ask:
                if deals[deal_position - 1][1] == 'B':
                    last = ask
                else:
                    last = bid

            sell_book = list(reversed(list(data[index][3:33])))
            buy_book = list(data[index][36:66])
            sup_array = [deal_position, DatetimeToSecond(data[index][1]), bid, ask, last, sell_book, buy_book]

            # Não está em leilão
            if ask > bid:
                books_register.append(sup_array)

        # Primeiro spread igual a 0.5
        while books_register[0][3] - books_register[0][2] != 0.5:
            books_register.pop(0)

        return books_register

    def ManagePlayersDecisions(self):
        '''Checar modificações e novas ordens pelo player e enviá-las ao DOM.'''

        self.player.UpdateBook(self.current_book)
        to_modify_orders, to_open_orders = self.player.Decisions()
        for order in to_modify_orders:
            self.current_book.ModifyOrder(order)
        for order in to_open_orders:
            self.current_book.SendOrder(order)

    def UpdateDOM(self):
        '''Atualizar DOM e obter informações sobre ordens do player.'''

        self.current_book.Update(*self.offers[self.offers_index])
        current_position = self.GetPosition(self.current_book.orders)
        self.player.UpdateSituation(self.current_book.orders, current_position)
        self.offers_index += 1

    def GetPosition(self, orders):
        '''Obter atual posição do player, com determinado lado (long/short) e volume
        (netting).'''

        position = self.GetCleanPosition()
        volume_total = 0
        for order in orders:
            if order["status"] == "filled" or order["status"] == "done":
                if order["type"] == "B":
                    volume_total += order["volume"]
                if order["type"] == "S":
                    volume_total -= order["volume"]

        position["volume"] = abs(volume_total)
        if volume_total > 0:
            position["type"] = "B"
            position["status"] = "in"
        if volume_total < 0:
            position["type"] = "S"
            position["status"] = "in"

        return position

    def EndDay(self):
        '''Checar se o dia chegou ao fim e garantir que qualquer posição aberta seja fechada.'''

        # Fechar todas as posições antes do final do dia
        if self.offers_index == len(self.offers) - 1:
            self.current_book.CloseAllOrders()
            return False

        if self.offers_index == len(self.offers):
            return True

        return False

    def GetCleanPosition(self):
        '''Retorna uma posição "limpa".'''

        return {"type": "N", "status": "none", "volume": 0}

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
        self.previous_position = self.GetCleanPosition()
        self.position = self.GetCleanPosition()

    def Decisions(self):
        '''Função que deve ser sobreposta pela implementação de classe Player
        herdeira customizada. Responsável pela tomada de decisões'''

        return [], []

    def DisplayProduce(self):
        '''Função que deve ser sobreposta pela implementação de classe Player
        herdeira customizada. Responsável pela exibição dos resultados.'''

        return

    def UpdateBook(self, book):
        '''Obter status do book atual.'''

        self.sell_book = book.sell_book
        self.buy_book = book.buy_book
        self.bid = book.bid
        self.ask = book.ask
        self.last = book.last
        self.booktime = book.time

    def UpdateDeals(self, deals):
        '''Obter todos os negócios realizados no dia até o presente momento.'''

        self.deals = deals

    def UpdateSituation(self, orders, position):
        '''Obter histórico de ordens e atual posição do player.'''

        self.previous_history_orders = self.history_orders
        self.history_orders = orders
        self.previous_position = self.position
        self.position = position

    def GetClearToModifyOrder(self):
        '''Retorna uma ordem para modificação "limpa".'''

        return {"number": 0, "price": 0.0, "sl": 0.0, "tp": 0.0, "action": "none"}

    def GetCleanToOpenOrder(self):
        '''Retorna uma ordem para abertura "limpa".'''

        return {"number": 0, "type": "N", "entry": "none", "price": 0.0, "volume": 0, "sl": 0.0, "tp": 0.0}

    def GetCleanPosition(self):
        '''Retorna uma posição "limpa".'''

        return {"type": "N", "status": "none", "volume": 0}

class DOM():
    '''Classe responsável por armazenar valores do book atual e controlar o desenvolvimento
    de ordens a mercado e pendentes (ofertas) enviadas pelo player.'''

    def __init__(self, deals, deal_position, time, bid, ask, last, sell_book, buy_book):
        '''Obter valores do primeiro book do dia'''

        self.deals = deals
        self.deal_position = deal_position
        self.time = time
        self.bid = bid
        self.ask = ask
        self.last = last
        self.sell_book = sell_book
        self.buy_book = buy_book
        self.orders = []

    def Update(self, deal_position, time, bid, ask, last, sell_book, buy_book):
        '''Atualizar book atual e gerenciar mudanças nas ordens do player.'''

        delta, diffs, bid, ask, sell_book, buy_book = self.GetBooksVariance(self.deal_position, self.ask, self.bid,
                                                                       deal_position, ask, bid, last, self.sell_book,
                                                                       self.buy_book, sell_book, buy_book, self.deals)

        new_orders = []
        for order in self.orders:
            if order["status"] == "done" or order["status"] == "canceled":
                continue

            # --- Lidar com ordens não consumidas
            if order["status"] == "placed" and order["entry"] == "limit":

                # Checagem de potenciais erros
                if order["spot"] < 0:
                    print "Error - Update - Order spot < 0."
                if order["type"] == "B":
                    total_offers = self.buy_book[order["level"]]
                else:
                    total_offers = self.sell_book[order["level"]]
                if order["spot"] > total_offers:
                    print "Error - Update - Order spot > full size."
                if order["type"] == "B":
                    if order["level"] != int((self.bid - order["price"])/0.5):
                        print "Error - Update - Order level is wrong."
                if order["type"] == "S":
                    if order["level"] != int((order["price"] - self.ask) / 0.5):
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

                if order["type"] == "B":
                    total_offers = buy_book[order["level"]]
                else:
                    total_offers = sell_book[order["level"]]
                if order["spot"] > total_offers and order["status"] != "filled":
                    print "Error - Update - order spot > full size2."

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
        self.bid = bid
        self.ask = ask
        self.last = last
        self.sell_book = sell_book
        self.buy_book = buy_book

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
            while offers_to_remove % 5 != 0:
                offers_to_remove -= 1
        else:
            while offers_to_remove % 5 != 0:
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
                         previous_sell_book, previous_buy_book, sell_book, buy_book, deals):
        '''Retorna variação entre books subsequentes e negócios realizados no interim (nos níveis mais
        extremos de preço - novos bid e ask).'''

        # Checar potenciais erros
        if previous_ask - previous_bid != 0.5:
            print "Error - GetBooksVariance - Previous bid and ask does not match."

        if last != bid and last != ask:
            print "Error - GetBooksVariance - Last is different from ask and bid."

        # --- Make spread = 0.5
        spread = ask - bid - 0.5

        if spread < 0:
            print "Error - GetBooksVariance - Ask is lower than bid."

        # Ajustar book para baixo
        if last == bid:
            ask -= spread
            for i in range(0, int(spread / 0.5)):
                sell_book.pop(len(sell_book) - 1)
                sell_book.insert(0, 0)

        # Ajustar book para cima
        if last == ask:
            bid += spread
            for i in range(0, int(spread / 0.5)):
                buy_book.pop(len(buy_book) - 1)
                buy_book.insert(0, 0)

        # --- Detectar variações no book
        delta = int((bid - previous_bid) / 0.5)

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

        # Não Divisível por 5
        if int(price * 10) % 5 != 0:
            return False

        # Mais de uma casa decimal
        if int(price * 10) / float(price) != 10:
            return False

        return True

    def ModifyOrder(self, order):
        '''Modificar ordem previamente enviada.'''

        # Deletar ordens ainda não consumidas
        if order["action"] == "delete":
            to_modify_order = self.GetHistoricalOrder(order["number"])
            if order["number"] == 0:
                print "Error - modifyorder - No order with given number."
                return
            if to_modify_order["status"] != "placed":
                print "Error - modifyorder - Order status isn't placed."
            else:
                to_modify_order["status"] = "canceled"

        # Fechar ordens já consumidas
        elif order["action"] == "close":
            to_modify_order = self.GetHistoricalOrder(order["number"])
            if order["number"] == 0:
                print "Error - modifyorder - No order with given number."
                return
            if to_modify_order["status"] != "filled":
                print "Error - modifyorder - Order status isn't filed."
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
                self.SendOrder(new_order)

        # Alterar valores de sl e tp
        elif order["action"] == "outs":
            to_modify_order = self.GetHistoricalOrder(order["number"])
            if order["number"] == 0:
                print "Error - modifyorder - No order with given number."
                return
            if to_modify_order["status"] != "placed" and to_modify_order["status"] != "filled":
                print "Error - modifyorder - Order status isn't placed or filled."
            else:
                if to_modify_order["type"] == "B":
                    if order["tp"] < order["sl"]:
                        print "Error - modifyorder - TP and SL values incorrect."
                    if order["tp"] <= self.ask:
                        print "Error - modifyorder - TP incorrect."
                        return
                    if order["sl"] >= self.bid:
                        print "Error - modifyorder - SL incorrect."
                        return
                else:
                    if order["tp"] > order["sl"]:
                        print "Error - modifyorder - TP and SL values incorrect."
                    if order["tp"] >= self.bid:
                        print "Error - modifyorder - TP incorrect."
                        return
                    if order["sl"] <= self.ask:
                        print "Error - modifyorder - SL incorrect."
                        return

                to_modify_order["tp"] = order["tp"]
                to_modify_order["sl"] = order["sl"]

        # Mudar preço de ordem ainda não consumida (deletar e colocar nova ordem)
        else:
            pass

    def SendOrder(self, order):
        '''Enviar nova ordem.'''

        if self.GetHistoricalOrder(order["number"])["number"] != 0:
            print "Error - SendOrder - Order with given number already exists."

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
            if new_order["tp"] < new_order["sl"]:
                print "Error - sendorder - TP and SL values incorrect."
        else:
            if new_order["tp"] > new_order["sl"]:
                print "Error - sendorder - TP and SL values incorrect."

        # Status da ordem
        if order["number"] > 0:
            new_order["status"] = "placed"
        else:
            new_order["status"] = "placedclose"
            if order["entry"] == "limit":
                print "Error - sendorder - Placedclose order can't have limit entry."

        # Checar validade do preço
        if not self.IsPriceValid(order["price"]):
            new_order["status"] = "canceled"

        # Definir level e spot da ordem
        if order["entry"] == "limit":
            if order["type"] == "B":
                new_order["level"] = int((self.bid - order["price"]) / 0.5)
                if new_order["level"] < 0:
                    new_order["status"] = "canceled"
                else:
                    new_order["spot"] = self.buy_book[new_order["level"]]
            if order["type"] == "S":
                new_order["level"] = int((order["price"] - self.ask) / 0.5)
                if new_order["level"] < 0:
                    new_order["status"] = "canceled"
                else:
                    new_order["spot"] = self.sell_book[new_order["level"]]

        # Inserir ordem
        self.orders.append(new_order)

    def MatchOrders(self, in_orders, out_orders):
        '''Casar ordens de lados opostos que não são intrinsecamente opostas, ex:
        Ordem limitada de venda funcionando como tp para uma ordem de compra.'''

        # Informações das ordens de "entrada"
        in_volume = 0
        in_side = "N"
        for order in in_orders:
            to_match_order = self.GetHistoricalOrder(order["number"])
            if to_match_order["status"] != "filled":
                print "Error - MatchOrders - Orders status isn't filled."
            if in_side == "N":
                in_side = to_match_order["type"]
            else:
                if to_match_order["status"] != in_side:
                    print "Error - MatchOrders - Orders side diverge."
            in_volume += to_match_order["volume"]
            to_match_order["status"] = "done"

        # Informações das ordens de "saída"
        out_volume = 0
        out_side = "N"
        for order in out_orders:
            to_match_order = self.GetHistoricalOrder(order["number"])
            if to_match_order["status"] != "filled":
                print "Error - MatchOrders - Orders status isn't filled."
            if out_side == "N":
                out_side = to_match_order["type"]
            else:
                if to_match_order["status"] != out_side:
                    print "Error - matchorders - Orders side diverge."
            out_volume += to_match_order["volume"]
            to_match_order["status"] = "done"

        if in_side == out_side:
            print "Error - MatchOrders - Orders in and out sides are equal."

        if in_volume != out_volume:
            print "Error - MatchOrders - Orders in and out volumes diverge."

    def CloseAllOrders(self):
        '''Fechar todas as ordens ainda abertas.'''

        for order in self.orders:
            # Deletar ordens não consumidas
            if order["status"] == "placed":
                modified_order = self.GetCleanToModifyOrder()
                modified_order["number"] = order["number"]
                modified_order["action"] = "delete"
                self.ModifyOrder(modified_order)

            # Fechar ordens consumidas
            if order["status"] == "filled":
                modified_order = self.GetCleanToModifyOrder()
                modified_order["number"] = order["number"]
                modified_order["action"] = "close"
                self.ModifyOrder(modified_order)

    def GetHistoricalOrder(self, number):
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

def RunBacktest(day, takeprofit):
    '''Função responsável pela iniciação e execução do teste no dia especificado.'''

    dolar = Market(takeprofit)
    dolar.Initiate(day)

    while not dolar.EndDay():
        dolar.ManagePlayersDecisions()
        dolar.UpdateDOM()

    takeprofit.DisplayProduce()

    del takeprofit
    del dolar.current_book
    del dolar
