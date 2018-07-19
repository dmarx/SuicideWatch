#! /bin/sh

PROJ_DIR= ~/SuicideWatch

python3 $PROJ_DIR/src/build_dataset.py --get-new-submissions
python3 $PROJ_DIR/src/build_dataset.py --parse-sentences
