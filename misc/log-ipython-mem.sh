while true; do
ps -C ipython -o pid=,%mem=,vsz= >> ipython.log
sleep 1
done