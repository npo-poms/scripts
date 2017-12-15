
check := ../check_with_sitemap.py
magnolia1 := https://magnolia1-frontend1-prod.vpro.nl/
target := ~/integrity-check-results
reportdir = $(target)/reports/`date +'%FT%H'`

.PHONY: vpro 3voor12 human vpro-clean-api 3voor12-clean-api human-clean-api report clean

all: clean vpro 3voor12 human report


report:
	@for f in `find $(target) -type f '(' -iname 'report.*.txt' -or -iname 'done.*.txt' -or -iname 'todo.*.txt' ')'`; do wc -l  $$f ; done
	@mkdir -p $(reportdir)
	@cp $(target)/report.*.txt $(reportdir)

vpro:
	$(check) \
		-e prod --http_to_https \
		--clean \
		--target_directory $(target) \
		--post_process "lambda url: re.sub(r'^https://www.vpro.nl/speel[~\.](.*?)[~\.](.*)', r'https://www.vpro.nl/speel~\1~.html', url)" \
		$(magnolia1)/vpronl/sitemap.xml \
		vpro-predictions


3voor12:
	$(check) \
		-e prod --http_to_https \
		 --clean \
		--target_directory $(target) \
		--post_process "lambda url: re.sub(r'^https://3voor12.vpro.nl(.*)/update[~\.](.*?)[~\.](.*)', r'https://3voor12.vpro.nl/update~\2~.html', url)" \
		$(magnolia1)/3v12/sitemap.xml \
		3voor12

human:
	$(check) \
		-e prod --http_to_https \
		--clean \
		--target_directory $(target) \
		--post_process "lambda url: re.sub(r'^https://www.human.nl/speel[~\.](.*?)[~\.](.*)', r'https://www.human.nl/speel~\1~.html', url)" \
		$(magnolia1)/human/sitemap.xml \
		human


clean-api: vpro-clean-api 3voor12-clean-api human-clean-api

vpro-clean-api:
	$(check) --use_database --target_directory $(target) -D $(magnolia1)/vpronl/sitemap.xml vpro-predictions


3voor12-clean-api:
	$(check) --use_database --target_directory $(target) -D $(magnolia1)/3v12/sitemap.xml 3voor12

human-clean-api:
	$(check) --use_database --target_directory $(target) -D $(magnolia1)/human/sitemap.xml human


clean:
	rm -f $(target)/*.p $(target)/*.txt
