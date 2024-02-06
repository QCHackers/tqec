cp ../requirements.txt .
mkdir -p "tqec" && cp -r ../tqec/* tqec/
gcloud app deploy
