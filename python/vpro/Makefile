
check := ./check_with_sitemap_vpro.py
magnolia1 := https://magnolia1-frontend1-prod.vpro.nl/
target := $(HOME)/integrity-check-results
reportdir := $(target)/reports/`date +'%FT%H'`
lastmonth := $(shell python3 -c 'from datetime import datetime, timedelta; print((datetime.now() - timedelta(days=31)).strftime("%Y-%m-%dT%H"))')
now := $(shell python3 -c 'from datetime import datetime, timedelta; print((datetime.now()).strftime("%Y-%m-%dT%H"))')

docker_image := mihxil/npo-vpro-check:latest

jmx_url := localhost:5000
jmx_binary := ''
resolve := false
get_check := true
tunnel := false

ifeq (true, $(resolve))
   extra_args := --delete --jmx_url $(jmx_url) --target_directory $(target) --jmxterm_binary $(jmx_binary)
   ifeq (false, $(get_check))
      extra_args := --no_get_check $(extra_args)
   endif
   ifeq (true, $(tunnel))
      extra_args := --tunnel $(extra_args)
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



.PHONY: all all_sites vpro 3voor12 human npodoc vprobroadcast  gids report clean plots

all: clean all_sites plots
all_sites: vpro 3voor12 human npodoc vprobroadcast gids


help:     ## Show this help.
	@sed -n 's/^##//p' $(MAKEFILE_LIST)
	@grep -E '^[/%a-zA-Z._-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
	@printf "\nCommon arguments for targets are:\n\
	   resolve=true Will via page api, and via jmx try to correct differences\n\
	   get_check=false To speed up the run you may skip the HEAD checks before deleting from api\n\
	   tunnel=true  Also set up the tunnel needed for JMX\n\
	   clean=false  Will not clean the pickle databases before runs\n\
	   as_now=true  After a correction run, you may check again with this\n\
	   jmx_url=$(jmx_url)  You may override the connection settings for jmx\n\
	   reportdir=$(reportdir) Where reports are to be generated\n\
	   docker_image=$(docker_image)\
	"

plots: report $(target)/plots/plot-all.svg   ## After running the scripts, generate plots form that, and combine everying in one plot too.

report:  ## Show an abstract of the reports
	@for f in `find $(target) -maxdepth 2 -type f '(' -iname 'report.*.txt' -or -iname 'done.*.txt' -or -iname 'todo.*.txt' ')'`; do wc -l  $$f ; done
	@mkdir -p $(reportdir)
	@cp $(target)/report.*.txt $(reportdir)

vpro:    ## Perform checks for vpro.nl.
	$(check) \
		-e prod --http_to_https \
		$(extra_args) \
		--post_process "lambda url: re.sub(r'^https://www.vpro.nl/speel[~\.](.*?)[~\.](.*)', r'https://www.vpro.nl/speel~\1~.html', url)" \
		$(magnolia1)/vpronl/sitemap.xml \
		vpro-predictions


gids:   ## Perform checks for vprogids.nl
	$(check) \
		-e prod \
		$(extra_args) \
		--post_process_api "lambda url: None if url.startswith('https://www.vprogids.nl/cinema/personen/persoon~') else url" \
		$(magnolia1)/gids/sitemap.xml \
		vprocinema


3voor12:  ## Perform checks for 3voor12
	$(check) \
		-e prod --http_to_https \
		$(extra_args) \
		--post_process "lambda url: re.sub(r'^https://3voor12.vpro.nl(.*)/update[~\.](.*?)[~\.](.*)', r'https://3voor12.vpro.nl/update~\2~.html', url)" \
		$(magnolia1)/3v12/sitemap.xml \
		3voor12

human:   ## Perform checks for human.nl
	$(check) \
		-e prod --http_to_https \
		$(extra_args) \
		$(magnolia1)/human/sitemap.xml \
		human



npodoc:   ## Perform checks for 2doc.nl
	$(check) \
		-e prod --http_to_https \
		$(extra_args) \
		--post_process "lambda url: re.sub(r'^https://www.2doc.nl/speel[~\.](.*?)[~\.](.*)', r'https://www.2doc.nl/speel~\1~.html', url)" \
		$(magnolia1)/npodoc/sitemap.xml \
		npodoc

vprobroadcast:  ## Perform checks for vprobroadcast.com
	$(check) \
		-e prod  \
		$(extra_args) \
		$(magnolia1)/international/sitemap.xml \
		vprobroadcast



%-plot:
	mkdir -p $(target)/plots
	cd $(target) ; for i in `ls reports/*/report.$*.in_sitemap*.txt`; do wc -l $$i  ; done | awk '{print $$2"/"$$1}' | awk -F '/' '{print $$2" "$$4}' > $(target)/$*.not-in-api.data || true
	cd $(target) ; for i in `ls reports/*/report.$*.in_api*.txt`; do wc -l $$i  ; done | awk '{print $$2"/"$$1}' | awk -F '/' '{print $$2" "$$4}' > $(target)/$*.not-in-sitemap.data || true
	gnuplot -e "xstart='$(lastmonth)';xstop='$(now)';file='$(target)/$*.not-in-api.data';title='$* not in api';dest='$(target)/plots/$*-not-in-api.svg'" plot.gp  || true
	gnuplot -e "xstart='$(lastmonth)';xstop='$(now)';file='$(target)/$*.not-in-sitemap.data';title='$* not in sitemap';dest='$(target)/plots/$*-not-in-sitemap.svg'" plot.gp || true


$(target)/plots/plot-all.svg: vpro-predictions-plot human-plot 3voor12-plot npodoc-plot vprobroadcast-plot vprocinema-plot
	echo "Creating $@"
	gnuplot -e "xstart='$(lastmonth)';xstop='$(now)';destdir='$(target)/'" plot-all.gp


docker:  ## Builds and pushes docker image
	docker build -t $(docker_image)  .
	docker push $(docker_image)

clean:   ## remove all results, clean run
	rm -rf $(target)/plots/*
	rm -f $(target)/*.p $(target)/*.txt
