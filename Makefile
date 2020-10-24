# Dev utilities. No impact on the deployed application.

install:
	pip3 install -r requirements.txt

run:
	dev_appserver.py --port=8080 app.yaml

open:
	open http://localhost:8080/

clean:
	rm -rf __pycache__

deploy:
	gcloud app deploy --project "arxiv-feeds"

open-prod:
	gcloud app browse -s itsnicethat-feed
