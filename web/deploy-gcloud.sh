cp ../requirements.txt .
mkdir -p "tqec" && cp -r ../src/tqec/ tqec/
gcloud app deploy
