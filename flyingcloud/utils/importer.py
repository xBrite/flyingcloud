# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import, print_function

import imp
import os
import sys


def import_derived_class(implementation_filename, base_class):
    impl_dir, impl_filename = os.path.split(implementation_filename)
    module_name, _ = os.path.splitext(impl_filename)

    try:
        sys.path.insert(0, impl_dir)
        fp, filename, description = imp.find_module(module_name)
        module = imp.load_module(module_name, fp, filename, description)
        for name in dir(module):
            obj = getattr(module, name)
            if (type(obj) == type(base_class)
                and issubclass(obj, base_class)
                and obj != base_class):
                return obj
        raise ValueError("No subclass of {0} in {1}".format(
            base_class.__name__, implementation_filename))
    finally:
        sys.path.pop(0)
