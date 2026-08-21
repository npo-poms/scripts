

postinvalide:
	curl -XPOST -H 'Content-Type: application/json'  -u "${RCRS_CREDS}"  https://api.poms.omroep.nl/authority/RCRS?validationLevel=WARNING -d@invalid_input.json

postinvalidtest:
	curl -XPOST -H 'Content-Type: application/json'  -u "${RCRS_CREDS_TEST}"  'https://api-test.poms.omroep.nl/authority/RCRS?validationLevel=WARNING&validate=false' -d@invalid_input.json

postinvalidlocalhost:
	curl -XPOST -H 'Content-Type: application/json'  -u "${RCRS_CREDS_TEST}"  'http://localhost:8071/rs/authority/RCRS?validateInput=false' -d@invalid_input.json


postfixablelocalhost:
	curl -XPOST -H 'Content-Type: application/json'  -u "${RCRS_CREDS_TEST}"  'http://localhost:8071/rs/authority/RCRS' -d@fixable_input.json


postvalid:
	curl -XPOST -H 'Content-Type: application/json'  -u "${RCRS_CREDS}" https://api.poms.omroep.nl/authority/RCRS?validationLevel=WARNING -d@input.json


postsegmentacc:
	curl -XPOST -H 'Content-Type: application/xml'  -u "${RCRS_CREDS_TEST}" https://api-acc.poms.omroep.nl/authority/RCRS?validationLevel=WARNING -d@segment.xml

postlongacc:
	curl -XPOST -H 'Content-Type: application/json'  -u "${RCRS_CREDS_TEST}" 'https://api-acc.poms.omroep.nl/authority/RCRS?validate=true' -d@longtitle.json

postlonglocalhost:
	curl -XPOST -H 'Content-Type: application/json'  -u "${RCRS_CREDS_TEST}" 'http://localhost:8071/rs/authority/RCRS?validationLevel=POMS' -d@longtitle.json

postsegmenttest:
	curl -XPOST -H 'Content-Type: application/xml'  -u "${RCRS_CREDS_TEST}" https://api-test.poms.omroep.nl/authority/RCRS?validationLevel=WARNING -d@segment.xml


postvalidacc:
	curl -XPOST -H 'Content-Type: application/json'  -u "${RCRS_CREDS_TEST}" https://api-test.poms.omroep.nl/authority/RCRS?validationLevel=WARNING -d@input.json

quick:
	curl -XPOST -H 'Content-Type: application/xml'  -u "${RCRS_CREDS_TEST}" 'https://api-acc.poms.omroep.nl/authority/RCRS?validationLevel=WARNING&errors=michiel.meeuwissen@gmail.com' -d@quick_program.xml
