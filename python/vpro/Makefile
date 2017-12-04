
all: clean vpro 3voor12 human

.PHONY: vpro 3voor12 human clean

vpro:
	../check_with_sitemap.py \
		-e prod --http_to_https \
		--clean \
		--target_directory ~/integrity-check-results \
		--post_process "lambda url: re.sub(r'^https://www.vpro.nl/speel[~\.](.*?)[~\.](.*)', r'https://www.vpro.nl/speel~\1~.html', url)" \
		https://magnolia1-frontend1-prod.vpro.nl/vpronl/sitemap.xml \
		vpro-predictions


3voor12:
	../check_with_sitemap.py \
		-e prod --http_to_https \
		--clean \
		--target_directory ~/integrity-check-results \
		--post_process "lambda url: re.sub(r'^https://3voor12.vpro.nl(.*)/update[~\.](.*?)[~\.](.*)', r'https://3voor12.vpro.nl/\1update~\2~.html', url)" \
		https://magnolia1-frontend1-prod.vpro.nl/3v12/sitemap.xml \
		3voor12

human:
	../check_with_sitemap.py \
		-e prod --http_to_https \
		--clean \
		--target_directory ~/integrity-check-results \
		--post_process "lambda url: re.sub(r'^https://www.human.nl/speel[~\.](.*?)[~\.](.*)', r'https://www.human.nl/speel~\1~.html', url)" \
		https://magnolia1-frontend1-prod.vpro.nl/human/sitemap.xml \
		human

clean:
	rm -f /tmp/*.p ~/integrity-check-results/*.txt
