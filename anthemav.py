#!/usr/bin/env python

import re
import time
import socket
import select

# import the anthemav dictionaries
# import anthemav.api as api
api = {
    # Commands for the anthemav receiver using named format tags.
    'cmds': {
        'x00': {
            'ZoneQuery': 'P{zone}?;',

            'PowerOn': 'P{zone}P1;',
            'PowerOff': 'P{zone}P0;',
            'PowerQuery': 'P{zone}P?;',

            'VolumeUp': 'P{zone}VU;',
            'VolumeDown': 'P{zone}VD;',
            'VolumeSet': 'P{zone}V{volume};',
            'VolumeQuery': 'P{zone}V?;',

            'MuteOn': 'P{zone}M1;',
            'MuteOff': 'P{zone}M0;',
            'MuteToggle': 'P{zone}MT;',
            'MuteQuery': 'P{zone}M?;',

            'DecoderQuery': 'P{zone}D?;',

            'SourceSet': 'P{zone}S{source};',
            'SourceQuery': 'P{zone}S?;',
        },
        'x10': {
            'PowerOn': 'Z{zone}POW1;',
            'PowerOff': 'Z{zone}POW0;',
            'PowerQuery': 'Z{zone}POW?;',

            'VolumeUp': 'Z{zone}VUP;',
            'VolumeDown': 'Z{zone}VDN;',
            'VolumeSet': 'Z{zone}VOL{volume};',
            'VolumeQuery': 'Z{zone}V?;',

            'MuteOn': 'Z{zone}MUT1;',
            'MuteOff': 'Z{zone}MUT0;',
            'MuteToggle': 'Z{zone}MUTt;',
            'MuteQuery': 'Z{zone}M?;',

            'SourceSet': 'Z{zone}INP{source};',
            'SourceQuery': 'Z{zone}INP?;',

            'SourceActiveQuery': 'ICN?;',
            'SourceNameShortQuery': 'ISN{source_num}?;',
            'SourceNameLongQuery': 'ILN{source_num}?;',

            'ModelQuery': 'IDQ?;',
            'HardwareQuery': 'IDH?;',
        }
    },
    # Regex matches with named groups.
    # Each item will be checked against response.
    'regex': {
        'x00': [
            'P(?P<zone>.).*?P(?P<power>[0-1])',
            'P(?P<zone>.).*?S(?P<source>[a-zA-Z0-9])',
            'P(?P<zone>.).*?VM(?P<volume>-[0-9][0-9]|[0-9][0-9]|-[0-9]|[0-9])',
            'P(?P<zone>.).*?V(?P<volume>-[0-9][0-9]|[0-9][0-9]|-[0-9]|[0-9])',
            'P(?P<zone>.).*?M(?P<mute>[0-1])',
            'P(?P<zone>.).*?D(?P<decoder>[a-zA-Z0-9])',
        ],
        'x10': [
            'Z(?P<zone>.).*?POW(?P<power>.)',
            'Z(?P<zone>.).*?MUT(?P<mute>.)',
            'Z(?P<zone>.).*?INP(?P<source>.*)',
        ]
    },
    # Regex replacement for specific repsonses when reiever is in standby.
    # The structure is ['REGEX', 'REPLACEMENT RESPONSE TO BE PARSED'].
    # x10 and x20 models return "!Z<OriginalMessage>" when in Standby.
    'response_replace': {
        'x00': [
            ['Main.Off', 'P1P0'],
            ['Zone2.Off', 'P2P0'],
        ],
        'x10': [
            ['!Z.*?Z(?P<zone>.)', 'Z{zone}POW0'],
        ],
        'x20': [
            ['!Z.*?Z(?P<zone>.)', 'Z{zone}POW0'],
        ]
    },
    # Default source list for receiver.
    'sources': {
        'x00': {
            '1': 'BDP',
            '2': 'CD',
            '3': 'TV',
            '4': 'SAT',
            '5': 'GAME',
            '6': 'AUX',
            '7': 'MEDIA',
            '8': 'AM/FM',
            '9': 'iPod',
            'c': 'current main zone source',
            'd': 'USB',
            'e': 'Internet Radio'
        },
        'x10': {
        },
        'x20': {
        }
    }
}


class AnthemAV():
    """Representation of a AnthemAV receiver."""

    def __init__(self, host, port, model='x00', zone='1'):
        self._host = host
        self._port = port
        self._model = model
        self._timeout = 2
        self._buffersize = 32
        self._zone = zone
        self._api_regex = api['regex'][model]
        self._api_cmds = api['cmds'][model]
        self._api_response_replace = api['response_replace'][model]
        self._api_sources = api['sources'][model]
        self.status = {}

    def update(self, zone=None):
        """Retrieve the latest data."""
        if zone is None:
            zone = self._zone
            self.send_command('ZoneQuery', zone)
        return self.status

    def volume_set(self, volume):
        """Volume commands."""
        self.send_command('ZoneQuery')
        return

    def sourcelist_create(self):
        """Create a reverse dictionary for the sources."""
        self._source_s2l = self._api_sources
        self._source_l2s = {v: k for k, v in self._api_source.items()}
        return

    def sourcelist_set(self, source):
        """Set the source list, overriding default list."""
        return

    def _update_status(self, response):
        """Convert the response into a command reponse using api."""
        response = self._standarise_response(response)
        for regex in self._api_regex:
            m = re.search(r'{}'.format(regex), response)
            if m:
                for k, v in m.groupdict().items():
                    if m.group('zone') not in self.status:
                        self.status[m.group('zone')] = {}
                    self.status[m.group('zone')][k] = v
        return

    def send_command(self, cmd, zone='', volume='', source=''):
        """Convert command to payload and send."""
        if cmd in self._api_cmds:
            payload = self._api_cmds[cmd].format(zone=zone,
                                                 volume=volume,
                                                 source=source)
            print('Payload convert:', payload)
            response = self._send_payload(payload)
        else:
            print('Command not found.')
            response = 'failed'
        self._update_status(response)
        return self.status

    def _standarise_response(self, response):
        """Convert the response into a standard response.
        Responses for standby are different.
        """
        # add x10 and x20 support with zone insertion
        for regex in self._api_response_replace:
            # print(regex[0], regex[1])
            # print(response)
            m = re.search(r'{}'.format(regex[0]), response)
            if m:
                response = regex[1]
                print("Updated response: %s" % response)
        return response

    def _send_payload(self, payload):
        """Send a command to the AnthemAV receiver and return the response."""
        print("Payload: %s" % payload)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(self._timeout)
            try:
                sock.connect((self._host, self._port))
            except socket.error as err:
                print("Unable to connect to %s on port %s: %s" %
                      self._host, self._post, err)
                return

            try:
                sock.send(payload.encode())
            except socket.error as err:
                print("Unable to send payload %s to %s on port %s: %s" %
                      payload, self._host, self._port, err)
                return

            readable, _, _ = select.select([sock], [], [], self._timeout)
            if not readable:
                print("Timeout (%s second(s)) waiting for a response after "
                      "sending %s to %s on port %s." %
                      self._timeout, payload, self._host, self._port)
                return
            self._lastupdatetime = time.time()
            value = sock.recv(self._buffersize).decode().rstrip()
            print("Response: %s" % value)
        return value
