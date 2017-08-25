
.PHONY: clean vpro 3voor12

vpro:
	../check_with_sitemap.py \
		-e prod --http_to_https \
		--delete \
		--post_process "lambda url: re.sub(r'^https://www.vpro.nl/speel[~\.](.*?)[~\.](.*)', r'https://www.vpro.nl/speel~\1~.html', url)" \
		https://magnolia1-frontend1-prod.vpro.nl/vpronl/sitemap.xml \
		vpro-predictions
		#		https://www.vpro.nl/sitemap.xml vpro-predictions


3voor12:
	../check_with_sitemap.py \
		-e prod --http_to_https \
		--post_process "lambda url: re.sub(r'^https://3voor12.vpro.nl(.*)/update[~\.](.*?)[~\.](.*)', r'https://3voor12.vpro.nl/\1update~\2~.html', url)" \
		https://magnolia1-frontend1-prod.vpro.nl/3v12/sitemap.xml \
		3voor12

clean:
	rm -f /tmp/*.p
