"""
Support for interface with a AnthemAV Receiver.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/media_player/
"""
import logging
import socket
import select
import time
import re
import voluptuous as vol


from homeassistant.components.media_player import (
    SUPPORT_TURN_OFF, SUPPORT_VOLUME_MUTE, SUPPORT_VOLUME_SET,
    SUPPORT_SELECT_SOURCE, SUPPORT_VOLUME_STEP, MediaPlayerDevice,
    PLATFORM_SCHEMA)
from homeassistant.const import (
    CONF_HOST, CONF_NAME, STATE_OFF, STATE_ON, STATE_UNKNOWN, CONF_PORT)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'AnthemAV'
DEFAULT_PORT = 4999
DEFAULT_MRXZONE = 1
CONF_MRXZONE = "mrxzone"
CONF_MINVOL = "minvol"
CONF_MAXVOL = "maxvol"
DEFAULT_MINVOL = -60
DEFAULT_MAXVOL = -30
CONF_TIMEOUT = "timeout"
CONF_BUFFER_SIZE = "buffer_size"
DEFAULT_TIMEOUT = 10
DEFAULT_BUFFER_SIZE = 1024
# mrx_payload = "payload"
# CONF_MRXMODEL = "mrxmodel"

SUPPORT_ANTHEMMRX = SUPPORT_SELECT_SOURCE | SUPPORT_VOLUME_STEP | \
    SUPPORT_VOLUME_SET | SUPPORT_VOLUME_MUTE | SUPPORT_TURN_OFF

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    # vol.Optional(CONF_MRXMODEL): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_MRXZONE, default=DEFAULT_MRXZONE): cv.positive_int,
    vol.Optional(CONF_MINVOL, default=DEFAULT_MINVOL): vol.Coerce(float),
    vol.Optional(CONF_MAXVOL, default=DEFAULT_MAXVOL): vol.Coerce(float),
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the AnthemAV platform."""
    add_devices([AnthemAV(hass, config)])
    return True


# pylint: disable=abstract-method, too-many-instance-attributes
class AnthemAV(MediaPlayerDevice):
    """Representation of a AnthemAV Receiver."""

    def __init__(self, hass, config):
        """Initialize the AnthemAV device."""
        mrx_sources = {
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
        }

        self._name = config.get(CONF_NAME)
        self._muted = None
        self._volume = 0
        self._state = STATE_UNKNOWN
        self._response = None
        self._lastupdatetime = None
        self._selected_source = ''
        self._source_name_to_number = {v: k for k,
                                       v in mrx_sources.items()}
        self._source_number_to_name = mrx_sources
        self._config = {
            CONF_NAME: config.get(CONF_NAME),
            CONF_HOST: config[CONF_HOST],
            CONF_PORT: config[CONF_PORT],
            CONF_MRXZONE: config.get(CONF_MRXZONE, DEFAULT_MRXZONE),
            CONF_MINVOL: config.get(CONF_MINVOL, DEFAULT_MINVOL),
            CONF_MAXVOL: config.get(CONF_MAXVOL, DEFAULT_MAXVOL),
            CONF_TIMEOUT: config.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
            CONF_BUFFER_SIZE: config.get(
                CONF_BUFFER_SIZE, DEFAULT_BUFFER_SIZE),
        }
        self.update()

    def update(self):
        """Retrieve the latest data."""
        mrx_payload = "P{}?;".format(self._config[CONF_MRXZONE])
        response = self.send_command(mrx_payload)
        self._response = response
        # self._state = response

        try:
            # check for the power off default messages for zone 1 and zone 2
            if bool(re.search("Main.Off", response))\
                    and self._config[CONF_MRXZONE] == 1:
                self._state = STATE_OFF
                return
            if bool(re.search("Zone2.Off", response))\
                    and self._config[CONF_MRXZONE] == 2:
                self._state = STATE_OFF
                return

            # regex the response
            response = re.match(r'P(.)S(.)V(.*)M(.)D(.)', response)

            # check if the correct zone has been returned
            if int(response.group(1)) != self._config[CONF_MRXZONE]:
                return

            self._volume = max(min((int(response.group(3))
                                    + (0 - self._config[CONF_MINVOL]))
                                   / (self._config[CONF_MAXVOL]
                                      - self._config[CONF_MINVOL]), 1), 0)

            # check if it is muted
            if int(response.group(4)) == 0:
                self._muted = False
            else:
                self._muted = True

            self._selected_source = self._source_number_to_name.get(
                response.group(2))
            _LOGGER.info("SourceNum: %s SourceName: %s",
                         response.group(2), self._selected_source)

            # if the try is passed then make the state on
            self._state = STATE_ON
        except (socket.timeout, TimeoutError, OSError):
            self._state = STATE_OFF

    def send_command(self, payload):
        """Send a command to the AnthemMRX and return the response."""
        _LOGGER.info("Payload: %s", payload)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(self._config[CONF_TIMEOUT])
            try:
                sock.connect(
                    (self._config[CONF_HOST], self._config[CONF_PORT]))
            except socket.error as err:
                _LOGGER.error("Unable to connect to %s on port %s: %s",
                              self._config[CONF_HOST],
                              self._config[CONF_PORT],
                              err)
                return

            try:
                sock.send(payload.encode())
            except socket.error as err:
                _LOGGER.error("Unable to send payload %s to %s on port %s: %s",
                              payload,
                              self._config[CONF_HOST],
                              self._config[CONF_PORT],
                              err)
                return

            readable, _, _ = select.select(
                [sock], [], [], self._config[CONF_TIMEOUT])
            if not readable:
                _LOGGER.warning(
                    "Timeout (%s second(s)) waiting for a response after "
                    "sending %s to %s on port %s.",
                    self._config[CONF_TIMEOUT], payload,
                    self._config[CONF_HOST],
                    self._config[CONF_PORT])
                return
            self._lastupdatetime = time.time()
            value = sock.recv(self._config[CONF_BUFFER_SIZE]).decode()
            _LOGGER.info("Response: %s", value)
        return value

    @property
    def source(self):
        """Return the current input source."""
        return self._selected_source

    @property
    def source_list(self):
        """List of available input sources."""
        return list(self._source_name_to_number.keys())

    def select_source(self, source):
        """Select input source."""
        _LOGGER.info("Select Source: %s",
                     self._source_name_to_number.get(source))
        mrx_payload = "P{}S{};".format(self._config[CONF_MRXZONE],
                                       self._source_name_to_number
                                       .get(source))
        self.send_command(mrx_payload)

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def volume_level(self):
        """Volume level of the media player (0..1)."""
        return self._volume

    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        return self._muted

    @property
    def supported_media_commands(self):
        """Flag of media commands that are supported."""
        return SUPPORT_ANTHEMMRX

    def turn_off(self):
        """Turn off media player."""
        mrxcmd = "P0"
        mrx_payload = "P{zone}{cmd};".format(zone=self._config[CONF_MRXZONE], cmd=mrxcmd)
        self.send_command(mrx_payload)

    def turn_on(self):
        """Turn off media player."""
        mrxcmd = "P1"
        mrx_payload = "P{zone}{cmd};".format(zone=self._config[CONF_MRXZONE], cmd=mrxcmd)
        self.send_command(mrx_payload)

    def volume_up(self):
        """Volume up the media player."""
        mrxcmd = "VU"
        mrx_payload = "P{zone}{cmd};".format(zone=self._config[CONF_MRXZONE], cmd=mrxcmd)
        self.send_command(mrx_payload)

    def volume_down(self):
        """Volume down media player."""
        mrxcmd = "VD"
        mrx_payload = "P{zone}{cmd};".format(zone=self._config[CONF_MRXZONE], cmd=mrxcmd)
        self.send_command(mrx_payload)

    def mute_volume(self, mute):
        """Send mute command."""
        mrxcmd = "MT"
        mrx_payload = "P{zone}{cmd};".format(zone=self._config[CONF_MRXZONE], cmd=mrxcmd)
        self.send_command(mrx_payload)

    def set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        mrxvol = int(((self._config[CONF_MAXVOL]
                       - self._config[CONF_MINVOL])
                      * volume) - (0 - self._config[CONF_MINVOL]))

        mrx_payload = "P{}V{};".format(self._config[CONF_MRXZONE], mrxvol)
        self.send_command(mrx_payload)


# new class for mrx control

    # object for each model type with commands and regex
        # volume_up
        # volume_down
        # volume_set
        # volume_get
        # power_on
        # power_off
        # power_get
        # mute_on
        # mute_off
        # mute_toggle
        # mute_get
        # source_set
        # source_get

# Use regex with named groups
# >>> m = re.match(r"(?P<first_name>\w+) (?P<last_name>\w+)", "Malcolm Reynolds")
# >>> m.group('first_name')
# 'Malcolm'
# >>> m.group('last_name')
# 'Reynolds'
# combine dictionary

# Use format tags

# use server client method like squeezebox to limit polling of mrx

    # # initialise mrx:
        # mrx.initialise(host, port, model)
        # mrx.initialise(192.168.2.200, 4998, 'x00')
        # models: x00, x10, x20

    # # store mrx response in object:
        # mrx.state.[zone].[state]
        # mrx.state.[1].volume = -60
        # mrx.state.[1].mute = 0
        # mrx.state.[1].source = 3
        # mrx.state.[1].power = 1
        # store timestamp of last received command

    # # commands:
        # mrx.[command](zone, value)
        # mrx.setvolume(1, -60)
        # mrx.setsource(1, 1), use source numbers
        # mrx.setmute(1, 0), options 0, 1, T
        # mrx.setpower(1, 1), options 0, 1

    # # Update:
        # mrx.update()
        # optional: limit to 5 seconds since last complete set of information

    # # Socket connection:
        # Current: open, send, receive, close every command.
        # optional: open socket connection and watch all responses.
