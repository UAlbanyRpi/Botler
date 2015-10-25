from multiprocessing import Pool
import os
from os import path, listdir
import itertools
from engine_pipe import Engine
import re
import json
import sys

# todo: get rid of exec, do this with sockets

SCRIPT_PATH = 'player_scripts'
DATA_PATH = 'player_data'

# this is the horrible runtime code version

class UserScript:

    def __init__(self, script, filepath, player_id):
        print "init user script for ", filepath
        # should trycatch
        self.executable = compile(script, filepath, 'exec')

        self.chances = 3
        self.id = player_id


        stats_file_path = os.path.join(DATA_PATH, str(self.id) + '.json')

        with open(stats_file_path, 'r') as f:
            try:
                text = f.read()
                current_stats = json.loads(text)
                print "PATH!", stats_file_path
                print 'CURR', text
                self.wins = current_stats['wins']
                self.losses = current_stats['losses']
                self.ties = current_stats['ties']
                self.history = current_stats['history']

            except ValueError:
                # defaults...
                self.chances = 3
                self.id = player_id
                self.wins = 0
                self.losses = 0
                self.ties = 0
                self.update_stats()


    def take_turn(self, world_state):
        exec (self.executable, globals())  # oh absolute horror
        # I hope context works the way I'd expect here
        return main(world_state)
        # fantasy football for competitive coding
    

    def update_stats(self):
        stats_file_path = os.path.join(DATA_PATH, str(self.id) + '.json')

        with open(stats_file_path, 'a+') as f:
            f.seek(0)
            try:
                text = f.read()
                current_stats = json.loads(text)
            except ValueError:
                print "no stats file for user #", self.id
                print "creating one..."
                current_stats = {}

            # should do something else/more here
            current_stats['wins'] = self.wins
            current_stats['losses'] = self.losses
            current_stats['ties'] = self.ties
            current_stats['history'] = self.history
            print current_stats
            new_stats = json.dumps(current_stats, sort_keys=True,
                                   indent=4, separators=(',', ': '))
            f.truncate(0)
            f.write(new_stats)

    def win(self):
        self.wins = self.wins + 1
        self.history.append("win")
        self.update_stats()

    def lose(self):
        self.losses = self.losses + 1
        self.history.append("loss")
        self.update_stats()

    def tie(self):
        self.ties = self.ties + 1
        self.history.append("draw")
        self.update_stats()


def create_sandbox(path, filename):
    # horrible brittle regexy piece of shit.
    filepath = os.path.join(path, filename)
    with open(filepath, "r") as f:
        return UserScript(f.read(), filepath, filename)


def run_sim(player_programs):
    print "playing", player_programs[0], "against", player_programs[1]
    n = 10 # number of games

    game_type = player_programs[0].split('-')[0]

    player1 = create_sandbox(SCRIPT_PATH, player_programs[0])
    player2 = create_sandbox(SCRIPT_PATH, player_programs[1])
    #creates player object for each challenger
    players = [player1, player2]
    cycleit = itertools.cycle([0, 1])
    #cycle object to iterate between p1 and p2

    engine = Engine(game_type)
    
    #game engine object with game type entered
    player_1_history = []
    player_2_history = []

    # stats_obj = get_player_stats(player1)
    rps_mapping = {'r': "Rock", 'p': 'Paper', 's': "Scissors"}

    print '---------'

    for player_id in [next(cycleit) for i in range(0, n)]:

        print '(', player_id, ')'
        current_player = players[player_id]

        world_state = engine.getState()

        valid_moves = engine.getValidMoves()

        try:
            if game_type == 'rps':
                ret = current_player.take_turn({"valid_moves": valid_moves, "player": 1, "history": player_1_history})
                print ret

                engine.makeMove({'contents': [], 'tag': rps_mapping[ret]})
                status = engine.getStatus()
                print status

                if status['tag'] == 'PlayerWin' and status['contents'] == 1:
                    print player_id, "player wins"
                    players[1].win()
                    players[0].lose()
                    engine.reset()
                    continue
                
                if status['tag'] == 'PlayerWin' and status['contents'] == 0:
                    print player_id, "player loses"
                    players[0].win()
                    players[1].lose()
                    engine.reset()
                    continue

                if status['tag'] == 'Drawn':
                    print player_id, "player drawn"
                    players[0].tie()
                    players[1].tie()
                    engine.reset()
                    continue
        except:
            print sys.exc_info()
            break
    # player1.update_stats()
    # player2.update_stats()


if __name__ == '__main__':
    num_processes = 4 #4 total processes after each call
    
    p = Pool(num_processes)

    files = [f for f in listdir(SCRIPT_PATH) if (
        path.isfile(path.join(SCRIPT_PATH, f)) and f[0] != '.')]
    matches = [m for m in itertools.combinations(files, r=2) ]
    matches = filter(lambda m: m[0].split('-')[0] == m[1].split('-')[0], matches)
    print matches
    print(map(run_sim, matches))  # todo: switch to p.map after debug
    #stdout each match with run_sim function
