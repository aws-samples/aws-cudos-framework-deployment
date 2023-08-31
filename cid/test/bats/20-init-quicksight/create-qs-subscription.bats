#!/bin/bats

account_id=$(aws sts get-caller-identity --query "Account" --output text )
BATS_TEST_TIMEOUT=300

# Helper function for waiting for the requred SubscriptionStatus status.
# TODO: add timeout
function wait_subscription {
  status=$1
  until (aws quicksight describe-account-subscription \
     --aws-account-id $account_id \
     --query AccountInfo.AccountSubscriptionStatus | grep -m 1 $status);
  do : 
      sleep 5; 
  done
}

@test "Delete Account Subscription" {
  aws quicksight update-account-settings \
   --aws-account-id $account_id \
   --default-namespace default \
   --no-termination-protection-enabled
  aws quicksight delete-account-subscription --aws-account-id $account_id
}

@test "Waiting for SubscriptionStatus = UNSUBSCRIBED (can take 2 minutes)" {
  wait_subscription "UNSUBSCRIBED"
}

@test "Run cid-cmd initqs (can take 1 minute)" {
  run timeout 300 cid-cmd -vv initqs \
    --enable-quicksight-enterprise yes \
    --account-name $account_id \
    --notification-email 'aaa@bb.com'

  [ "$status" -eq 0 ]
}

@test "SubscriptionStatus is ACCOUNT_CREATED" {
  wait_subscription "ACCOUNT_CREATED"
}

@test "Edition is ENTERPRISE" {
  aws quicksight describe-account-subscription \
     --aws-account-id $account_id \
     --query AccountInfo.Edition | grep "ENTERPRISE"
}
