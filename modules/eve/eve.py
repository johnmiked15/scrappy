# Eve API module

import time

import eveapi.eveapi as eveapi

from module import Module

from eve_cache import EveCache


class eve(Module):
    def __init__(self, scrap):
        super(eve, self).__init__(scrap)

        scrap.register_event("eve", "msg", self.distribute)

        self.register_cmd("eve-wallet", self.wallet)
        self.register_cmd("eve-skill", self.skill)
        self.register_cmd("eve-add", self.eve_add)

    def setup_table(self, server):
        db_conn = self.get_db()
        # TODO: Could probably hash this, if there is no need to go from table->server/target again
        sql = "CREATE TABLE IF NOT EXISTS %s (name TEXT, id TEXT, key TEXT)" % server
        db_cursor = db_conn.cursor()
        db_cursor.execute(sql)
        db_conn.commit()
        db_conn.close()

    def skill(self, server, event, bot):
        c = server["connection"]

        credentials = self.get_credentials(server["servername"], event.source.nick)
        if credentials is None:
            c.privmsg(event.target, "%s isn't in the database, see the %seve-add command" % (event.source.nick, server["cmdchar"]))
            return

        (eve_id, eve_vcode) = credentials

        api = eveapi.EVEAPIConnection(cacheHandler=EveCache())
        auth = api.auth(keyID=eve_id, vCode=eve_vcode)
        result = auth.account.Characters()

        skills = api.eve.SkillTree()

        for character in result.characters:
            c.privmsg(event.target, "Training queue for %s" % character.name)
            queue = auth.char.SkillQueue(characterID=character.characterID)
            for training_skill in queue.skillqueue:
                # Oh boy, this is going to be horrible.
                for group in skills.skillGroups:
                    for skill in group.skills:
                        if skill.typeID == training_skill.typeID:
                            time_str = time.strftime("%B %d %H:%M:%S",time.gmtime(training_skill.endTime))
                            c.privmsg(event.target, "%s: %s to level %s. Ends %s." % (group.groupName, skill.typeName, training_skill.level, time_str))




    def wallet(self, server, event, bot):
        """ List all character wallets """
        c = server["connection"]

        credentials = self.get_credentials(server["servername"], event.source.nick)
        if credentials is None:
            c.privmsg(event.target, "%s isn't in the database, see the %seve-add command" % (event.source.nick, server["cmdchar"]))
            return

        (eve_id, eve_vcode) = credentials

        api = eveapi.EVEAPIConnection(cacheHandler=EveCache())
        auth = api.auth(keyID=eve_id, vCode=eve_vcode)
        result = auth.account.Characters()

        for character in result.characters:
            wallet = auth.char.AccountBalance(characterID=character.characterID)
            isk = wallet.accounts[0].balance
            c.privmsg(event.target, "Character: %s has %s ISK" % (character.name, isk))

    def eve_add(self, server, event, bot):
        """ Add account to eve using <ID> <VCODE> """
        c = server["connection"]

        if len(event.tokens) < 3:
            c.privmsg(event.target, "Not enough arguments, <ID> and <VCODE> required.")
            return

        eve_id = event.tokens[1]
        eve_vcode = event.tokens[2]

        self.setup_table(server["servername"])
        db_conn = self.get_db()
        db_curs = db_conn.cursor()

        sql = "SELECT 1 FROM %s WHERE name=?" % server["servername"]
        db_curs.execute(sql, (event.source.nick,))
        if db_curs.fetchone() is None:
            sql = "INSERT INTO %s (name, id, key) VALUES (?, ?, ?)" % server["servername"]
            db_curs.execute(sql,(event.source.nick, eve_id, eve_vcode))
            c.privmsg(event.target, "Added %s to the database with ID %s" % (event.source.nick, eve_id))
        else:
            sql = "UPDATE %s SET id=?,key=? WHERE name=?" % server["servername"]
            db_curs.execute(sql, (eve_id, eve_vcode, event.source.nick))
            c.privmsg(event.target, "Updated %s in the database to ID %s" % (event.source.nick, eve_id))

        db_conn.commit()
        db_conn.close()

    def get_credentials(self, server, nick):
        self.setup_table(server)
        db_conn = self.get_db()
        db_curs = db_conn.cursor()
        sql = "SELECT id, key FROM %s WHERE name=? " % server
        db_curs.execute(sql, (nick,))

        credentials = db_curs.fetchone()
        db_conn.close()
        return credentials


