# CARDS AGAINST HUMANITY!

import threading
from module import Module
from cards import Cards, add_card, init_db

from cards import Deck

from CAHGame import CAHGame


class cah(Module):
    models = [Cards]

    def __init__(self, scrap):
        super(cah, self).__init__(scrap)

        self.lock = threading.Lock()

        self.game = None

        scrap.register_event("cah", "msg", self.distribute)
        # but how do you handle commands for privmsg?
        self.register_cmd("cah", self.cah)
        self.register_cmd("cah-init", self.cah_init)

    def cah(self, server, event, bot):
        '''Main command to parse arguments to !cah trigger.'''

        usage = "new, start, join, end, add <black|white> <body>, select <1 2 ... N>,"
        if self.game is not None and self.game.running:
            if event.type == "privmsg":
                if self.game.get_player(event.source.nick) is None:
                    server.privmsg(event.source.nick, "There is a game currently running in another channel, please wait until it finishes.")
                    return
            elif event.type == "pubmsg":
                if event.target != self.game.channel:
                    server.privmsg(event.target, "There is a game currently running in another channel, please wait until it finishes.")
                    return

        if len(event.tokens) >= 2:
            arg = event.arg[0]
            msg = event.arg[1:]
            if event.type == "pubmsg":
                if arg == "start":
                    self.cah_start(server, event, bot)
                    return

                elif arg == "new":
                    self.cah_new(server, event, bot)
                    return

                elif arg == "join":
                    self.cah_join(server, event, bot)
                    return

                elif arg == "end":
                    self.cah_end(server, event, bot)
                    return

            elif event.type == "privmsg":
                if arg == "select":
                    if len(msg) >= 1:
                        cards = msg[0:]
                        self.cah_select(server, event, bot, cards)
                    else:
                        usage = "Select card usage"
                        server.privmsg(event.target, usage)
                    return

            if arg == "add":
                if len(msg) >= 2:
                    color = msg[0]
                    body = ' '.join(msg[1:])
                    self.cah_add(server, event, bot, color, body)
                else:
                    usage = "Add card usage"
                    server.privmsg(event.target, usage)

            elif arg == "vote":
                if len(msg) == 1:
                    #going to need some args here
                    self.cah_vote(server, event, bot, msg[0])
                else:
                    usage = "Vote usage"
                    server.privmsg(event.target, usage)

            elif arg == "draw":
                color = msg[0]
                self.cah_draw(server, event, bot, color)

            elif arg == "madlib":
                self.cah_madlib(server, event, bot)

        else:
            server.privmsg(event.target, usage)

        ################################################################################
        # Function prototypes to fill in
        ################################################################################

    # PUBMSG
    def cah_new(self, server, event, bot):
        '''Initialize a new game.'''
        #check if game is already running
        if self.game is not None and self.game.running:
            msg = "A game is already running!  Use '@cah end' to end it."
        else:
            msg = "A new game of Cards Against Humanity has started!  Use '%scah join' to join the game." % server.cmdchar
            self.game = CAHGame(server, event.target)
        server.privmsg(event.target, msg)

    #PUBMSG
    def cah_start(self, server, event, bot):
        '''Start the game once all players have joined..'''
        self.game.start()

    #PUBMSG
    def cah_join(self, server, event, bot):
        '''Join the current game.'''
        player = self.game.add_player(event.source.nick)
        #server.privmsg(event.target, "%s joined game." % player.name)
        if player:
            server.privmsg(event.target, "%s has joined the game." % player.name)
        else:
            server.privmsg(event.target, "Already joined.")

    #PUBMSg
    def cah_end(self, server, event, bot):
        '''Abort the current game.'''
        #check if game is already running
        if self.game.running:
            server.privmsg(event.target, "The game has ended.")
            for place, player in enumerate(sorted(self.game.players, key=lambda x: x.score, reverse=True)):
                server.privmsg(event.target, "%d. %s with %d points" % (place+1, player.name, player.score))
            self.game.running = False
        else:
            server.privmsg(event.target, "There's no game running!  Use '@cah new' to start a new game.")

    #PUBMSG or PRIVMSG
    def cah_add(self, server, event, bot, color, body):
        '''Add a card to the database.'''
        add_card(color, body)
        replyto = event.target if event.type == "pubmsg" else event.source.nick
        server.privmsg(replyto, "Added %s card: %s" % (color, body))

    #PRIVMSG
    def cah_select(self, server, event, bot, cards):
        '''Select card(s) to play from your hand.'''
        sanitized_cards = []
        for card in cards:
            try:
                sanitized_cards.append(int(card))
            except ValueError:
                server.privmsg(event.source.nick, "'%s' is not a valid card." % card)
                return

        player = self.game.get_player(event.source.nick)
        self.game.select(player, sanitized_cards)

    #PUBMSG or PRIVMSG
    def cah_vote(self, server, event, bot, voted):
        '''Czar voting for group #.'''
        replyto = event.target if event.type == "pubmsg" else event.source.nick
        server.privmsg(replyto, "PLACEHOLDER: czar is voting for %s" % voted)

    #PUBMSG or PRIVMSG
    def cah_init(self, server, event, bot):
        replyto = event.target if event.type == "pubmsg" else event.source.nick
        server.privmsg(replyto, "Adding cards to DB")
        init_result = init_db()
        server.privmsg(replyto, init_result)

    #PUBMSG or PRIVMSG
    def cah_draw(self, server, event, bot, color):
        '''For testing only, delete later.'''
        d = Deck()
        c = d.draw(color)
        replyto = event.target if event.type == "pubmsg" else event.source.nick
        server.privmsg(replyto, c.body)

    #PUBMSG or PRIVMSG
    def cah_madlib(self, server, event, bot):
        '''Entertaining function for dev, delete later.'''
        d = Deck()
        b = d.draw("black")
        madlib = b.body
        blanks = madlib.count('_')
        if blanks == 0:
            madlib += ' ' + d.draw("white").body.rstrip('.')
        else:
            replacements = []
            madlib = madlib.replace("_", "%s")
            for i in range(blanks):
                replacements.append("\x02\x1F%s\x0F" % d.draw("white").body.rstrip('.'))
            madlib = madlib % tuple(replacements)

        replyto = event.target if event.type == "pubmsg" else event.source.nick
        server.privmsg(replyto, madlib)
