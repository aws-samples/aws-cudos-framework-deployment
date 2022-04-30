
athena_database=athenacurcfn_cur1

cid-cmd deploy \
  --dashboard-id 'cudos'  \
  --athena-database $athena_database  \
  --account-map-source 'dummy'


cid-cmd -y delete \
   --dashboard-id 'cudos' \
   --athena-database $athena_database
