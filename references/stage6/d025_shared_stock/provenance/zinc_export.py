from __future__ import absolute_import, print_function

import csv
import datetime
import os
from flask import current_app
from flask.ext.script import (
    Command,
    Manager,
    Option,
)

from zinc.extensions import db
from zinc.data.models import (
    Protomer,
    Substance,
    Tranche,
    CONFIG_PROTOMER_PATH,
    ProtomerFileFactory,
)
from zinc.data.models.comparators import (
    Tranche2DComparator,
    Tranche3DComparator
)
from zinc.data.actions.tranche import get_tranche_by_name
from zinc.extensions.sqlalchemy.poly_utils import and_
from zinc.utils import clone_namedtuple


class TrancheExport(Command):
    TARGET = None
    OPTIONS = ()
    HEADER = ()
    FIELDS = ()
    OUTPUTS = ()

    def __init__(self, logger=None):
        self.tranches = {}
        self.handles = []
        self.writers = []
        self.tranche_names = {}
        super(TrancheExport, self).__init__()

    def get_options(self):
        return [
            Option('tranche_name'),
            Option('-d', '--dir', dest='root', default=os.getcwd()),
            Option('-C', '--no-update-counts', dest='update_counts', action='store_false', default=True)
        ]

    def open_tranche_writer(self, tranche, formatter_spec, root=None):
        root = root or os.getcwd()
        path_tpl, sep, fields = formatter_spec
        file_name = path_tpl.format(tranche)
        path = os.path.join(root, file_name)
        dirname = os.path.dirname(path)
        if not os.path.exists(dirname):
            current_app.logger.info("Creating {}".format(dirname))
            os.makedirs(dirname)
        current_app.logger.info("Opening {}".format(path))
        handle = open(path, 'wb')
        self.handles.append(handle)
        writer = csv.writer(handle, delimiter=sep, quoting=csv.QUOTE_NONE)
        self.writers.append(writer)
        num_fields = len(fields)
        getter = lambda row: row[:num_fields]
        writer.writerow(fields)
        return handle, writer, getter

    def close_tranche_writers(self):
        for handle in self.handles:
            if not handle.closed:
                handle.close()
        self.handles = []
        self.writers = []

    def get_tranche_output(self, tranche_name, root=None, create=True, clear_counts=False):
        try:
            return self.tranches[tranche_name]
        except KeyError:
            tranche = get_tranche_by_name(tranche_name, create=create)
            if tranche.tranche_id is None:
                db.session.add(tranche)
            if clear_counts or tranche.size is None:
                tranche.size = 0
                tranche.last = datetime.date.today()
                tranche.num_mol2 = tranche.num_mol2 or 0
                tranche.num_db = tranche.num_db or 0
                tranche.num_db2 = tranche.num_db2 or 0

            if root is not None:
                writers = [self.open_tranche_writer(tranche, spec, root=root) for spec in self.OUTPUTS]
                writers = tuple([(getter, writer) for _handle, writer, getter in writers])
            else:
                writers = ()
            return self.tranches.setdefault(tranche_name, (tranche, writers))

    def get_tranche_items(self, tranche_name):
        raise NotImplementedError()

    def get_row(self, row):
        return row

    def dump_substances_to_outputs(self, tranche_prefix, root=None, update_counts=False):
        rows = self.get_tranche_items(tranche_name=tranche_prefix)
        for row in rows:
            processed_row = self.get_row(row)
            tranche_name = processed_row.tranche_name
            tranche, writers = self.get_tranche_output(tranche_name=tranche_name, root=root,
                                                       create=True, clear_counts=update_counts)
            tranche.size += 1
            for getter, writer in writers:
                writer.writerow(getter(processed_row))

        if update_counts:
            db.session.commit()
        else:
            for tranche, _ in self.tranches.values():
                current_app.logger.info("{}: {}".format(tranche.name, tranche.size))

    def run(self, tranche_name, root=None, update_counts=False):
        db.session.configure(autoflush=False)
        try:
            self.dump_substances_to_outputs(tranche_prefix=tranche_name, root=root, update_counts=update_counts)
        finally:
            self.close_tranche_writers()


class Tranche2DExport(TrancheExport):
    HEADER = ["smiles", "zinc_id", "inchikey", "mwt", "logp", "reactive", "purchasable", "tranche_name", "features"]
    OUTPUTS = [
        ('{0.name}.txt', '\t', HEADER),
        ('{0.name}.smi', ' ', HEADER[:2]),
    ]

    def get_tranche_items(self, tranche_name):
        query = db.session.query().add_columns(
            Substance.smiles, Substance.zinc_id, Substance.inchikey,
            Substance.mwt, Substance.logp, Substance.reactive, Substance.purchasable,
            Substance.tranche_prefix,
            Substance.features,
        )
        query = query.filter(
            and_(
                Substance.tranche_name == tranche_name,
                Substance.purchasable > 0
            )
        )
        query = query.yield_per(100)

        return query

    def get_tranche_name(self, row):
        key = (row.tranche_prefix, row.reactive, row.purchasable)
        try:
            tranche_name = self.tranche_names[key]
        except KeyError:
            tranche = Tranche2DComparator.from_attributes(mwt=row.mwt, logp=row.logp,
                                                          reactive=row.reactive, purchasable=row.purchasable,
                                                          tranche_prefix=row.tranche_prefix)

            tranche_name = tranche.name
            self.tranche_names[key] = tranche_name
        return tranche_name

    def get_row(self, row):
        tranche_name = self.get_tranche_name(row)
        features = ','.join(sorted(row.features or ()))
        result = clone_namedtuple(row, self.HEADER,
                                  features=features,
                                  tranche_name=tranche_name)
        return result


class Tranche3DExport(TrancheExport):
    TARGET = Protomer
    HEADER = ["smiles", "zinc_id", "prot_id", "files.db2", "substance.inchikey",
              "net_charge", "ph_mod_fk", "substance.mwt", "substance.logp", "purchasable", "reactive", "features",
              "tranche_name"]
    FIELDS = [f.split('.')[-1] for f in HEADER]
    OUTPUTS = [
        ('{0.name_suffix}/{0.name}.txt', '\t', HEADER),
        ('{0.name_suffix}/{0.name}.smi', ' ', HEADER[:2]),
    ]

    def __init__(self, *args, **kwargs):
        super(Tranche3DExport, self).__init__(*args, **kwargs)

    def _get_root(self):
        if not hasattr(self, '_prot_root'):
            self._prot_root = current_app.config.get(CONFIG_PROTOMER_PATH, Protomer.DEFAULT_FILE_STORE)
        return self._prot_root

    def get_tranche_items(self, tranche_name):
        substance_tranche = tranche_name[:4]
        protomer_tranche = tranche_name[4:]

        query = db.session.query().add_columns(
            Protomer.smiles, Protomer.zinc_id, Protomer.prot_id, Protomer.substance_inchikey,
            Protomer.net_charge, Protomer.ph_mod_fk,
            Protomer.mwt, Protomer.logp,
            Protomer.purchasable, Protomer.reactive,
            Protomer.features,
            Protomer.tranche_prefix
        )
        query = query.join(Substance, Protomer.sub_id_fk == Substance.sub_id)
        query = query.filter(
            and_(
                Substance.tranche_name == substance_tranche,
                Substance.purchasable > 0
            )
        )
        if protomer_tranche:
            protomer_tranche = ('-' * len(substance_tranche)) + protomer_tranche
            query = query.filter(Protomer.tranche_name == protomer_tranche)
        query = query.yield_per(100)

        return query

    def get_tranche_name(self, row):
        key = (row.tranche_prefix, row.reactive, row.purchasable, row.ph_mod_fk, row.net_charge)
        try:
            tranche_name = self.tranche_names[key]
        except KeyError:
            tranche = Tranche3DComparator.from_attributes(mwt=row.mwt, logp=row.logp,
                                                          reactive=row.reactive, purchasable=row.purchasable,
                                                          ph_mod_fk=row.ph_mod_fk, net_charge=row.net_charge,
                                                          tranche_prefix=row.tranche_prefix)
            tranche_name = tranche.name
            self.tranche_names[key] = tranche_name
        return tranche_name

    def get_row(self, row):
        files = ProtomerFileFactory(row.prot_id, root=self._get_root())
        features = ','.join(sorted(row.features or ()))
        result = clone_namedtuple(row, self.FIELDS,
                                  db2=files.db2,
                                  features=features,
                                  tranche_name=self.get_tranche_name(row))
        return result


manager = Manager(usage="Commands for exporting tranche data from ZINC")
manager.add_command('tranches-2d', Tranche2DExport)
manager.add_command('tranches-3d', Tranche3DExport)