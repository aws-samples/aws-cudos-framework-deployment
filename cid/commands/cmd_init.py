import importlib.resources as pkg_resources
import json
import logging
import sys
from typing import Dict

from cid.commands.command_base import Command
from cid.exceptions import CidCritical, CidError
from cid.utils import (
    get_parameter,
    get_yesno_parameter,
    inject_variables,
    unset_parameter,
)

logger = logging.getLogger(__name__)


class InitCommand(Command):  # pylint: disable=too-few-public-methods
    """Init Command for CLI"""

    def __init__(self, cid, **kwargs):
        self.cid = cid

        self.bucket_name = f"aws-athena-query-results-cid-{self.cid.base.account_id}-{self.cid.base.region}"
        self.athena_workgroup_name = "cid"
        self.database_name = "cid_cur"
        self.catalog_id = self.cid.base.account_id
        self.cur_path = f"s3://cid-{self.cid.base.account_id}-shared/cur/"
        self.cid_crawler_role_name = "CidCURCrawlerRole"
        self.cid_crawler_role_arn = ""
        self.aws_partition = "aws"
        self.processed_cur_path = None
        self.cid_crawler_name = "CidCrawler"
        self.cur_is_managed_by_cf = True
        self.athena_bucket_lifecycle_expiration = 7
        self.variables = {}

    def execute(self, *args, **kwargs):
        """Execute the initilization"""
        print("Initializing AWS environment...")
        print("-------------------------------")
        # Collect partition and CUR bucket path
        self._get_base_data()
        # Create QuickSight Enterprise subscription
        self._create_quicksight_enterprise_subscription()
        # Create query results bucket
        self._create_query_results_bucket()
        # Create Athena workgroup "cid"
        self._create_athena_workgroup()
        # Create Glue database
        self._create_glue_database()
        # Create Glue crawler role with permissions
        self._create_glue_crawler_role()
        self._attach_policies_to_crawler_role()

        # Create crawler and table
        self._create_glue_crawler()
        self._create_glue_table()

    def _get_base_data(self):
        self.aws_partition = get_parameter("aws-partition", "Please, choose an AWS partition", choices=["aws", "aws-cn"], default="aws")
        self.cur_path = get_parameter("cur-path", "Please, provide your CUR path", default=self.cur_path)
        self.processed_cur_path = extract_cur_bucket_parameters(self.cur_path)
        
        lifecycle_days = get_parameter("athena-bucket-lifecycle-expiration", 
                                       "Please, provide the number of days after which Athena queries should expire",
                                       default=str(self.athena_bucket_lifecycle_expiration))
        while not lifecycle_days.isdigit():
            print('Please, only use numbers.')
            lifecycle_days = get_parameter("athena-bucket-lifecycle-expiration", 
                                       "Please, provide the number of days after which Athena queries should expire",
                                       default=self.athena_bucket_lifecycle_expiration)
        
        self.athena_bucket_lifecycle_expiration = int(lifecycle_days)
            

        self.cid_crawler_role_arn = get_parameter("glue-role-arn", "Glue role ARN. Hit ENTER to create new role", default="")
        self.cur_is_managed_by_cf = get_yesno_parameter(
            "cur_is_managed_by_cf", message="If CUR was created manually AND it is a single account or single payer account CUR, select no", default="yes"
        )

        self.variables = {
            "${AWS::Region}": self.cid.base.region,
            "${AWS::Partition}": self.aws_partition,
            "${AWS::AccountId}": self.cid.base.account_id,
            "${CidCURDatabase}": self.database_name,
            "${ProcessedCURPath.Bucket}": self.processed_cur_path["Bucket"],
            "${ProcessedCURPath.Path}": self.processed_cur_path["Path"],
            "${ProcessedCURPath.Folder}": self.processed_cur_path["Folder"],
            "${GlueCrawlerName}": self.cid_crawler_name,
        }

    def _create_glue_crawler_role(self):
        """Create IAM role for Glue crawler"""
        if self.cid_crawler_role_arn != "":
            print(f"\tGlue role ARN...\tProvided ({self.cid_crawler_role_arn})")
        try:
            assume_role_policy_document = pkg_resources.read_text("cid.builtin.core.data.iam", "glue_assume_role_policy_document.json")
        except Exception:  # pylint: disable=broad-except
            logger.exception('ERROR')
            print("\tGlue role ARN...\tERROR: Could not load role policy document")

        try:
            self.cid_crawler_role_arn = self.cid.iam.create_role(role_name=self.cid_crawler_role_name, assume_role_policy_document=assume_role_policy_document)
            print(f"\tGlue role ARN...\tCreated ({self.cid_crawler_role_arn})")
        except Exception:  # pylint: disable=broad-except
            logger.warning("WARNING: Cannot create glue role")
            self.cid_crawler_role_arn = self.cid.iam.get_role_arn(role_name=self.cid_crawler_role_name)
            print(f"\tGlue role ARN...\tExists ({self.cid_crawler_role_arn})")

    def _attach_policies_to_crawler_role(self):
        managed_policies = [f"arn:{self.aws_partition}:iam::aws:policy/service-role/AWSGlueServiceRole"]
        custom_policies = {"AWSCURCrawlerComponentFunction": "aws_cur_crawler_component_function.json", "AWSCURKMSDecryption": "aws_cur_kms_decryption.json"}

        print("\tAttaching policies...")
        for policy in managed_policies:
            print(f"\t\t{policy}")
            self.cid.iam.attach_policy(role_name=self.cid_crawler_role_name, policy_arn=policy)

        for name, policy_file in custom_policies.items():
            policy_document = pkg_resources.read_text("cid.builtin.core.data.iam", policy_file)
            policy_document = inject_variables(source=policy_document, variables=self.variables)

            try:
                policy = self.cid.iam.create_policy_from_json(policy_name=name, policy_document=policy_document)
            except Exception:  # pylint: disable=broad-except
                policy = f"arn:{self.aws_partition}:iam::{self.cid.base.account_id}:policy/{name}"
            print(f"\t\t{policy}")
            self.cid.iam.attach_policy(role_name=self.cid_crawler_role_name, policy_arn=policy)

    def _create_glue_crawler(self):
        """Create a new Glue crawler"""
        try:
            self.cid.glue.create_crawler(
                name=self.cid_crawler_name, role_arn=self.cid_crawler_role_arn, database_name=self.database_name, processed_cur_path=self.processed_cur_path
            )
            print(f"\tGlue crawler...\t\tCreated ({self.cid_crawler_name})")
        except CidError:
            print(f"\tGlue crawler...\t\tExists ({self.cid_crawler_name})")
        except Exception as ex:  # pylint: disable=broad-except
            logger.exception("ERROR: %s", ex)
            print("\tGlue crawler...\t\tERROR: Could not create crawler")

    def _create_glue_table(self):
        """Create a new table in Glue"""
        print("\tGlue table...", end="")
        # Load table columns
        table_columns = json.loads(pkg_resources.read_text("cid.builtin.core.data.glue", "table_columns.json"))
        # Load table partition keys
        partition_keys = json.loads(pkg_resources.read_text("cid.builtin.core.data.glue", "table_partition_keys.json"))
        partition_keys = partition_keys["yes" if self.cur_is_managed_by_cf else "no"]
        # Load table definition
        table_definition_str = pkg_resources.read_text("cid.builtin.core.data.glue", "cur_table.json")
        # Inject variables
        table_definition_str = inject_variables(source=table_definition_str, variables=self.variables)
        table_definition = json.loads(table_definition_str)
        # Inject table columns and partition keys
        table_definition["TableInput"]["StorageDescriptor"]["Columns"] = table_columns
        table_definition["TableInput"]["PartitionKeys"] = partition_keys
        # Create table
        table_definition_str = json.dumps(table_definition)
        self.cid.glue.create_or_update_table(view_name="cur", view_query=table_definition_str)
        print("\t\tOK")

    def _create_glue_database(self):
        """Create Glue database"""
        try:
            self.cid.glue.create_database(name=self.database_name, catalog_id=self.catalog_id)
            print(f"\tGlue Database...\tCreated ({self.database_name} in {self.catalog_id})")
        except CidError:
            print(f"\tGlue Database...\tExists ({self.database_name} in {self.catalog_id})")
        except Exception as ex:  # pylint: disable=broad-except
            logger.exception(str(ex))
            print("\tGlue Database...\tFailed")

    def _create_athena_workgroup(self):
        """Create Athena workgroup"""
        try:
            self.cid.athena.create_workgroup(workgroup_name=self.athena_workgroup_name, s3_bucket_name=self.bucket_name)
            print(f"\tAthena Workgroup...\tCreated ({self.athena_workgroup_name})")
        except CidError:
            print(f"\tAthena Workgroup...\tExists ({self.athena_workgroup_name})")
        except Exception as ex:  # pylint: disable=broad-except
            logger.exception(str(ex))
            print("\tAthena Workgroup...\tFailed")

    def _create_query_results_bucket(self):
        """Create bucket for storing query results"""
        try:
            self.cid.s3.create_bucket(self.bucket_name, self.athena_bucket_lifecycle_expiration)
            print(f"\tAthena S3 Bucket...\tCreated ({self.bucket_name})")
        except CidError as ex:
            print(f'\tAthena S3 Bucket...\t{ex} ({self.bucket_name})')
        except CidCritical as ex:
            print(f'\tAthena S3 Bucket...\t{ex} ({self.bucket_name})')
            sys.exit(1)
        except Exception as ex:  # pylint: disable=broad-except
            print("\tAthena S3 Bucket...\tFailed")
            logger.error("ERROR: %s", ex)

    def _create_quicksight_enterprise_subscription(self):
        """Enable QuickSight Enterprise if not enabled already"""
        required_editions = {"ENTERPRISE", "ENTERPRISE_AND_Q"}

        if self.cid.qs.edition in required_editions:
            logger.info('QuickSight Edition: "%s", nothing to do', self.cid.qs.edition)
            print("\tQuickSight Edition...\tOK")
            return

        logger.info('QuickSight Edition: "%s", needs to be in [%s]', self.cid.qs.edition, ", ".join(required_editions))
        print(f'\tQuickSight Edition...\t{self.cid.qs.edition}, needs to be one of {", ".join(required_editions)}')
        print(
            "\tIMPORTANT: QuickSight Enterprise is required for Cost Intelligence Dashboard. "
            "This will lead to costs in your AWS account (https://aws.amazon.com/quicksight/pricing/)."
        )
        if not self.cid.all_yes:
            enable_quicksight_enterprise = get_yesno_parameter(
                param_name="enable-quicksight-enterprise", message="Please, confirm that you are OK with enabling QuickSight Enterprise", default="no"
            )
        else:
            enable_quicksight_enterprise = True

        if not enable_quicksight_enterprise:
            print("\tInitalization cancelled")
            return

        email = self.cid.organizations.get_account_email()
        print(
            "\n\tQuicksight needs an email address that you want it to send notifications to "
            "regarding your Amazon QuickSight account or Amazon QuickSight subscription."
        )
        counter = 0
        while not email or "@" not in email or "." not in email:
            counter += 1
            email = get_parameter("qs-notification-email", "Notification email", default=email)
            if "@" not in email or "." not in email:
                print(f"\t{email} does not seem to be a valid email. Please, try again.")
                unset_parameter("qs-notification-email")
                if counter >= 5:
                    exit(1)

        account_name = self.cid.organizations.get_account_name()
        counter = 0
        print(
            "\n\tPlease, choose a descriptive name for your QuickSight account. "
            "This will be used later to share it with your users. This can NOT be changed later."
        )
        while not account_name or account_name == "":
            counter += 1
            account_name = get_parameter("qs-account-name", "QuickSight Account Name", default=account_name)
            if account_name == "":
                print("\t The account name must not be empty. Please, try again.")
                unset_parameter("qs-account-name")
                if counter >= 5:
                    sys.exit(1)

        params = {
            "Edition": "ENTERPRISE",
            "AuthenticationMethod": "IAM_AND_QUICKSIGHT",
            "AwsAccountId": self.cid.base.account_id,
            "AccountName": account_name,  # Should be a parameter with a reasonable default
            "NotificationEmail": email,  # Read the value from account parameters as a default
        }

        response = self.cid.qs.client.create_account_subscription(**params)
        if response.get("Status", 0) == 200:
            print("\tQuickSight Edition...\tSubscribed")


def extract_cur_bucket_parameters(s3_path: str) -> Dict[str, str]:
    """Extract CUR bucket parameters from s3_path string"""
    partitions = {
        "managed_by_cfn": ["source_account_id", "cur_name_1", "cur_name_2", "year", "month"],
        "manual": ["year", "month"],
    }

    data = {}
    if s3_path.startswith("s3://"):
        s3_path = s3_path[len("s3://") :]
    if s3_path.endswith("/"):
        s3_path = s3_path[:-1]
    parts = s3_path.split("/")
    data["Bucket"] = parts[0]
    if len(parts[1:]) == 1:  # most likely it is created by CFN or similar
        data["Partitions"] = partitions["managed_by_cfn"]
    elif len(parts) > 3 and parts[-1] == parts[-2]:  # most likely it is manual CUR
        data["Partitions"] = partitions["manual"]
    else:
        raise CidError(
            f"CUR BucketPath={parts[0]} format is not recognized. It must be s3://(bucket)/cur or s3://{bucket}/{curprefix}/{curname}/{curname} "
        )  # pylint: disable=line-too-long
    data["Partitions"] = [{"Name": p, "Type": "string"} for p in data["Partitions"]]
    data["Path"] = "/".join(parts[1:])
    data["Folder"] = parts[-1] if len(parts) > 1 else ""
    data["Folder"] = data["Folder"].replace("-", "_").lower()  # this is used for a Glue table name that will be managed by crawler

    return data
