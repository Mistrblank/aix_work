#!/usr/bin/perl -w

##This script is meant to be run AT the unix host.  

my(@ethchannel_list)=`lsdev | grep EtherChannel | awk '{print \$1}'`;
my($ethChanState)="";
my($ethChanConfigLocation)="/usr/lib/methods/ethchan_config -f ";
foreach $ethchannel (@ethchannel_list) {
        substr($ethchannel, 2, 1) = "" ;
	chomp($ethchannel);
	($ethChanState) = `netstat -v $ethchannel | grep Active | awk '{print \$3}'`;
	chomp($ethChanState);
	print "$ethchannel:$ethChanState\n"; 
	if ("backup" eq $ethChanState) {
		##We have a match for backup adapter, run the appropriate command; 	
		print "Attempting to swap to primary adapter on interface $ethchannel.\n";
		system("$ethChanConfigLocation $ethchannel");
	} elsif ("primary" eq $ethChanState) {
		##We're on the primary adapter, do nothing
		##print "active\n";	
	} else {
		##Response was not recognized
		print "Unrecognizable state response on $ethchannel.";
	}
}
exit 0;

