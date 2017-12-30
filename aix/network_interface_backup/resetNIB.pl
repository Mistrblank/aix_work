#!/usr/bin/perl -w

##This script is meant to be run AT the unix host and as root

# The script determines all of the etherchannels on the host and then determines
# if the adapter is operating on the primary or backup adapter
# if the adapter is running on the backup adapter it makes an attempt to swap
# back to the primary adapter, there is no guarantee of state however or attempt
# to force back to the primary adapter.  

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
