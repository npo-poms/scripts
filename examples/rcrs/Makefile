

postinvalide:
	curl -XPOST -H 'Content-Type: application/json'  -u "${RCRS_CREDS}"  https://api.poms.omroep.nl/authority/RCRS?validationLevel=WARNING -d@invalid_input.json

postvalid:
	curl -XPOST -H 'Content-Type: application/json'  -u "${RCRS_CREDS}"' https://api.poms.omroep.nl/authority/RCRS?validationLevel=WARNING -d@input.json


postvalidacc:
	curl -XPOST -H 'Content-Type: application/json'  -u "${RCRS_CREDS_TEST}" https://api-test.poms.omroep.nl/authority/RCRS?validationLevel=WARNING -d@input.json

quick:
	curl -XPOST -H 'Content-Type: application/xml'  -u "${RCRS_CREDS_TEST}	" 'https://api-acc.poms.omroep.nl/authority/RCRS?validationLevel=WARNING&errors=michiel.meeuwissen@gmail.com' -d@quick_program.xml
