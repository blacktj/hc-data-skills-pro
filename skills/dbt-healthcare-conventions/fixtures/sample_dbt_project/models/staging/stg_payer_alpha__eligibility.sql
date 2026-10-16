select
    member_id,
    effective_date,
    term_date,
    payer_id,
    plan_type,
    subscriber_id
from {{ source('payer_alpha', 'raw_eligibility') }}
