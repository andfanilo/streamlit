# -*- coding: utf-8 -*-
# Copyright 2018-2020 Streamlit Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A Python wrapper around Vega."""

# Python 2/3 compatibility
from __future__ import print_function, division, unicode_literals, absolute_import
from streamlit.compatibility import setup_2_3_shims

setup_2_3_shims(globals())

import json

import streamlit.elements.lib.dicttools as dicttools
import streamlit.elements.data_frame_proto as data_frame_proto

from streamlit.logger import get_logger

LOGGER = get_logger(__name__)

DEFAULT_DATA_NAME = "source"


def marshall(proto, data=None, spec=None, use_container_width=False, **kwargs):
    """Construct a Vega chart object.

    See DeltaGenerator.vega_chart for docs.
    """
    # Support passing data inside spec['data'].
    # (The data gets pulled out of the spec dict later on.)

    # proto is a VegaChart protobuf message

    # If data is JSON format, move it to spec
    if (
        type(data) in dict_types and spec is None
    ):  # noqa: F821 pylint:disable=undefined-variable
        spec = data
        data = None

    # Support passing no spec arg, but filling it with kwargs.
    # Example:
    #   marshall(proto, baz='boz')
    if spec is None:
        spec = dict()
    else:
        # Clone the spec dict, since we may be mutating it.
        spec = dict(spec)

    # Support passing in kwargs. Example:
    #   marshall(proto, {foo: 'bar'}, baz='boz')
    if len(kwargs):
        # Merge spec with unflattened kwargs, where kwargs take precedence.
        # This only works for string keys, but kwarg keys are strings anyways.
        spec = dict(spec, **dicttools.unflatten(kwargs, _CHANNELS))

    if len(spec) == 0:
        raise ValueError("Vega charts require a non-empty spec dict.")

    if "autosize" not in spec:
        spec["autosize"] = {"type": "fit", "contains": "padding"}

    # Pull data out of spec in 'data' key array:
    #   marshall(proto, {data: [{name: table, values: df1}], ...})
    if "data" in spec:
        for data_spec in spec["data"]:
            data_proto = proto.data.add()
            data_proto.name = str(data_spec["name"])
            data_proto.has_name = True
            data_frame_proto.marshall_data_frame(data_spec["values"], data_proto.data)
        del spec["data"]

    proto.spec = json.dumps(spec)
    proto.use_container_width = use_container_width

    # If data was provided as DataFrame, put it in a named dataset proto
    if data is not None:
        data_proto = proto.data.add()
        data_proto.name = str(DEFAULT_DATA_NAME)
        data_proto.has_name = True
        data_frame_proto.marshall_data_frame(data, data_proto.data)


# See https://vega.github.io/vega/docs/specification/
_CHANNELS = set(["signals", "scales", "projections", "axes", "legends", "marks",])
