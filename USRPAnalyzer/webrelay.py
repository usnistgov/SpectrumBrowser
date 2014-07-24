#!/usr/bin/env python

import urllib2
import xml.etree.ElementTree as et

class X300WebRelay(object):
    def __init__(self, ip, port):

        self.__ctrl_url = ip + ":" + str(port) + "/state.xml"

        self.statexml = None

    def _update_state(self):
        # TODO: handle errors, report success or fail
        print("GET {0}".format(self.__ctrl_url))
        response = urllib2.urlopen(self.__ctrl_url)
        xmltree = et.parse(response)
        self.statexml = xmltree.getroot()

    def tag_exists(self, tag):
        if self.statexml.find(tag) is None:
            # Available children: ['units', 'sensor1temp', 'sensor2temp', 'sensor3temp',
            # 'sensor4temp', 'sensor5temp', 'sensor6temp', 'sensor7temp', 'sensor8temp',
            # 'relay1state', 'relay2state', 'relay3state', 'extvar0', 'extvar1', 'extvar2',
            # 'extvar3', 'extvar4', 'extvar5', 'time', 'serialNumber']

            # TODO: import logging and log to stderr
            print("ERROR: tag {0} not one of {1}").format(
                tag, [c.tag for c in self.statexml.getchildren()]
            )
            return False
        else:
            return True

    def get_state(self, tag):
        self._update_state()
        if self.tag_exists(tag):
            return self.statexml.find(tag).text

    def set_relay_state(self, relay, state):
        """Set a relay state.

        # Turn relay 1 off
        set_relay_state(1, 0)
        """
        assert(type(relay) is int and relay in (1,2,3))
        assert(type(state) is int and state in (0,1))
        ctrl_url = self.__ctrl_url
        self.__ctrl_url += "?relay" + str(relay) + "State=" + str(state)
        self._update_state()
        self.__ctrl_url = ctrl_url


if __name__ == '__main__':
    wr = X300WebRelay(ip="http://192.168.130.221", port=80)
    print("relay1state = {0}".format(wr.get_state('relay1state')))
    print("Switching relay1state to on...")
    wr.set_relay_state(1, 1)
    print("relay1state = {0}".format(wr.get_state('relay1state')))
    print("Switching relay1state to off...")
    wr.set_relay_state(1, 0)
    print("relay1state = {0}".format(wr.get_state('relay1state')))

