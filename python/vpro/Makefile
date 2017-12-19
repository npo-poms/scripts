
check := ../check_with_sitemap.py
magnolia1 := https://magnolia1-frontend1-prod.vpro.nl/
target := $(HOME)/integrity-check-results
reportdir = $(target)/reports/`date +'%FT%H'`

.PHONY: vpro 3voor12 human vpro-clean-api 3voor12-clean-api human-clean-api report clean

all: clean vpro 3voor12 human report


report:
	@for f in `find $(target) -maxdepth 2 -type f '(' -iname 'report.*.txt' -or -iname 'done.*.txt' -or -iname 'todo.*.txt' ')'`; do wc -l  $$f ; done
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


vpro-plot:
	cd $(target) ; for i in `ls reports/*/report.vpro-predictions.in_sitemap*.txt`; do wc -l $$i  ; done | awk '{print $$2"/"$$1}' | awk -F '/' '{print $$2","$$4}' > $(target)/gnuplot.vpro.toolittle.data
	cd $(target) ; for i in `ls reports/*/report.vpro-predictions.in_api*.txt`; do wc -l $$i  ; done | awk '{print $$2"/"$$1}' | awk -F '/' '{print $$2","$$4}' > $(target)/gnuplot.vpro.toomuch.data
	gnuplot -e "files='$(target)/gnuplot.vpro'" plot.gp




clean:
	rm -f $(target)/*.p $(target)/*.txt
