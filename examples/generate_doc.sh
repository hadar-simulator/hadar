#! /bin/bash

for f in *.ipynb; do
  jupyter nbconvert  --execute \'$f\' --ExecutePreprocessor.store_widget_state=True --to HTML;
done

for f in *.html; do
  mv \'$f\' \'../docs/sources/_static/examples/$f\';
done