#!/usr/bin/perl

use Text::ParseWords;

my ($date) = `date +\"%Y%m%d\"`;
chomp($date); 

open (DATA, "/home/vjohnson/data/svcdata3.csv") || warn "Could Not Open input file";
open (OUTFILE, ">/home/vjohnson/data/$date-SVC-Report.csv") || warn "Could not open output file";

print OUTFILE "date,svc_name,id,name,status,mdisk_count,vdisk_count,capacity,extent_size,free_capacity,virtual_capacity,used_capacity,real_capacity,overallocation,warning,easy_tier,easy_tier_status,compression_active,compression_virtual_capacity,compression_compressed_capacity,compression_uncompressed_capacity\n";
while (<DATA>) {
	chomp($_);
	print OUTFILE parse_line($_);
}

exit 0; 

sub parse_csv {
	return quotewords (",", 0, $_[0]);
}

sub parse_line {
	#print $_[0];
	my (@fields) = parse_csv($_[0]);
	my ($returnval) = "";
	for ($i = 0; $i < @fields; $i++) {
		if ($i > 0) {
			$returnval = $returnval.",";
		}
		if ( ($i == 7)||($i == 9)||($i == 10)||($i == 11)||($i == 12) ) {
			$fields[$i]=$fields[$i] / 1073741824;
		}  	
		#print "$i : $fields[$i]\n";
		$returnval = $returnval.$fields[$i];
		#print "$returnval\n";
	}
	return "$returnval\n";
}
