cp ../requirements.txt .
mkdir -p "tqec" && cp -r ../tqec/* tqec/
gcloud app deploy
rm requirements.txt
rm -rf tqec/