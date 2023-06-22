CREATE OR REPLACE VIEW compute_optimizer_all_options AS
(
   SELECT *
   FROM
     compute_optimizer_ec2_instance_options
UNION    SELECT *
   FROM
     compute_optimizer_auto_scale_options
UNION    SELECT *
   FROM
     compute_optimizer_ebs_volume_options
UNION    SELECT *
   FROM
     compute_optimizer_lambda_options
)