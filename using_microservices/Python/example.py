# -*- coding: utf-8 -*-

from mdstudio.deferred.chainable import chainable
from mdstudio.component.session import ComponentSession
from mdstudio.runner import main


class PythonExample(ComponentSession):

    def authorize_request(self, uri, claims):
        return True

    @chainable
    def on_run(self):

        # Convert SMILES string into 1D mol2 file
        mol = yield self.call('mdgroup.lie_structures.endpoint.convert',
                              {"output_format": "mol2",
                               "input_format": "smi",
                               "mol": "O1[C@@H](CCC1=O)CCC"})
        print(mol)

        # Convert 1D mol2 file into 3D PDB file
        pdb = yield self.call(
            'mdgroup.lie_structures.endpoint.make3d',
            {'input_format': 'mol2',
             'output_format': 'pdb',
             'mol': mol['mol'],
             'from_file': False,
             'to_file': False})

        print(pdb['mol'])


if __name__ == '__main__':
    main(PythonExample)
