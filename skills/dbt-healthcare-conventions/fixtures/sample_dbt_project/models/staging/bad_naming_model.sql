select
    encounter_id,
    patient_id,
    admit_date,
    discharge_date
from {{ source('ehr', 'encounters') }}
