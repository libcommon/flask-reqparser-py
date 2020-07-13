## -*- coding: UTF-8 -*-
## request_parser.py
##
## Copyright (c) 2019 libcommon
##
## Permission is hereby granted, free of charge, to any person obtaining a copy
## of this software and associated documentation files (the "Software"), to deal
## in the Software without restriction, including without limitation the rights
## to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
## copies of the Software, and to permit persons to whom the Software is
## furnished to do so, subject to the following conditions:
##
## The above copyright notice and this permission notice shall be included in all
## copies or substantial portions of the Software.
##
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
## OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
## SOFTWARE.
# pylint: disable=arguments-differ


from argparse import ArgumentParser, Namespace
import os
from typing import List, NoReturn, Optional, Tuple

from flask.ctx import _request_ctx_stack, RequestContext    # type: ignore


__author__ = "libcommon"


class RequestParser(ArgumentParser):
    """Parse arguments from an HTTP request to a Flask app
    using a ArgumentParser-style parser.  This allows a route
    to define its known arguments, and provides a thin abstraction
    over GET and PUT/POST requests."""

    def __init__(self, **kwargs):
        kwargs["add_help"] = False
        kwargs["allow_abbrev"] = False
        super().__init__(**kwargs)

    def add_argument(self, urlparam: str, **kwargs) -> "RequestParser":     # type: ignore
        super().add_argument("--{}".format(urlparam), **kwargs)
        return self

    def parse_known_args(self,  # type: ignore
                         args: Optional[List[str]] = None,
                         namespace: Optional[Namespace] = None,
                         drop_unknown: bool = True) -> Tuple[Namespace, Optional[List[str]]]:
        # Parse known args
        known_args, unknown_args = super().parse_known_args(args, namespace)
        # Drop unknown args if specified
        if drop_unknown:
            return (known_args, None)
        return (known_args, unknown_args)

    def parse_args(self,    # type: ignore
                   args: Optional[List[str]] = None,
                   namespace: Optional[Namespace] = None,
                   ctx: Optional[RequestContext] = None,
                   drop_unknown: bool = True) -> Tuple[Namespace, Optional[List[str]]]:
        # If args not provided
        if not args:
            # If no request context provided, get it from the stack
            if not ctx:
                if _request_ctx_stack.top:
                    ctx = _request_ctx_stack.top
                else:
                    raise RuntimeError("Request context stack is empty, must be within an app context")
            # Get request arguments by request method.
            #     GET => URL parameters
            #     PUT/POST => request body
            if ctx.request.method == "GET":
                args = ctx.request.args.items()
            elif ctx.request.method in {"POST", "PUT"}:
                args = ctx.request.get_json() if ctx.request.is_json else ctx.request.form
                args = args.items()
            else:
                args = list()
            # Generate CLI-style arguments from request args
            split_args = list()
            for arg_name, arg_value in args:    # type: ignore
                split_args.append("--{}".format(arg_name))
                split_args.append(arg_value)
            return self.parse_known_args(split_args, namespace, drop_unknown)
        # Otherwise, just pass args through
        return self.parse_known_args(args, namespace, drop_unknown)

    def error(self, message: str) -> NoReturn:
        raise RuntimeError("Failed to parse provided arguments ({})".format(message))
