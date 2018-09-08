PROJ_DIR=~/SuicideWatch

# scraper commands

setup_aws:
	sudo amazon-linux-extras install python3
	curl -O https://bootstrap.pypa.io/get-pip.py
	python3 get-pip.py --user

prebuilt_dataset:
	python3 download_file_from_google_drive.py

setup_scraper:
	pip install ipython --user
	pip install psaw --user
	pip install numpy --user
	pip install nltk --user
	python3 -c 'import nltk; nltk.download("punkt")'

	sudo cp $(PROJ_DIR)/src/data_update_cronjob.sh /etc/cron.daily/

backfill_data:
	python3 $(PROJ_DIR)/src/build_dataset.py --backfill-submissions
	python3 $(PROJ_DIR)/src/build_dataset.py --parse-sentences

update_data:
	python3 $(PROJ_DIR)/src/build_dataset.py --get-new-submissions
	python3 $(PROJ_DIR)/src/build_dataset.py --parse-sentences
