# CUDOS Framework: Enterprise Dashboards

## Welcome to customer automation for CUDOS Framework repository

### The scripts in this repo have been succesfully tested in [AWS CloudShell](https://console.aws.amazon.com/cloudshell/home)

In the [**cudos**](./cudos/) subdirectory you will find a set of scripts automate some parts of the [CUDOS workshop](https://cudos.workshop.aws/), specifically parts of:
  - creating Athena views
  - creating Amazon QuickSight datasource
  - creating Amazon QuickSight datasets
  - deploying the CUDOS dashboard to Amazon QuickSight
  - creating proper account mapping from account id's to account names

In the [**tao**](./tao/) subdirectory you will find a set of scripts automate [Trusted Advisor Organisation view dashboard](https://d1s0yx3p3y3rah.cloudfront.net/anonymous-embed) deployment, specifically parts of:
  - creating AWS Glue Data Catalog
  - creating Amazon QuickSight datasource
  - creating Amazon QuickSight datasets
  - deploying the TAO dashboard to Amazon QuickSight

In the [**trends**](./trends/) subdirectory you will find a set of scripts automate some parts of the [CUDOS workshop](https://cudos.workshop.aws/workshop-trends.html), specifically parts of:
  - creating Athena views
  - creating Amazon QuickSight datasource
  - creating Amazon QuickSight datasets
  - deploying the Trends dashboard to Amazon QuickSight
  - creating proper account mapping from account id's to account names

## How to use this repo

##### Important: Complete the [Prerequisites](https://cudos.workshop.aws/prerequisites.html)
##### Important: [Specifying a Query Result Location Using a Workgroup](https://docs.aws.amazon.com/athena/latest/ug/querying.html#query-results-specify-location-workgroup)

1. Launch [AWS CloudShell](https://console.aws.amazon.com/cloudshell/home)
2. Clone the repo

  ```bash
  git clone https://github.com/aws-samples/aws-cudos-framework-deployment
  ```

3. Change directory to the respectful dashboard deployment. Run the setup scripts per the instructions in the repo

  ```bash
  cd cudos
  ./shell-script/customer-cudos.sh
  ```



