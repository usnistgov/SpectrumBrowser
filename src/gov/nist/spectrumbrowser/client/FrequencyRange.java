/*
* Conditions Of Use 
* 
* This software was developed by employees of the National Institute of
* Standards and Technology (NIST), and others. 
* This software has been contributed to the public domain. 
* Pursuant to title 15 Untied States Code Section 105, works of NIST
* employees are not subject to copyright protection in the United States
* and are considered to be in the public domain. 
* As a result, a formal license is not needed to use this software.
* 
* This software is provided "AS IS."  
* NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
* OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
* AND DATA ACCURACY.  NIST does not warrant or make any representations
* regarding the use of the software or the results thereof, including but
* not limited to the correctness, accuracy, reliability or usefulness of
* this software.
*/
package gov.nist.spectrumbrowser.client;

class FrequencyRange {
	long minFreq;
	long maxFreq;
	String sys2detect;

	public FrequencyRange(String sys2detect, long minFreq, long maxFreq) {
		this.minFreq = minFreq;
		this.maxFreq = maxFreq;
		this.sys2detect = sys2detect;
	}
	
	public String getBandName() {
		return sys2detect + ":" + minFreq + ":" + maxFreq;
	}

	@Override
	public boolean equals(Object that) {
		FrequencyRange thatRange = (FrequencyRange) that;
		return this.minFreq == thatRange.minFreq
				&& this.sys2detect.equals(thatRange.sys2detect)
				&& this.maxFreq == thatRange.maxFreq;
	}

	@Override
	public int hashCode() {
		return (Long.toString(maxFreq + minFreq) + sys2detect).hashCode();
	}

	@Override
	public String toString() {
		return sys2detect + " "
				+ Double.toString((double) minFreq / 1000000.0) + " MHz - "
				+ Double.toString((double) (maxFreq / 1000000.0)) + " MHz";
	}
	
}