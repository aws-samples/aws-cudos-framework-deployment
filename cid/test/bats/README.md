# CID Bash tests

## Prerequisites
* Account with data from Cost Optimization Collection Lab, CUR, Configured Athena and QuickSight


## Install
on Mac:

	brew install bats-core
	brew install parallel


Others: see https://bats-core.readthedocs.io/en/latest/installation.html

## Run

Non-parallel (each test runs in 1-3 min)

	bats cid/test/bats/cudos.bats \
		--print-output-on-failure \
		--recursive  \
		--timing \
		--trace


Parallel (All test test run in 3 min)

	bats cid/test/bats/ \
		--jobs 5 \
		--no-parallelize-within-files \
		--print-output-on-failure \
		--recursive  \
		--timing \
		--trace
