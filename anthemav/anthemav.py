#!/usr/bin/env python

import re
import time
import socket
import select

# import the anthemav dictionaries
import anthem_api


class AnthemAV(object):
    """Representation of a AnthemAV receiver."""

    def __init__(self, host, port, model='x00', zone='1'):
        self._host = host
        self._port = port
        self._api = anthem_api
        self._model = model
        self._timeout = 10
        self._buffersize = 1024
        self._zone = zone
        self.status = {}

        # self._response = ''
        self._lastupdatetime = None

        self._selected_source = ''
        self._source_name_to_number = {v: k for k, v in self._api.sources[
                                                        self._model].items()}
        self._source_number_to_name = self._api.sources[self._model]
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # self.test()
        self.update()

        # print(self._api.regex[self._model][4]['replace'][1])

    def _update_status(self, response):
        """Convert the response into a command reponse using api."""
        response = self._standarise_response(response)
        for regex in self._api.regex[self._model]:
            m = re.search(r'{}'.format(regex), response)
            if m:
                for k, v in m.groupdict().items():
                    if m.group('zone') not in self.status:
                        self.status[m.group('zone')] = {}
                    self.status[m.group('zone')][k] = v
        print(self.status)
        return

    def send_command(self, cmd):
        """Convert command to payload and send."""
        if cmd in self._api.cmds[self._model]:
            payload = self._api.cmds[self._model][cmd].format(zone=self._zone)
            # print('Payload convert:', payload)
            response = self._send_payload(payload)
        return response

    def update(self):
        """Retrieve the latest data."""
        # response = self._send_payload("P{}?;".format(self._zone))
        self.send_command('ZoneQuery')

        return

    def _standarise_response(self, response):
        """Convert the response into a standard response.
        Responses for standby are different.
        """
        # add x10 and x20 support with zone insertion
        for regex in self._api.response_replace[self._model]:
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

            readable, _, _ = select.select(
                [sock], [], [], self._timeout)
            if not readable:
                print(
                    "Timeout (%s second(s)) waiting for a response after "
                    "sending %s to %s on port %s." %
                    self._timeout, payload, self._host, self._port)
                return
            self._lastupdatetime = time.time()
            value = sock.recv(self._buffersize).decode().rstrip()
            print("Response: %s" % value)
            self._update_status(value)
        return value

    def _test(self):
        """Open a socket and watch the recieved traffic continuosly."""
        self.sock.connect((self._host, self._port))
        chunks = []
        bytes_recd = 0
        MSGLEN = 1000
        while bytes_recd < MSGLEN:
            chunk = self.sock.recv(1024)
            print('new chunk')
            print(chunk.decode())
            if chunk == '':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
            print(bytes_recd, len(chunk), 'bytes')

        # print(''.join(chunks).decode())
        return


AnthemAV('192.168.2.200', 4999, 'x00', 1)
AnthemAV('192.168.2.200', 4999, 'x00', 2)
