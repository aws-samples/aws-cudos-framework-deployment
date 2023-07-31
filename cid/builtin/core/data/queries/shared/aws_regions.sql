CREATE OR REPLACE VIEW aws_regions AS
SELECT *
FROM
  (
 VALUES
     ROW ('ap-northeast-1', 'Japan', 'Tokyo', '35.64', '139.76', 'Asia/Tokyo')
   , ROW ('ap-south-1', 'India', 'Mumbai', '19.08', '72.88', 'Asia/Kolkata')
   , ROW ('cn-northwest-1', 'China', 'Ningxia', '38.47', '106.26', 'Asia/Beijing')
   , ROW ('eu-central-1', 'Germany', 'Frankfurt', '50.11', '8.68', 'Europe/Berlin')
   , ROW ('eu-north-1', 'Sweden', 'Stockholm', '59.33', '18.07', 'Europe/Stockholm')
   , ROW ('eu-west-1', 'Ireland', 'Dublin', '53.28', '-7.71', 'Europe/Dublin')
   , ROW ('us-east-2', 'USA', 'Ohio', '40.36', '-82.91', 'America/New_York')
   , ROW ('us-gov-west-1', 'USA', 'Oregon', '39.53', '-119.88', 'US/Pacific')
   , ROW ('us-west-1', 'USA', 'N. California', '36.55', '-119.89', 'America/Los_Angeles')
   , ROW ('us-west-2', 'USA', 'Oregon', '43.82', '-120.33', 'America/Los_Angeles')
   , ROW ('ap-east-1', 'Hong Kong', 'Hong Kong', '22.28', '114.15', 'Asia/Hong_Kong')
   , ROW ('ap-northeast-2', 'South Korea', 'Seoul', '37.72', '126.04', 'Asia/Seoul')
   , ROW ('ap-northeast-3', 'Japan', 'Osaka', '34.69', '135.5', 'Asia/Tokyo')
   , ROW ('ap-southeast-2', 'Australia', 'Sydney', '-33.88', '151.23', 'Australia/Sydney')
   , ROW ('ca-central-1', 'Canada', 'Montral', '44.08', '-77.42', 'America/Toronto')
   , ROW ('cn-north-1', 'China', 'Beijing', '39.91', '116.41', 'Asia/Beijing')
   , ROW ('eu-west-3', 'France', 'Paris', '48.85', '2.35', 'Europe/Paris')
   , ROW ('me-south-1', 'Bahrain', 'Bahrain', '26.11', '50.50', 'Asia/Riyadh')
   , ROW ('sa-east-1', 'Brazil', 'Sao Paulo', '-23.37', '-46.63', 'America/Sao_Paulo')
   , ROW ('us-gov-east-1', 'USA', 'Ohio', '40.4897', '-81.45', 'US/Eastern')
   , ROW ('ap-southeast-1', 'Singapore', 'Singapore', '1.35', '103.86', 'Asia/Singapore')
   , ROW ('eu-west-2', 'UK', 'London', '51.53', '0.12', 'Europe/London')
   , ROW ('us-east-1', 'USA', 'Washington DC', '38.80', '-77.11', 'America/New_York')
   , ROW ('eu-south-1', 'Italy', 'Milan', '45.46', '9.18', 'Europe/Rome')
   , ROW ('af-south-1', 'Africa', 'Cape Town', '-33.91', '18.42', 'Africa/Blantyre')
   , ROW ('ap-southeast-3', 'Indonesia', 'Jakarta', '-6.17', '106.82', 'Asia/Jakarta')
   , ROW ('ap-southeast-4', 'Australia', 'Melbourne', '-37.81', '144.96', 'Australia/Melbourne')
   , ROW ('eu-south-2', 'Spain', 'Madrid', '40.41', '-3.70', 'Europe/Madrid')
   , ROW ('eu-central-2', 'Switzerland', 'Zurich', '47.37', '8.54', 'Europe/Zurich')
   , ROW ('me-central-1', 'UAE', 'Dubai', '25.27', '55.29', 'Asia/Dubai')
)  ignored_table_name (region_name, region_country, region_city, region_latitude, region_longitude, region_timezone)
