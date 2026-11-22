#!/bin/sh
# start|stop the ranked dev hub on 8652 under /hubs/test (test copy only; the live hub is faqueue.service on 8651).
# FAQUEUE_RANKED_ALL=1 makes the unchanged client's 1v1 search ranked 1v1 and its 2v2-5v5 searches the ranked team queue.
D=${DEVHUB_DIR:-/tmp/heli3}
case "$1" in
start) FAQUEUE_URL=http://127.0.0.1:8652 FAQUEUE_PREFIX=/hubs/test FAQUEUE_RANKED_ALL=1 FAQUEUE_RANKED_DIR=$D/ranked-test nohup /home/sam/tars/work/ba-dev/toolkit/tools/dotnet.sh $D/faq-dev-out/FAQueue.dll > $D/faq-dev.log 2>&1 & echo $! > $D/devhub.pid ;;
stop) for p in $(ps -eo pid,cmd | awk '/faq-dev-out\/FAQueue.dll/ && !/awk/ && !/devhub/ {print $1}'); do kill $p; done ;;
esac
