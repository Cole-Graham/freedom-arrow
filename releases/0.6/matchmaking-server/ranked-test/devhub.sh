#!/bin/sh
# start|stop the ranked dev hub on 8652 (test copy only; the live hub is faqueue.service on 8651)
case "$1" in
start) FAQUEUE_URL=http://127.0.0.1:8652 FAQUEUE_RANKED_DIR=/tmp/heli3/ranked-test nohup /home/sam/tars/work/ba-dev/toolkit/tools/dotnet.sh /tmp/heli3/faq-dev-out/FAQueue.dll > /tmp/heli3/faq-dev.log 2>&1 & echo $! > /tmp/heli3/devhub.pid ;;
stop) for p in $(ps -eo pid,cmd | awk '/faq-dev-out\/FAQueue.dll/ && !/awk/ && !/devhub/ {print $1}'); do kill $p; done ;;
esac
