"""This is the AnthemAV commands, regex and source dictionaries."""

# Commands for the anthemav receiver using named format tags.
cmds = {
    'x00': {
        'ZoneQuery': 'P{zone}?;',

        'PowerOn': 'P{zone}P1;',
        'PowerOff': 'P{zone}P0;',
        'PowerQuery': 'P{zone}P?;',

        'VolumeUp': 'P{zone}VU{step};',
        'VolumeDown': 'P{zone}VD{step};',
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

        'VolumeUp': 'Z{zone}VUP{step};',
        'VolumeDown': 'Z{zone}VDN{step};',
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
}

# Regex matches with named groups.
# Each item will be checked against response.
regex = {
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
}


# Regex replacement for specific repsonses. Usually when the receiver is off.
# The structure is ['REGEX', 'REPLACEMENT RESPONSE TO BE PARSED'].
# x10 and x20 models return "!Z<OriginalMessage>" when in Standby.
response_replace = {
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
}

# Default source list for receiver.
sources = {
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
    }
}
