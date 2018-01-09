from time import *

def Init_Execution(magic_number, printt=False):
    '''Start counting time from given magic number'''

    global register

    current_time = time()
    if magic_number in register:
        print "Magic Number already exists!!!"
    else:
        register[magic_number] = current_time

    if printt:
        print "Execution from(" + str(magic_number) + ") started!"

def End_Execution(magic_number, printt=True):
    '''Start counting time from given magic number'''

    global register

    current_time = time()
    exec_time = 0.0
    if magic_number not in register:
        print "Magic Number doesn't exists!!!"
    else:
        exec_time = current_time - register[magic_number]
        if printt:
            print "Execution time from(" + str(magic_number) + "):", round(exec_time, 2)

    del register[magic_number]

    return exec_time

register = {}