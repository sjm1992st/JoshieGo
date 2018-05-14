import glob
import cv2
import pickle
from game import Board, Game
from multiprocessing import  Pool, Queue


class SGFParser(object):

    def __init__(self, f_):
        self.bd = -1
        self.wd = -1
        self.f = f_
        self.result = None
        self.ha = False
        self.game = Game()
        self.pre_move = None
        self.moves = []

        self.num_moves = -1
        self.cs = []

    def valid(self):
        return (self.result is not None)

    def parse_kgs(self):
        for line in self.f:
            #print(line)
            if not line.startswith(';'):
                tokens = line.split(']')
                for token in tokens:
                    if token[:2] == 'BR':
                        self.bd = int(token[3])
                    if token[:2] == 'WR':
                        self.wd = int(token[3])
                    if token[:2] == 'RE':
                        if '+' not in line or not line.split('+')[1].startswith('Time'):
                            self.result = token[3]
                    if token[:2] == 'HA':
                        self.ha = True
            else:
                if not self.valid():
                    return
                tokens = [token for token in line.split(';') if 5 <= len(token) <= 6 and token[2] != ']']
                for token in tokens:
                    self.moves.append(token)

    def parse_aya(self):
        for line in self.f:
            if line[0] == '(':
                self.num_moves = int(line.split(',')[1])
            if line[0] == ';' and line[3] != 't':
                tokens = [token for token in line.split(';') if len(token) > 1]
                for token in tokens:
                    self.moves.append(token[:5])
                    win_rate = token.split('C')
                    if len(win_rate) > 1:
                        rate, cnt = float(win_rate[1].split(',')[0][1:]), int(win_rate[1].split(',')[1][:-2])
                        self.cs.append((rate, cnt))
                    else:
                        self.cs.append((-1, -1))

    def add_data(self, x_list, y_list):
        last = -1
        for i, move in enumerate(self.moves[:-1]):
            self.game.mk_move(*Board.letter2num(move))

            if self.cs[i][1] > 2500 and i < self.num_moves and i-last > 30 or \
               self.cs[i][1] > 2000 and i < 50 and i-last > 30:
                    board_mtx = self.game.boards[-1].board_mtx
                    label = {'current_move': Board.letter2num(move),
                             'next_move': Board.letter2num(self.moves[i+1]),
                             'next_to_play': self.game.next_to_play,
                             'ko_state:': self.game.ko_state[-1],
                             'result': self.cs[i][0]
                             }
                    x_list.append(board_mtx)
                    y_list.append(label)
                    last = i

                    img = self.game.get_current_board_img()
                    print(board_mtx)
                    print(label)
                    print(self.cs[i])
                    cv2.imshow('img', img)
                    cv2.waitKey()

            if i >= self.num_moves:
                return
    def add_kgs_data(self):
        last = -1
        x_list1=[]
        y_list1=[]
        for i, move in enumerate(self.moves[:-1]):
            self.game.mk_move(*Board.letter2num(move))

            board_mtx = self.game.boards[-1].board_mtx
            label = {'current_move': Board.letter2num(move),
                     'next_move': Board.letter2num(self.moves[i+1]),
                     'next_to_play': self.game.next_to_play,
                     'ko_state:': self.game.ko_state[-1]
                     }
            x_list1.append(board_mtx)
            y_list1.append(label)
            last = i

            img = self.game.get_current_board_img()
            #print(board_mtx)
            #print(label)
            #cv2.imshow('img', img)
            #cv2.waitKey(2)
        return x_list1,y_list1
            #if i >= self.num_moves:
            #return
def go_data(name):
    print(name)
    data_list_x=[]
    with open(name, 'r',errors="ignore") as f:
        sgf = SGFParser(f)
        sgf.parse_kgs()
        x_list1,y_list1=sgf.add_kgs_data()
    data_list_x.append(x_list1)
    data_list_x.append(y_list1)
    #print(x_list1)
    #print(y_list1)
    return data_list_x

if __name__ == '__main__':

    # directory = 'F:\\database\\computer-go-dataset-master\\KGS\\kgs4d-19-2008\\'
    # directory = 'F:\\database\\computer-go-dataset-master\\KGS\\kgs-19-2017-02-new\\'
    # dirs = glob.glob('F:\\database\\computer-go-dataset-master\\KGS\\*')

    pool = Pool(processes=4)

    dirs = glob.glob('F:\\database\\*')
    q=Queue()
    data_list_x=Queue()
    data_list_y=Queue()
    x_list = []
    y_list = []
    prev = 0
    cnt = 0
    Name=[]
    for directory in dirs:
        names = glob.glob(directory + '\\*.sgf')
        for name in names:
            #print(name)
        ##for i in range(4):
            #print(directory)
            list1=pool.apply_async(go_data, (name, ))
            print('-------------')
            #print(list1.get()[0])
            #print(list1.get()[1])

            x_list.append(list1.get()[0])
            y_list.append(list1.get()[1])
            cnt=cnt+1
            if int(len(x_list) / 10000) > prev:
                print(len(x_list), len(y_list))
                prev += 1

            if len(x_list) > 1000000:
            # if len(x_list) > 1000:
                cnt += 1
                pickle.dump((x_list, y_list), open('aya_value_ko_feat' + str(cnt).zfill(2) + '.pkl', 'wb'), protocol=2)
                x_list = []
                y_list = []
                prev = 0
            print(cnt)
            #print(multiprocessing.current_process().name,cnt)
        if(q.qsize()>0):
            pool.close()
            pool.join()
    cnt += 1
    pickle.dump((x_list, y_list), open('aya_value_ko_feat' + str(cnt).zfill(2) + '.pkl', 'wb'), protocol=2)
