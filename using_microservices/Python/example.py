# -*- coding: utf-8 -*-

from twisted.internet import reactor

from mdstudio.deferred.chainable import chainable
from mdstudio.component.session import ComponentSession
from mdstudio.runner import main


class PythonExample(ComponentSession):

    def authorize_request(self, uri, claims):
        return True

    @chainable
    def on_run(self):

        # Convert SMILES string into 1D mol2 file
        # Note: the SMILES string is defined as 'path_file' object
        mol = yield self.call('mdgroup.lie_structures.endpoint.convert',
                              {"output_format": "mol2",
                               "mol": {"content": "O1[C@@H](CCC1=O)CCC",
                                       "extension": "smi",
                                       "path": None}
                               })

        # Convert 1D mol2 file into 3D PDB file
        # Note: the returned 'mol' path_file object is used as input for make3D
        pdb = yield self.call(
            'mdgroup.lie_structures.endpoint.make3d',
            {'input_format': 'mol2',
             'output_format': 'pdb',
             'mol': mol['mol']})

        print(pdb['mol']['content'])

        # Disconnect from broker and stop reactor event loop
        self.disconnect()
        reactor.stop()


if __name__ == '__main__':
    main(PythonExample, daily_log=False)
