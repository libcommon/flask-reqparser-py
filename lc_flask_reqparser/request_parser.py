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


if os.environ.get("ENVIRONMENT") == "TEST":
    import unittest
    import flask

    app = flask.Flask(__name__)     # pylint: disable=invalid-name
    app.testing = True


    class TestFlaskReqparser(unittest.TestCase):
        """Tests for Flask request parser."""

        def test_add_argument_actions(self):
            arguments = (("username", str), ("password", str), ("retries", int), ("help", float))
            parser = RequestParser()
            for argument, argument_type in arguments:
                parser.add_argument(argument, type=argument_type)
            for idx, action in enumerate(parser._actions):
                with self.subTest(argument=action.dest):
                    self.assertEqual(action.dest, arguments[idx][0])

        def test_parse_args(self):
            tests = [
                ("GET request to /, no URL parameters",
                 dict(path="/", method="GET"),
                 ("username", "password"),
                 True,
                 (Namespace(username=None, password=None), None)),
                ("GET request to /, URL parameters username, password",
                 dict(path="/?username=lib&password=common", method="GET"),
                 ("username", "password"),
                 True,
                 (Namespace(username="lib", password="common"), None)),
                ("GET request to /libcommon, URL parameter username, extra parameter",
                 dict(path="/libcommon?username=lib&password=common", method="GET"),
                 ("username",),
                 False,
                 (Namespace(username="lib"), ["--password", "common"])),
                ("POST request to /, no request body",
                 dict(path="/", method="POST"),
                 ("username", "password"),
                 False,
                 (Namespace(username=None, password=None), list())),
                ("POST request to /, body parameters username, password, extra parameter",
                 dict(path="/", method="POST", json=dict(username="lib", password="common", apple="honey crisp")),
                 ("username", "password", "help"),
                 False,
                 (Namespace(username="lib", password="common", help=None), ["--apple", "honey crisp"])),
                # #1: Handle JSON _and_ form data in POST/PUT requests
                ("POST request to /, body parameters username and password as form data",
                 dict(path="/", method="POST", data=dict(username="lib", password="common")),
                 ("username", "password"),
                 True,
                 (Namespace(username="lib", password="common"), None)),
                ("PUT request to /libcommon, body parameter username",
                 dict(path="/", method="PUT", json=dict(username="lib", app="le")),
                 ("username", "apple"),
                 True,
                 (Namespace(username="lib", apple=None), None)),
                ("HEAD request to /",
                 dict(path="/", method="HEAD"),
                 ("username",),
                 True,
                 (Namespace(username=None), None))
            ]

            for test_name, ctx_params, request_args, drop_unknown, expected in tests:
                with self.subTest(test_name=test_name), app.test_request_context(**ctx_params):
                    parser = RequestParser()
                    for arg in request_args:
                        parser.add_argument(arg)
                    (known_args, unknown_args) = parser.parse_args(drop_unknown=drop_unknown)
                    (expected_known_args, expected_unknown_args) = expected
                    self.assertEqual(expected_known_args, known_args)
                    self.assertEqual(expected_unknown_args, unknown_args)
