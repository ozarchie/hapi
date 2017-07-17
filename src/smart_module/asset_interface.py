#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
HAPI Generic Asset Interface
Release: April 2017, Alpha Milestone
Copyright 2016 Maya Culpa, LLC

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import importlib
import random
import asset_wt

class AssetInterface(object):
    def __init__(self, asset_type, mock):
        """Determine the correct asset library and import it."""
        self.mock = mock
        if asset_type.lower() == "mock":
            self.mock = True
        else:
            self.asset_lib = importlib.import_module("asset_" + str(asset_type))

    def read_value(self):
        if self.mock:
            return float(random.randrange(8, 34, 1))

        return asset_wt.AssetImpl().read_value()
