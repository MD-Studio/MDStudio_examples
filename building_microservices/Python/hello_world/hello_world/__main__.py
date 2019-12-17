# -*- coding: utf-8 -*

import os
import sys

modulepath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
sys.path.insert(0, modulepath)

from mdstudio.runner import main
from hello_world.application import HelloWorldComponent

if __name__ == '__main__':
    main(HelloWorldComponent)