while true; do
ps --pid 8615 -o pid=,%mem=,vsz=,rss= >> python.log
sleep 1
done