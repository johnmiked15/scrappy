from __future__ import unicode_literals
import urllib2
import sys
import re
from lxml import html
from lxml.etree import HTMLParser

def get_lunch_url():
    return 'http://treatamerica.essentialpos.com/menu/intro.php?bid=1651&week=1'

def get_text_from_node(node):
    if node is not None:
        return ''.join([x.strip() for x in node.itertext() if x and not x.isspace()]).strip()
    return None

def get_lunch_menu():
    try :
        text = urllib2.urlopen(get_lunch_url()).read()
        parser = HTMLParser(encoding="utf-8")
        tree = html.fromstring(text, parser=parser)
        test = tree.xpath('/html/body/center[3]/table/tr/td[2]/table')[0]
        ret = []
        for row in test.getiterator("tr"):
            bold_element = row.find('.//b')
            title = get_text_from_node(bold_element)
            if title:
                item = [title]
                serving = row.find('.//font[@color="gray"]')
                item.append(get_text_from_node(serving))
                desc = row.find('.//i')
                item.append(get_text_from_node(desc))
                ret.append(item)

        return ret
    except urllib2.HTTPError, e:
        return ["Cannot retrieve URL: HTTP Error Code " + e.code]
    except urllib2.URLError, e:
        return ["Cannot retrieve URL: " + e.reason[1]]

if __name__ != '__main__':
    from ..module import Module

    class lunch(Module):

        def __init__(self, scrap):
            super(lunch, self).__init__(scrap)
            scrap.register_event("lunch", "msg", self.distribute)

            self.register_cmd("lunch", self.lunch)

        def lunch(self, server, event, bot):
            if len(event.arg) == 1:
                arg = event.arg[0]
                if arg == "url":
                    server.privmsg(event.target, get_lunch_url())
                else:
                    server.privmsg('argument not supported')
            else:
                data = get_lunch_menu()
                for item in data:
                    if not item[1]:
                        server.privmsg(event.target, '\x02\x1F%s\x0F' % item[0])
                    else:
                        server.privmsg(event.target, '\x02%s\x0F: %s' % (item[0], item[1]))
                    if item[2]:
                        server.privmsg(event.target, '\x1D%s\x0F' % item[2])
                    #server.privmsg(event.target, '')


def main():
    for item in get_lunch_menu():
        if not item[1]:
            print '\x02\x1F%s\x0F' % item[0]
        else:
            print '\x02%s\x0F: %s' % (item[0], item[1])
        if item[2]:
            print '\x1D%s\x0F' % item[2]
        #print '\x02\x1F%s\x0F: %s' % (items[0], items[1:])

if __name__ == '__main__':
    sys.exit(main())
