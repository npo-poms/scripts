
.PHONY: clean vpro

vpro:
	../check_with_sitemap.py \
		-e localhost --http_to_https \
		--post_process "lambda url: re.sub(r'^https://www.vpro.nl/speel[~\.](.*?)[~\.](.*)', r'https://www.vpro.nl/speel~\1~.html', url)" \
		https://www.vpro.nl/sitemap.xml vpro-predictions


clean:
	rm /tmp/*.p
