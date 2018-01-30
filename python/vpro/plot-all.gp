load 'plot-settings.gp'

profiles="vpro-predictions human 3voor12"
set output destdir.'plots/plot-all.png'
plot for [profile in profiles] \
     destdir.profile.'.not-in-api.data' using 1:2 with linespoints title profile." not in api", \
     for [profile in profiles] \
     destdir.profile.'.not-in-sitemap.data' using 1:2 with linespoints title profile." not in sitemap"
