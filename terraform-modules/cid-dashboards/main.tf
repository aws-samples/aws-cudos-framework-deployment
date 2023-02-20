resource "aws_cloudformation_stack" "cid" {
  name              = var.stack_name
  template_url      = "https://${data.aws_s3_bucket.template_bucket.bucket_regional_domain_name}/${aws_s3_object.template.key}?etag=${aws_s3_object.template.etag}"
  capabilities      = ["CAPABILITY_NAMED_IAM"]
  parameters        = var.stack_parameters
  iam_role_arn      = var.stack_iam_role
  policy_body       = var.stack_policy_body
  policy_url        = var.stack_policy_url
  notification_arns = var.stack_notification_arns
  tags              = var.stack_tags
}
