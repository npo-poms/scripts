load 'plot-settings.gp'

set output destdir.'plots/plot-all.png'
plot \
     destdir.'vpro-predictions.not-in-api.data' using 1:2 with lines title "vpro not in api", \
     destdir.'vpro-predictions.not-in-sitemap.data' using 1:2 with lines title "vpro not in sitemap", \
     destdir.'human.not-in-api.data' using 1:2 with lines title "human not in api", \
     destdir.'human.not-in-sitemap.data' using 1:2 with lines title "human not in sitemap", \
     destdir.'3voor12.not-in-api.data' using 1:2 with lines title "3voor12 not in api", \
     destdir.'3voor12.not-in-sitemap.data' using 1:2 with lines title "3voor12 not in sitemap"