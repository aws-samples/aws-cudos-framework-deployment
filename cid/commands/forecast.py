import os
import json
import logging
import datetime
import tempfile
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

from cid.commands.command_base import CommandBase
from cid.utils import get_parameter, get_parameters, set_parameters, cid_print

logger = logging.getLogger(__name__)

class ForecastCommand(CommandBase):
    """Command to generate AWS Cost Explorer forecasts"""

    def __init__(self, cid, **kwargs):
        super().__init__(cid, **kwargs)
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.output_dir = os.path.join(os.getcwd(), 'output', self.timestamp)
        self.temp_dir = os.path.join(self.output_dir, 'temp')
        self.output_file = os.path.join(self.output_dir, f'forecast_{self.timestamp}.csv')

        # Available metrics for Cost Explorer forecasts
        self.metrics = [
            "AMORTIZED_COST",
            "BLENDED_COST",
            "NET_AMORTIZED_COST",
            "NET_UNBLENDED_COST",
            "UNBLENDED_COST",
            "USAGE_QUANTITY",
            "NORMALIZED_USAGE_AMOUNT"
        ]

        # Available dimensions for Cost Explorer forecasts
        self.dimensions = [
            "AZ",
            "INSTANCE_TYPE",
            "LINKED_ACCOUNT",
            "LINKED_ACCOUNT_NAME",
            "OPERATION",
            "PURCHASE_TYPE",
            "REGION",
            "SERVICE",
            "USAGE_TYPE",
            "USAGE_TYPE_GROUP",
            "RECORD_TYPE",
            "OPERATING_SYSTEM",
            "TENANCY",
            "SCOPE",
            "PLATFORM",
            "SUBSCRIPTION_ID",
            "LEGAL_ENTITY_NAME",
            "DEPLOYMENT_OPTION",
            "DATABASE_ENGINE",
            "INSTANCE_TYPE_FAMILY",
            "BILLING_ENTITY",
            "RESERVATION_ID",
            "SAVINGS_PLAN_ARN"
        ]

        # Create output directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

    def execute(self) -> None:
        """Execute the forecast command"""
        cid_print("<BLUE><BOLD>AWS Cost Forecast Data Fetch Tool</BOLD></BLUE>")

        # Get time period
        self._get_time_period()

        # Select metrics, dimensions, and granularity
        self._select_options()

        # Process forecast
        cid_print("\n<YELLOW><BOLD>Processing Forecasts</BOLD></YELLOW>\n")
        self._process_forecast()

        # Upload to S3 if requested
        self._upload_to_s3()

        # Generate QuickSight manifest if uploaded to S3
        if get_parameters().get('s3-bucket'):
            self._generate_quicksight_manifest()

        # Clean up temporary files
        self._cleanup()

    def _get_time_period(self) -> None:
        """Get the time period for the forecast"""
        cid_print("<YELLOW><BOLD>Time Period Selection</BOLD></YELLOW>")

        choice = get_parameter(
            param_name='time-period',
            message="Select Time Period",
            choices={
                "Next 30 days": "30",
                "Next 90 days": "90",
                "Next 180 days": "180",
                "Next 365 days": "365",
                "Custom period": "custom"
            },
            default="30"
        )

        today = datetime.date.today().strftime('%Y-%m-%d')
        self.start_date = today

        if choice == "custom":
            self.end_date = get_parameter(
                param_name='end-date',
                message="Enter end date (YYYY-MM-DD)",
                default=(datetime.date.today() + datetime.timedelta(days=30)).strftime('%Y-%m-%d')
            )
        else:
            days = int(choice)
            self.end_date = (datetime.date.today() + datetime.timedelta(days=days)).strftime('%Y-%m-%d')

        self.time_period = f"Start={self.start_date},End={self.end_date}"
        cid_print(f"Time period set: {self.start_date} to {self.end_date}")

    def _select_options(self) -> None:
        """Select metrics, dimensions, and granularity"""
        cid_print("<YELLOW><BOLD>Metric Selection</BOLD></YELLOW>")

        # Select metrics
        metric_choices = {"All metrics": "all"}
        for i, metric in enumerate(self.metrics):
            metric_choices[metric] = metric

        metric_selection = get_parameter(
            param_name='metrics',
            message="Select metrics (comma-separated for multiple)",
            choices=metric_choices,
            default="UNBLENDED_COST"
        )

        if metric_selection == "all":
            self.selected_metrics = self.metrics
        else:
            self.selected_metrics = [m.strip() for m in metric_selection.split(',')]

        cid_print(f"Selected {len(self.selected_metrics)} metrics")

        # Select dimensions
        cid_print("<YELLOW><BOLD>Dimension Selection</BOLD></YELLOW>")

        dimension_choices = {"All dimensions": "all"}
        for i, dimension in enumerate(self.dimensions):
            dimension_choices[dimension] = dimension

        dimension_selection = get_parameter(
            param_name='dimensions',
            message="Select dimensions (comma-separated for multiple)",
            choices=dimension_choices,
            default="SERVICE"
        )

        if dimension_selection == "all":
            self.selected_dimensions = self.dimensions
        else:
            self.selected_dimensions = [d.strip() for d in dimension_selection.split(',')]

        cid_print(f"Selected {len(self.selected_dimensions)} dimensions")

        # Select granularity
        cid_print("<YELLOW><BOLD>Granularity Selection</BOLD></YELLOW>")

        self.granularity = get_parameter(
            param_name='granularity',
            message="Select Granularity",
            choices={"DAILY": "DAILY", "MONTHLY": "MONTHLY"},
            default="MONTHLY"
        )

        cid_print(f"Selected {self.granularity} granularity")

    def _get_dimension_values(self, dimension: str) -> List[str]:
        """Get values for a specific dimension"""
        cid_print(f"Fetching values for dimension: {dimension}")

        try:
            response = self.cid.base.session.client('ce').get_dimension_values(
                TimePeriod={
                    'Start': (datetime.date.today() - datetime.timedelta(days=30)).strftime('%Y-%m-%d'),
                    'End': datetime.date.today().strftime('%Y-%m-%d')
                },
                Dimension=dimension
            )

            values = [item['Value'] for item in response.get('DimensionValues', [])]
            return values
        except Exception as e:
            logger.warning(f"Failed to fetch dimension values for {dimension}: {str(e)}")
            return []

    def _fetch_forecast(self, dimension: str, value: str, metric: str) -> None:
        """Fetch forecast for a specific dimension, value, and metric"""
        output_file = os.path.join(self.temp_dir, f"{dimension}_{value.replace('/', '_')}_{metric}.json")

        filter_json = {
            "Dimensions": {
                "Key": dimension,
                "Values": [value]
            }
        }

        try:
            response = self.cid.base.session.client('ce').get_cost_forecast(
                TimePeriod={
                    'Start': self.start_date,
                    'End': self.end_date
                },
                Metric=metric,
                Granularity=self.granularity,
                PredictionIntervalLevel=95,
                Filter=filter_json
            )

            with open(output_file, 'w') as f:
                json.dump(response, f)

            # Process the response and append to the output file
            with open(f"{self.output_file}.tmp", 'a') as out_file:
                for result in response.get('ForecastResultsByTime', []):
                    row = [
                        dimension,
                        value,
                        metric,
                        result['TimePeriod']['Start'],
                        result['TimePeriod']['End'],
                        result['MeanValue'],
                        result.get('PredictionIntervalLowerBound', ''),
                        result.get('PredictionIntervalUpperBound', '')
                    ]
                    out_file.write(','.join([str(item) for item in row]) + '\n')

            # Remove the temporary JSON file
            os.remove(output_file)

        except Exception as e:
            logger.warning(f"Failed to fetch forecast for {dimension}={value}, metric={metric}: {str(e)}")

    def _process_forecast(self) -> None:
        """Process forecasts in parallel using boto3 client"""
        # Create header for the output file
        with open(self.output_file, 'w') as f:
            f.write("Dimension,Value,Metric,StartDate,EndDate,MeanValue,LowerBound,UpperBound\n")

        # Create temporary file for results
        with open(f"{self.output_file}.tmp", 'w'):
            pass  # Just create an empty file

        # Calculate total jobs
        total_jobs = 0
        dimension_values = {}

        for dimension in self.selected_dimensions:
            values = self._get_dimension_values(dimension)
            dimension_values[dimension] = values
            value_count = len(values)
            dimension_total = value_count * len(self.selected_metrics)
            total_jobs += dimension_total

            cid_print(f"Found {value_count} values for {dimension}, adding {dimension_total} jobs")

        cid_print(f"Total jobs to process: {total_jobs}")

        # Process forecasts
        completed_jobs = 0

        for dimension in self.selected_dimensions:
            cid_print(f"Processing dimension: {dimension}")

            for value in dimension_values[dimension]:
                for metric in self.selected_metrics:
                    self._fetch_forecast(dimension, value, metric)
                    completed_jobs += 1
                    progress = int(completed_jobs * 100 / total_jobs)
                    self._display_progress(progress, "Processing forecasts")

        # Combine results
        if os.path.exists(f"{self.output_file}.tmp"):
            with open(f"{self.output_file}.tmp", 'r') as tmp_file:
                with open(self.output_file, 'a') as out_file:
                    out_file.write(tmp_file.read())
            os.remove(f"{self.output_file}.tmp")
            cid_print("\nData collection completed")
        else:
            cid_print("\nNo data was collected")

    def _display_progress(self, progress: int, text: str) -> None:
        """Display progress bar"""
        width = 40
        filled = int(progress * width / 100)
        empty = width - filled

        bar = '█' * filled + '░' * empty
        cid_print(f"\r\033[0;36m{text}: [{bar}] {progress}%\033[0m", end='')

    def _upload_to_s3(self) -> None:
        """Upload results to S3"""
        cid_print("\n<YELLOW><BOLD>S3 Upload</BOLD></YELLOW>")

        s3_bucket = get_parameter(
            param_name='s3-bucket',
            message="Enter S3 bucket name (or press Enter to skip)",
            default=""
        )

        if s3_bucket:
            set_parameters({'s3-bucket': s3_bucket})
            cid_print(f"Uploading to S3...")

            try:
                s3_client = self.cid.base.session.client('s3')
                s3_key = f"forecasts/{os.path.basename(self.output_file)}"

                s3_client.upload_file(
                    self.output_file,
                    s3_bucket,
                    s3_key
                )

                cid_print(f"File uploaded to s3://{s3_bucket}/{s3_key}")
            except Exception as e:
                cid_print(f"Failed to upload to S3: {str(e)}")

    def _generate_quicksight_manifest(self) -> None:
        """Generate QuickSight manifest file"""
        s3_bucket = get_parameters().get('s3-bucket')
        if not s3_bucket:
            return

        cid_print("<YELLOW><BOLD>QuickSight Configuration</BOLD></YELLOW>")
        cid_print("Generating QuickSight manifest file...")

        csv_s3_uri = f"s3://{s3_bucket}/forecasts/{os.path.basename(self.output_file)}"
        manifest_file = os.path.join(self.output_dir, "manifest.json")

        manifest = {
            "fileLocations": [
                {
                    "URIs": [
                        csv_s3_uri
                    ]
                }
            ],
            "globalUploadSettings": {
                "format": "CSV",
                "delimiter": ",",
                "textqualifier": "\"",
                "containsHeader": "true"
            }
        }

        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=4)

        try:
            s3_client = self.cid.base.session.client('s3')
            s3_client.upload_file(
                manifest_file,
                s3_bucket,
                "forecasts/manifest.json"
            )

            cid_print(f"QuickSight manifest uploaded to s3://{s3_bucket}/forecasts/manifest.json")

            cid_print("<YELLOW><BOLD>QuickSight Setup</BOLD></YELLOW>")
            cid_print("<GREEN><BOLD>QuickSight Import Instructions:</BOLD></GREEN>")
            cid_print("1. In QuickSight, create a new dataset")
            cid_print("2. Choose 'S3' as the data source")
            cid_print(f"3. Use this manifest URL: s3://{s3_bucket}/forecasts/manifest.json")
            cid_print("4. Configure permissions to allow QuickSight to access the S3 bucket")
        except Exception as e:
            cid_print(f"Failed to upload manifest file to S3: {str(e)}")

    def _cleanup(self) -> None:
        """Clean up temporary files"""
        cid_print("Cleaning up temporary files...")
        if os.path.exists(self.temp_dir):
            for file in os.listdir(self.temp_dir):
                os.remove(os.path.join(self.temp_dir, file))
            os.rmdir(self.temp_dir)
