set xdata time
set timefmt '%Y-%m-%dT%H'

set term png
set output dest
plot file  using 1:2 with lines title title