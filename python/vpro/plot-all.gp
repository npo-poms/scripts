load 'plot-settings.gp'

profiles="vpro-predictions human 3voor12 npodoc vprobroadcast gids"
set output destdir.'plots/plot-all.svg'
plot for [profile in profiles] \
     destdir.profile.'.not-in-api.data' using 1:2 with linespoints title profile." not in api", \
     for [profile in profiles] \
     destdir.profile.'.not-in-sitemap.data' using 1:2 with linespoints title profile." not in sitemap"
