# -*- coding: utf-8 -*-

from mdstudio.deferred.chainable import chainable
from mdstudio.component.session import ComponentSession
from mdstudio.runner import main


dict_convert = {
    "output_format": "mol2",
    "workdir": "/tmp/mdstudio/lie_structures/convert",
    "input_format": "smi",
    "mol": "O1[C@@H](CCC1=O)CCC",
    "from_file": False,
    "to_file": False
}


class Run_example(ComponentSession):

    def authorize_request(self, uri, claims):
        return True

    @chainable
    def on_run(self):

        mol = yield self.call(
            'mdgroup.lie_structures.endpoint.convert', dict_convert)
        print(mol)

        pdb = yield self.call(
            'mdgroup.lie_structures.endpoint.make3d',
            {'input_format': 'mol2',
             'output_format': 'pdb',
             'mol': mol['mol'],
             'from_file': False,
             'to_file': False,
             'workdir': "/tmp/mdstudio/lie_structures/convert"})
        print(pdb['mol'])


if __name__ == '__main__':
    main(Run_example)
