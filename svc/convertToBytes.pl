#!/usr/bin/perl

use Text::ParseWords;

open (DATA, "./svcdata2.csv") || warn "Could Not Open input file";
open (OUTFILE, ">./svcdata3.csv") || warn "Could not open output file";

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
		if (substr($fields[$i], -2) eq "TB") {
			substr($fields[$i], -2) = "";
			$fields[$i]=$fields[$i] * 1099511627776;
		}  elsif (substr($fields[$i], -2) eq "GB") {
			substr($fields[$i], -2) = "";
			$fields[$i]=$fields[$i] * 1073741824;
		}  elsif (substr($fields[$i], -2) eq "MB") {
			substr($fields[$i], -2) = "";
			$fields[$i]=$fields[$i] * 1048576;
		}
		#print "$i : $fields[$i]\n";
		$returnval = $returnval.$fields[$i];
		#print "$returnval\n";
	}
	return "$returnval\n";
}
