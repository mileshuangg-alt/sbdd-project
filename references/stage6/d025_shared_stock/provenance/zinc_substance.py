from __future__ import absolute_import, division

from datetime import datetime as dt

from flask import (
    request,
    url_for,
)
from flask.ext.login import current_user

from .. import identifiers
from sqlalchemy.util import memoized_property
from .core import (
    ARRAY,
    association_proxy,
    annotatable_aggregate,
    and_,
    backref,
    Mol,
    BigInteger,
    Boolean,
    cast,
    CHAR,
    Column,
    column_property,
    Comparator,
    config,
    Date,
    deferred,
    ForeignKey,
    func,
    FeatureSetType,
    FormattedSubIdComparator,
    get_active_purchasability_labels,
    get_active_reactivity_labels,
    Numeric,
    hybrid_property,
    typed_hybrid_property,
    in_,
    InChIKeyPrefixComparator,
    Index,
    Integer,
    join,
    JSON,
    Model,
    overlap,
    PurchasabilityComparator,
    relationship,
    ReactivityComparator,
    SmallInteger,
    String,
    tanimoto_threshold,
    to_external_label,
    to_internal_label,
    to_purchasable_level,
    to_reactive_level,
    to_mol_element,
    Text,
    Tranche2DComparator,
    TSVECTOR,
)

from .mixins import (
    AnnotationMixin,
    StructureMixin,
    ZincIDMixin,
    TextSearchMixin)

from .subsets import (
    Subset,
    SubsetManager
)
from zinc.extensions.sqlalchemy.poly_utils import hasany

__all__ = [
    'FEATURE_CODES',
    'Substance',
    'SubstanceName',
    'to_substance_structure'
]


UNSET_PURCHASABILITY = 'not-computed'
UNSET_REACTIVITY = 'not-computed'


FEATURE_CODES = [
    (201, "endogenous"),
    (202, "metabolite"),
    (203, "biogenic"),

    (210, "fda"),
    (211, "world"),
    (212, "investigational"),
    (213, "in-man"),
    (214, "in-vivo"),
    (215, "in-cells"),
    (216, "in-vitro"),

    (220, "aggregator"),
]


class TrancheSubsetManager(SubsetManager):

    def __contains__(self, item):
        if super(TrancheSubsetManager, self).__contains__(item):
            return True
        else:
            try:
                self.get_constraints(item)
            except KeyError:
                return False
            else:
                return True

    def get_constraints(self, key):
        constraints = []
        for item in key:
            if item in self.definitions:
                constraints.extend(self.definitions[item].constraints)
            elif len(item) <= 6 and item.isalpha():
                try:
                    constraints.append(self.model.tranche_name == item)
                except ValueError:
                    raise KeyError("Invalid Subset: {}".format(item))
            else:
                raise KeyError("Invalid select: {}".format(item))
        return tuple(constraints)


SubsetManager.purchasable_subset_constraints.extend([
    ('substance', lambda attr: attr.has(Substance.purchasable >= 10)),
    ('substances', lambda attr: attr.any(Substance.purchasable >= 10)),
])


class Substance(StructureMixin,
                ZincIDMixin,
                AnnotationMixin,
                Model):

    __tablename__ = 'substance'
    __auto_join_priority__ = 10
    __public_identifier__ = 'zinc_id'
    __default_ordering__ = 'sub_id'
    __default_view_attrs__ = ['zinc_id', 'smiles']
    __subset_manager_class__ = TrancheSubsetManager

    sub_id = Column('sub_id', BigInteger, primary_key=True, nullable=False,
                    doc="A numeric (integer) representation of ZINC ID")
    structure = Column('smiles', Mol(sanitized_=True, inchi_options_=''), unique=True, nullable=False,
                       doc="A query-enabled molecular structure (use the contains and match operators)")
    inchikey = Column('inchikey', CHAR(27), unique=True, nullable=False,
                      doc="The Substance's InChI key")
    features = Column('features', FeatureSetType(choices=FEATURE_CODES, container=set), nullable=True, server_default='NULL',
                      doc="A list of statically-computed interesting attributes of this molecule")
    purchasable = Column('purchasable', Integer, default=-1, nullable=True, server_default='0',
                         doc="A numeric representation of the commercial availability of this compound (high is better)")
    reactive = Column('reactive', SmallInteger, default=-1, nullable=False, server_default='-1',
                      doc="A numeric representation of the worst functionality present (low is better)")
    bb = Column('bb', SmallInteger, default=0, nullable=False, server_default='0',
                doc="Is this substance available in preparative quantities (1 for True)")
    added_on = Column('added_on', Date, nullable=False, server_default='CURRENT_DATE',
                      doc="The date that this molecule was first added to ZINC (or best estimate)")
    purchasable_since = Column('purchasable_since', Date, nullable=True, server_default='CURRENT_DATE',
                               doc="The date that this molecule became commercially available")
    _protomers_last_built = Column('last_seen', Date, nullable=True, server_default='NULL',
                                   doc="The last date that protomers were built (or attempted ot build) for this substance")
    tranche_prefix = Column('tranche_prefix', CHAR(2), nullable=False, default='  ',
                            doc="The 2D mwt/logp tranche of this substance")
    _inchi = deferred(Column('inchi', String, nullable=True, doc="The Substance's InChI"))
    _free = Column('free', SmallInteger, default=1, nullable=False, server_default='1',
                   doc="Is this substance can be publicly disclosed 1 for True)")

    _annotations = deferred(Column('annotations', JSON, nullable=False, server_default='NULL',
                                   doc='Additional ad-hoc annotations that may be computed for the substance.'))

    __table_args__ = (
        #Index('substance_structure_idx', structure, postgresql_using='gist'),
        #Index('substance_inchikey_idx', inchikey, postgresql_using='gist'),
    )

    def __init__(self, sub_id=None, structure=None, **kwargs):
        sub_id = identifiers.to_sub_id(sub_id)
        if 'zinc_id' in kwargs:
            zinc_id = identifiers.to_sub_id(kwargs.pop('zinc_id'))
            if sub_id is not None and zinc_id != sub_id:
                raise ValueError("Conflicting ZINC_ID and sub_id provided")
            else:
                sub_id = zinc_id
        if 'smiles' in kwargs:
            if structure is not None:
                raise ValueError("Cannot construct Substance with smiles and structure")
            else:
                structure = kwargs.pop('smiles')
        if structure is not None:
            structure = to_mol_element(structure, template=Substance.structure)  # Cast to MolElement
        super(Substance, self).__init__(sub_id=sub_id, structure=structure, **kwargs)

    @staticmethod
    def _get_sub_id(obj):
        return obj.sub_id

    def get_smiles_line(self, *extra, **kwargs):
        delimiter = kwargs.pop('delimiter', ' ')
        line = (self.smiles, self.zinc_id) + extra
        return delimiter.join(line)

    def get_image(self, *args, **kwargs):
        return self.structure.get_image(*args, **kwargs)

    #@property
    #def niceness(self):
    #    return NICENESS_LEVELS.get(self.niceness_fk, NICENESS_LEVELS[None])

    @typed_hybrid_property(type_=String, sql_type=Integer, python_type=str)
    def purchasability(self):
        "An English representation of the commercial availability of this substance"
        purch_levels = get_active_purchasability_labels(this_request=request, this_user=current_user)
        return to_external_label(purch_levels.map_to_value(self.purchasable, UNSET_PURCHASABILITY))

    @purchasability.comparator
    def purchasability(cls):
        return PurchasabilityComparator(cls.purchasable)

    @purchasability.setter
    def purchasability(self, value):
        self.purchasable = to_purchasable_level(value)

    @typed_hybrid_property(type_=String, sql_type=Integer, python_type=str)
    def reactivity(self):
        "An English representation of the commercial availability of this substance"
        react_level = get_active_reactivity_labels(this_request=request, this_user=current_user)
        return to_external_label(react_level.map_to_value(self.reactive, UNSET_REACTIVITY))

    @reactivity.comparator
    def reactivity(cls):
        return ReactivityComparator(cls.reactive)

    @reactivity.setter
    def reactivity(self, value):
        self.reactive = to_reactive_level(value)

    @typed_hybrid_property(type_=String)
    def tranche_name(self):
        return Tranche2DComparator(self).name

    @tranche_name.comparator
    def tranche_name(cls):
        return Tranche2DComparator(cls)

    @typed_hybrid_property(type_=String)
    def inchi(self):
        if self._inchi is not None:
            return self._inchi
        else:
            return self.structure.inchi

    @inchi.selectable_comparator
    def inchi(cls):
        return cls.structure.inchi

    @inchi.setter
    def inchi(self, value):
        self._inchi = value

    def __repr__(self):
        return "Substance({0}, {1!r})".format(self.sub_id, self.structure)

    def __str__(self):
        return self.zinc_id

    ecfp4_fp = association_proxy('ecfp4_new', 'data')

    supplier_codes = association_proxy('catitems', 'supplier_code')
    catalog_names = association_proxy('catalogs', 'name')

    chembl_max_phases = association_proxy('chembl_molecules', 'max_phase')
    chembl_orals = association_proxy('chembl_molecules', 'oral')
    chembl_parenterals = association_proxy('chembl_molecules', 'parenteral')
    chembl_topicals = association_proxy('chembl_molecules', 'topical')
    chembl_prodrug = association_proxy('chembl_molecules', 'prodrug')
    chembl_usan_substem_list = association_proxy('chembl_molecules', 'usan_substem')
    chembl_usan_stem_definitions = association_proxy('chembl_molecules', 'usan_stem_definition')
    chembl_indication_classes = association_proxy('chembl_molecules', 'indication_class')
    chembl_action_types = association_proxy('chembl_molecules', 'action_types')

    atc_code_names = association_proxy('atc_codes', 'name')
    atc_code_descriptions = association_proxy('atc_codes', 'description')
    atc_who_ids = association_proxy('atc_classifications', 'who_id')
    atc_level5_codes = association_proxy('atc_classifications', 'level5')

    gene_names = association_proxy('genes', 'name')
    target_names = association_proxy('targets', 'name')
    predicted_gene_names = association_proxy('predictions', 'gene_name')

    ring_names = association_proxy('rings', 'name')

    _preferred_name = association_proxy('preferred_name_entry', 'name')

    _names = association_proxy('name_entries', 'name')
    _lower_names = association_proxy('name_entries', '_lower_name')

    # Already lower-cased
    _atc_who_names = association_proxy('atc_classifications', 'who_name')
    _lower_atc_who_names = association_proxy('atc_classifications', '_lower_who_name')

    _chembl_molecule_names = association_proxy('chembl_molecules', 'pref_name')
    _lower_chembl_molecule_names = association_proxy('chembl_molecules', '_lower_pref_name')

    _synonym_names = association_proxy('synonyms', 'synonym')
    _lower_synonym_names = association_proxy('synonyms', '_lower_synonym')

    _cas_numbers = association_proxy('casnumbers', 'casnumber')
    _lower_cas_numbers = association_proxy('casnumbers', '_lower_casnumber')

    trial_condition_names = association_proxy('trial_conditions', 'name')


    @typed_hybrid_property(type_=String)
    def cas_numbers(self):
        return sorted(set([cas.replace('[', '').replace(']', '') for cas in self._cas_numbers]), key=len)

    @cas_numbers.comparator
    def cas_numbers(cls):
        return cls._lower_cas_numbers

    @typed_hybrid_property(type_=String)
    def chembl_molecule_names(self):
        return sorted(set(self._chembl_molecule_names))

    @chembl_molecule_names.comparator
    def chembl_molecule_names(cls):
        return cls._lower_chembl_molecule_names

    @typed_hybrid_property(type_=String)
    def synonym_names(self):
        return sorted(set(self._synonym_names))

    @synonym_names.comparator
    def synonym_names(cls):
        return cls._lower_synonym_names

    @typed_hybrid_property(type_=String)
    def atc_who_names(self):
        return sorted(set(self._atc_who_names))

    @atc_who_names.comparator
    def atc_who_names(cls):
        return cls._lower_atc_who_names

    @typed_hybrid_property(type_=String)
    def names(self):
        return self._names

    @names.comparator
    def names(cls):
        return cls._lower_names

    @memoized_property
    def any_name(self):
        pref = self.preferred_name
        if pref:
            return pref
        for name in self.names:
            if name is not None:
                return name
        for name in self.atc_who_names:
            if name is not None:
                return name
        for name in self.chembl_molecule_names:
            if name is not None:
                return name
        for name in self.synonym_names:
            if name is not None:
                return name
        for name in self.cas_numbers:
            if name is not None:
                return name
        return self.inchikey

    @typed_hybrid_property(type_=String)
    def preferred_name(self):
        return getattr(self.preferred_name_entry, 'name', '')

    @preferred_name.comparator
    def preferred_name(cls):
        return cls._preferred_name

    @preferred_name.selectable
    def preferred_name(cls):
        return SubstanceName.name

    @property
    def preferred_identifier(self):
        name = self.preferred_name
        if name:
            return name
        else:
            return self.inchikey

    @property
    def png_image_url(self):
        return url_for('substance.image', key=self.public_identifier, ext='png')

    __subsets__ = dict(
        endogenous=Subset(
            lambda substance: in_('endogenous', substance.features),
            "Primary metabolites observed in humans",
            group='Biogenic',
            show=True,
            approx_size=50504,
            approx_purchasable_size=10115),
        metabolites=Subset(
            lambda substance: overlap(substance.features, ('endogenous', 'metabolite')),
            "Primary metabolites of any species, including humans",
            group='Biogenic',
            show=['selector', 'list'],
            approx_size=52538,
            approx_purchasable_size=11096),
        nonhuman_metabolites=Subset(
            'nonhuman-metabolites',
            lambda substance: in_('metabolite', substance.features),
            "Primary metabolites - also known as metabolites, not reported in humans",
            group='Biogenic',
            show=['list', 'instance'],
            approx_size=2034,
            approx_purchasable_size=944),
        natural_products=Subset(
            'natural-products',
            lambda substance: in_('biogenic', substance.features),
            "Natural products, also known as secondary metabolites, i.e. explicitly  excluding metabolites",
            group='Biogenic',
            show=['list', 'instance'],
            approx_size=80617,
            approx_purchasable_size=48164),
        biogenic=Subset(
            lambda substance: overlap(substance.features, ('endogenous', 'metabolite', 'biogenic')),
            "Made by nature, including primary metabolites (metabolites) and secondary metabolites (natural products)",
            group='Biogenic',
            show=['selector', 'list'],
            approx_size=135335,
            approx_purchasable_size=61592),
        fda=Subset(
            lambda substance: in_('fda', substance.features),
            "FDA Approved drugs,  per DrugBank",
            group='Bioactive and Drugs',
            approx_size=1379,
            show=True,
            approx_purchasable_size=1355),
        world_not_fda=Subset(
            'world-not-fda',
            lambda substance: in_('world', substance.features),
            "Drugs approved, but not by the FDA",
            group='Bioactive and Drugs',
            show=['list', 'instance'],
            approx_size=2068,
            approx_purchasable_size=1922),
        world=Subset(
            'world',
            lambda substance: overlap(substance.features, ('fda', 'world')),
            "Approved drugs in major juridications, including the FDA, i.e DrugBank approved",
            group='Bioactive and Drugs',
            show=['selector', 'list'],
            approx_size=3447,
            approx_purchasable_size=3278),
        investigational_only=Subset(
            'investigational-only',
            lambda substance: in_('investigational', substance.features),
            "Investigational compounds - in clinical trials - not approved or used as drugs",
            group='Bioactive and Drugs',
            show=['list', 'instance'],
            approx_size=2364,
            approx_purchasable_size=1619),
        investigational=Subset(
            'in-trials',
            lambda substance: overlap(substance.features, ('fda', 'world', 'investigational')),
            "Compounds that have been investigated, including drugs",
            group='Bioactive and Drugs',
            show=['selector', 'list'],
            approx_size=5811,
            approx_purchasable_size=4897),
        in_man=Subset(
            'in-man',
            lambda substance: overlap(substance.features, ('fda', 'world', 'investigational', 'in-man')),
            "Substances that have been in man",
            group='Bioactive and Drugs',
            show=['selector', 'list'],
            approx_size=98168,
            approx_purchasable_size=27505),
        in_man_only=Subset(
            'in-man-only',
            lambda substance: in_('in-man', substance.features),
            "Substances that have been in man, but not approved or in trials,  e.g nutriceuticals and many metabolites",
            group='Bioactive and Drugs',
            show=['list', 'instance'],
            approx_size=92365,
            approx_purchasable_size=22608),
        in_vivo=Subset(
            'in-vivo',
            lambda substance: overlap(substance.features, ('fda', 'world', 'investigational', 'in-man', 'in-vivo')),
            "Substances tested in animals including man",
            group='Bioactive and Drugs',
            show=['selector', 'list'],
            approx_size=114555,
            approx_purchasable_size=34016),
        in_vivo_only=Subset(
            'in-vivo-only',
            lambda substance: in_('in-vivo', substance.features),
            "Substances tested in animals but not in man,  e.g. DrugBank Experimental",
            group='Bioactive and Drugs',
            show=['list', 'instance'],
            approx_size=16385,
            approx_purchasable_size=6511),
        in_cells=Subset(
            'in-cells',
            lambda substance: overlap(substance.features, ('fda', 'world', 'investigational',
                                                           'in-man', 'in-vivo', 'in-cells')),
            "Substances reported or inferred active in cells",
            group='Bioactive and Drugs',
            show=['selector', 'list'],
            approx_size=114561,
            approx_purchasable_size=34016),
        in_cells_only=Subset(
            'in-cells-only',
            lambda substance: in_('in-cells', substance.features),
            "Substances reported or inferred active in cells only",
            group='Bioactive and Drugs',
            show=['list', 'instance'],
            approx_size=129,
            approx_purchasable_size=0),
        in_vitro=Subset(
            'in-vitro',
            lambda substance: overlap(substance.features, ('fda', 'world', 'investigational',
                                                           'in-man', 'in-vivo', 'in-cells', 'in-vitro')),
            "Substances reported or inferred active at 10 uM or better in direct binding assays",
            group='Bioactive and Drugs',
            show=['selector', 'list'],
            approx_size=276003,
            approx_purchasable_size=137990),
        in_vitro_only=Subset(
            'in-vitro-only',
            lambda substance: in_('in-vitro', substance.features),
            "Substances reported or inferred active at 10 uM or better in direct binding assays only",
            group='Bioactive and Drugs',
            show=['list', 'instance'],
            approx_size=161442,
            approx_purchasable_size=103974),
        aggregators=Subset(
            lambda substance: in_('aggregator', substance.features),
            "These compounds have been observed to form colloidal aggregates under assay conditions",
            show=True,
            group='Other',
            approx_size=15229,
            approx_purchasable_size=13201),
        bb=Subset(
            lambda substance: substance.bb > 0,
            "Available in preparative quantities, typically at least 250 mg",
            group='Availability',
            show=True,
            approx_size=42908449,
            approx_purchasable_size=42908449),
        interesting=Subset(
            lambda item: overlap(item.features, set(name for code, name in FEATURE_CODES)),
            'Compounds with currently known "interesting" attributes (aggregators, biogenic, and bioactive)',
            group='Other',
            show=False,
            approx_size=291359,
            approx_purchasable_size=150872),
        in_stock=Subset(
            'in-stock',
            lambda substance: substance.purchasable >= 40,
            "Compounds purchased direct from manufacturer, already made, sitting on a shelf, ready to ship to you.",
            group='Availability',
            show=['list', 'instance'],
            approx_size=12084317,
            approx_purchasable_size=12084317),
        agent=Subset(
            lambda substance: substance.purchasable == 30,
            "All substances that are available in stock, via procurement agents",
            group='Availability',
            show=['list', 'instance'],
            approx_size=3010821,
            approx_purchasable_size=3010821),
        on_demand=Subset(
            'on-demand',
            lambda substance: substance.purchasable == 20,
            "All substances that are for sale",
            group='Availability',
            show=['list', 'instance'],
            approx_size=95008076,
            approx_purchasable_size=95008076),
        boutique=Subset(
            lambda substance: substance.purchasable == 10,
            "Boutique substances are generally much more expensive than $100/sample, often made to order, yet still cheaper than making it yourself.",
            group='Availability',
            show=['list', 'instance'],
            approx_size=12949291,
            approx_purchasable_size=12949291),
        now=Subset(
            lambda substance: substance.purchasable >= 30,
            "Immediate delivery, includes in-stock and agent",
            group='Availability',
            show=['selector', 'list'],
            approx_size=21455156,
            approx_purchasable_size=21455156),
        wait_ok=Subset(
            'wait-ok',
            lambda substance: substance.purchasable >= 20,
            "Compounds you can get in 8-10 weeks at modest prices, includes in-stock, agent and on-demand",
            group='Availability',
            show=['selector', 'list'],
            approx_size=116463232,
            approx_purchasable_size=116463232),
        for_sale=Subset(
            'for-sale',
            lambda substance: substance.purchasable >= 10,
            "All substances that are for sale, includes in-stock, on-demand, and boutique",
            group='Availability',
            show=True,
            approx_size=389000000,
            approx_purchasable_size=389000000),
        not_for_sale=Subset(
            'not-for-sale',
            lambda substance: substance.purchasable < 10,
            "All substances that cannot be bought as far as we know - tell us if we are mistaken",
            group='Availability',
            show=True,
            approx_size=2100644,
            approx_purchasable_size=0),
        anodyne=Subset(
            'anodyne',
            lambda substance: substance.reactive == 0,
            'Substances matching no reactivity patterns, including PAINS',
            group='Reactivity',
            show=True,
            approx_size=123060385,
            approx_purchasable_size=120153867),
        clean=Subset(
            'clean',
            lambda substance: substance.reactive <= 10,
            'Substances with "clean" reactivity, i.e. many PAINS allowed',
            group='Reactivity',
            show=['selector', 'list'],
            approx_size=124936189,
            approx_purchasable_size=121922647),
        not_anodyne=Subset(
            'not-anodyne',
            lambda substance: substance.reactive == 10,
            'Substances that match one or more reactivity pattern',
            group='Reactivity',
            show=['list', 'instance'],
            approx_size=1875804,
            approx_purchasable_size=1768780),
        standard_ok=Subset(
            'standard-ok',
            lambda substance: substance.reactive <= 30,
            'Substances with "standard" reactivity, including PAINS and ZINC12 "clean" filters',
            group='Reactivity',
            show=['selector', 'list'],
            approx_size=129767718,
            approx_purchasable_size=129394572),
        standard=Subset(
            'standard',
            lambda substance: substance.reactive == 30,
            'Substances that match one of the ZINC12 "clean" filters',
            group='Reactivity',
            show=['list', 'instance'],
            approx_size=7845071,
            approx_purchasable_size=7471925),
        reactive_ok=Subset(
            'reactive-ok',
            lambda substance: substance.reactive <= 50,
            'All molecules except those matching hot patterns',
            group='Reactivity',
            show=['selector', 'list'],
            approx_size=124767718,
            approx_purchasable_size=126394572),
        reactive=Subset(
            'reactive',
            lambda substance: substance.reactive == 50,
            'Substances matching one of the reactive patterns',
            group='Reactivity',
            show=['list', 'instance'],
            approx_size=4558215,
            approx_purchasable_size=2708679),
        hot_ok=Subset(
            'hot-ok',
            lambda substance: substance.reactive <= 50,
            'All molecules, including those with hot patterns',
            group='Reactivity',
            show=['selector', 'list'],
            approx_size=4087805,
            approx_purchasable_size=2191351),
        hot=Subset(
            'hot',
            lambda substance: substance.reactive == 70,
            'Substances matching one of the hot patterns',
            group='Reactivity',
            show=['list', 'instance'],
            approx_size=4087805,
            approx_purchasable_size=2191351),
        current=Subset(
            lambda substance: substance.purchasable > 0,
            'Compounds currently listed in one or more catalogs, both purchasable and annotated',
            group='Other',
            show=False,
            approx_size=164546067,
            approx_purchasable_size=129412523),
        named=Subset(
            lambda substance: hasany(substance.name_entries),
            'Compounds that have names in ZINC',
            group='Other',
            show=['selector', 'list'],
            approx_size=105854,
            approx_purchasable_size=27876),
        benched=Subset(
            lambda substance: substance.purchasable == 0,
            'Compounds not currently in a catalog, either annotated or purchasable',
            group='Other',
            show=False,
            approx_size=64870118,
            approx_purchasable_size=0),
        to_process=Subset(
            'to-process',
            lambda substance: substance.purchasable == -1,
            'Compounds awaiting processing. Internal use only',
            group='Other',
            show=False),
    )


class SubstanceName(ZincIDMixin, TextSearchMixin, Model):
    __tablename__ = 'subname'
    __auto_join_priority__ = 1
    __public_identifier__ = 'subname_id'
    __default_ordering__ = 'name'
    __default_view_attrs__ = ('zinc_id', 'name')
    __text_search_columns__ = ('name',)

    subname_id = Column('subname_id', Integer, primary_key=True)
    sub_id_fk = Column('sub_id_fk', ForeignKey(Substance.sub_id))
    name = Column('name', String)
    terms = deferred(Column('terms', TSVECTOR))
    preferred = Column('preferred', Boolean, default=False, nullable=False)

    _lower_name = column_property(func.lower(cast(name, Text)))
    _name_length = column_property(func.length(name))

    substance = relationship(Substance,
                             primaryjoin=sub_id_fk == Substance.sub_id,
                             viewonly=True,
                             uselist=True,
                             innerjoin=True,
                             backref=backref('name_entries',
                                             uselist=True,
                                             viewonly=True,
                                             innerjoin=True))

    __substance_preferred_name = relationship(Substance,
                                              primaryjoin=and_(sub_id_fk == Substance.sub_id, preferred == True),
                                              viewonly=True,
                                              uselist=False,
                                              innerjoin=True,
                                              backref=backref('preferred_name_entry',
                                                              lazy='joined',
                                                              uselist=False,
                                                              viewonly=True,
                                                              innerjoin=False))

    def __repr__(self):
        return "SubstanceName(subname_id={0.subname_id!r}, sub_id_fk={0.sub_id_fk!r}, name={0.name!r})".format(self)

    def __str__(self):
        return self.name


def to_substance_structure(data, **kwargs):
    s = to_mol_element(data, template=Substance.structure, **kwargs)
    return s
