
check := ./check_with_sitemap_vpro.py
magnolia1 := https://magnolia1-frontend1-prod.vpro.nl/
target := $(HOME)/integrity-check-results
reportdir := $(target)/reports/`date +'%FT%H'`
lastmonth := $(shell python3 -c 'from datetime import datetime, timedelta; print((datetime.now() - timedelta(days=31)).strftime("%Y-%m-%dT%H"))')
now := $(shell python3 -c 'from datetime import datetime, timedelta; print((datetime.now()).strftime("%Y-%m-%dT%H"))')


jmx_url := localhost:5000
resolve := false
get_check := true

ifeq (true, $(resolve))
   extra_args := --delete --no_get_check --jmx_url $(jmx_url) --target_directory $(target)
   ifeq (false, $(get_check))
      extra_args := --no_get_check $(target)
   endif
else
   extra_args := --target_directory $(target)
endif

clean := true
ifeq (true, $(clean))
   extra_args := --clean $(extra_args)
endif

as_now := false
ifeq (true, $(as_now))
   extra_args := --api_as_now $(extra_args)
endif

.PHONY: vpro 3voor12 human npodoc vprobroadcast  gids report clean plots

all: clean vpro 3voor12 human npodoc vprobroadcast gids plots

plots: report $(target)/plots/plot-all.png


report:
	@for f in `find $(target) -maxdepth 2 -type f '(' -iname 'report.*.txt' -or -iname 'done.*.txt' -or -iname 'todo.*.txt' ')'`; do wc -l  $$f ; done
	@mkdir -p $(reportdir)
	@cp $(target)/report.*.txt $(reportdir)

vpro:
	$(check) \
		-e prod --http_to_https \
		$(extra_args) \
		--post_process "lambda url: re.sub(r'^https://www.vpro.nl/speel[~\.](.*?)[~\.](.*)', r'https://www.vpro.nl/speel~\1~.html', url)" \
		$(magnolia1)/vpronl/sitemap.xml \
		vpro-predictions


gids:
	$(check) \
		-e prod \
		$(extra_args) \
		--post_process_api "lambda url: None if url.startswith('https://www.vprogids.nl/cinema/personen/persoon~') else url" \
		$(magnolia1)/gids/sitemap.xml \
		vprocinema


3voor12:
	$(check) \
		-e prod --http_to_https \
		$(extra_args) \
		--post_process "lambda url: re.sub(r'^https://3voor12.vpro.nl(.*)/update[~\.](.*?)[~\.](.*)', r'https://3voor12.vpro.nl/update~\2~.html', url)" \
		$(magnolia1)/3v12/sitemap.xml \
		3voor12

human:
	$(check) \
		-e prod --http_to_https \
		$(extra_args) \
		$(magnolia1)/human/sitemap.xml \
		human



npodoc:
	$(check) \
		-e prod --http_to_https \
		$(extra_args) \
		--post_process "lambda url: re.sub(r'^https://www.2doc.nl/speel[~\.](.*?)[~\.](.*)', r'https://www.2doc.nl/speel~\1~.html', url)" \
		$(magnolia1)/npodoc/sitemap.xml \
		npodoc

vprobroadcast:
	$(check) \
		-e prod  \
		$(extra_args) \
		$(magnolia1)/international/sitemap.xml \
		vprobroadcast





%-plot:
	mkdir -p $(target)/plots
	cd $(target) ; for i in `ls reports/*/report.$*.in_sitemap*.txt`; do wc -l $$i  ; done | awk '{print $$2"/"$$1}' | awk -F '/' '{print $$2" "$$4}' > $(target)/$*.not-in-api.data
	cd $(target) ; for i in `ls reports/*/report.$*.in_api*.txt`; do wc -l $$i  ; done | awk '{print $$2"/"$$1}' | awk -F '/' '{print $$2" "$$4}' > $(target)/$*.not-in-sitemap.data
	gnuplot -e "xstart='$(lastmonth)';xstop='$(now)';file='$(target)/$*.not-in-api.data';title='$* not in api';dest='$(target)/plots/$*-not-in-api.svg'" plot.gp
	gnuplot -e "xstart='$(lastmonth)';xstop='$(now)';file='$(target)/$*.not-in-sitemap.data';title='$* not in sitemap';dest='$(target)/plots/$*-not-in-sitemap.svg'" plot.gp


$(target)/plots/plot-all.png: vpro-predictions-plot human-plot 3voor12-plot npodoc-plot vprobroadcast-plot
	gnuplot -e "xstart='$(lastmonth)';xstop='$(now)';destdir='$(target)/'" plot-all.gp



clean:
	rm -rf $(target)/plots/*
	rm -f $(target)/*.p $(target)/*.txt
