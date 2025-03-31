CREATE OR REPLACE VIEW compute_optimizer_all_options AS
SELECT
    lastrefreshtimestamp_utc,
    bu.account_name accountid,
    arn,
    region,
    service,
    name,
    module,
    recommendationsourcetype,
    finding,
    reason,
    lookbackperiodindays,
    currentperformancerisk,
    errorcode,
    errormessage,
    ressouce_details,
    utilizationmetrics,
    option_name,
    option_from,
    option_to,
    currency,
    monthlyprice,
    hourlyprice,
    estimatedmonthlysavings_value,
    estimatedmonthly_ondemand_cost_change,
    max_estimatedmonthlysavings_value_very_low,
    max_estimatedmonthlysavings_value_low,
    max_estimatedmonthlysavings_value_medium,
    option_details,
    tags

FROM (
    SELECT * FROM compute_optimizer_ec2_instance_options
    UNION
    SELECT * FROM compute_optimizer_auto_scale_options
    UNION
    SELECT * FROM compute_optimizer_ebs_volume_options
    UNION
    SELECT * FROM compute_optimizer_lambda_options
) base
JOIN business_units_map bu ON bu.account_id = base.accountid;

