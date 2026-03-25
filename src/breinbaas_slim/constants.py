GEF_COLUMN_Z = 1
GEF_COLUMN_QC = 2
GEF_COLUMN_FS = 3
GEF_COLUMN_U = 6
GEF_COLUMN_Z_CORRECTED = 11

CPT_FR_MAX = 99.9
CPT_QC_MAX = 30.0
QCMAX_PEAT = 1.0  # if we use a friction ratio for peat we check two things, is fr >= the given friction ratio AND is qc < QCMAX peat

DEFAULT_CPT_INTERPRETATION_MIN_LAYERHEIGHT = 0.5
DEFAULT_CPT_INTERPRETATION_PEAT_FRICTION_RATIO = 6.0
DEFAULT_CHAINAGE_LENGTH_PER_PLOT = 500

NEN5140 = [
    ["nl_veen", 8.1],
    ["nl_venige_klei", 5],
    ["nl_humeuze_klei", 4],
    ["nl_klei", 2.9],
    ["nl_siltige_klei", 2.5],
    ["nl_zandige_klei", 2.2],
    ["nl_kleiig_zand", 1.8],
    ["nl_siltig_zand", 1.4],
    ["nl_fijn_zand", 1.1],
    ["nl_middelgrof_zand", 0.8],
    ["nl_grof_zand", 0.0],
]

A3_SIZE_LANDSCAPE = (16.53, 11.69)
A3_SIZE_PORTRAIT = (11.69, 16.53)
A4_SIZE_LANDSCAPE = (11.69, 8.27)
A4_SIZE_PORTRAIT = (8.27, 11.69)

PLOT_WIDTH_FACTOR = 0.1
PLOT_QC_MAX = 20.0
