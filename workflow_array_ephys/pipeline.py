import datajoint as dj
import os
from element_animal import subject
from element_lab import lab
from element_session import session
from element_event import trial, event
from element_array_ephys import probe
from element_electrode_localization import coordinate_framework, electrode_localization

from element_animal.subject import Subject
from element_lab.lab import Source, Lab, Protocol, User, Project
from element_session.session_with_datetime import Session

from .paths import get_ephys_root_data_dir, get_session_directory, get_electrode_localization_dir

if 'custom' not in dj.config:
    dj.config['custom'] = {}

db_prefix = dj.config['custom'].get('database.prefix', '')

# ------------- Import the configured "ephys mode" -------------
ephys_mode = os.getenv('EPHYS_MODE',
                       dj.config['custom'].get('ephys_mode', 'acute'))
if ephys_mode == 'acute':
    from element_array_ephys import ephys
elif ephys_mode == 'chronic':
    from element_array_ephys import ephys_chronic as ephys
elif ephys_mode == 'no-curation':
    from element_array_ephys import ephys_no_curation as ephys
else:
    raise ValueError(f'Unknown ephys mode: {ephys_mode}')
    
__all__ = ['subject', 'lab', 'session', 'trial', 'event', 'probe', 'ephys', 'Subject',
           'Source', 'Lab', 'Protocol', 'User', 'Project', 'Session', 'coordinate_framework', 'electrode_localization',
           'get_ephys_root_data_dir', 'get_session_directory', 'get_electrode_localization_dir']


# Activate "lab", "subject", "session" schema ---------------------------------

lab.activate(db_prefix + 'lab')

subject.activate(db_prefix + 'subject', linking_module=__name__)

Experimenter = lab.User
session.activate(db_prefix + 'session', linking_module=__name__)


# Activate "event" and "trial" schema ---------------------------------

trial.activate(db_prefix + 'trial', db_prefix + 'event', linking_module=__name__)


# Declare table "SkullReference" for use in element-array-ephys ---------------

@lab.schema
class SkullReference(dj.Lookup):
    definition = """
    skull_reference   : varchar(60)
    """
    contents = zip(['Bregma', 'Lambda'])


# Activate "ephys" schema -----------------------------------------------------

ephys.activate(db_prefix + 'ephys', 
               db_prefix + 'probe', 
               linking_module=__name__)

# Activate "electrode-localization" schema ------------------------------------

ProbeInsertion = ephys.ProbeInsertion
Electrode = probe.ProbeType.Electrode

electrode_localization.activate(db_prefix + 'electrode_localization',
                                db_prefix + 'ccf',
                                linking_module=__name__)

ccf_id = 0
voxel_resolution = 100

if not (coordinate_framework.CCF & {'ccf_id': ccf_id}):
    coordinate_framework.load_ccf_annotation(
        ccf_id=ccf_id, version_name='ccf_2017', voxel_resolution=voxel_resolution,
        nrrd_filepath=f'./data/annotation_{voxel_resolution}.nrrd',
        ontology_csv_filepath='./data/query.csv')
