CREATE OR REPLACE VIEW marketplace_licenses_grants_view AS
SELECT
    CAST(NULL AS varchar) AS management_account_id,
    CAST(NULL AS varchar) AS subscribed_account_id,
    CAST(NULL AS varchar) AS grantee_account_id,
    CAST(NULL AS timestamp) AS license_create_time,
    CAST(NULL AS varchar) AS license_id,
    CAST(NULL AS varchar) AS productname,
    CAST(NULL AS varchar) AS seller,
    CAST(NULL AS varchar) AS agreement_id,
    CAST(NULL AS varchar) AS license_status,
    CAST(NULL AS timestamp) AS license_start_date,
    CAST(NULL AS timestamp) AS license_end_date,
    CAST(NULL AS varchar) AS productsku,
    CAST(NULL AS varchar) AS license_issuer,
    CAST(NULL AS varchar) AS homeregion,
    CAST(NULL AS varchar) AS license_version,
    CAST(NULL AS varchar) AS grant_name,
    CAST(NULL AS varchar) AS grant_id,
    CAST(NULL AS varchar) AS grant_status,
    CAST(NULL AS varchar) AS grant_version,
    CAST(NULL AS varchar) AS granted_operations,
    CAST(NULL AS varchar) AS activation_override_behavior
WHERE 1 = 0
