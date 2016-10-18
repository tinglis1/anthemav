#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division, absolute_import, print_function

from .anthemav import ANTHEMAV
from . import ssdp

__all__ = ['ANTHEMAV']


def find(timeout=1.5):
    """Find all AnthemAV receivers on local network."""
    return
