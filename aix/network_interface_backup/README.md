# Network Interface Tools

resetNB.pl

This script was originally created to provide a means of identifying all Network Interface Backup adapters on a host and if they are currently on their backup adapter, switch them back to the primary adapter designated.  What we learned was on some versions of AIX with some hardware, automatic failback would not trigger.  

This code was written a long time ago.  It could very much use some modularization by making some of repeated portions of the code into function calls.  It may also be less prudent to use this today, I don't know that I would even recommend Network Interface Backup over Share Ethernet Failover configurations which are far simpler to manage, particularly in large scale deployments.  It would also be helpful if this code had a "report mode".  


